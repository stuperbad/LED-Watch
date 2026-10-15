/* main.c - the watch firmware for the AVR128DB48: connects the portable core (watch.c) to the hardware.
 *
 * THE LOOP, in plain words
 * ------------------------
 *  1. Sleep until something happens: the real-time clock's periodic interrupt, a button, or the accelerometer.
 *       display ON  : the periodic interrupt comes 64 times a second (every 15.6 ms), the CPU naps in "idle" sleep between them, the LED scan keeps running
 *       display OFF : the periodic interrupt comes once a second; the chip sleeps in "standby" (a few microamps) and only wakes to count time, or at once
 *                     when a button is pressed or the accelerometer reports motion
 *  2. Read the inputs: the two buttons (debounced), the accelerometer (milli-g), the battery voltage, the BAT_OK pin.
 *  3. Hand them, with the exact number of milliseconds that passed according to the crystal, to watch_step() - the core decides everything
 *     (modes, games, whether the display should be on, what to draw).
 *  4. Give the core's picture and scan plan to the LED driver (matrix.c).
 *  5. Decide how fast to run next: fast while the display is on or a button is held or a motion is being classified, slow otherwise.
 *
 * MOTION WHILE THE DISPLAY IS OFF: the accelerometer sleeps at a low sample rate and raises its interrupt pin when it feels a movement. We then run the fast
 * loop for about 0.7 s so the core can look at the samples: it decides whether this was a wrist raise (the watch ends up face up), a shake, or a tap, and wakes
 * the display or goes back to sleep.
 *
 * NOT YET DONE (see README): saving settings to EEPROM, the solar/charging readings, calibration of axis directions and thresholds on the real board.
 */
#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <string.h>
#include "../watch.h"
#include "hw_config.h"
#include "hw_pure.h"
#include "matrix.h"
#include "clock.h"
#include "buttons.h"
#include "buzzer.h"
#include "vbat.h"
#include "i2c.h"
#include "imu.h"
#include "matrix_map.h"
#include "hwmap.h"
#include "ledmap.h"

static watch_io_t io;
static debounce_t deb;
static raise_t raise;
static uint8_t imu_ok;
static uint8_t fast = 1, imu_is_awake = 1;
static int32_t motion_ms;                     /* time left in the fast loop after the accelerometer reported motion */

/* Pins nobody drives would float, and a floating input with its input buffer on can draw current. Switch the buffers off on every unused pin of the
 * 48-pin chip (ports A-F). The pins the design uses are set up afterwards by their own init functions. PF0/PF1 (crystal) and PF6 (reset) are left alone. */
static void unused_pins_off(void) {
    static PORT_t *const P[6] = { &PORTA, &PORTB, &PORTC, &PORTD, &PORTE, &PORTF };
    static const uint8_t present[6] = { 0xFF, 0x3F, 0xFF, 0xFF, 0x0F, 0x3C };       /* pins that exist (PF: only PF2..PF5 are free to configure) */
    uint8_t used[6] = {
        (uint8_t)(MATRIX_ALL_ROWS[0] | MATRIX_ALL_COLS[0] | (1u << HW_SDA_BIT) | (1u << HW_SCL_BIT)),    /* the I2C pins keep their input buffer */
        (uint8_t)(MATRIX_ALL_ROWS[1] | MATRIX_ALL_COLS[1] | (1u << HW_BUZ_A_BIT) | (1u << HW_BUZ_B_BIT)),   /* the buzzer pins are outputs */
        (uint8_t)(MATRIX_ALL_ROWS[2] | MATRIX_ALL_COLS[2]),
        (uint8_t)(MATRIX_ALL_ROWS[3] | MATRIX_ALL_COLS[3]),
        (uint8_t)((1u << HW_BTN1_BIT) | (1u << HW_BTN2_BIT) | (1u << HW_IMU_INT_BIT) | (1u << HW_BAT_OK_BIT)), 0 };
    for (uint8_t p = 0; p < 6; p++)
        for (uint8_t b = 0; b < 8; b++)
            if ((present[p] >> b & 1) && !(used[p] >> b & 1)) (&P[p]->PIN0CTRL)[b] = PORT_ISC_INPUT_DISABLE_gc;
}

static void wait_for_event(uint8_t light) {
    set_sleep_mode(light ? SLEEP_MODE_IDLE : SLEEP_MODE_STANDBY);
    cli();
    if (!clock_tick_flag && !pin_event) { sleep_enable(); sei(); sleep_cpu(); sleep_disable(); }   /* checked with interrupts off: a wake-up cannot slip between the check and the sleep */
    sei();
}

/* Power-on self-test shown on the seven indicator LEDs (left to right SET TMR ALM BAT FUN CFG LCK) for 2 seconds, so the first bring-up needs no serial cable or debugger:
 *   SET lit = the 32 kHz crystal started        TMR lit = the accelerometer answered        BAT lit = BAT_OK pin is high (battery fine)
 *   FUN lit = supply voltage reads above 3.0 V   CFG lit = supply voltage reads above 3.6 V   ALM and LCK are not used (a short beep also confirms the piezo)
 * A missing SET means the watch is timing itself from the inaccurate internal oscillator. */
