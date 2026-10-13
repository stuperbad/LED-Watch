/* imu.h - LIS2DW12 accelerometer driver (I2C address 0x18, interrupt INT1 -> PE0). Register facts are from ST DS11811 Rev 9. */
#pragma once
#include <stdint.h>

#define IMU_EV_FF      0x01     /* free-fall (never wakes the display) */
#define IMU_EV_WAKEUP  0x02     /* motion above the wake-up threshold */
#define IMU_EV_TAP1    0x04     /* single tap */
#define IMU_EV_TAP2    0x08     /* double tap */

uint8_t imu_init(void);                              /* 1 = sensor found (WHO_AM_I = 0x44) and configured, 0 = not answering; starts in the awake profile */
void    imu_profile_awake(void);                     /* 50 Hz samples for games and shake detection */
void    imu_profile_sleep(uint8_t tap_enabled);      /* about 1 uA (12.5 Hz) or 5 uA (100 Hz, needed to see double-taps); interrupts on */
uint8_t imu_read_mg(int16_t *x, int16_t *y, int16_t *z);   /* acceleration in the watch frame, milli-g; 0 if the read failed */
uint8_t imu_events(void);                            /* reads ALL_INT_SRC, which also clears the latched interrupt; returns IMU_EV_* bits */
