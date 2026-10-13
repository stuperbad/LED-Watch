/* watch.c - platform-independent watch logic. Port of firmware/sim/watch_core.js (the behaviour reference).
 *
 * Rules for this file (so it behaves the same on the 16-bit-int AVR and on the PC):
 *   - stdint types only, every multiplication that can exceed 16 bits is done in int32_t / uint32_t;
 *   - no floating point (angles are 16-bit "binary angles": 65536 = one full turn, 0 = 12 o'clock, clockwise);
 *   - 64-bit multiplies only in the light-show code (orbit) and a few rare one-off calls (random numbers).
 */
#include <string.h>
#include <stddef.h>
#include "watch.h"
#include "ledmap.h"            /* generated: HOUR_LED[12], MINUTE_LED[60], SECOND_LED[60], MODE_LED[6] = {row, col} per LED */

/* ------------------------------------------------------------------ constants ---- */
enum { M_TIME, M_SET, M_TMR, M_BAT, M_FUN, M_CFG, M_COUNT };
enum { C_BRI, C_WAKE, C_DUR, C_AUTO, C_SEC, C_RAISE, C_SHAKE, C_TAP, C_BTNW, C_LOCKD, C_COUNT };
enum { G_PART, G_RUN, G_TARGET, G_QD, G_ORBIT, G_RNG, G_PACER, G_SIMON, G_PONG, G_COUNT };
enum { QD_IDLE, QD_WAIT, QD_GO, QD_RESULT };
enum { SM_READY, SM_NEXT, SM_SHOW, SM_INPUT };
enum { PG_READY, PG_PLAY, PG_POINT, PG_OVER };

#define LONG_MS 1000
#define LOCK_MS 2000
#define HOLD_MS 400
#define REPEAT_MS 120
#define MENU_CONFIRM_MS 2500
#define TMR_KEEP_MS 90000UL
#define GAME_IDLE_MS 300000UL
#define MODE_IDLE_MS 15000UL
#define SCORE_CAP 999
#define SHAKE_JERK 3000          /* summed |delta a|, milli-g */
#define ROW_SINK_UA 10000
#define I_REF_UA 1600
#define PONG_Z_Q16 10486         /* 0.16 */
#define PONG_WIN 5

static const int8_t  MODE_IND[M_COUNT]  = { -1, 0, 1, 2, 3, 4 };       /* indicator index per mode; indicator 5 is LCK */
static const uint16_t BRI_Q16[5] = { 3277, 6554, 13107, 19661, 32768 };
static const uint8_t  WAKE_SENS[3] = { 70, 50, 30 };
static const uint16_t DUR_MS[4] = { 2000, 3000, 5000, 10000 };
static const uint8_t  CFG_COUNT[C_COUNT] = { 5, 3, 4, 2, 2, 2, 2, 2, 4, 3 };
static const uint8_t  TENTHS_LED[10] = { 1, 2, 3, 4, 5, 7, 8, 9, 10, 11 };
static const uint8_t  DAYS_IN[12] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

/* ------------------------------------------------------------------ lookup tables ---- */
static const int16_t SIN_Q[65] = { 0, 804, 1608, 2410, 3212, 4011, 4808, 5602, 6393, 7179, 7962, 8739, 9512, 10278, 11039, 11793, 12539, 13279, 14010, 14732, 15446, 16151, 16846, 17530, 18204, 18868, 19519, 20159, 20787, 21403, 22005, 22594, 23170, 23731, 24279, 24811, 25329, 25832, 26319, 26790, 27245, 27683, 28105, 28510, 28898, 29268, 29621, 29956, 30273, 30571, 30852, 31113, 31356, 31580, 31785, 31971, 32137, 32285, 32412, 32521, 32609, 32678, 32728, 32757, 32767 };
static const uint16_t ATAN_Q[65] = { 0, 163, 326, 489, 651, 813, 975, 1136, 1297, 1457, 1617, 1775, 1933, 2090, 2246, 2401, 2555, 2708, 2860, 3010, 3159, 3307, 3453, 3599, 3742, 3884, 4025, 4164, 4302, 4438, 4572, 4705, 4836, 4966, 5094, 5220, 5344, 5467, 5589, 5708, 5826, 5943, 6058, 6171, 6282, 6392, 6500, 6607, 6712, 6815, 6917, 7018, 7117, 7214, 7310, 7405, 7498, 7589, 7679, 7768, 7856, 7942, 8026, 8110, 8192 };
static const uint8_t SOLAR_BAR[31] = { 0, 12, 19, 24, 28, 31, 34, 36, 38, 40, 42, 43, 45, 46, 47, 48, 50, 51, 51, 52, 53, 54, 55, 56, 56, 57, 58, 58, 59, 59, 60 };  /* minute-ring LEDs for 0..30 mW (log scale) */
static const uint8_t RADAR_LVL[7] = { 255, 134, 91, 69, 55, 46, 40 };
static const uint8_t COMET_LVL[8] = { 255, 150, 106, 82, 67, 57, 49, 43 };
static const uint8_t AWARD_LVL[4] = { 255, 128, 85, 64 };
static const int16_t BEAD_K[3] = { 475, 401, 359 };                    /* BAM/s^2 per milli-g on the hour / minute / second ring */
static const uint16_t RING_R_Q8[3] = { 3939, 4657, 5202 };             /* ring radii 15.385 / 18.19 / 20.32 mm in 1/256 mm */

#define BAM_PER_RAD 10430.378
#define RAD(x) ((int32_t)((x) * BAM_PER_RAD + 0.5))                    /* compile-time constant, positive x only */

/* particle modes: damping /s (Q8), bounce (Q8), wall friction (Q8), grain mixing (Q8), pressure, static friction (Q8) */
typedef struct { uint16_t damp, rest, fric, mix; uint8_t press; uint16_t mu; } pmode_t;
static const pmode_t PM[4] = {
    { 384, 13, 10, 77, 0, 77 },       /* sand   */
    { 230, 51, 5, 26, 0, 31 },        /* gravel */
    { 1280, 13, 0, 0, 1, 0 },         /* oil    */
    { 102, 90, 0, 0, 1, 0 } };        /* water  */
#define R_IN_Q8   3555                /* 13.885 mm */
#define R_OUT_Q8  5509                /* 21.52 mm  */
#define PR_Q8     205                 /* 0.8 mm    */

/* ------------------------------------------------------------------ state ---- */
static watch_t W;
static uint8_t fb[WATCH_ROWS * WATCH_COLS];
static watch_scan_t scan;
static const watch_io_t *io;
static uint32_t rng_state = 1;
static int16_t px = 0, py = 0, pz = 1000; static int32_t shake_acc = 0;    /* shake detector history */

const uint8_t *watch_fb(void) { return fb; }
const watch_scan_t *watch_scan(void) { return &scan; }
const watch_t *watch_state(void) { return &W; }
uint8_t watch_awake(void) { return W.awake; }

/* ------------------------------------------------------------------ small helpers ---- */
static uint32_t rnd32(void) { uint32_t x = rng_state; x ^= x << 13; x ^= x >> 17; x ^= x << 5; rng_state = x; return x; }
static uint32_t rnd_n(uint32_t n) { return (uint32_t)(((uint64_t)rnd32() * n) >> 32); }   /* 0 .. n-1, same as floor(random * n) */

static uint32_t isqrt32(uint32_t v) { uint32_t r = 0, b = 1UL << 30; while (b > v) b >>= 2; while (b) { if (v >= r + b) { v -= r + b; r = (r >> 1) + b; } else r >>= 1; b >>= 2; } return r; }

static int16_t sin256(uint8_t i) {
    uint8_t q = i >> 6, j = i & 63;
    switch (q) { case 0: return SIN_Q[j]; case 1: return SIN_Q[64 - j]; case 2: return (int16_t)-SIN_Q[j]; default: return (int16_t)-SIN_Q[64 - j]; }
}
static int16_t sin16(uint16_t a) {                         /* sine of a binary angle, Q15 */
    uint8_t i = (uint8_t)(a >> 8); int16_t s0 = sin256(i), s1 = sin256((uint8_t)(i + 1));
    return (int16_t)(s0 + (((int32_t)(s1 - s0) * (a & 255)) >> 8));
}
static int16_t cos16(uint16_t a) { return sin16((uint16_t)(a + 16384)); }
static uint16_t atan_ratio(uint32_t t15) {                 /* atan of a Q15 ratio 0..1, binary angle 0..8192 */
    uint32_t i = t15 >> 9, f = t15 & 511; uint16_t a0 = ATAN_Q[i > 64 ? 64 : i], a1 = ATAN_Q[i >= 64 ? 64 : i + 1];
    return (uint16_t)(a0 + (((int32_t)a1 - a0) * (int32_t)f >> 9));
}
static uint16_t atan2_bam(int32_t y, int32_t x) {          /* angle of (x, y) counter-clockwise from +x, binary angle */
    uint32_t ax = x < 0 ? (uint32_t)-x : (uint32_t)x, ay = y < 0 ? (uint32_t)-y : (uint32_t)y; uint16_t a;
    if (!ax && !ay) return 0;
    if (ay <= ax) a = atan_ratio((ay << 15) / ax); else a = (uint16_t)(16384 - atan_ratio((ax << 15) / ay));
    if (x < 0) a = (uint16_t)(32768 - a);
    if (y < 0) a = (uint16_t)(-a);
    return a;
}
static int32_t mulq15(int32_t a, int16_t b) { return ((a >> 4) * (int32_t)b) >> 11; }   /* a * b / 32768 for |a| <= 1,000,000 */

