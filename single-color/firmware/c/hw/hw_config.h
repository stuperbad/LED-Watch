/* hw_config.h - every number in the hardware layer that has to be checked or tuned on the real board.
 * They are starting values chosen from the datasheets; nothing here has run on hardware yet. */
#pragma once

#define F_CPU_HZ            4000000UL   /* internal oscillator; the 32 kHz crystal keeps the time, this clock only paces animation */

/* ---- LED matrix scan ---- */
#define SCAN_FRAME_US       8000        /* target time for one pass over all slots (8 ms = 125 Hz refresh) */
#define SCAN_SLOT_MIN_US    250         /* never make a slot shorter than this (interrupt load) */
#define SCAN_SLOT_MAX_US    3000        /* ... or longer than this */

/* ---- supply voltage ---- */
#define VDD_CAL_PERMILLE    1000        /* multiply the ADC result by this/1000. The VDD/10 divider is only +-10 % accurate (datasheet
                                           Table 39-24), so measure the real battery voltage with a multimeter once and correct it here. */

/* ---- accelerometer LIS2DW12 on I2C (SA0 = GND -> address 0x18, INT1 -> PE0) ---- */
#define IMU_I2C_ADDR        0x18
/* How the chip is mounted: board axis X (to 3 o'clock) / Y (to 12 o'clock) / Z (out of the glass) = sign * sensor axis.
 * Axis index 0 = sensor X, 1 = sensor Y, 2 = sensor Z. UNKNOWN until checked on the board: lay the watch flat face-up, z must read about +1000;
 * lift the 12 o'clock edge, y must go positive; lift the 3 o'clock edge, x must go positive. Change these until it does. */
#define IMU_MAP_X_AXIS 0
#define IMU_MAP_X_SIGN (+1)
#define IMU_MAP_Y_AXIS 1
#define IMU_MAP_Y_SIGN (+1)
#define IMU_MAP_Z_AXIS 2
#define IMU_MAP_Z_SIGN (+1)

#define IMU_AWAKE_CTRL1     0x41        /* ODR 50 Hz (0100), low-power mode (00), low-power mode 2 = 14-bit (01) */
#define IMU_SLEEP_CTRL1_NOTAP 0x21      /* ODR 12.5 Hz (0010), low-power mode 2: about 1 uA, wake-up only */
#define IMU_SLEEP_CTRL1_TAP   0x51      /* ODR 100 Hz (0101), low-power mode 2: about 5 uA, needed to see taps */
#define IMU_WAKE_THS        3           /* wake-up threshold, 1 LSB = full scale / 64 = 62.5 mg at +-4 g -> 187 mg of change */
#define IMU_TAP_THS_Z       6           /* tap threshold on Z, 1 LSB = 125 mg at +-4 g -> 0.75 g (tune: lower = lighter tap) */
#define IMU_INT_DUR         0x15        /* double-tap: latency 1, quiet 1, shock 1 (see datasheet Table 66/67) */

/* ---- wrist-raise detection (done in firmware from accelerometer samples) ---- */
#define RAISE_WINDOW_SAMPLES 12         /* about 240 ms at the 50 Hz tick */
#define RAISE_MG_PER_PERCENT 15         /* strength = size of the change in mg / this, capped at 100 (so 1500 mg of change = 100) */
#define RAISE_MIN_Z_MG       400         /* the watch must end up facing up at least this much (z) */

/* ---- timing ---- */
#define TICK_FAST_MS        16          /* display on: 64 Hz RTC periodic interrupt (512 cycles of 32.768 kHz = 15.6 ms) */
#define MOTION_WINDOW_MS    700         /* after an accelerometer interrupt keep the fast loop running this long to classify the motion */
#define VDD_PERIOD_FAST_MS  1000
#define VDD_PERIOD_SLOW_MS  30000
