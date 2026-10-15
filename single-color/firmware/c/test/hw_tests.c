/* hw_tests.c - PC tests for the parts of the hardware layer that need no hardware:
 *   the matrix pin map and the slot planner (brightness timing), button debounce, battery maths, time conversion, accelerometer conversion and
 *   raise detection, and the accelerometer start-up register sequence (against a pretend sensor on a fake I2C bus). */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "../watch.h"
#include "../hw/matrix_map.h"
#include "../hw/hw_pure.h"
#include "../hw/hw_config.h"
#include "../hw/imu.h"
#include "../hw/i2c.h"

static int fails = 0, checks = 0;
#define CHECK(cond, msg) do { checks++; if (!(cond)) { fails++; printf("FAIL: %s  (line %d)\n", msg, __LINE__); } } while (0)

/* ---------------- a pretend LIS2DW12 on the I2C bus ---------------- */
static uint8_t regs[256]; static uint8_t whoami = 0x44; static int writes_log[64][2]; static int nwrites;
void i2c_init(void) {}
uint8_t i2c_write_reg(uint8_t a, uint8_t reg, uint8_t v) { if (a != IMU_I2C_ADDR) return 0; regs[reg] = v; if (nwrites < 64) { writes_log[nwrites][0] = reg; writes_log[nwrites][1] = v; nwrites++; } return 1; }
uint8_t i2c_read_regs(uint8_t a, uint8_t reg, uint8_t *buf, uint8_t n) { if (a != IMU_I2C_ADDR) return 0; for (uint8_t i = 0; i < n; i++) buf[i] = (reg + i == 0x0F) ? whoami : regs[reg + i]; return 1; }

static void test_pin_map(void) {
    for (int c = 0; c < 12; c++) {
        uint8_t m[MATRIX_PORTS]; matrix_col_masks((uint8_t)c, m);
        int bits = 0; for (int p = 0; p < MATRIX_PORTS; p++) bits += __builtin_popcount(m[p]);
        CHECK(bits == 1, "each column is exactly one pin");
    }
    for (int r = 0; r < 12; r++) {
        uint8_t m[MATRIX_PORTS]; matrix_row_masks((uint8_t)r, m);
        int bits = 0; for (int p = 0; p < MATRIX_PORTS; p++) bits += __builtin_popcount(m[p]);
        CHECK(bits == 1, "each row is exactly one pin");
    }
    int tot = 0; for (int p = 0; p < MATRIX_PORTS; p++) {
        CHECK((MATRIX_ALL_ROWS[p] & MATRIX_ALL_COLS[p]) == 0, "no pin is both a row and a column");
        tot += __builtin_popcount(MATRIX_ALL_ROWS[p]) + __builtin_popcount(MATRIX_ALL_COLS[p]);
    }
    CHECK(tot == 24, "24 matrix pins in all");
    /* the wiring facts we rely on (from the schematic): ROW0 = PC2, COL0 = PA0 */
    uint8_t m[MATRIX_PORTS];
    matrix_row_masks(0, m); CHECK(m[2] == (1 << 2), "ROW0 is PC2");
    matrix_col_masks(0, m); CHECK(m[0] == (1 << 0), "COL0 is PA0");
    matrix_col_masks(10, m); CHECK(m[2] == (1 << 0), "COL10 is PC0");
}

