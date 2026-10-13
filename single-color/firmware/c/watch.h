/* watch.h - public interface of the platform-independent watch logic (port of firmware/sim/watch_core.js).
 *
 * No hardware access and no floating point in here: the same code is built for the AVR128DB48 (avr-gcc) and for the PC
 * (host tests, differential tests against the JavaScript simulator). The hardware layer feeds watch_step() the
 * buttons / accelerometer / battery readings and scans out the 12 x 12 framebuffer using the scan plan.
 *
 * Accelerometer frame: x -> 3 o'clock, y -> 12 o'clock, z out of the glass, milli-g. The sensor reads +1000 on the axis
 * pointing UP (flat face-up = 0, 0, +1000). Raising the 12 o'clock edge makes y positive.
 */
#pragma once
#include <stdint.h>

#define WATCH_ROWS          12
#define WATCH_COLS          12
#define WATCH_MAX_PARTICLES 40      /* the JavaScript simulator allows 60; 40 keeps the O(n^2) pair loop cheap on an 8-bit core */
#define WATCH_MAX_SLOTS     72      /* worst case: 12 rows x 6 sub-slots (2 LEDs per sub-slot at 4.2 V) */
#define WATCH_MAX_OBS       8

typedef struct {
    int16_t  ax, ay, az;        /* milli-g */
    uint8_t  btn;               /* bit0 = left pressed, bit1 = right pressed */
    uint8_t  wake_strength;     /* 0 = no wrist-raise event this tick, 1..100 = how hard the raise was */
    uint8_t  tap;               /* double-tap event */
    uint8_t  ff;                /* free-fall event (logged only; it never wakes the display) */
    uint16_t vdd_mv;            /* supply, millivolts (3000 .. 4200) */
    uint16_t soc_pm;            /* state of charge, per mille (0 .. 1000) */
    uint8_t  bat_ok;            /* BAT_OK pin from the BQ25570: 1 = battery fine, 0 = low */
    uint8_t  solar_mw;          /* solar input, whole milliwatts (only used by the battery screen) */
    uint8_t  charging;
    uint8_t  ambient;           /* ambient light 0..100 (auto brightness) */
} watch_io_t;

/* What the matrix driver should do. Each slot sinks ONE row and sources up to m columns at the same time (the row pin
 * can only sink 10 mA). A full-level LED is on for on_q16/65536 of its slot, scaled by its framebuffer level / 255. */
typedef struct {
    uint8_t  n;                 /* number of slots in this frame (0 = display off) */
    uint8_t  m;                 /* LEDs per slot allowed by the 10 mA row-sink limit */
    uint16_t on_q16;            /* fraction of a slot a full-level LED stays on (Q16, 65536 = whole slot) */
    uint16_t needed_q16;        /* on-time fraction of the whole frame that keeps brightness constant vs VDD (Q16) */
    uint16_t achievable_q16;    /* what the slot count allows: min(needed, 1/n) (Q16) */
    uint8_t  limited;           /* 1 if the picture is too crowded to reach the wanted brightness */
    uint16_t i_led_ua;          /* LED current at this VDD, microamps */
    uint16_t avg_ua;            /* time-averaged LED current for this picture, microamps */
    struct { uint8_t row; uint16_t cols; } slot[WATCH_MAX_SLOTS];
} watch_scan_t;

/* ----- game state (public so the host tests can look inside; the firmware never needs to) ----- */
typedef struct { int16_t x, y; int32_t vx, vy; } particle_t;              /* x,y: 1/256 mm.  vx,vy: 1/256 mm/s */
typedef struct { particle_t p[WATCH_MAX_PARTICLES]; uint8_t n; int16_t flash; uint8_t bead_ring; int32_t bead_th_q8; int32_t bead_w; } part_game_t;
typedef struct { int32_t ang; uint8_t lane, k, passed; } obs_t;
typedef struct { obs_t obs[WATCH_MAX_OBS]; uint8_t nobs, lane, over, award; int32_t th; uint16_t passed, pts; int32_t spawn, flash; } run_game_t;
typedef struct { uint8_t lvl, over, award, last_k; uint16_t pts; uint32_t pos_q16, spd_q16, tol_q16; int16_t hit_flash; int32_t t; } tg_game_t;
typedef struct { uint8_t st, arm_held, win, was_false; int32_t t, wait; } qd_game_t;
typedef struct { uint32_t ph_q8; uint16_t stars[132]; } orb_game_t;   /* star brightness in Q8 */   /* ph_q8: phase in 1/256 of a binary angle; wraps harmlessly after ~13 minutes */
typedef struct { uint8_t has_res, c, d1, d2, h, m, s; uint16_t n; int16_t roll, cool, flash; int32_t age; } rng_game_t;
typedef struct { int32_t t; int16_t show; } pc_game_t;
typedef struct { uint8_t st, len, i, over, award, fside; uint32_t seq; int32_t t; uint16_t pts; int16_t flash; } sim_game_t;
typedef struct { uint8_t st, s1, s2, winner, award; int8_t dir; int32_t pos_q16, spd_q16, t; uint16_t pts; int16_t hit[2]; } pg_game_t;

typedef struct { uint8_t down, long_, chord, eat, raw; int32_t t, rep; } button_t;

typedef struct {
    uint8_t  mode, awake, locked, ind_only, dead, shaken;
    uint8_t  menu_on, menu_sel, menu_from; int32_t menu_t;
    uint32_t tms, idle;                 /* tms: free-running ms (blinking); idle: ms since the last user action */
    uint32_t rtc_ms;                    /* milliseconds since midnight */
    int16_t  lock_flash, peek, date_peek;
    uint16_t year; uint8_t month, day;
    uint8_t  set_field, cfg_sel, bat_view;
    uint8_t  tmr_run; uint32_t tmr_el;
    uint8_t  fun_g, fun_playing;
    uint8_t  set[10];                   /* CFG values, index = CFG number - 1 */
    uint8_t  pref_sand_mode, pref_orb_pat, pref_rng_mode, pref_pc_kind, pref_pg_mode;
    uint8_t  pref_pc_bpm, pref_pc_br;
    button_t b[2];
    int32_t  both_t; uint8_t lock_done;
    union { part_game_t part; run_game_t run; tg_game_t tg; qd_game_t qd; orb_game_t orb; rng_game_t rng; pc_game_t pc; sim_game_t sim; pg_game_t pg; } g;
} watch_t;

void              watch_init(uint32_t seed);
/* dt_real_ms: wall-clock ms since the previous call (buttons, blinking, games). dt_sim_ms: ms the real-time clock advanced
 * (equal to dt_real_ms in the watch; larger only when a simulator speeds the clock up). */
void              watch_step(uint16_t dt_real_ms, uint32_t dt_sim_ms, const watch_io_t *io);
const uint8_t    *watch_fb(void);       /* 144 bytes, row-major (row * 12 + col), brightness 0..255 */
const watch_scan_t *watch_scan(void);   /* the plan computed by the last watch_step() */
const watch_t    *watch_state(void);
void              watch_set_time(uint8_t h, uint8_t m, uint8_t s);
void              watch_set_date(uint16_t y, uint8_t mo, uint8_t d);
void              watch_set_cfg(uint8_t idx, uint8_t v);     /* idx 0..9 = CFG 1..10; used by tests and to load saved settings */
uint8_t           watch_weekday_iso(void);   /* Monday = 1 ... Sunday = 7 */
uint8_t           watch_awake(void);         /* 1 while the display is on (the MCU may sleep when 0) */