static uint8_t ring_len(uint8_t r) { return r == 0 ? 12 : 60; }
static led_pos_t ring_led(uint8_t r, uint8_t k) { return r == 0 ? HOUR_LED[k] : r == 1 ? MINUTE_LED[k] : SECOND_LED[k]; }
static uint8_t ring_k(uint8_t r, uint16_t ang) { uint8_t n = ring_len(r); return (uint8_t)((((uint32_t)ang * n) + 32768UL) >> 16) % n; }
static led_pos_t hour_led(uint8_t n) { return HOUR_LED[n % 12]; }      /* hour LED 1..12 (12 = top) */
static uint8_t in_half(uint8_t r, uint8_t k, uint8_t side) {           /* side 0 = left half, 1 = right half; 12 and 6 o'clock belong to neither */
    int16_t s = sin16((uint16_t)(((uint32_t)k * 65536UL) / ring_len(r)));
    return side ? s > 655 : s < -655;
}

static void put(led_pos_t l, uint8_t lvl) { if (l.row < WATCH_ROWS) { uint8_t *p = &fb[(uint8_t)(l.row * WATCH_COLS + l.col)]; if (lvl > *p) *p = lvl; } }
static void ind(uint8_t i, uint8_t lvl) { put(MODE_LED[i], lvl); }
static void putr(uint8_t r, uint8_t k, uint8_t lvl) { put(ring_led(r, k), lvl); }
static void bar_n(uint8_t r, uint8_t n, uint8_t lvl) { uint8_t len = ring_len(r); if (n > len) n = len; for (uint8_t i = 0; i < n; i++) putr(r, i, lvl); }   /* n LEDs clockwise from 12 */

/* ------------------------------------------------------------------ calendar ---- */
static uint8_t is_leap(uint16_t y) { return (y % 4 == 0 && y % 100 != 0) || y % 400 == 0; }
static uint8_t days_in(uint16_t y, uint8_t m) { return (uint8_t)(DAYS_IN[m - 1] + (m == 2 && is_leap(y) ? 1 : 0)); }
static uint8_t weekday_iso(uint16_t y, uint8_t m, uint8_t d) {          /* Sakamoto; Monday = 1 .. Sunday = 7 */
    static const uint8_t t[12] = { 0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4 };
    if (m < 3) y--;
    uint8_t dow = (uint8_t)(((uint32_t)y + y / 4 - y / 100 + y / 400 + t[m - 1] + d) % 7);   /* 0 = Sunday */
    return (uint8_t)((dow + 6) % 7 + 1);
}
uint8_t watch_weekday_iso(void) { return weekday_iso(W.year, W.month, W.day); }
static void hms(uint8_t *h, uint8_t *m, uint8_t *s) { uint32_t t = (W.rtc_ms / 1000UL) % 86400UL; *h = (uint8_t)(t / 3600); *m = (uint8_t)(t / 60 % 60); *s = (uint8_t)(t % 60); }
void watch_set_time(uint8_t h, uint8_t m, uint8_t s) { W.rtc_ms = ((uint32_t)(h % 24) * 3600UL + (uint32_t)(m % 60) * 60UL + (s % 60)) * 1000UL; }
void watch_set_cfg(uint8_t idx, uint8_t v) { if (idx < C_COUNT && v < CFG_COUNT[idx]) W.set[idx] = v; }
void watch_set_date(uint16_t y, uint8_t mo, uint8_t d) { W.year = y; W.month = mo; W.day = d > days_in(y, mo) ? days_in(y, mo) : d; }
static void next_day(void) { W.day++; if (W.day > days_in(W.year, W.month)) { W.day = 1; W.month++; if (W.month > 12) { W.month = 1; W.year++; } } }

/* ------------------------------------------------------------------ mode / wake logic ---- */
static void game_start(uint8_t g);
static void game_button(uint8_t g, uint8_t b);
static void part_remove(uint8_t n);

static void wake(void) { W.awake = 1; W.idle = 0; W.ind_only = 0; }
static void wake_ind(void) { if (!W.awake) { W.awake = 1; W.ind_only = 1; } W.idle = 0; }   /* light ONLY the LCK LED (lock feedback) */
static uint8_t tmr_keep(void) { return W.mode == M_TMR && (W.tmr_run || W.tmr_el > 0); }
static uint8_t btn_wake_ok(uint8_t i) { uint8_t v = W.set[C_BTNW]; return v == 0 || (v == 1 && i == 0) || (v == 2 && i == 1); }
static void motion_wake(void) { if (!W.awake || W.ind_only) { wake(); if (!tmr_keep()) W.mode = M_TIME; } else W.idle = 0; }
static void to_mode(uint8_t m) {
    W.mode = m; W.idle = 0; W.date_peek = 0; W.peek = 0; W.menu_on = 0;
    if (m == M_SET) W.set_field = 0;
    if (m == M_FUN) W.fun_playing = 0;                              /* entering FUN always shows the game picker */
}
static void menu_open(void) { W.menu_on = 1; W.menu_sel = W.mode; W.menu_from = W.mode; W.menu_t = 0; }
static void menu_confirm(void) { uint8_t m = W.menu_sel; W.menu_on = 0; to_mode(m); }
static void toggle_lock(void) { W.locked = !W.locked; W.lock_flash = 600; W.menu_on = 0; if (W.mode != M_TIME) to_mode(M_TIME); }

static void set_add(void) {
    uint8_t h, m, s; hms(&h, &m, &s);
    switch (W.set_field) {
    case 0: watch_set_time((uint8_t)(h + 1), m, s); break;
    case 1: watch_set_time(h, (uint8_t)(m + 1), s); break;
    case 2: watch_set_time(h, m, (uint8_t)(s + 1)); break;
    case 3: watch_set_date(W.year, (uint8_t)(W.month % 12 + 1), W.day); break;
    case 4: W.day = (uint8_t)(W.day % days_in(W.year, W.month) + 1); break;
    default: W.year = W.year >= 2099 ? 2024 : (uint16_t)(W.year + 1); if (W.day > days_in(W.year, W.month)) W.day = days_in(W.year, W.month); break;
    }
}
static void cfg_change(void) { W.set[W.cfg_sel] = (uint8_t)((W.set[W.cfg_sel] + 1) % CFG_COUNT[W.cfg_sel]); }

static void on_short(uint8_t b) {
    W.idle = 0;
    if (W.menu_on) {                                                 /* Left = one mode left, Right = one mode right (wraps) */
        W.menu_sel = (uint8_t)((W.menu_sel + (b == 1 ? 1 : M_COUNT - 1)) % M_COUNT); W.menu_t = 0; return;
    }
    switch (W.mode) {
    case M_TIME: if (b == 1) { W.date_peek = 2000; W.peek = 0; } break;
    case M_SET: if (b == 0) W.set_field = (uint8_t)((W.set_field + 1) % 6); else set_add(); break;
    case M_TMR:
        if (b == 1) W.tmr_run = !W.tmr_run;
        else if (!W.tmr_run && W.tmr_el > 0) W.tmr_el = 0;
        break;
    case M_BAT: W.bat_view = (uint8_t)((W.bat_view + (b == 1 ? 1 : 2)) % 3); break;
    case M_FUN:
        if (!W.fun_playing) {
            if (b == 0) W.fun_g = (uint8_t)((W.fun_g + 1) % G_COUNT); else { W.fun_playing = 1; game_start(W.fun_g); }
        } else game_button(W.fun_g, b);
        break;
    default: if (b == 0) W.cfg_sel = (uint8_t)((W.cfg_sel + 1) % C_COUNT); else cfg_change(); break;
    }
}
static void on_long(uint8_t b) {
    W.idle = 0;
    if (W.menu_on) { if (b == 0) to_mode(M_TIME); else menu_confirm(); return; }
    if (b == 0) { menu_open(); return; }
    switch (W.mode) {
    case M_TIME: W.peek = 2000; W.date_peek = 0; break;
    case M_SET: set_add(); break;                                     /* then auto-repeats while held */
    case M_TMR: W.tmr_run = 0; W.tmr_el = 0; break;
    case M_FUN:
        if (W.fun_playing && W.fun_g == G_PART) { if (W.pref_sand_mode == 4) W.g.part.bead_w = 0; else part_remove(4); }
        else if (W.fun_playing && W.fun_g == G_PACER) { W.pref_pc_kind ^= 1; W.g.pc.t = 0; W.g.pc.show = 2500; }
        break;
    default: break;
    }
}
static uint16_t long_ms(uint8_t i) { return (i == 1 && W.mode == M_SET) ? HOLD_MS : LONG_MS; }