static void test_slot_timing(void) {
    CHECK(matrix_slot_us(1) == SCAN_SLOT_MAX_US, "one slot: capped length");
    CHECK(matrix_slot_us(3) == SCAN_FRAME_US / 3, "three slots share the frame");
    CHECK(matrix_slot_us(72) == SCAN_SLOT_MIN_US, "72 slots: minimum length");
    for (int n = 1; n <= 72; n++) { uint16_t u = matrix_slot_us((uint8_t)n); CHECK(u >= SCAN_SLOT_MIN_US && u <= SCAN_SLOT_MAX_US, "slot length in range"); }

    /* a slot with columns at different brightness: switch-off times must be proportional to the level */
    uint8_t fb[144]; memset(fb, 0, sizeof fb);
    fb[4 * 12 + 0] = 255; fb[4 * 12 + 3] = 128; fb[4 * 12 + 7] = 64; fb[4 * 12 + 9] = 1;
    matrix_slot_t s; matrix_plan_slot(fb, 4, (1u << 0) | (1u << 3) | (1u << 7) | (1u << 9), 2000, 65536 / 2, &s);   /* full on-time = 1000 us */
    uint8_t rm[MATRIX_PORTS]; matrix_row_masks(4, rm);
    CHECK(memcmp(s.row_clr, rm, MATRIX_PORTS) == 0, "the right row is pulled low");
    CHECK(s.n_events == 4, "all four columns have a timed switch-off (the slot is longer than the full on-time)");
    CHECK(s.ev[0].t <= s.ev[1].t && s.ev[1].t <= s.ev[2].t && s.ev[2].t <= s.ev[3].t, "events sorted by time");
    CHECK(s.ev[0].t == 1000 * 1 / 255 && s.ev[1].t == 1000 * 64 / 255 && s.ev[2].t == 1000 * 128 / 255, "switch-off times are proportional to brightness");
    CHECK(s.ev[3].t == 1000, "a full-level LED stays on for the full on-time (slot_us x duty)");
    /* a column with level 1 is too dim for a 1000 us on-time: 1000*1/255 = 3 us: still scheduled */
    uint8_t any = 0; for (int p = 0; p < MATRIX_PORTS; p++) any |= s.col_set[p]; CHECK(any != 0, "columns are raised");

    /* full on-time == whole slot: no event for full-level LEDs */
    matrix_plan_slot(fb, 4, 1u << 0, 2000, 65535, &s);
    CHECK(s.n_events == 0 || s.ev[0].t >= 1999, "full level with full duty needs no early switch-off");
    /* dim level with tiny duty is dropped rather than flickering */
    fb[4 * 12 + 9] = 1; matrix_plan_slot(fb, 4, 1u << 9, 250, 100, &s);
    uint8_t any2 = 0; for (int p = 0; p < MATRIX_PORTS; p++) any2 |= s.col_set[p]; CHECK(any2 == 0, "an LED too dim for the slot stays off");
}

/* Simulate a whole frame: for every lit LED, add up how many microseconds the plan keeps it on, and compare with the framebuffer level. */
static void test_frame_brightness(void) {
    watch_init(99);
    watch_io_t io; memset(&io, 0, sizeof io); io.az = 1000; io.vdd_mv = 3700; io.soc_pm = 700; io.bat_ok = 1; io.ambient = 50;
    io.btn = 2; for (int i = 0; i < 20; i++) watch_step(10, 10, &io);       /* wake */
    io.btn = 0; for (int i = 0; i < 20; i++) watch_step(10, 10, &io);
    const watch_scan_t *sc = watch_scan(); const uint8_t *fb = watch_fb();
    CHECK(sc->n > 0, "display on has slots");
    uint16_t slot_us = matrix_slot_us(sc->n);
    uint32_t on_us[144]; memset(on_us, 0, sizeof on_us);
    for (int i = 0; i < sc->n; i++) {
        matrix_slot_t s; matrix_plan_slot(fb, sc->slot[i].row, sc->slot[i].cols, slot_us, sc->on_q16, &s);
        for (int c = 0; c < 12; c++) {
            uint8_t cm[MATRIX_PORTS]; matrix_col_masks((uint8_t)c, cm);
            if (!(sc->slot[i].cols >> c & 1)) continue;
            int raised = 0; for (int p = 0; p < MATRIX_PORTS; p++) raised |= (s.col_set[p] & cm[p]) != 0;
            if (!raised) continue;
            uint32_t t = slot_us;
            for (int e = 0; e < s.n_events; e++) { int mine = 0; for (int p = 0; p < MATRIX_PORTS; p++) mine |= (s.ev[e].col_clr[p] & cm[p]) != 0; if (mine) t = s.ev[e].t; }
            on_us[sc->slot[i].row * 12 + c] += t;
        }
    }
    int lit = 0, ok = 1;
    for (int k = 0; k < 144; k++) if (fb[k]) { lit++; if (on_us[k] == 0) ok = 0; }
    CHECK(lit >= 2, "the time screen lights LEDs");
    CHECK(ok, "every lit LED gets some on-time in the frame");
    /* the planned on-time of a full LED equals slot_us * on_q16 */
    for (int k = 0; k < 144; k++) if (fb[k] == 255) CHECK(on_us[k] > 0 && on_us[k] <= slot_us, "full LED on-time within its slot");
}

