/* vbat.h - measuring the supply (= battery) voltage with the MCU's own ADC. No extra pin is needed: the ADC has an internal VDD/10 channel. */
#pragma once
#include <stdint.h>
void     vbat_init(void);
uint16_t vbat_read_mv(void);      /* supply voltage in millivolts (accuracy about +-10 % until VDD_CAL_PERMILLE is set from a multimeter reading) */