static void buttons(uint16_t dt) {
    uint8_t down0 = io->btn & 1, down1 = (io->btn >> 1) & 1, both = down0 && down1;
    if (both) {                                                       /* both held: lock / unlock after 2 s, no other action */
        W.both_t += dt; W.b[0].chord = W.b[1].chord = 1;
        if (W.both_t >= 400 && !W.lock_done) wake_ind();               /* LCK blinks while both are held */
        if (W.both_t >= LOCK_MS && !W.lock_done) { W.lock_done = 1; toggle_lock(); wake_ind(); }
    } else if (!down0 && !down1) { W.both_t = 0; W.lock_done = 0; }
    for (uint8_t i = 0; i < 2; i++) {
        button_t *b = &W.b[i]; uint8_t d = i ? down1 : down0, other = i ? down0 : down1;
        if (d && !b->down) {                                          /* press */
            b->down = 1; b->t = 0; b->long_ = 0; b->chord = other; b->rep = 0; b->eat = 0; b->raw = 0;
            if (!W.awake) {
                b->eat = 1;                                           /* a press on a dark watch is never also an action */
                if (W.locked) { if (!b->chord) { wake_ind(); W.lock_flash = 600; } }   /* buttons do not wake a locked watch, they only show LCK */
                else if (btn_wake_ok(i)) wake();
            } else if (W.locked && !b->chord) { b->eat = 1; W.lock_flash = 600; wake_ind(); }
            else if (!b->chord && !W.menu_on && W.mode == M_FUN && W.fun_playing &&
                     (W.fun_g == G_RUN || W.fun_g == G_TARGET || W.fun_g == G_SIMON || W.fun_g == G_PONG)) { game_button(W.fun_g, i); b->raw = 1; }   /* arcade games react on press */
            W.idle = 0;
        } else if (d && b->down) {
            b->t += dt;
            if (!b->eat && !b->chord && !both) {
                if (!b->long_ && b->t >= long_ms(i)) { b->long_ = 1; b->rep = 0; on_long(i); }
                else if (b->long_ && i == 1 && W.mode == M_FUN && W.fun_playing && W.fun_g == G_PART && W.pref_sand_mode < 4 && !W.menu_on) {
                    b->rep += dt; if (b->rep >= 200) { b->rep -= 200; part_remove(2); }
                } else if (b->long_ && i == 1 && W.mode == M_SET && !W.menu_on) {
                    b->rep += dt; { int32_t gap = b->t > 2500 ? 50 : REPEAT_MS; if (b->rep >= gap) { b->rep -= gap; set_add(); } }
                }
            }
        } else if (!d && b->down) {                                   /* release */
            b->down = 0;
            if (!b->eat && !b->long_ && !b->chord && !b->raw && !W.locked) on_short(i);
        }
    }
}

/* ------------------------------------------------------------------ score display and award ---- */
static void show_score(uint16_t score, int32_t t) {                  /* hundreds: hour ring, tens: minute ring, ones: outer ring */
    uint8_t d[3] = { (uint8_t)(score / 100 % 10), (uint8_t)(score / 10 % 10), (uint8_t)(score % 10) };
    uint8_t on = t > 8000 || (t / 200) % 2 == 0;
    for (uint8_t r = 0; r < 3; r++) { putr(r, 0, 35); if (on) bar_n(r, d[r], 255); }
}
static void award_step(int32_t t) {                                  /* 10 s of comets, sparkles and flashing indicators */
    int32_t ph_ms = t;                                                /* phase in ms; 'ph' seconds = ph_ms / 1000 */
    for (uint8_t r = 0; r < 3; r++) {
        /* angle (rad) = sp * ph, sp = +-(1.2 + ph*0.5 + r*0.7)  ->  in binary angle: sp_q10 * ph_ms ... done in 32-bit pieces */
        int32_t sp_q10 = (int32_t)((1200 + (ph_ms >> 1) + (int32_t)r * 700) * 1024L / 1000L);      /* rad/s in Q10, before sign */
        int32_t ang = (int32_t)(((int64_t)sp_q10 * ph_ms / 1000 * (int32_t)BAM_PER_RAD) >> 10);      /* sp*ph in binary angle (64-bit: light-show only) */
        int8_t sgn = (r & 1) ? -1 : 1;
        if (sgn < 0) ang = -ang;
        for (uint8_t c = 0; c < 6; c++) for (uint8_t k = 0; k < 4; k++) {
            int32_t a = ang + (int32_t)c * (65536L / 6) - sgn * (int32_t)k * 939;
            putr(r, ring_k(r, (uint16_t)a), AWARD_LVL[k]);
        }
    }
    for (uint8_t i = 0; i < 10; i++) { uint32_t n = rnd_n(132); uint8_t r = n < 12 ? 0 : n < 72 ? 1 : 2; uint8_t k = (uint8_t)(r == 0 ? n : r == 1 ? n - 12 : n - 72); putr(r, k, 255); }
    if ((t / 250) % 2 == 0) for (uint8_t i = 0; i < 5; i++) ind(i, 255);
}
static void game_over_display(uint16_t score, uint8_t award, int32_t t) { if (award && t < 10000) award_step(t); else show_score(score, t); }

/* ------------------------------------------------------------------ games: Particles (sand, gravel, oil, water) and bead ---- */
static void ring_xy(uint8_t r, uint8_t k, int32_t *x, int32_t *y) {    /* LED position, 1/256 mm, y down */
    uint16_t a = (uint16_t)(((uint32_t)k * 65536UL) / ring_len(r));
    *x = ((int32_t)RING_R_Q8[r] * sin16(a)) >> 15; *y = -(((int32_t)RING_R_Q8[r] * cos16(a)) >> 15);
}
static void part_add(uint8_t init) {
    part_game_t *s = &W.g.part; if (s->n >= WATCH_MAX_PARTICLES) return;
    uint16_t ang; int32_t r;
    if (init) { ang = (uint16_t)rnd32(); r = R_IN_Q8 + 256 + (int32_t)(((uint32_t)(rnd32() >> 16) * (uint32_t)(R_OUT_Q8 - R_IN_Q8 - 512)) >> 16); }
    else { ang = (uint16_t)(-RAD(0.2) + (int32_t)(((uint32_t)(rnd32() >> 16) * (uint32_t)RAD(0.4)) >> 16)); r = (R_IN_Q8 + R_OUT_Q8) / 2; }
    particle_t *p = &s->p[s->n++];
    p->x = (int16_t)((r * sin16(ang)) >> 15); p->y = (int16_t)(-((r * cos16(ang)) >> 15)); p->vx = p->vy = 0;
}
static void part_remove(uint8_t n) {
    part_game_t *s = &W.g.part; if (!s->n) return; if (n > s->n) n = s->n;
    for (uint8_t i = 0; i + n < s->n; i++) s->p[i] = s->p[i + n];
    s->n = (uint8_t)(s->n - n);
}
static int32_t clampv(int32_t v) { return v > 256000L ? 256000L : v < -256000L ? -256000L : v; }