static void test_inputs_and_math(void) {
    debounce_t d = { 0, 0 };
    CHECK(debounce_step(&d, 1) == 0, "a single sample is not accepted yet");
    CHECK(debounce_step(&d, 1) == 1, "two equal samples are");
    CHECK(debounce_step(&d, 0) == 1, "a glitch to 0 is ignored");
    CHECK(debounce_step(&d, 1) == 1, "and the glitch is forgotten");
    CHECK(debounce_step(&d, 0) == 1 && debounce_step(&d, 0) == 0, "release needs two samples too");

    CHECK(soc_from_mv(2900) == 0 && soc_from_mv(3000) == 0, "empty at 3.0 V");
    CHECK(soc_from_mv(4200) == 1000 && soc_from_mv(4300) == 1000, "full at 4.2 V");
    CHECK(soc_from_mv(3800) == 500, "half at 3.8 V");
    uint16_t prev = 0; int mono = 1; for (uint16_t mv = 2800; mv < 4400; mv += 10) { uint16_t s = soc_from_mv(mv); if (s < prev) mono = 0; prev = s; }
    CHECK(mono, "state of charge never goes down as voltage goes up");

    CHECK(adc_vdd_mv(1639, 1000) >= 4090 && adc_vdd_mv(1639, 1000) <= 4110, "ADC reading 1639 = about 4.1 V");
    CHECK(adc_vdd_mv(1639, 1100) > adc_vdd_mv(1639, 1000), "calibration factor scales the result");

    uint32_t acc = 0, total = 0;
    for (int i = 0; i < 32768; i++) total += ticks_to_ms(1, &acc);
    CHECK(total == 1000, "32768 single ticks make exactly one second");
    acc = 0; CHECK(ticks_to_ms(512, &acc) == 15 && acc != 0, "512 ticks = 15.6 ms: 15 now, the remainder is kept");
    acc = 0; total = 0; for (int i = 0; i < 64; i++) total += ticks_to_ms(512, &acc);
    CHECK(total == 1000, "64 heartbeats of 512 ticks make exactly one second");

    CHECK(imu_raw_to_mg(8192) == 1000 && imu_raw_to_mg(-8192) == -1000, "raw 8192 = +1 g at +-4 g");
    CHECK(imu_raw_to_mg(0) == 0, "zero stays zero");
    int16_t s[3] = { 100, 200, 1000 }, x, y, z; imu_map_axes(s, &x, &y, &z);
    CHECK(x == 100 * IMU_MAP_X_SIGN && z == 1000 * IMU_MAP_Z_SIGN && y == 200 * IMU_MAP_Y_SIGN, "identity axis map by default");
}

static void test_raise(void) {
    raise_t r; int16_t out;
    /* hanging arm (watch facing the body: z ~ 0, y ~ -1000) to face-up (z ~ +900) in 12 samples: a raise */
    raise_arm(&r); out = -1;
    for (int i = 0; i < RAISE_WINDOW_SAMPLES; i++) out = raise_feed(&r, 0, (int16_t)(-1000 + i * 90), (int16_t)(i * 80));
    CHECK(out > 50, "a big swing that ends face-up is a strong raise");
    /* a shake that ends face-up but barely changes the gravity vector: weak */
    raise_arm(&r); out = -1;
    for (int i = 0; i < RAISE_WINDOW_SAMPLES; i++) out = raise_feed(&r, (int16_t)(i % 2 ? 30 : -30), 0, 980);
    CHECK(out >= 0 && out < 10, "a tiny wobble is not a raise");
    /* the same swing but ending face-down: not a raise at all */
    raise_arm(&r); out = -1;
    for (int i = 0; i < RAISE_WINDOW_SAMPLES; i++) out = raise_feed(&r, 0, (int16_t)(-1000 + i * 90), (int16_t)(-i * 80));
    CHECK(out == 0, "ending face-down is not a raise");
    CHECK(raise_feed(&r, 0, 0, 1000) == -1, "not armed: ignores samples");
}

