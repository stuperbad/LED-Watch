/* Toolchain smoke test: drive one LED of the matrix using the generated pin map (../pins.h).
   Row pin low (sink) + column pin high (source) lights one LED through its 220 ohm resistor.
   Row 0 = PC2 and column 0 = PA0 are the hour-ring LED at 12 o'clock (H12). */
#include <avr/io.h>
#include <util/delay.h>
#include "../pins.h"

#define PORT_OF(p, b)   (PORT##p)
/* pins.h gives "PORTx, bit": these helpers split it */
#define _DIR(port, bit)  (port.DIRSET = (1 << (bit)))
#define DIRSET_PIN(x)    _DIR(x)
#define _HI(port, bit)   (port.OUTSET = (1 << (bit)))
#define _LO(port, bit)   (port.OUTCLR = (1 << (bit)))
#define HI(x)            _HI(x)
#define LO(x)            _LO(x)

int main(void)
{
    _PROTECTED_WRITE(CLKCTRL.OSCHFCTRLA, CLKCTRL_FRQSEL_4M_gc);   /* 4 MHz internal oscillator */
    DIRSET_PIN(PIN_ROW0);
    DIRSET_PIN(PIN_COL0_MCU);
    HI(PIN_ROW0);                                                 /* row off (high) */
    for (;;) {
        LO(PIN_ROW0); HI(PIN_COL0_MCU);                           /* LED on  */
        _delay_ms(250);
        HI(PIN_ROW0); LO(PIN_COL0_MCU);                           /* LED off */
        _delay_ms(750);
    }
}