static void part_step(uint16_t dt) {
    part_game_t *s = &W.g.part; const pmode_t *pm = &PM[W.pref_sand_mode];
    uint8_t n = (uint8_t)((dt + 3) / 4); if (!n) n = 1;
    int32_t h_us = (int32_t)dt * 1000L / n;
    int32_t gx = -(int32_t)io->ax, gy = io->ay;                       /* gravity in milli-g, board coordinates (y down) */
    int32_t gdx = (((gx * 179) >> 4) * h_us) / 62500L, gdy = (((gy * 179) >> 4) * h_us) / 62500L;   /* velocity change per substep, 1/256 mm/s */
    int32_t damp_q16 = (int32_t)pm->damp * h_us / 3906L;
    for (uint8_t it = 0; it < n; it++) {
        for (uint8_t i = 0; i < s->n; i++) {
            particle_t *q = &s->p[i];
            q->vx += gdx; q->vy += gdy;
            q->vx -= ((q->vx >> 4) * damp_q16) >> 12; q->vy -= ((q->vy >> 4) * damp_q16) >> 12;
            q->vx = clampv(q->vx); q->vy = clampv(q->vy);
            q->x = (int16_t)(q->x + q->vx * h_us / 1000000L); q->y = (int16_t)(q->y + q->vy * h_us / 1000000L);
        }
        for (uint8_t i = 0; i < s->n; i++) for (uint8_t j = (uint8_t)(i + 1); j < s->n; j++) {
            particle_t *a = &s->p[i], *b = &s->p[j];
            int32_t dx = (int32_t)b->x - a->x, dy = (int32_t)b->y - a->y, d2 = dx * dx + dy * dy, md = 2 * PR_Q8;
            if (d2 < md * md && d2 > 0) {
                int32_t d = (int32_t)isqrt32((uint32_t)d2); if (d < 1) d = 1;
                int16_t nx = (int16_t)((dx * 32768L) / d), ny = (int16_t)((dy * 32768L) / d);
                int32_t ov = (md - d) / 2;
                a->x = (int16_t)(a->x - ((ov * nx) >> 15)); a->y = (int16_t)(a->y - ((ov * ny) >> 15));
                b->x = (int16_t)(b->x + ((ov * nx) >> 15)); b->y = (int16_t)(b->y + ((ov * ny) >> 15));
                int32_t rv = mulq15(b->vx - a->vx, nx) + mulq15(b->vy - a->vy, ny);
                if (rv < 0) {
                    int32_t k = (-rv * (256 + (int32_t)pm->rest)) >> 9;
                    a->vx -= mulq15(k, nx); a->vy -= mulq15(k, ny); b->vx += mulq15(k, nx); b->vy += mulq15(k, ny);
                    if (pm->mix) {
                        int32_t mx = ((b->vx - a->vx) >> 1) * pm->mix >> 8, my = ((b->vy - a->vy) >> 1) * pm->mix >> 8;
                        a->vx += mx; b->vx -= mx; a->vy += my; b->vy -= my;
                    }
                }
                if (pm->press) {
                    int32_t push = ov * 60 * h_us / 1000000L;
                    a->vx -= mulq15(push, nx); a->vy -= mulq15(push, ny); b->vx += mulq15(push, nx); b->vy += mulq15(push, ny);
                }
            }
        }
        for (uint8_t i = 0; i < s->n; i++) {
            particle_t *q = &s->p[i];
            int32_t r = (int32_t)isqrt32((uint32_t)((int32_t)q->x * q->x + (int32_t)q->y * q->y)); if (r < 1) r = 1;
            int16_t nx = (int16_t)(((int32_t)q->x * 32768L) / r), ny = (int16_t)(((int32_t)q->y * 32768L) / r);
            int32_t lim = -1; uint8_t outer = 0;
            if (r > R_OUT_Q8 - PR_Q8) { lim = R_OUT_Q8 - PR_Q8; outer = 1; } else if (r < R_IN_Q8 + PR_Q8) lim = R_IN_Q8 + PR_Q8;
            if (lim > 0) {
                q->x = (int16_t)((lim * nx) >> 15); q->y = (int16_t)((lim * ny) >> 15);
                int32_t vn = mulq15(q->vx, nx) + mulq15(q->vy, ny);
                if ((outer && vn > 0) || (!outer && vn < 0)) {
                    int32_t bo = (vn * (256 + (int32_t)pm->rest)) >> 8;
                    q->vx -= mulq15(bo, nx); q->vy -= mulq15(bo, ny);
                    int32_t vn2 = mulq15(q->vx, nx) + mulq15(q->vy, ny);
                    int32_t tx = q->vx - mulq15(vn2, nx), ty = q->vy - mulq15(vn2, ny);
                    q->vx -= (tx * pm->fric) >> 8; q->vy -= (ty * pm->fric) >> 8;
                }
                if (pm->mu && outer) {                                /* static friction on the OUTER wall only: a grain holds until the slope exceeds atan(mu) */
                    int32_t gN = (gx * nx + gy * ny) >> 15, gT = (-gx * ny + gy * nx) >> 15; if (gT < 0) gT = -gT;
                    int32_t vt = mulq15(-q->vx, ny) + mulq15(q->vy, nx); if (vt < 0) vt = -vt;
                    if (gN > 0 && gT * 256 < (int32_t)pm->mu * gN && vt < 6400) { q->vx >>= 1; q->vy >>= 1; if (vt < 2048) { q->vx = 0; q->vy = 0; } }
                }
            }
        }
    }
    if (s->flash > 0) { s->flash = (int16_t)(s->flash - dt); put(hour_led((uint8_t)(W.pref_sand_mode + 1)), 255); }   /* mode 1-4 on the hour ring for 1.2 s */
    for (uint8_t i = 0; i < s->n; i++) {                              /* light the nearest LED (within 2.2 mm) */
        const particle_t *q = &s->p[i];
        int32_t r = (int32_t)isqrt32((uint32_t)((int32_t)q->x * q->x + (int32_t)q->y * q->y));
        uint8_t ring = 0; int32_t best = 0x7FFFFFFF;
        for (uint8_t rr = 0; rr < 3; rr++) { int32_t dr = r - RING_R_Q8[rr]; if (dr < 0) dr = -dr; if (dr < best) { best = dr; ring = rr; } }
        uint8_t k0 = ring_k(ring, atan2_bam(q->x, -(int32_t)q->y)), nn = ring_len(ring); uint8_t bk = 255; int32_t bd = 317000L;   /* 2.2 mm squared in 1/256 mm */
        for (int8_t dk = -1; dk <= 1; dk++) {
            uint8_t k = (uint8_t)((k0 + nn + dk) % nn); int32_t lx, ly; ring_xy(ring, k, &lx, &ly);
            int32_t ex = lx - q->x, ey = ly - q->y, d2 = ex * ex + ey * ey; if (d2 < bd) { bd = d2; bk = k; }
        }
        if (bk != 255) putr(ring, bk, 255);
    }
}

static void bead_step(uint16_t dt) {
    part_game_t *s = &W.g.part; uint8_t ring = s->bead_ring;
    uint16_t th = (uint16_t)(s->bead_th_q8 >> 8);
    int32_t gt = (-(int32_t)io->ax * cos16(th) + (int32_t)io->ay * sin16(th)) >> 15;          /* tangential gravity, milli-g */
    s->bead_w += gt * BEAD_K[ring] * dt / 1000;
    s->bead_w -= (s->bead_w * (int32_t)dt) / 1250;                                             /* damping 0.8 /s */
    if (s->bead_w > 400000L) s->bead_w = 400000L; else if (s->bead_w < -400000L) s->bead_w = -400000L;
    s->bead_th_q8 += (s->bead_w * (int32_t)dt) * 32 / 125;                                     /* BAM/s * ms -> Q8 BAM */
    th = (uint16_t)(s->bead_th_q8 >> 8);
    int32_t aw = s->bead_w < 0 ? -s->bead_w : s->bead_w; int32_t tail = (aw + 13037) / 26075; if (tail > 4) tail = 4;
    int8_t dir = s->bead_w >= 0 ? -1 : 1; uint8_t n = ring_len(ring), k = ring_k(ring, th);
    static const uint8_t TAIL[4] = { 116, 80, 61, 49 };               /* 255 / (i + 1.2) */
    putr(ring, k, 255);
    for (int32_t i = 1; i <= tail; i++) putr(ring, (uint8_t)((k + n + dir * i) % n), TAIL[i - 1]);
}

/* ------------------------------------------------------------------ games: Ring Runner ---- */
static void run_step(uint16_t dt) {
    run_game_t *r = &W.g.run;
    if (r->over) {
        r->flash += dt; game_over_display(r->pts, r->award, r->flash);
        if (r->flash < 8000 && (r->flash / 400) % 2 == 0) ind(3, 255);
        return;
    }
    int32_t speed = 9000L + 1200L * (r->passed / 10);                  /* rad/s * 10000: 0.9 plus 0.12 per 10 obstacles */
    r->th += ((speed * (int32_t)dt) / 100) * 10430L / 100000L;          /* binary angle */
    r->spawn -= dt;
    if (r->spawn <= 0 && r->nobs < WATCH_MAX_OBS) {
        uint8_t lane = (uint8_t)rnd_n(3);
        int32_t ang = r->th + RAD(2.4) + (int32_t)(rnd32() >> 16) * RAD(0.6) / 65536;
        uint8_t k = ring_k(lane, (uint16_t)ang), same = 0;
        for (uint8_t i = 0; i < r->nobs; i++) { int32_t d = r->obs[i].ang - ang; if (d < 0) d = -d; if (d < RAD(0.5)) same++; }
        if (same < 2) {
            int32_t turn = ang & ~0xFFFFL, led_ang = ((int32_t)k * 65536L) / ring_len(lane);
            obs_t *o = &r->obs[r->nobs++]; o->lane = lane; o->k = k; o->ang = led_ang + turn; o->passed = 0;
        }
        int32_t base = 1000 - (int32_t)r->passed * 12; if (base < 350) base = 350;
        r->spawn = base * (60 + (int32_t)rnd_n(80)) / 100;
    }
    uint8_t mk = ring_k(r->lane, (uint16_t)r->th);
    for (uint8_t i = 0; i < r->nobs; i++) {
        obs_t *o = &r->obs[i]; int32_t d = o->ang - r->th; if (d < 0) d = -d;
        if (o->lane == r->lane && o->k == mk && d < RAD(0.35)) { r->over = 1; r->flash = 0; return; }
        if (!o->passed && r->th > o->ang + RAD(0.4)) {
            o->passed = 1; r->passed++; r->pts = (uint16_t)(r->pts + 10 > SCORE_CAP ? SCORE_CAP : r->pts + 10);   /* 10 points per obstacle */
            if (r->pts >= SCORE_CAP) { r->over = 1; r->award = 1; r->flash = 0; return; }
        }
    }
    { uint8_t w = 0; for (uint8_t i = 0; i < r->nobs; i++) if (r->th - r->obs[i].ang < RAD(1.0)) r->obs[w++] = r->obs[i]; r->nobs = w; }   /* drop obstacles more than ~1 rad behind */
    for (uint8_t i = 0; i < r->nobs; i++) if ((W.tms / 150) % 2 == 0) putr(r->obs[i].lane, r->obs[i].k, 200);
    putr(r->lane, mk, 255);
}