static void test_imu_driver(void) {
    memset(regs, 0, sizeof regs); nwrites = 0; whoami = 0x44;
    CHECK(imu_init() == 1, "init succeeds with a LIS2DW12 present");
    CHECK(regs[0x20] == IMU_AWAKE_CTRL1, "ends with the awake sample rate set (CTRL1)");
    CHECK(regs[0x21] == 0x0C, "BDU + address auto-increment (CTRL2)");
    CHECK(regs[0x25] == 0x10, "+-4 g (CTRL6)");
    CHECK(regs[0x22] == 0x10, "latched interrupts (CTRL3)");
    CHECK((regs[0x32] & 0xE0) == 0x20, "tap enabled on Z only (TAP_THS_Z)");
    CHECK(regs[0x34] & 0x80, "double-tap enabled (WAKE_UP_THS)");
    CHECK((regs[0x34] & 0x3F) == IMU_WAKE_THS, "wake-up threshold programmed");
    CHECK(regs[0x23] == 0x28, "INT1 carries wake-up and double-tap (CTRL4_INT1_PAD_CTRL)");
    CHECK(regs[0x3F] == 0x20, "interrupts enabled (CTRL7)");
    CHECK(writes_log[0][0] == 0x20 && writes_log[0][1] == 0x00, "power-down first while configuring");
    CHECK(writes_log[nwrites - 1][0] == 0x20 && writes_log[nwrites - 1][1] == IMU_AWAKE_CTRL1, "sampling switched on last");
    imu_profile_sleep(0); CHECK(regs[0x20] == IMU_SLEEP_CTRL1_NOTAP, "sleep profile without tap");
    imu_profile_sleep(1); CHECK(regs[0x20] == IMU_SLEEP_CTRL1_TAP, "sleep profile with tap");
    imu_profile_awake(); CHECK(regs[0x20] == IMU_AWAKE_CTRL1, "back to awake");

    /* samples: sensor reports +1 g on Z (raw 8192) */
    regs[0x28] = 0; regs[0x29] = 0; regs[0x2A] = 0; regs[0x2B] = 0; regs[0x2C] = 0x00; regs[0x2D] = 0x20;
    int16_t x, y, z; CHECK(imu_read_mg(&x, &y, &z) && x == 0 && y == 0 && z == 1000 * IMU_MAP_Z_SIGN, "reads +1000 mg on z when flat");
    regs[0x28] = 0x00; regs[0x29] = 0xF0;                        /* X = -4096 = -0.5 g */
    imu_read_mg(&x, &y, &z); CHECK(x == -500 * IMU_MAP_X_SIGN, "negative values decode correctly");
    regs[0x3B] = 0x0A; CHECK(imu_events() == 0x0A, "event bits pass through (double tap + wake-up)");

    whoami = 0x00; CHECK(imu_init() == 0, "init reports a missing / wrong sensor");
}

static void test_buzzer_plan(void) {
    buzzer_plan_t p;
    CHECK(buzzer_plan(4000, F_CPU_HZ, &p) && p.div_idx == 2 && p.per == 249, "4 kHz: DIV4, period 250 clocks = exactly 4000 Hz");
    CHECK(!buzzer_plan(0, F_CPU_HZ, &p), "0 Hz is silence, no plan");
    static const uint16_t tones[] = { 1300, 1500, 1800, 2000, 2200, 2400, 2600, 3000, 3200, 3300, 3500, 3600, 4000, 4200, 4800, 5000, 8000 };
    static const uint16_t DIV[8] = { 1, 2, 4, 8, 16, 64, 256, 1024 };
    for (unsigned i = 0; i < sizeof tones / sizeof tones[0]; i++) {
        int ok = buzzer_plan(tones[i], F_CPU_HZ, &p);
        CHECK(ok && p.per >= 3, "every tone the firmware plays fits the 8-bit timer");
        if (ok) { long f = (long)(F_CPU_HZ / DIV[p.div_idx] / (p.per + 1u)); long err = f > tones[i] ? f - tones[i] : tones[i] - f; CHECK(err * 100 <= tones[i], "frequency within 1 % of the wanted tone"); }
    }
}

int main(void) {
    test_pin_map(); test_slot_timing(); test_buzzer_plan(); test_frame_brightness(); test_inputs_and_math(); test_raise(); test_imu_driver();
    printf("%d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
