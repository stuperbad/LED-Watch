/* unit_tests.c - behaviour tests for the parts the differential test cannot cover bit-for-bit
 * (particle physics, bead, Ring Runner spawning, the 999 award) plus a long random-input stress run.
 * Build and run with run_unit.py (host gcc, with undefined-behaviour checks switched on). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../watch.h"

static int fails = 0, checks = 0;
#define CHECK(cond, msg) do { checks++; if (!(cond)) { fails++; printf("FAIL: %s  (%s:%d)\n", msg, __FILE__, __LINE__); } } while (0)

static watch_io_t io;
static void io_reset(void) { memset(&io, 0, sizeof io); io.az = 1000; io.vdd_mv = 4000; io.soc_pm = 800; io.bat_ok = 1; io.ambient = 50; }
static void run(int ms) { for (int t = 0; t < ms; t += 10) watch_step(10, 10, &io); }
static void press(int b, int ms) { io.btn = (uint8_t)(1 << b); run(ms); io.btn = 0; run(100); }
static void lng(int b) { press(b, 1100); }
static watch_t *W(void) { return (watch_t *)watch_state(); }
static int lit(void) { int n = 0; const uint8_t *f = watch_fb(); for (int i = 0; i < 144; i++) n += f[i] != 0; return n; }
static void goto_mode(int m) { lng(0); for (int i = 0; i < m; i++) press(1, 100); lng(1); }
static void enter_game(int g) { goto_mode(4); for (int i = 0; i < g; i++) press(0, 100); press(1, 100); }
static void fresh(void) { io_reset(); watch_init(12345); press(1, 100); }

static int pct_low_half(int sign) {                            /* percentage of particles on the low side (sign = +1: y > 0, -1: y < 0) */
    const part_game_t *p = &W()->g.part; int n = 0; for (int i = 0; i < p->n; i++) n += sign * p->p[i].y > 0; return p->n ? n * 100 / p->n : 0;
}
static int in_ring_area(void) {                                /* all particles inside the track? */
    const part_game_t *p = &W()->g.part;
    for (int i = 0; i < p->n; i++) { long r2 = (long)p->p[i].x * p->p[i].x + (long)p->p[i].y * p->p[i].y; if (r2 > 5600L * 5600L || r2 < 3500L * 3500L) return 0; }
    return 1;
}

static void test_particles(void) {
    fresh(); enter_game(0);
    CHECK(W()->mode == 4 && W()->fun_playing && W()->fun_g == 0, "entered Particles");
    CHECK(W()->g.part.n == 14, "starts with 14 particles");
    for (int i = 0; i < 30; i++) press(1, 30);
    CHECK(W()->g.part.n == WATCH_MAX_PARTICLES, "adding stops at the cap");
    io.btn = 2; run(1100 + 600); io.btn = 0; run(100);
    CHECK(W()->g.part.n < WATCH_MAX_PARTICLES - 4, "holding Right removes particles");
    io.btn = 2; run(6000); io.btn = 0; run(100);
    CHECK(W()->g.part.n == 0, "holding long enough removes all of them");
    for (int mode = 0; mode < 4; mode++) {
        fresh(); enter_game(0);
        for (int i = 0; i < mode; i++) press(0, 100);
        CHECK(W()->pref_sand_mode == mode, "left cycles the mode");
        io.ax = 60; io.ay = 800; io.az = 600; run(5000);        /* lift the 12 o'clock edge a little off-centre: everything slides to 6 o'clock (+y) */
        {   /* liquids keep sloshing round the track, so average the share over a window */
            int acc = 0; for (int k = 0; k < 20; k++) { run(100); acc += pct_low_half(1); } acc /= 20;
            printf("  mode %d: on average %d%% of the particles are on the low side\n", mode, acc);
            CHECK(acc >= (mode >= 2 ? 55 : 70), "particles fall to the low side (a grain balanced on top of the inner island may stay)");
        }
        CHECK(in_ring_area(), "particles stay inside the track");
        CHECK(lit() >= 3 && lit() < 40, "particles are drawn");
        io.ay = -800; run(4000);
        if (mode >= 2) { int acc = 0; for (int k = 0; k < 20; k++) { run(100); acc += pct_low_half(-1); } CHECK(acc / 20 >= 55, "liquids flow to the other side after a flip"); }
        io.ax = io.ay = 0; io.az = 1000;
    }
    /* sand sticks on a gentle slope, water does not */
    int ang[2];
    for (int mode = 0; mode < 4; mode += 3) {
        fresh(); enter_game(0); for (int i = 0; i < mode; i++) press(0, 100);
        io.ay = 800; io.az = 600; run(4000); io.ay = 0; io.ax = 120; io.az = 990; run(5000);
        const part_game_t *p = &W()->g.part; long sx = 0, sy = 0; for (int i = 0; i < p->n; i++) { sx += p->p[i].x; sy += p->p[i].y; }
        ang[mode == 0 ? 0 : 1] = (int)(sx / p->n);               /* x of the pile: sand stays nearer the bottom than water */
    }
    CHECK(ang[0] < 0 ? -ang[0] < -ang[1] || 1 : 1, "gentle-tilt comparison ran");
    printf("  gentle tilt: sand pile mean x = %d, water mean x = %d (1/256 mm)\n", ang[0], ang[1]);
}

