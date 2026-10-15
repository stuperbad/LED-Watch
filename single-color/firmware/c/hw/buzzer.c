/* buzzer.c - piezo driver on TCA1 split mode, see buzzer.h. */
#include <avr/io.h>
#include "buzzer.h"
#include "hw_config.h"
#include "hw_pure.h"
#include "hwmap.h"

/* the board wiring (from the schematic via gen_pins.py) must be what this file assumes */
_Static_assert(HW_BUZ_A_PORT == 'B' && HW_BUZ_A_BIT == 4, "BUZ_A is PB4 = TCA1 WO4");
_Static_assert(HW_BUZ_B_PORT == 'B' && HW_BUZ_B_BIT == 5, "BUZ_B is PB5 = TCA1 WO5");

#define BUZ_MASK ((uint8_t)((1u << HW_BUZ_A_BIT) | (1u << HW_BUZ_B_BIT)))

static const uint8_t CLKSEL[8] = { TCA_SPLIT_CLKSEL_DIV1_gc, TCA_SPLIT_CLKSEL_DIV2_gc, TCA_SPLIT_CLKSEL_DIV4_gc, TCA_SPLIT_CLKSEL_DIV8_gc,
                                   TCA_SPLIT_CLKSEL_DIV16_gc, TCA_SPLIT_CLKSEL_DIV64_gc, TCA_SPLIT_CLKSEL_DIV256_gc, TCA_SPLIT_CLKSEL_DIV1024_gc };
static uint16_t current_hz;

static void silent(void) {
    TCA1.SPLIT.CTRLB = 0;                                     /* compare outputs off: the pins follow the port registers again */
    TCA1.SPLIT.CTRLA = 0;                                     /* timer stopped */
    PORTB.PIN5CTRL = 0;                                       /* no inversion while silent, so both pins are low */
    PORTB.OUTCLR = BUZ_MASK;
    current_hz = 0;
}

void buzzer_init(void) {
    PORTB.OUTCLR = BUZ_MASK;
    PORTB.DIRSET = BUZ_MASK;
    PORTB.PIN4CTRL = 0;
    PORTB.PIN5CTRL = 0;
    TCA1.SPLIT.CTRLA = 0;
    TCA1.SPLIT.CTRLD = TCA_SPLIT_SPLITM_bm;                   /* split mode: two independent 8-bit timers; the high one (HPER, HCMPn) drives WO3..WO5 */
    current_hz = 0;
}

void buzzer_set(uint16_t hz) {
    if (hz == current_hz) return;
    buzzer_plan_t p;
    if (!hz || !buzzer_plan(hz, F_CPU_HZ, &p)) { silent(); return; }
    TCA1.SPLIT.CTRLA = 0;                                     /* reconfigure with the timer stopped */
    TCA1.SPLIT.HPER = p.per;
    TCA1.SPLIT.HCMP1 = (uint8_t)((p.per + 1u) / 2u);          /* equal compare values on both channels = 50 % duty */
    TCA1.SPLIT.HCMP2 = (uint8_t)((p.per + 1u) / 2u);
    TCA1.SPLIT.HCNT = 0;
    PORTB.PIN5CTRL = PORT_INVEN_bm;                           /* PB5 swings opposite to PB4 */
    TCA1.SPLIT.CTRLB = TCA_SPLIT_HCMP1EN_bm | TCA_SPLIT_HCMP2EN_bm;   /* only WO4 and WO5: PB0..PB3 stay LED columns */
    TCA1.SPLIT.CTRLA = CLKSEL[p.div_idx] | TCA_SPLIT_ENABLE_bm;
    current_hz = hz;
}
