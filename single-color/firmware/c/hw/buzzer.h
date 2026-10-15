/* buzzer.h - drives the Murata piezo sounder PKMCS0909E4000-R1 (AVR only).
 *
 * The piezo sits between PB4 (BUZ_A) and PB5 (BUZ_B). Both pins are outputs of timer TCA1 in SPLIT mode (the 8-bit "high" timer, compare channels
 * HCMP1 -> WO4 = PB4 and HCMP2 -> WO5 = PB5, default PORTB routing). Both channels get the same compare value (50 % duty) and PB5's pin output is inverted
 * (PORTB.PIN5CTRL.INVEN), so the two pins swing in opposite phase: about 2 x 3.3 V = 6.6 V across the piezo. When silent both pins are driven low and
 * the inversion is switched off, so there is never a DC voltage across the piezo. The timer only runs while a tone plays (it stops in standby sleep). */
#pragma once
#include <stdint.h>

void buzzer_init(void);                 /* both pins low, timer stopped */
void buzzer_set(uint16_t hz);           /* 0 = silent; otherwise start / change the tone (about 1 kHz to 8 kHz; the piezo is loudest near 4 kHz) */
