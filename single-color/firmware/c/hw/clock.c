/* clock.c - clocks, RTC and sleep (AVR128DB48).
 *
 * TWO CLOCKS
 *   - The main clock is the internal 4 MHz oscillator. It runs the CPU and the LED scan. It is only about +-1-2 % accurate, which does not matter for animation.
 *   - The 32.768 kHz crystal runs the real-time counter (RTC). RTC.CNT counts 32768 ticks per second and keeps running while the chip sleeps. ALL timekeeping
 *     (the time of day, the stopwatch, button timing, game timing) is derived from RTC.CNT, so it is crystal-accurate (about 20 ppm = 2 seconds a day).
 *
 * WAKING UP
 *   The RTC also has a "periodic interrupt timer" (PIT) that interrupts every 2^n crystal cycles. With the display on we use 512 cycles (15.6 ms = 64 times a
 *   second) as the heartbeat of the main loop; with the display off we use 32768 cycles (once a second), so the chip wakes only to count time. Button and
 *   accelerometer pins can also wake it immediately (see main.c). The PIT and the RTC counter share one free-running prescaler, so changing the PIT period
 *   never disturbs RTC.CNT.
 */
#include <avr/io.h>
#include <avr/interrupt.h>
#include "clock.h"
#include "hw_config.h"
#include "hw_pure.h"

volatile uint8_t clock_tick_flag;                 /* set by the periodic interrupt; main.c checks it just before sleeping */
static uint8_t crystal = 0;
static uint16_t last_cnt;
static uint32_t acc_q12;

ISR(RTC_PIT_vect) { RTC.PITINTFLAGS = RTC_PI_bm; clock_tick_flag = 1; }

static uint16_t read_cnt(void) {                  /* RTC.CNT is in the slow clock domain: read until two reads agree */
    uint16_t a, b;
    do { a = RTC.CNT; b = RTC.CNT; } while (a != b);
    return a;
}

void clock_init(void) {
    _PROTECTED_WRITE(CLKCTRL.OSCHFCTRLA, CLKCTRL_FRQSEL_4M_gc);                       /* 4 MHz internal oscillator */
    /* crystal on PF0/PF1: crystal mode (SEL = 0), normal drive (LPMODE = 0, more reliable start-up; try LPMODE = 1 to save current once it works),
     * 32k cycles start-up time (1 s), keeps running in standby sleep */
    _PROTECTED_WRITE(CLKCTRL.XOSC32KCTRLA, CLKCTRL_CSUT_32K_gc | CLKCTRL_RUNSTDBY_bm | CLKCTRL_ENABLE_bm);
    uint32_t guard = 0;
    while (!(CLKCTRL.MCLKSTATUS & CLKCTRL_XOSC32KS_bm) && ++guard < 1500000UL) { }   /* about 3 s at 4 MHz */
    crystal = (CLKCTRL.MCLKSTATUS & CLKCTRL_XOSC32KS_bm) ? 1 : 0;
    RTC.CLKSEL = crystal ? RTC_CLKSEL_XOSC32K_gc : RTC_CLKSEL_OSC32K_gc;                /* fallback: internal 32 kHz oscillator, inaccurate */
    RTC.PER = 0xFFFF;
    RTC.CTRLA = RTC_PRESCALER_DIV1_gc | RTC_RUNSTDBY_bm | RTC_RTCEN_bm;
    RTC.PITINTCTRL = RTC_PI_bm;
    while (RTC.PITSTATUS & RTC_CTRLBUSY_bm) { }
    RTC.PITCTRLA = RTC_PERIOD_CYC512_gc | RTC_PITEN_bm;
    last_cnt = read_cnt(); acc_q12 = 0;
}

uint8_t clock_crystal_ok(void) { return crystal; }
uint16_t clock_seed(void) { return read_cnt(); }

uint32_t clock_elapsed_ms(void) {
    uint16_t now = read_cnt();
    uint16_t delta = (uint16_t)(now - last_cnt);                                       /* wraps correctly as long as we look at least every 2 s */
    last_cnt = now;
    return ticks_to_ms(delta, &acc_q12);
}

void clock_set_fast(uint8_t fast) {
    while (RTC.PITSTATUS & RTC_CTRLBUSY_bm) { }
    RTC.PITCTRLA = (uint8_t)((fast ? RTC_PERIOD_CYC512_gc : RTC_PERIOD_CYC32768_gc) | RTC_PITEN_bm);
}

uint8_t clock_tick_pending(void) { uint8_t t; cli(); t = clock_tick_flag; clock_tick_flag = 0; sei(); return t; }
