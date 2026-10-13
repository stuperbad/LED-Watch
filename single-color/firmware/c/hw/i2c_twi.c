/* i2c_twi.c - I2C host on TWI0 (SDA = PA2, SCL = PA3, the default pins), polled, with time-outs so a missing or stuck sensor can never hang the watch. */
#include <avr/io.h>
#include "i2c.h"
#include "hw_config.h"

#define I2C_SCL_HZ 100000UL
/* datasheet: BAUD = F_CPU / (2 * f_SCL) - (5 + F_CPU * t_rise / 2), with t_rise about 300 ns -> 14 at 4 MHz */
#define I2C_BAUD ((uint8_t)(F_CPU_HZ / (2 * I2C_SCL_HZ) - 5 - (F_CPU_HZ / 1000000UL * 3 / 20)))
#define I2C_TIMEOUT 6000                    /* loop counts, about 10 ms: far longer than one byte takes (about 90 us) */

void i2c_init(void) {
    TWI0.MBAUD = I2C_BAUD;
    TWI0.MCTRLA = TWI_ENABLE_bm;
    TWI0.MSTATUS = TWI_BUSSTATE_IDLE_gc;
}

static uint8_t wait_flag(uint8_t mask) {    /* wait until a flag is set (or a bus error); 1 = flag */
    for (uint16_t t = 0; t < I2C_TIMEOUT; t++) {
        uint8_t s = TWI0.MSTATUS;
        if (s & (TWI_ARBLOST_bm | TWI_BUSERR_bm)) return 0;
        if (s & mask) return 1;
    }
    return 0;
}
static void bus_reset(void) { TWI0.MCTRLB = TWI_MCMD_STOP_gc; TWI0.MSTATUS = TWI_BUSSTATE_IDLE_gc | TWI_ARBLOST_bm | TWI_BUSERR_bm | TWI_WIF_bm | TWI_RIF_bm; }

uint8_t i2c_write_reg(uint8_t addr7, uint8_t reg, uint8_t value) {
    TWI0.MADDR = (uint8_t)(addr7 << 1);                                           /* START + address + write */
    if (!wait_flag(TWI_WIF_bm) || (TWI0.MSTATUS & TWI_RXACK_bm)) { bus_reset(); return 0; }
    TWI0.MDATA = reg;                         if (!wait_flag(TWI_WIF_bm) || (TWI0.MSTATUS & TWI_RXACK_bm)) { bus_reset(); return 0; }
    TWI0.MDATA = value;                       if (!wait_flag(TWI_WIF_bm) || (TWI0.MSTATUS & TWI_RXACK_bm)) { bus_reset(); return 0; }
    TWI0.MCTRLB = TWI_MCMD_STOP_gc;
    return 1;
}

uint8_t i2c_read_regs(uint8_t addr7, uint8_t reg, uint8_t *buf, uint8_t n) {
    TWI0.MADDR = (uint8_t)(addr7 << 1);                                           /* START + address + write, then the register to read */
    if (!wait_flag(TWI_WIF_bm) || (TWI0.MSTATUS & TWI_RXACK_bm)) { bus_reset(); return 0; }
    TWI0.MDATA = reg;                         if (!wait_flag(TWI_WIF_bm) || (TWI0.MSTATUS & TWI_RXACK_bm)) { bus_reset(); return 0; }
    TWI0.MADDR = (uint8_t)((addr7 << 1) | 1);                                     /* repeated START + address + read */
    for (uint8_t i = 0; i < n; i++) {
        if (!wait_flag(TWI_RIF_bm)) { bus_reset(); return 0; }
        buf[i] = TWI0.MDATA;                                                      /* reading the data register starts the next byte when we ack */
        if (i + 1 < n) TWI0.MCTRLB = TWI_ACKACT_ACK_gc | TWI_MCMD_RECVTRANS_gc;   /* more to come: ACK and continue */
        else           TWI0.MCTRLB = TWI_ACKACT_NACK_gc | TWI_MCMD_STOP_gc;       /* last byte: NACK and STOP */
    }
    return 1;
}
