/* buttons.h - the two buttons, the accelerometer interrupt pin and the BAT_OK pin (all on port E). */
#pragma once
#include <stdint.h>

extern volatile uint8_t pin_event;       /* a button or the accelerometer pin changed (set in the interrupt, wakes the chip from sleep) */
extern volatile uint8_t imu_int_event;   /* the accelerometer interrupt pin changed */

void    inputs_init(void);               /* pull-ups on the buttons, pin-change interrupts that also work in sleep */
uint8_t buttons_raw(void);               /* bit0 = left pressed, bit1 = right pressed (not debounced) */
uint8_t bat_ok_pin(void);                /* BQ25570 VBAT_OK: 1 = battery fine */
