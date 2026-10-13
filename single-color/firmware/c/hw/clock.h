/* clock.h - timekeeping and sleeping (AVR). The 32.768 kHz watch crystal on PF0/PF1 drives the real-time counter (RTC); it is the only time source that matters. */
#pragma once
#include <stdint.h>

void     clock_init(void);               /* main clock 4 MHz, crystal started (falls back to the internal 32 kHz oscillator if it does not start), RTC + periodic interrupt on */
uint8_t  clock_crystal_ok(void);         /* 1 = running from the crystal, 0 = fell back to the (inaccurate) internal oscillator */
uint32_t clock_elapsed_ms(void);         /* whole milliseconds since the previous call (the sub-millisecond remainder is kept) */
uint16_t clock_seed(void);               /* a number that changes from run to run (RTC counter) for the random generator */
void     clock_set_fast(uint8_t fast);   /* 1: wake 64 times a second (display on); 0: wake once a second (display off) */
uint8_t  clock_tick_pending(void);       /* periodic interrupt happened since the last call? (clears the flag) */
extern volatile uint8_t clock_tick_flag;   /* periodic interrupt happened (see main.c: it is checked with interrupts off just before sleeping, so no wake-up is lost) */
