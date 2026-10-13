/* buttons.c - inputs on port E.
 *
 * Buttons: the switch connects the pin to ground, so the pin needs its internal pull-up and reads LOW while pressed.
 * Wake-up: a pin interrupt can wake the chip from sleep. The "both edges" setting works in every sleep mode (some pins only wake on both edges or on a low
 * level while the peripheral clock is stopped), so both edges is used for all three pins. The interrupt routine only records that something happened;
 * the main loop then reads the real state.
 */
#include <avr/io.h>
#include <avr/interrupt.h>
#include "buttons.h"
#include "hwmap.h"

#define BIT_L (1u << HW_BTN1_BIT)
#define BIT_R (1u << HW_BTN2_BIT)
#define BIT_I (1u << HW_IMU_INT_BIT)
#define BIT_B (1u << HW_BAT_OK_BIT)
_Static_assert(HW_BTN1_PORT == 'E' && HW_BTN2_PORT == 'E' && HW_IMU_INT_PORT == 'E' && HW_BAT_OK_PORT == 'E', "buttons, IMU interrupt and BAT_OK are expected on port E");

volatile uint8_t pin_event;
volatile uint8_t imu_int_event;

void inputs_init(void) {
    PORTE.DIRCLR = (uint8_t)(BIT_L | BIT_R | BIT_I | BIT_B);
    (&PORTE.PIN0CTRL)[HW_BTN1_BIT] = PORT_PULLUPEN_bm | PORT_ISC_BOTHEDGES_gc;
    (&PORTE.PIN0CTRL)[HW_BTN2_BIT] = PORT_PULLUPEN_bm | PORT_ISC_BOTHEDGES_gc;
    (&PORTE.PIN0CTRL)[HW_IMU_INT_BIT] = PORT_ISC_BOTHEDGES_gc;                 /* the sensor drives this pin actively */
    (&PORTE.PIN0CTRL)[HW_BAT_OK_BIT] = PORT_ISC_INTDISABLE_gc;                 /* just read it; the BQ25570 drives it */
    PORTE.INTFLAGS = 0xFF;
}

ISR(PORTE_PORT_vect) {
    uint8_t f = PORTE.INTFLAGS;
    PORTE.INTFLAGS = f;
    if (f & BIT_I) imu_int_event = 1;
    pin_event = 1;
}

uint8_t buttons_raw(void) { uint8_t in = (uint8_t)~PORTE.IN; return (uint8_t)(((in & BIT_L) ? 1 : 0) | ((in & BIT_R) ? 2 : 0)); }
uint8_t bat_ok_pin(void) { return (PORTE.IN & BIT_B) ? 1 : 0; }