static void boot_diag(uint8_t crystal, uint8_t imu_found, uint8_t bat_ok, uint16_t vdd_mv) {
    uint8_t ok[7] = { crystal, imu_found, 0, bat_ok, (uint8_t)(vdd_mv > 3000), (uint8_t)(vdd_mv > 3600), 0 };      /* index = MODE_LED index = position on the face */
    static watch_scan_t sc; static uint8_t fb[WATCH_ROWS * WATCH_COLS];
    memset(&sc, 0, sizeof sc); memset(fb, 0, sizeof fb);
    for (uint8_t i = 0; i < 7; i++) if (ok[i]) { led_pos_t l = MODE_LED[i]; fb[l.row * WATCH_COLS + l.col] = 255; sc.slot[sc.n].row = l.row; sc.slot[sc.n].cols = (uint16_t)(1u << l.col); sc.n++; }
    sc.m = 1; sc.on_q16 = 16000;                                    /* about 25 % of each slot: bright enough to see, gentle on the battery */
    if (!sc.n) { sc.n = 1; sc.slot[0].row = MODE_LED[6].row; sc.slot[0].cols = 0; }   /* nothing OK: keep the display off (an empty slot lights nothing) */
    matrix_update(&sc, fb);
    uint32_t t = 0; (void)clock_elapsed_ms();
    buzzer_set(4000);                                                /* a 150 ms beep proves the piezo and its drive */
    while (t < 2000) { wait_for_event(1); if (clock_tick_pending()) t += clock_elapsed_ms(); pin_event = 0; if (t >= 150) buzzer_set(0); }
    buzzer_set(0);
    matrix_off();
}

int main(void) {
    unused_pins_off();
    clock_init();
    inputs_init();
    matrix_init();
    buzzer_init();                                  /* after unused_pins_off(): PB4/PB5 are outputs */
    vbat_init();
    i2c_init();
    imu_ok = imu_init();
    uint16_t vdd_mv = vbat_read_mv();
    sei();
    boot_diag(clock_crystal_ok(), imu_ok, bat_ok_pin(), vdd_mv);
    watch_init(((uint32_t)clock_seed() << 16) ^ vdd_mv ^ 1UL);

    memset(&io, 0, sizeof io);
    io.ax = 0; io.ay = 0; io.az = 1000; io.vdd_mv = vdd_mv; io.bat_ok = 1; io.ambient = 50;
    sei();
    (void)clock_elapsed_ms();
    uint32_t vdd_age = 0;

    for (;;) {
        wait_for_event(fast);
        uint8_t tick = clock_tick_pending();
        uint8_t pins; cli(); pins = pin_event; pin_event = 0; sei();
        if (!tick && !pins) continue;
        uint32_t ms = clock_elapsed_ms();
        if (ms == 0) continue;
        if (ms > 2000) ms = 2000;

        /* ---- inputs ---- */
        io.btn = debounce_step(&deb, buttons_raw());
        io.tap = io.ff = 0; io.wake_strength = 0;
        uint8_t imu_ev = 0;
        cli(); uint8_t imu_pin = imu_int_event; imu_int_event = 0; sei();
        if (imu_ok && imu_pin) {
            imu_ev = imu_events();                                      /* also clears the sensor's latched interrupt */
            if (imu_ev & IMU_EV_TAP2) io.tap = 1;
            if (imu_ev & IMU_EV_FF) io.ff = 1;
            if (imu_ev & IMU_EV_WAKEUP) { raise_arm(&raise); motion_ms = MOTION_WINDOW_MS; }
        }
        if (fast && imu_ok) {                                           /* samples are only worth reading while the loop is fast */
            int16_t x, y, z;
            if (imu_read_mg(&x, &y, &z)) {
                io.ax = x; io.ay = y; io.az = z;
                int16_t r = raise_feed(&raise, x, y, z);
                if (r >= 0) io.wake_strength = (uint8_t)r;
            }
        }
        vdd_age += ms;
        if (vdd_age >= (fast ? VDD_PERIOD_FAST_MS : VDD_PERIOD_SLOW_MS)) { vdd_mv = vbat_read_mv(); vdd_age = 0; }
        io.vdd_mv = vdd_mv; io.soc_pm = soc_from_mv(vdd_mv); io.bat_ok = bat_ok_pin();
        io.solar_mw = 0; io.charging = 0;                               /* not measured yet */

        /* ---- the watch ---- */
        watch_step((uint16_t)ms, ms, &io);
        matrix_update(watch_scan(), watch_fb());
        buzzer_set(watch_awake() ? watch_tone_hz() : 0);                /* a tone only plays while the display is on (the alarm wakes it) */

        /* ---- how fast to run next ---- */
        if (motion_ms > 0) motion_ms -= (int32_t)ms;
        uint8_t want_fast = watch_awake() || motion_ms > 0 || io.btn || pins || buttons_raw();
        if (want_fast != fast) {
            fast = want_fast;
            clock_set_fast(fast);
        }
        if (imu_ok && fast != imu_is_awake) {
            imu_is_awake = fast;
            if (fast) imu_profile_awake();
            else imu_profile_sleep(watch_state()->set[7] == 0);          /* CFG 8 "wake by tap" is on when its value is 0 */
        }
    }
}
