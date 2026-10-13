/* i2c.h - the little I2C interface the accelerometer driver needs. The AVR version is i2c_twi.c; the PC tests use a pretend sensor instead. */
#pragma once
#include <stdint.h>

void    i2c_init(void);
uint8_t i2c_write_reg(uint8_t addr7, uint8_t reg, uint8_t value);             /* 1 = acknowledged, 0 = no answer / bus error */
uint8_t i2c_read_regs(uint8_t addr7, uint8_t reg, uint8_t *buf, uint8_t n);   /* register address is auto-incremented by the sensor; 1 = ok */
