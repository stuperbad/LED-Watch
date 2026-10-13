/* hw_pure.c - see hw_pure.h */
#include "hw_pure.h"
#include "hw_config.h"

uint8_t debounce_step(debounce_t *d, uint8_t raw) { if (raw == d->last) d->stable = raw; d->last = raw; return d->stable; }

/* Resting LiPo voltage -> charge, piecewise linear through typical points. The curve is flat in the middle, so this is only good to about +-10 %;
 * under load the voltage sags and the number reads low. It is only used for the battery-bar display and the "low battery" screens. */
uint16_t soc_from_mv(uint16_t mv) {
    static const uint16_t V[6] = { 3000, 3300, 3650, 3800, 4000, 4200 };
    static const uint16_t S[6] = { 0, 50, 200, 500, 800, 1000 };
    if (mv <= V[0]) return 0;
    if (mv >= V[5]) return 1000;
    uint8_t i = 1; while (mv > V[i]) i++;
    return (uint16_t)(S[i - 1] + (uint32_t)(S[i] - S[i - 1]) * (uint32_t)(mv - V[i - 1]) / (uint32_t)(V[i] - V[i - 1]));
}

uint16_t adc_vdd_mv(uint16_t adc12, uint16_t cal_permille) {
    uint32_t mv = (uint32_t)adc12 * 10240UL / 4095UL;            /* x10 for the VDD/10 divider, x1024 mV reference, 12-bit full scale */
    return (uint16_t)(mv * cal_permille / 1000UL);
}

uint32_t ticks_to_ms(uint16_t ticks, uint32_t *acc_q12) {         /* 1 tick = 1000/32768 ms = 125/4096 ms */
    *acc_q12 += (uint32_t)ticks * 125UL;
    uint32_t ms = *acc_q12 >> 12; *acc_q12 &= 0xFFFUL;
    return ms;
}

int16_t imu_raw_to_mg(int16_t raw16) { return (int16_t)(((int32_t)raw16 * 125L) >> 10); }   /* 4000 / 32768 = 125 / 1024 exactly */

void imu_map_axes(const int16_t s[3], int16_t *x, int16_t *y, int16_t *z) {
    *x = (int16_t)(IMU_MAP_X_SIGN * s[IMU_MAP_X_AXIS]);
    *y = (int16_t)(IMU_MAP_Y_SIGN * s[IMU_MAP_Y_AXIS]);
    *z = (int16_t)(IMU_MAP_Z_SIGN * s[IMU_MAP_Z_AXIS]);
}

static uint32_t isqrt(uint32_t v) { uint32_t r = 0, b = 1UL << 30; while (b > v) b >>= 2; while (b) { if (v >= r + b) { v -= r + b; r = (r >> 1) + b; } else r >>= 1; b >>= 2; } return r; }

void raise_arm(raise_t *r) { r->armed = 1; r->n = 0; r->max_d = 0; }

/* A wrist raise is a big change of the gravity vector that ends with the watch face up. Compare every sample of the window with the first one, remember
 * the biggest difference; at the end of the window it counts as a raise only if the watch is now facing up (z large). The result is a 0..100 strength that the
 * core compares with the "raise sensitivity" setting (30 / 50 / 70). */
int16_t raise_feed(raise_t *r, int16_t x, int16_t y, int16_t z) {
    if (!r->armed) return -1;
    if (r->n == 0) { r->x0 = x; r->y0 = y; r->z0 = z; }
    int32_t dx = (int32_t)x - r->x0, dy = (int32_t)y - r->y0, dz = (int32_t)z - r->z0;
    int32_t d = (int32_t)isqrt((uint32_t)(dx * dx + dy * dy + dz * dz));
    if (d > r->max_d) r->max_d = d;
    if (++r->n < RAISE_WINDOW_SAMPLES) return -1;
    r->armed = 0;
    if (z < RAISE_MIN_Z_MG) return 0;
    int32_t s = r->max_d / RAISE_MG_PER_PERCENT;
    return (int16_t)(s > 100 ? 100 : s);
}