/* ------------------------------------------------------------------ games: Target ---- */
static void target_step(uint16_t dt) {
    tg_game_t *t = &W.g.tg; t->t += dt;
    if (t->over) { game_over_display(t->pts, t->award, t->t); if (t->t < 8000 && (t->t / 400) % 2 == 0) ind(3, 255); return; }
    t->pos_q16 += (uint32_t)((uint32_t)t->spd_q16 * dt / 1000UL); if (t->pos_q16 >= 60UL * 65536UL) t->pos_q16 -= 60UL * 65536UL;
    uint8_t nrun = (uint8_t)(1 + (t->lvl / 4 > 2 ? 2 : t->lvl / 4));
    uint32_t pos = t->pos_q16;
    putr(1, (uint8_t)(((pos + 32768UL) >> 16) % 60), 255);
    for (uint8_t i = 1; i < nrun; i++) putr(1, (uint8_t)((((pos + (uint32_t)i * 60UL * 65536UL / nrun) + 32768UL) >> 16) % 60), 110);
    uint8_t tol = (uint8_t)(t->tol_q16 >> 16);                          /* target zone shrinks as you improve */
    putr(1, 0, 70); for (uint8_t i = 1; i <= tol; i++) { putr(1, i, 30); putr(1, (uint8_t)(60 - i), 30); }
    put(hour_led(12), 120);
    if (t->hit_flash > 0) { t->hit_flash = (int16_t)(t->hit_flash - dt); if ((t->hit_flash / 100) % 2 == 0) { bar_n(0, 12, 255); putr(1, 0, 255); } }
    else bar_n(0, t->lvl > 12 ? 12 : t->lvl, 120);
}

/* ------------------------------------------------------------------ games: Quick Draw ---- */
static void half_all(uint8_t side, uint8_t lvl) { for (uint8_t r = 0; r < 3; r++) for (uint8_t k = 0; k < ring_len(r); k++) if (in_half(r, k, side)) putr(r, k, lvl); }
static void qd_step(uint16_t dt) {
    qd_game_t *q = &W.g.qd; q->t += dt; uint8_t blink = (W.tms / 300) % 2 == 0;
    uint8_t any = io->btn & 3;
    if (q->st == QD_IDLE) {                                            /* hold both buttons 0.5 s, release both = armed */
        ind(3, blink ? 255 : 60);
        if (W.b[0].down && W.b[1].down && W.b[0].t > 500 && W.b[1].t > 500) { q->arm_held = 1; for (uint8_t k = 0; k < 60; k++) if (k <= 1 || k == 59) putr(2, k, 180); }
        else if (q->arm_held && !W.b[0].down && !W.b[1].down) { q->arm_held = 0; q->st = QD_WAIT; q->t = 0; q->wait = 2000 + (int32_t)rnd_n(4000); }
    } else if (q->st == QD_WAIT) {
        ind(3, 255);
        if (any) { uint8_t who = (io->btn & 1) ? 0 : 1; q->win = (uint8_t)(1 - who); q->st = QD_RESULT; q->t = 0; q->was_false = 1; }
        else if (q->t >= q->wait) { q->st = QD_GO; q->t = 0; }
    } else if (q->st == QD_GO) {
        bar_n(2, 60, 255); bar_n(1, 60, 255);
        if (any) { q->win = (io->btn & 1) ? 0 : 1; q->st = QD_RESULT; q->t = 0; q->was_false = 0; }
        else if (q->t > 2500) q->st = QD_IDLE;
    } else {                                                           /* result: the winner's half lights */
        half_all(q->win == 0 ? 0 : 1, q->was_false ? ((q->t / 150) % 2 ? 255 : 90) : 255);
        if (q->t > 3000) q->st = QD_IDLE;
    }
}

/* ------------------------------------------------------------------ games: Orbit (six light-show patterns) ---- */
static uint16_t ang_mul(uint32_t ph_q8, uint16_t c_q8) { return (uint16_t)(((uint64_t)ph_q8 * c_q8) >> 16); }   /* ph * c as a binary angle (c in Q8) */
static void orbit_step(uint16_t dt) {
    orb_game_t *o = &W.g.orb;
    int32_t rate = 1000 + ((int32_t)io->ax * 3) / 2 + io->ay;                                   /* milli: 1.0 + 1.5 fx + fy */
    int32_t w = rate * 10430 / 1000;                                                            /* binary angle per second */
    o->ph_q8 += (uint32_t)(w * (int32_t)dt * 256 / 1000);                                      /* signed delta added with wrap-around */
    uint8_t pat = W.pref_orb_pat;
    if (pat == 0) {                                                                             /* radar sweep with a trail */
        for (uint8_t r = 0; r < 3; r++) for (uint8_t t = 0; t < 7; t++) putr(r, ring_k(r, (uint16_t)(ang_mul(o->ph_q8, 384) - t * 939)), RADAR_LVL[t]);
    } else if (pat == 1) {                                                                      /* 1:2:3 Lissajous: three dots */
        putr(0, ring_k(0, ang_mul(o->ph_q8, 256)), 255);
        putr(1, ring_k(1, (uint16_t)-ang_mul(o->ph_q8, 512)), 255);
        putr(2, ring_k(2, ang_mul(o->ph_q8, 768)), 255);
    } else if (pat == 2) {                                                                      /* spiral comet across the rings */
        uint32_t phb = o->ph_q8 >> 8; uint8_t k = (uint8_t)(((uint64_t)phb * 4117710UL >> 32) % 60);
        for (uint8_t t = 0; t < 8; t++) { uint8_t kk = (uint8_t)((k + 60 - t) % 60); putr(kk % 3, ring_k(kk % 3, (uint16_t)((uint32_t)kk * 5363UL)), COMET_LVL[t]); }
    } else if (pat == 3) {                                                                      /* ripple: waves from the inner ring outward */
        for (uint8_t r = 0; r < 3; r++) {
            int16_t s = sin16((uint16_t)(ang_mul(o->ph_q8, 768) - (uint16_t)((uint16_t)16688 * r)));
            if (s > 1638) { uint8_t lvl = (uint8_t)(((int32_t)255 * s + 16384) >> 15); for (uint8_t i = 0; i < ring_len(r); i = (uint8_t)(i + (r == 0 ? 1 : 3))) putr(r, i, lvl); }
        }
    } else if (pat == 4) {                                                                      /* pendulums: six dots at slightly different rates */
        static const uint16_t C[6] = { 410, 466, 522, 579, 635, 691 };
        for (uint8_t r = 0; r < 3; r++) for (uint8_t k = 0; k < 2; k++) {
            int16_t s = sin16(ang_mul(o->ph_q8, C[r * 2 + k]));
            putr(r, ring_k(r, (uint16_t)(32768 + ((int32_t)RAD(1.25) * s >> 15))), 255);
        }
    } else {                                                                                    /* twinkle: random LEDs fade in and out */
        int32_t x = (int32_t)dt * 65536L / 450;                                                  /* dt/450 in Q16 */
        uint32_t f = (uint32_t)(((uint64_t)(65536L - x / 2) << 16) / (uint64_t)(65536L + x / 2));  /* exp(-x) ~ (1 - x/2)/(1 + x/2), Q16 */
        for (uint8_t i = 0; i < 132; i++) o->stars[i] = (uint16_t)(((uint32_t)o->stars[i] * f) >> 16);
        for (uint8_t n = 0; n < dt / 50; n++) o->stars[rnd_n(132)] = 255 << 8;                          /* about 20 new stars a second */
        if ((int32_t)(rnd32() >> 16) < (int32_t)(dt % 50) * 65536L / 50) o->stars[rnd_n(132)] = 255 << 8;
        for (uint8_t i = 0; i < 132; i++) if ((o->stars[i] >> 8) > 20) { uint8_t r = i < 12 ? 0 : i < 72 ? 1 : 2; putr(r, (uint8_t)(r == 0 ? i : r == 1 ? i - 12 : i - 72), (uint8_t)(o->stars[i] >> 8)); }
    }
}

