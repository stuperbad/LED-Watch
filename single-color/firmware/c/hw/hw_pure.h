/* hw_pure.h - the small calculations of the hardware layer that need no hardware (so the PC tests can check them). */
#pragma once
#include <stdint.h>

/* ---- button debounce: a change is accepted once two consecutive samples agree ---- */
typedef struct { uint8_t last, stable; } debounce_t;
uint8_t  debounce_step(debounce_t *d, uint8_t raw);

/* ---- battery ---- */
uint16_t soc_from_mv(uint16_t mv);                          /* state of charge in per mille from the cell voltage (single LiPo cell, resting) */
uint16_t adc_vdd_mv(uint16_t adc12, uint16_t cal_permille); /* ADC reading of VDD/10 against the 1.024 V reference -> millivolts */

/* ---- time: the RTC counts 32768 ticks per second; turn elapsed ticks into whole milliseconds without losing the remainder ---- */
uint32_t ticks_to_ms(uint16_t ticks, uint32_t *acc_q12);

/* ---- accelerometer ---- */
int16_t  imu_raw_to_mg(int16_t raw16);                      /* LIS2DW12 at +-4 g, data left-justified in 16 bits: 0.122 mg per count */
void     imu_map_axes(const int16_t sensor_mg[3], int16_t *x, int16_t *y, int16_t *z);   /* sensor axes -> watch axes (see hw_config.h) */

/* ---- wrist-raise classifier: watch a short window of samples after the sensor reported motion ---- */
typedef struct { uint8_t n, armed; int16_t x0, y0, z0; int32_t max_d; } raise_t;
void     raise_arm(raise_t *r);                             /* start collecting at the next sample */
int16_t  raise_feed(raise_t *r, int16_t x, int16_t y, int16_t z);   /* -1 while collecting; when the window ends: strength 0..100 (0 = not a raise) */
