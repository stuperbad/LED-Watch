/* vbat.c - supply voltage through the ADC's internal "VDD / 10" input, measured against the internal 1.024 V reference.
 * A 12-bit reading r means VDD = r * 10 * 1.024 V / 4095. The datasheet gives the divider only +-10 % accuracy, so VDD_CAL_PERMILLE (hw_config.h) is a
 * correction factor to set once with a multimeter. The ADC clock is 4 MHz / 8 = 500 kHz, the maximum allowed with this reference. */
#include <avr/io.h>
#include "vbat.h"
#include "hw_config.h"
#include "hw_pure.h"

void vbat_init(void) {
    VREF.ADC0REF = VREF_REFSEL_1V024_gc;
    ADC0.CTRLC = ADC_PRESC_DIV8_gc;
    ADC0.SAMPCTRL = 16;                                    /* a longer sample time: the divider is a high-impedance source */
    ADC0.MUXPOS = ADC_MUXPOS_VDDDIV10_gc;
}

uint16_t vbat_read_mv(void) {
    ADC0.CTRLA = ADC_ENABLE_bm;
    uint32_t sum = 0;
    for (uint8_t i = 0; i < 4; i++) {                      /* average four readings; the first also gives the reference time to settle */
        ADC0.COMMAND = ADC_STCONV_bm;
        for (uint16_t t = 0; t < 20000 && !(ADC0.INTFLAGS & ADC_RESRDY_bm); t++) { }
        sum += ADC0.RES;                                   /* reading RES clears the ready flag */
    }
    ADC0.CTRLA = 0;                                        /* off again: the ADC costs current */
    return adc_vdd_mv((uint16_t)(sum / 4), VDD_CAL_PERMILLE);
}