/* ------------------------------------------------------------------ games: Random ---- */
static void rng_roll(void) {
    rng_game_t *r = &W.g.rng; r->roll = 900; r->age = 0; r->cool = 1500; r->has_res = 1;
    switch (W.pref_rng_mode) {
    case 0: r->c = (uint8_t)(1 + rnd_n(2)); break;
    case 1: r->d1 = (uint8_t)(1 + rnd_n(6)); break;
    case 2: r->d1 = (uint8_t)(1 + rnd_n(6)); r->d2 = (uint8_t)(1 + rnd_n(6)); break;
    case 3: r->n = (uint16_t)(1 + rnd_n(999)); break;
    default: r->h = (uint8_t)(1 + rnd_n(12)); r->m = (uint8_t)rnd_n(60); r->s = (uint8_t)rnd_n(60); break;
    }
}
static void rng_step(uint16_t dt) {
    rng_game_t *r = &W.g.rng; r->age += dt; if (r->cool > 0) r->cool = (int16_t)(r->cool - dt);
    if (W.shaken && r->cool <= 0 && r->roll <= 0) rng_roll();
    uint8_t mode = W.pref_rng_mode;
    if (r->flash > 0) { r->flash = (int16_t)(r->flash - dt); put(hour_led((uint8_t)(mode + 1)), 255); }
    if (r->roll > 0) {                                                  /* tumbling */
        r->roll = (int16_t)(r->roll - dt);
        uint8_t first = mode <= 1 ? 2 : mode == 2 ? 1 : 0;
        for (uint8_t rg = first; rg < 3; rg++) for (uint8_t i = 0; i < 4; i++) putr(rg, (uint8_t)rnd_n(ring_len(rg)), 255);
        return;
    }
    if (!r->has_res) { if ((W.tms / 500) % 2 == 0) put(hour_led(12), 160); return; }
    if (mode == 0) { uint8_t heads = r->c == 1; for (uint8_t k = 0; k < 60; k++) if (in_half(2, k, heads)) putr(2, k, 255); put(hour_led(heads ? 3 : 9), 255); }
    else if (mode == 1) bar_n(2, r->d1, 255);
    else if (mode == 2) { bar_n(1, r->d1, 255); bar_n(2, r->d2, 255); bar_n(0, (uint8_t)(r->d1 + r->d2), 120); }
    else if (mode == 3) show_score(r->n, r->age + 6500);
    else { put(hour_led(r->h), 255); put(MINUTE_LED[r->m], 255); put(SECOND_LED[r->s], 255); }
}

/* ------------------------------------------------------------------ games: Pacer ---- */
static int32_t ease_q15(int32_t x_q15) { return (32768 - cos16((uint16_t)x_q15)) >> 1; }     /* 0.5 - 0.5 cos(pi x) */
static void pacer_step(uint16_t dt) {
    pc_game_t *p = &W.g.pc; p->t += dt;
    if (p->show > 0) { p->show = (int16_t)(p->show - dt); show_score(W.pref_pc_kind ? W.pref_pc_br : W.pref_pc_bpm, 9000); return; }   /* the tempo as a number */
    if (W.pref_pc_kind == 0) {                                          /* metronome */
        int32_t per = 60000L / W.pref_pc_bpm, beat = p->t / per, since = p->t - beat * per;
        for (uint8_t trail = 0; trail < 2; trail++) {
            int32_t t = p->t - (trail ? 60 : 0), tm = ((t % (2 * per)) + 2 * per) % (2 * per);
            int32_t pos = -cos16((uint16_t)(tm * 32768L / per));         /* Q15, -1 at a beat on the left, +1 on the right */
            uint16_t ang = (uint16_t)(32768 - ((int32_t)13559 * pos >> 15));
            putr(2, ring_k(2, ang), trail ? 90 : 255);
        }
        if (since < 80) { if (beat % 4 == 0) { put(hour_led(12), 255); put(hour_led(6), 255); } else put(hour_led(6), 160); }
        { static const uint8_t BEAT_LED[4] = { 12, 3, 6, 9 }; put(hour_led(BEAT_LED[beat % 4]), 110); }
    } else {                                                            /* breath pacer: fill 40 %, empty 60 % */
        int32_t per = 60000L / W.pref_pc_br, tm = p->t % per, inh = per * 2 / 5, f;
        if (tm < inh) f = ease_q15(tm * 32768L / inh); else f = 32768 - ease_q15((tm - inh) * 32768L / (per - inh));
        bar_n(1, (uint8_t)((f * 60 + 16384) >> 15), 255); bar_n(0, (uint8_t)((f * 12 + 16384) >> 15), 110);
    }
}

/* ------------------------------------------------------------------ games: Simon ---- */
static void sim_half(uint8_t side, uint8_t lvl) { for (uint8_t k = 0; k < 60; k++) if (in_half(2, k, side)) putr(2, k, lvl); put(hour_led(side == 0 ? 9 : 3), lvl); }
static void simon_press(uint8_t side) {
    sim_game_t *m = &W.g.sim;
    if (m->over) { game_start(G_SIMON); return; }
    if (m->st != SM_INPUT) return;                                      /* presses while the watch shows the sequence are ignored */
    m->flash = 220; m->fside = side; m->t = 0;
    if (((m->seq >> m->i) & 1) == side) {
        m->i++; m->pts = (uint16_t)(m->pts + 5 > SCORE_CAP ? SCORE_CAP : m->pts + 5);
        if (m->pts >= SCORE_CAP) { m->over = 1; m->award = 1; m->t = 0; }
        else if (m->i == m->len) { m->st = SM_NEXT; m->t = 0; }
    } else { m->over = 1; m->t = 0; }
}
static void simon_step(uint16_t dt) {
    sim_game_t *m = &W.g.sim; m->t += dt;
    if (m->over) { game_over_display(m->pts, m->award, m->t); if (m->t < 8000 && (m->t / 400) % 2 == 0) ind(3, 255); return; }
    if (m->flash > 0) { m->flash = (int16_t)(m->flash - dt); sim_half(m->fside, 255); }
    bar_n(0, m->len > 12 ? 12 : m->len, 70);
    if (m->st == SM_READY || m->st == SM_NEXT) {
        if (m->t > (m->st == SM_READY ? 900 : 700)) { if (rnd32() >= 0x80000000UL) m->seq |= 1UL << m->len; m->len++; m->st = SM_SHOW; m->t = 0; }   /* symbol 0 if random < 0.5 */
        return;
    }
    if (m->st == SM_SHOW) {
        int32_t on = 600 - 22 * (int32_t)m->len; if (on < 200) on = 200;
        int32_t slot = on + 140, i = m->t / slot;
        if (i >= m->len) { m->st = SM_INPUT; m->i = 0; m->t = 0; return; }
        if (m->t % slot < on) sim_half((uint8_t)((m->seq >> i) & 1), 255);
        return;
    }
    putr(1, 0, 170);                                                    /* "your turn" */
    if (m->t > 4000) { m->over = 1; m->t = 0; }
}

/* ------------------------------------------------------------------ games: Pong ---- */
static led_pos_t pong_led(int32_t pos_q16) { int32_t p = pos_q16 < 0 ? 0 : pos_q16 > 65536L ? 65536L : pos_q16; return ring_led(1, ring_k(1, (uint16_t)(49152 - (p >> 1)))); }
static void pong_serve(uint8_t loser) { pg_game_t *g = &W.g.pg; g->st = PG_PLAY; g->pos_q16 = 32768L; g->dir = loser == 0 ? -1 : 1; g->spd_q16 = 52429L; }
static void pong_point(uint8_t winner) {
    pg_game_t *g = &W.g.pg; if (winner == 0) g->s1++; else g->s2++;
    g->winner = winner; g->t = 0; g->st = (g->s1 >= PONG_WIN || g->s2 >= PONG_WIN) ? PG_OVER : PG_POINT;
}
static void pong_press(uint8_t b) {
    pg_game_t *g = &W.g.pg;
    if (g->st == PG_READY) { if (b == 0) W.pref_pg_mode ^= 1; else pong_serve(1); return; }
    if (g->st == PG_OVER) { if (W.pref_pg_mode == 0 && g->t < 3000) return; game_start(G_PONG); return; }
    if (g->st != PG_PLAY) return;
    uint8_t side = W.pref_pg_mode == 1 ? 1 : b;
    uint8_t in_zone = side == 0 ? g->pos_q16 <= PONG_Z_Q16 : g->pos_q16 >= 65536L - PONG_Z_Q16, toward = side == 0 ? g->dir < 0 : g->dir > 0;
    if (!in_zone || !toward) return;                                    /* a swing and a miss costs nothing */
    int32_t edge = side == 0 ? g->pos_q16 : 65536L - g->pos_q16;
    g->dir = (int8_t)-g->dir; g->spd_q16 += 4588 + (edge < 3277 ? 7864 : 0); if (g->spd_q16 > 144179L) g->spd_q16 = 144179L; g->hit[side] = 200;
    if (W.pref_pg_mode == 1) { g->pts = (uint16_t)(g->pts + 10 > SCORE_CAP ? SCORE_CAP : g->pts + 10); if (g->pts >= SCORE_CAP) { g->st = PG_OVER; g->award = 1; g->t = 0; } }
}
static void pong_step(uint16_t dt) {
    pg_game_t *g = &W.g.pg; g->t += dt; uint8_t solo = W.pref_pg_mode == 1;
    for (uint8_t i = 0; i < 2; i++) g->hit[i] = (int16_t)(g->hit[i] > (int16_t)dt ? g->hit[i] - (int16_t)dt : 0);
    if (g->st == PG_OVER && solo) { game_over_display(g->pts, g->award, g->t); if (g->t < 8000 && (g->t / 400) % 2 == 0) ind(3, 255); return; }
    for (uint8_t k = 0; k <= 30; k++) {                                 /* the field: paddle zones at both ends of the ball's path */
        int32_t pos = (int32_t)k * 65536L / 30; uint8_t inL = pos <= PONG_Z_Q16, inR = pos >= 65536L - PONG_Z_Q16;
        if (inL || inR) put(pong_led(pos), ((inL && g->hit[0] > 0) || (inR && g->hit[1] > 0)) ? 255 : 45);
    }
    if (g->st == PG_READY) { put(hour_led((uint8_t)(W.pref_pg_mode + 1)), (W.tms / 300) % 2 ? 255 : 120); put(pong_led(32768L), 255); return; }
    if (!solo) { for (uint8_t i = 1; i <= g->s1; i++) put(hour_led((uint8_t)(12 - i)), 255); for (uint8_t i = 1; i <= g->s2; i++) put(hour_led(i), 255); }
    if (g->st == PG_OVER) {                                             /* two players: the winner's half blinks for 3 s */
        if ((g->t / 200) % 2 == 0) for (uint8_t k = 0; k < 60; k++) if (in_half(2, k, g->winner == 0 ? 0 : 1)) putr(2, k, 255);
        if (g->t > 3000) game_start(G_PONG);
        return;
    }
    if (g->st == PG_POINT) { put(pong_led(g->winner == 0 ? 0 : 65536L), 255); if (g->t > 900) pong_serve((uint8_t)(1 - g->winner)); return; }
    g->pos_q16 += (int32_t)g->dir * ((int32_t)g->spd_q16 * (int32_t)dt / 1000);
    if (g->pos_q16 <= 0) { if (solo) { g->pos_q16 = 0; g->dir = 1; } else { pong_point(1); return; } }
    else if (g->pos_q16 >= 65536L) { if (solo) { g->st = PG_OVER; g->t = 0; return; } else { pong_point(0); return; } }
    put(pong_led(g->pos_q16), 255);
}

