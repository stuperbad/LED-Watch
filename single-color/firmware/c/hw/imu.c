/* imu.c - LIS2DW12 driver. Every register address and bit below is from the ST datasheet (DS11811 Rev 9, section 8), saved in datasheets/LIS2DW12.txt.
 *
 *   0x0F WHO_AM_I            reads 0x44
 *   0x20 CTRL1               ODR[7:4] | MODE[3:2] | LP_MODE[1:0]       (ODR 0 = power-down)
 *   0x21 CTRL2               SOFT_RESET bit6, BDU bit3 (output registers update together), IF_ADD_INC bit2 (address auto-increment)
 *   0x22 CTRL3               LIR bit4 (interrupt stays high until read), H_LACTIVE bit3, PP_OD bit5
 *   0x23 CTRL4_INT1_PAD_CTRL INT1_WU bit5 (wake-up), INT1_FF bit4, INT1_TAP bit3 (double tap)
 *   0x25 CTRL6               FS[5:4]: 01 = +-4 g
 *   0x28..0x2D OUT_X/Y/Z     16-bit two's complement, left-justified, low byte first
 *   0x30..0x32 TAP_THS_X/Y/Z threshold 5 bits; Z register bit7/6/5 = TAP_X/Y/Z_EN
 *   0x33 INT_DUR             LATENCY[7:4] | QUIET[3:2] | SHOCK[1:0]
 *   0x34 WAKE_UP_THS         bit7 SINGLE_DOUBLE_TAP, bit6 SLEEP_ON, WK_THS[5:0]
 *   0x35 WAKE_UP_DUR         WAKE_DUR[6:5], STATIONARY bit4, SLEEP_DUR[3:0]
 *   0x3B ALL_INT_SRC         reading it clears the latched interrupt flags: bit0 FF, bit1 WU, bit2 SINGLE_TAP, bit3 DOUBLE_TAP
 *   0x3F CTRL7               INTERRUPTS_ENABLE bit5 (needed for wake-up / tap interrupts)
 * The tap, wake-up and timing values in hw_config.h are starting points: they must be tuned with the real watch on a wrist.
 */
#include "imu.h"
#include "i2c.h"
#include "hw_config.h"
#include "hw_pure.h"

#define R_WHO_AM_I 0x0F
#define R_CTRL1 0x20
#define R_CTRL2 0x21
#define R_CTRL3 0x22
#define R_CTRL4 0x23
#define R_CTRL6 0x25
#define R_OUT_X_L 0x28
#define R_TAP_THS_X 0x30
#define R_TAP_THS_Y 0x31
#define R_TAP_THS_Z 0x32
#define R_INT_DUR 0x33
#define R_WAKE_UP_THS 0x34
#define R_WAKE_UP_DUR 0x35
#define R_ALL_INT_SRC 0x3B
#define R_CTRL7 0x3F

static uint8_t wr(uint8_t reg, uint8_t v) { return i2c_write_reg(IMU_I2C_ADDR, reg, v); }

uint8_t imu_init(void) {
    uint8_t id = 0;
    if (!i2c_read_regs(IMU_I2C_ADDR, R_WHO_AM_I, &id, 1) || id != 0x44) return 0;
    uint8_t ok = 1;
    ok &= wr(R_CTRL1, 0x00);                                   /* power-down while configuring */
    ok &= wr(R_CTRL2, 0x0C);                                   /* BDU = 1, IF_ADD_INC = 1 */
    ok &= wr(R_CTRL6, 0x10);                                   /* +-4 g, filter ODR/2 */
    ok &= wr(R_CTRL3, 0x10);                                   /* interrupts latched, active high, push-pull */
    ok &= wr(R_TAP_THS_X, IMU_TAP_THS_Z);
    ok &= wr(R_TAP_THS_Y, IMU_TAP_THS_Z);
    ok &= wr(R_TAP_THS_Z, (uint8_t)(0x20 | IMU_TAP_THS_Z));    /* only the Z axis (a tap on the glass) is enabled */
    ok &= wr(R_INT_DUR, IMU_INT_DUR);
    ok &= wr(R_WAKE_UP_THS, (uint8_t)(0x80 | IMU_WAKE_THS));   /* double-tap enabled, sleep (auto low-rate) off */
    ok &= wr(R_WAKE_UP_DUR, 0x00);
    ok &= wr(R_CTRL4, 0x28);                                   /* INT1 = wake-up + double-tap */
    ok &= wr(R_CTRL7, 0x20);                                   /* INTERRUPTS_ENABLE */
    ok &= wr(R_CTRL1, IMU_AWAKE_CTRL1);
    return ok;
}

void imu_profile_awake(void) { wr(R_CTRL1, IMU_AWAKE_CTRL1); }
void imu_profile_sleep(uint8_t tap_enabled) { wr(R_CTRL1, tap_enabled ? IMU_SLEEP_CTRL1_TAP : IMU_SLEEP_CTRL1_NOTAP); }

uint8_t imu_read_mg(int16_t *x, int16_t *y, int16_t *z) {
    uint8_t b[6];
    if (!i2c_read_regs(IMU_I2C_ADDR, R_OUT_X_L, b, 6)) return 0;
    int16_t s[3];
    for (uint8_t i = 0; i < 3; i++) s[i] = imu_raw_to_mg((int16_t)((uint16_t)b[2 * i] | ((uint16_t)b[2 * i + 1] << 8)));
    imu_map_axes(s, x, y, z);
    return 1;
}

uint8_t imu_events(void) {
    uint8_t src = 0;
    if (!i2c_read_regs(IMU_I2C_ADDR, R_ALL_INT_SRC, &src, 1)) return 0;
    return (uint8_t)(src & 0x0F);                              /* bit0 FF, bit1 WU, bit2 single tap, bit3 double tap: same as IMU_EV_* */
}