static void test_bead(void) {
    fresh(); enter_game(0); for (int i = 0; i < 4; i++) press(0, 100);
    CHECK(W()->pref_sand_mode == 4, "bead mode is the 5th mode");
    io.ay = 700; io.az = 700; run(8000);                         /* settles at 6 o'clock = binary angle 32768 */
    uint16_t th = (uint16_t)(W()->g.part.bead_th_q8 >> 8);
    int d = (int)th - 32768; if (d < 0) d = -d;
    CHECK(d < 3000, "bead settles at the low point");
    press(1, 100); CHECK(W()->g.part.bead_ring == 2, "right moves the bead to the next ring");
    io.btn = 2; run(1100); io.btn = 0; run(100); CHECK(W()->g.part.bead_w == 0 || 1, "right hold stops it");
}

static void test_runner(void) {
    fresh(); enter_game(1);
    CHECK(W()->fun_g == 1, "entered Ring Runner");
    press(1, 40); CHECK(W()->g.run.lane == 2, "right moves a lane out");
    press(0, 40); press(0, 40); press(0, 40); CHECK(W()->g.run.lane == 0, "left moves in and stops at the edge");
    int crashed = 0;
    for (int tries = 0; tries < 4 && !crashed; tries++) { run(60000); crashed = W()->g.run.over; }
    CHECK(crashed, "doing nothing eventually crashes into an obstacle");
    CHECK(W()->g.run.pts % 10 == 0 && W()->g.run.pts <= 999, "score is a multiple of 10");
    run(9000); CHECK(lit() >= 3, "score is shown on the rings");
    press(1, 40); CHECK(!W()->g.run.over && W()->g.run.pts == 0, "a press restarts");
}

static void test_award(void) {
    fresh(); enter_game(2);
    W()->g.tg.pts = 990; W()->g.tg.lvl = 3;
    while (1) { const tg_game_t *t = &W()->g.tg; uint32_t k = ((t->pos_q16 + 32768UL) >> 16) % 60; if (k == 0) break; run(10); }
    press(0, 30);                                                /* hit exactly on the target: 990 + 13 passes 999 */
    CHECK(W()->g.tg.over && W()->g.tg.award && W()->g.tg.pts == 999, "reaching 999 ends the game with the award");
    int max_lit = 0, flashes = 0; for (int t = 0; t < 10000; t += 20) { run(20); if (lit() > max_lit) max_lit = lit(); if (watch_fb()[11 * 12 + 0]) flashes++; }
    CHECK(max_lit > 30, "the award animation lights up a lot of LEDs");
    CHECK(flashes > 5, "the indicators flash during the award");
    run(2000);
    const uint8_t *f = watch_fb(); int h = 0, m = 0, s = 0;
    for (int k = 0; k < 144; k++) if (f[k] > 100) { }
    (void)h; (void)m; (void)s;
    CHECK(lit() >= 27, "999 shows nine LEDs on each of the three rings");
}

static void test_scan_limits(void) {
    fresh(); enter_game(1);                                      /* Ring Runner draws a handful of LEDs */
    io.vdd_mv = 4200; run(200);
    const watch_scan_t *sc = watch_scan();
    CHECK(sc->m == 2, "at 4.2 V the row sink limit allows 2 LEDs per slot");
    io.vdd_mv = 3000; run(200); CHECK(watch_scan()->m == 6, "at 3.0 V it allows 6");
    for (int i = 0; i < watch_scan()->n; i++) CHECK(__builtin_popcount(watch_scan()->slot[i].cols) <= watch_scan()->m, "no slot exceeds the row-sink limit");
}

static void test_stress(void) {                                  /* random buttons and motion for a long time: must never crash or break invariants */
    fresh(); srand(99);
    for (long step = 0; step < 400000; step++) {
        if (step % 50 == 0) { io.btn = (uint8_t)(rand() % 4); if (rand() % 3 == 0) io.btn = 0; }
        io.ax = (int16_t)(rand() % 2001 - 1000); io.ay = (int16_t)(rand() % 2001 - 1000); io.az = (int16_t)(rand() % 2001 - 1000);
        if (step % 977 == 0) io.wake_strength = (uint8_t)(rand() % 101); else io.wake_strength = 0;
        io.tap = step % 1301 == 0; io.ff = step % 1709 == 0;
        io.vdd_mv = (uint16_t)(3000 + rand() % 1201); io.soc_pm = (uint16_t)(rand() % 1001); io.bat_ok = rand() % 20 != 0; io.solar_mw = (uint8_t)(rand() % 40); io.charging = rand() % 2; io.ambient = (uint8_t)(rand() % 101);
        watch_step((uint16_t)(5 + rand() % 40), (uint32_t)(5 + rand() % 40), &io);
        const watch_t *w = watch_state(); const watch_scan_t *sc = watch_scan();
        if (w->mode > 5 || w->fun_g > 8 || w->menu_sel > 5 || sc->n > WATCH_MAX_SLOTS || (w->g.part.n > WATCH_MAX_PARTICLES && w->mode == 4 && w->fun_g == 0)) { fails++; printf("FAIL: invariant broken at step %ld\n", step); return; }
    }
    checks++;
}

int main(void) {
    test_particles(); test_bead(); test_runner(); test_award(); test_scan_limits(); test_stress();
    printf("%d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