/* ------------------------------------------------------------------ games: start and buttons ---- */
static void game_start(uint8_t g) {
    memset(&W.g, 0, sizeof W.g);
    switch (g) {
    case G_PART: for (uint8_t i = 0; i < 14; i++) part_add(1); W.g.part.bead_ring = 1; W.g.part.bead_th_q8 = (int32_t)(RAD(1.5707963) << 8); break;
    case G_RUN: W.g.run.lane = 1; break;
    case G_TARGET: W.g.tg.spd_q16 = 14UL * 65536UL; W.g.tg.tol_q16 = 3UL * 65536UL; break;
    case G_QD: break;
    case G_ORBIT: break;
    case G_RNG: break;
    case G_PACER: W.g.pc.show = 2500; break;
    case G_SIMON: break;
    default: W.g.pg.pos_q16 = 32768L; W.g.pg.dir = 1; W.g.pg.spd_q16 = 52429L; break;
    }
}
static void game_button(uint8_t g, uint8_t b) {                        /* b: 0 = left, 1 = right (Quick Draw reads the buttons itself) */
    switch (g) {
    case G_PART:
        if (b == 1) { if (W.pref_sand_mode == 4) W.g.part.bead_ring = (uint8_t)((W.g.part.bead_ring + 1) % 3); else part_add(0); }
        else { W.pref_sand_mode = (uint8_t)((W.pref_sand_mode + 1) % 5); W.g.part.flash = 1200; }
        break;
    case G_RUN: {
        run_game_t *r = &W.g.run;
        if (r->over) { game_start(G_RUN); return; }
        if (b == 0) { if (r->lane > 0) r->lane--; } else if (r->lane < 2) r->lane++;
        break; }
    case G_TARGET: {
        tg_game_t *t = &W.g.tg;
        if (t->over) { game_start(G_TARGET); return; }
        uint32_t k = ((t->pos_q16 + 32768UL) >> 16) % 60; uint32_t dist = k < 60 - k ? k : 60 - k;
        if (dist * 65536UL <= t->tol_q16) {
            t->pts = (uint16_t)(t->pts + 10 + t->lvl > SCORE_CAP ? SCORE_CAP : t->pts + 10 + t->lvl); t->lvl++;
            t->spd_q16 = t->spd_q16 * 11UL / 10UL; if (t->spd_q16 > 90UL * 65536UL) t->spd_q16 = 90UL * 65536UL;
            t->tol_q16 = t->tol_q16 * 23UL / 25UL; if (t->tol_q16 < 39322UL) t->tol_q16 = 39322UL;    /* 0.6 LED minimum */
            t->hit_flash = 600;
            if (t->pts >= SCORE_CAP) { t->over = 1; t->award = 1; t->t = 0; }
        } else { t->over = 1; t->t = 0; t->last_k = (uint8_t)k; }
        break; }
    case G_ORBIT: W.pref_orb_pat = (uint8_t)((W.pref_orb_pat + (b == 1 ? 1 : 5)) % 6); break;
    case G_RNG:
        if (b == 1) { if (W.g.rng.roll <= 0) rng_roll(); }
        else { W.pref_rng_mode = (uint8_t)((W.pref_rng_mode + 1) % 5); W.g.rng.has_res = 0; W.g.rng.roll = 0; W.g.rng.flash = 1200; }
        break;
    case G_PACER:
        if (W.pref_pc_kind == 0) { int16_t v = (int16_t)(W.pref_pc_bpm + (b == 1 ? 5 : -5)); W.pref_pc_bpm = (uint8_t)(v < 40 ? 40 : v > 220 ? 220 : v); }
        else { int16_t v = (int16_t)(W.pref_pc_br + (b == 1 ? 1 : -1)); W.pref_pc_br = (uint8_t)(v < 3 ? 3 : v > 12 ? 12 : v); }
        W.g.pc.show = 2500; W.g.pc.t = 0;
        break;
    case G_SIMON: simon_press(b); break;
    case G_PONG: pong_press(b); break;
    default: break;
    }
}

/* ------------------------------------------------------------------ rendering of the modes ---- */
static void render_time(void) {
    uint8_t h, m, s; hms(&h, &m, &s);
    put(hour_led((uint8_t)(h % 12 == 0 ? 12 : h % 12)), 255); put(MINUTE_LED[m], 255);
    if (W.set[C_SEC] == 0 && !(W.locked && W.set[C_LOCKD] == 2)) put(SECOND_LED[s], 255);     /* locked always-on display: no seconds LED */
}
static void render_date(int8_t blink_field, uint8_t blink_on) {          /* month: hour ring, day: minute ring, weekday: bar on the outer ring */
    uint8_t m_lvl = (blink_field == 3 && !blink_on) ? 0 : 255, d_lvl = (blink_field == 4 && !blink_on) ? 0 : 255;
    put(hour_led(W.month), m_lvl); put(MINUTE_LED[W.day], d_lvl);
    bar_n(2, weekday_iso(W.year, W.month, W.day), (blink_field == 3 || blink_field == 4) ? 140 : 255);
}

static void render(uint16_t dt) {
    memset(fb, 0, sizeof fb);
    W.tms += dt;
    uint8_t blink2 = (W.tms / 250) % 2 == 0, blink4 = (W.tms / 125) % 2 == 0;
    if (!W.awake) return;
    uint8_t holding_both = W.both_t >= 400 && !W.lock_done;
    if (W.ind_only) {                                                    /* lock feedback: only the LCK LED */
        if (W.lock_flash > 0) W.lock_flash = (int16_t)(W.lock_flash - dt);
        ind(5, (holding_both || W.lock_flash > 0) ? (blink4 ? 255 : 0) : (W.locked ? 255 : 0));
        return;
    }
    if (W.menu_on) { if (blink2) { if (W.menu_sel == 0) put(hour_led(12), 255); else ind((uint8_t)MODE_IND[W.menu_sel], 255); } return; }
    if (W.dead) { if (blink4) ind(2, 255); return; }
    switch (W.mode) {
    case M_TIME:
        if (W.peek > 0) { bar_n(0, (uint8_t)(((uint32_t)io->soc_pm * 12 + 500) / 1000), 255); ind(2, 255); W.peek = (int16_t)(W.peek - dt); }
        else if (W.date_peek > 0) { render_date(-1, 1); W.date_peek = (int16_t)(W.date_peek - dt); }
        else render_time();
        break;
    case M_SET: {
        uint8_t h, m, s; hms(&h, &m, &s); uint8_t f = W.set_field, on = blink2, h12 = (uint8_t)(h % 12 == 0 ? 12 : h % 12), dim = 70;
        if (f <= 2) { put(hour_led(h12), f == 0 ? (on ? 255 : 0) : dim); put(MINUTE_LED[m], f == 1 ? (on ? 255 : 0) : dim); put(SECOND_LED[s], f == 2 ? (on ? 255 : 0) : dim); }
        else if (f <= 4) render_date((int8_t)f, on);
        else { put(MINUTE_LED[(W.year - 2000) % 60], on ? 255 : 0); put(hour_led(12), 60); }
        break; }
    case M_TMR: {
        uint32_t e = W.tmr_el; put(SECOND_LED[e / 1000 % 60], 255); put(MINUTE_LED[e / 60000UL % 60], 160); put(hour_led(TENTHS_LED[e / 100 % 10]), 90);
        break; }
    case M_BAT:
        if (W.bat_view == 0) bar_n(0, (uint8_t)(((uint32_t)io->soc_pm * 12 + 500) / 1000), 255);
        else if (W.bat_view == 1) bar_n(1, SOLAR_BAR[io->solar_mw > 30 ? 30 : io->solar_mw], 200);
        else if (io->charging) { uint8_t k = (uint8_t)((W.tms / 90) % 12); put(hour_led(k == 0 ? 12 : k), 255); put(hour_led((uint8_t)(((k + 11) % 12) ? (k + 11) % 12 : 12)), 90); }
        else put(hour_led(12), 120);
        { uint8_t lvl = 255; if (io->charging && W.bat_view == 2) { int16_t sv = sin16((uint16_t)((W.tms % 1571UL) * 65536UL / 1571UL)); lvl = (uint8_t)(188 + ((67L * sv + 16384) >> 15)); } ind(2, lvl); }
        break;
    case M_FUN:
        if (!W.fun_playing) put(hour_led((uint8_t)(W.fun_g + 1)), blink2 ? 255 : 120);          /* game picker: hour LED n = game n */
        break;
    default: {
        put(hour_led((uint8_t)(W.cfg_sel + 1)), 255);
        uint8_t v = W.set[W.cfg_sel], cnt = CFG_COUNT[W.cfg_sel];
        bar_n(1, (uint8_t)((2 * (v + 1) * 60 + cnt) / (2 * cnt)), 255);
        break; }
    }
    if (W.mode == M_FUN && W.fun_playing) {
        switch (W.fun_g) {
        case G_PART: if (W.pref_sand_mode == 4) { bead_step(dt); if (W.g.part.flash > 0) { W.g.part.flash = (int16_t)(W.g.part.flash - dt); put(hour_led(5), 255); } } else part_step(dt); break;
        case G_RUN: run_step(dt); break;
        case G_TARGET: target_step(dt); break;
        case G_QD: qd_step(dt); break;
        case G_ORBIT: orbit_step(dt); break;
        case G_RNG: rng_step(dt); break;
        case G_PACER: pacer_step(dt); break;
        case G_SIMON: simon_step(dt); break;
        default: pong_step(dt); break;
        }
    }
    if (MODE_IND[W.mode] >= 0 && W.mode != M_BAT) ind((uint8_t)MODE_IND[W.mode], 255);
    if (W.locked && !holding_both) ind(5, 255);
    if (holding_both && blink4) ind(5, 255);
    if (W.lock_flash > 0) { W.lock_flash = (int16_t)(W.lock_flash - dt); if (blink4) for (uint8_t i = 0; i < 6; i++) ind(i, 255); }
    if (!io->bat_ok && W.mode == M_TIME && blink4) ind(2, 255);
}

/* ------------------------------------------------------------------ scan plan ---- */
static void build_scan(uint16_t duty_q16) {
    int32_t i_ua = I_REF_UA + ((int32_t)io->vdd_mv - 3000) * 2667L / 1000; if (i_ua < 200) i_ua = 200;
    int32_t m = ROW_SINK_UA / i_ua; if (m < 1) m = 1;
    scan.n = 0; scan.m = (uint8_t)m; scan.i_led_ua = (uint16_t)i_ua;
    uint32_t sumfb = 0;
    for (uint8_t r = 0; r < WATCH_ROWS; r++) {
        uint16_t pending = 0; uint8_t cnt = 0;
        for (uint8_t c = 0; c < WATCH_COLS; c++) {
            uint8_t v = fb[(uint8_t)(r * WATCH_COLS + c)];
            if (!v) continue;
            sumfb += v; pending |= (uint16_t)(1u << c);
            if (++cnt == m) { if (scan.n < WATCH_MAX_SLOTS) { scan.slot[scan.n].row = r; scan.slot[scan.n].cols = pending; scan.n++; } pending = 0; cnt = 0; }
        }
        if (cnt && scan.n < WATCH_MAX_SLOTS) { scan.slot[scan.n].row = r; scan.slot[scan.n].cols = pending; scan.n++; }
    }
    uint32_t N = scan.n ? scan.n : 1;
    uint32_t needed = (uint32_t)duty_q16 * I_REF_UA / (uint32_t)i_ua;
    uint32_t cap = 65536UL / N, ach = needed < cap ? needed : cap;
    scan.needed_q16 = (uint16_t)(needed > 65535 ? 65535 : needed); scan.achievable_q16 = (uint16_t)(ach > 65535 ? 65535 : ach);
    scan.limited = ach + 1 < needed;
    scan.on_q16 = (uint16_t)((ach * N) > 65535 ? 65535 : ach * N);
    scan.avg_ua = (uint16_t)(((uint64_t)sumfb * ach * (uint32_t)i_ua) / (255ULL * 65536ULL));
}

/* ------------------------------------------------------------------ the step ---- */
void watch_init(uint32_t seed) {
    memset(&W, 0, sizeof W); memset(fb, 0, sizeof fb); memset(&scan, 0, sizeof scan);
    rng_state = seed ? seed : 1; px = 0; py = 0; pz = 1000; shake_acc = 0;
    W.rtc_ms = (10UL * 3600UL + 8UL * 60UL + 37UL) * 1000UL; W.year = 2026; W.month = 10; W.day = 11;
    W.set[C_BRI] = 2; W.set[C_WAKE] = 1; W.set[C_DUR] = 3;
    W.pref_pc_bpm = 100; W.pref_pc_br = 6;
}

void watch_step(uint16_t dt_real, uint32_t dt_sim, const watch_io_t *in) {
    io = in; W.shaken = 0;
    W.rtc_ms += dt_sim; while (W.rtc_ms >= 86400000UL) { W.rtc_ms -= 86400000UL; next_day(); }
    W.dead = io->soc_pm < 30;
    /* accelerometer events (the LIS2DW12 raises INT and wakes the MCU). Each motion has its own CFG switch; a locked watch can be told to stay dark. */
    uint8_t lock_dark = W.locked && W.set[C_LOCKD] == 1;
    int32_t jerk = (int32_t)isqrt32((uint32_t)(((int32_t)io->ax - px) * ((int32_t)io->ax - px) + ((int32_t)io->ay - py) * ((int32_t)io->ay - py) + ((int32_t)io->az - pz) * ((int32_t)io->az - pz)));
    px = io->ax; py = io->ay; pz = io->az;
    /* shake_acc = shake_acc * exp(-dt/250) + jerk, with exp(-x) ~ (1 - x/2)/(1 + x/2) */
    { int32_t x = (int32_t)dt_real * 1000L / 250; shake_acc = shake_acc * (2000 - x) / (2000 + x) + jerk; }
    if (shake_acc > SHAKE_JERK) { shake_acc = 0; W.shaken = 1; if (W.set[C_SHAKE] == 0 && !lock_dark) motion_wake(); }
    if (io->wake_strength > 0 && W.set[C_RAISE] == 0 && !lock_dark && io->wake_strength >= WAKE_SENS[W.set[C_WAKE]]) motion_wake();
    if (io->tap && W.set[C_TAP] == 0 && !lock_dark) motion_wake();
    buttons(dt_real);
    if (W.menu_on) { W.menu_t += dt_real; if (W.menu_t >= MENU_CONFIRM_MS) menu_confirm(); }
    uint8_t always_on = W.locked && W.set[C_LOCKD] == 2;                 /* locked, display stays lit showing Time */
    if (W.awake) {
        W.idle += dt_real;
        uint32_t lim = W.dead ? 1000UL : W.ind_only ? 1200UL : W.mode == M_TIME ? DUR_MS[W.set[C_DUR]] : W.mode == M_FUN ? (W.fun_playing ? GAME_IDLE_MS : MODE_IDLE_MS) : tmr_keep() ? TMR_KEEP_MS : MODE_IDLE_MS;
        if (always_on) W.idle = 0;
        else if (W.idle > lim) {
            if (W.mode != M_TIME && !tmr_keep() && !W.ind_only) { to_mode(M_TIME); W.idle = 0; }
            else { W.awake = 0; W.ind_only = 0; W.menu_on = 0; }
        }
    }
    if (always_on && !W.awake) { W.awake = 1; W.ind_only = 0; W.idle = 0; }
    if (W.tmr_run) W.tmr_el += dt_real;                                   /* the stopwatch keeps counting whatever the display is doing */
    render(dt_real);
    uint32_t duty = BRI_Q16[W.set[C_BRI]];
    if (W.set[C_AUTO]) { duty = duty * (35UL + 165UL * io->ambient / 100UL) / 100UL; if (duty > 52429UL) duty = 52429UL; }
    if (!io->bat_ok) duty /= 2;
    if (W.locked && W.set[C_LOCKD] == 2) duty /= 4;
    if (W.awake) build_scan((uint16_t)duty); else { memset(&scan, 0, offsetof(watch_scan_t, slot)); scan.m = 0; }
}
