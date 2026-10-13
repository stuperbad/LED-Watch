/* matrix_map.c - pin masks and the slot planner of the LED matrix scan driver (no hardware access, runs on the PC too). */
#include <string.h>
#include "matrix_map.h"
#include "hwmap.h"
#include "hw_config.h"

#define PIDX(c)   ((c) == 'A' ? 0 : (c) == 'B' ? 1 : (c) == 'C' ? 2 : (c) == 'D' ? 3 : -1)
#define BITIN(pc, bit, p)  ((PIDX(pc) == (p)) ? (uint8_t)(1u << (bit)) : (uint8_t)0)
#define ROW4(n)  { BITIN(HW_ROW##n##_PORT, HW_ROW##n##_BIT, 0), BITIN(HW_ROW##n##_PORT, HW_ROW##n##_BIT, 1), BITIN(HW_ROW##n##_PORT, HW_ROW##n##_BIT, 2), BITIN(HW_ROW##n##_PORT, HW_ROW##n##_BIT, 3) }
#define COL4(n)  { BITIN(HW_COL##n##_PORT, HW_COL##n##_BIT, 0), BITIN(HW_COL##n##_PORT, HW_COL##n##_BIT, 1), BITIN(HW_COL##n##_PORT, HW_COL##n##_BIT, 2), BITIN(HW_COL##n##_PORT, HW_COL##n##_BIT, 3) }

/* the matrix pins must all be on ports A-D (the driver has no code for other ports): fail the build if the schematic ever changes that */
#define CHECK_PORT(sig) _Static_assert(PIDX(HW_##sig##_PORT) >= 0, #sig " must be on port A, B, C or D")
CHECK_PORT(ROW0); CHECK_PORT(ROW1); CHECK_PORT(ROW2); CHECK_PORT(ROW3); CHECK_PORT(ROW4); CHECK_PORT(ROW5);
CHECK_PORT(ROW6); CHECK_PORT(ROW7); CHECK_PORT(ROW8); CHECK_PORT(ROW9); CHECK_PORT(ROW10); CHECK_PORT(ROW11);
CHECK_PORT(COL0); CHECK_PORT(COL1); CHECK_PORT(COL2); CHECK_PORT(COL3); CHECK_PORT(COL4); CHECK_PORT(COL5);
CHECK_PORT(COL6); CHECK_PORT(COL7); CHECK_PORT(COL8); CHECK_PORT(COL9); CHECK_PORT(COL10); CHECK_PORT(COL11);

static const uint8_t ROW_MASK[12][MATRIX_PORTS] = { ROW4(0), ROW4(1), ROW4(2), ROW4(3), ROW4(4), ROW4(5), ROW4(6), ROW4(7), ROW4(8), ROW4(9), ROW4(10), ROW4(11) };
static const uint8_t COL_MASK[12][MATRIX_PORTS] = { COL4(0), COL4(1), COL4(2), COL4(3), COL4(4), COL4(5), COL4(6), COL4(7), COL4(8), COL4(9), COL4(10), COL4(11) };

#define ALLOF(tab, p) (uint8_t)(tab[0][p] | tab[1][p] | tab[2][p] | tab[3][p] | tab[4][p] | tab[5][p] | tab[6][p] | tab[7][p] | tab[8][p] | tab[9][p] | tab[10][p] | tab[11][p])
const uint8_t MATRIX_ALL_ROWS[MATRIX_PORTS] = { ALLOF(ROW_MASK, 0), ALLOF(ROW_MASK, 1), ALLOF(ROW_MASK, 2), ALLOF(ROW_MASK, 3) };
const uint8_t MATRIX_ALL_COLS[MATRIX_PORTS] = { ALLOF(COL_MASK, 0), ALLOF(COL_MASK, 1), ALLOF(COL_MASK, 2), ALLOF(COL_MASK, 3) };

void matrix_col_masks(uint8_t col, uint8_t out[MATRIX_PORTS]) { memcpy(out, COL_MASK[col], MATRIX_PORTS); }
void matrix_row_masks(uint8_t row, uint8_t out[MATRIX_PORTS]) { memcpy(out, ROW_MASK[row], MATRIX_PORTS); }

/* A frame of n slots is stretched or squeezed so that the whole pass takes about SCAN_FRAME_US (125 Hz refresh): few slots -> long slots,
 * many slots -> short slots, within limits (short slots cost interrupt time, long slots make a dim LED look jumpy). */
uint16_t matrix_slot_us(uint8_t n_slots) {
    uint32_t us = n_slots ? SCAN_FRAME_US / n_slots : SCAN_SLOT_MAX_US;
    if (us < SCAN_SLOT_MIN_US) us = SCAN_SLOT_MIN_US;
    if (us > SCAN_SLOT_MAX_US) us = SCAN_SLOT_MAX_US;
    return (uint16_t)us;
}

/* Plan one slot: which row to pull low, which columns to raise, and when each column must switch off again so that an LED at brightness
 * level L (0..255) is on for L/255 of the "full" on-time (slot_us * on_q16 / 65536). Columns whose time reaches the end of the slot need no event. */
void matrix_plan_slot(const uint8_t *fb, uint8_t row, uint16_t cols, uint16_t slot_us, uint16_t on_q16, matrix_slot_t *o) {
    memset(o, 0, sizeof *o);
    for (uint8_t p = 0; p < MATRIX_PORTS; p++) o->row_clr[p] = ROW_MASK[row][p];
    uint32_t full = ((uint32_t)slot_us * on_q16) >> 16;                   /* microseconds a full-brightness LED stays on */
    for (uint8_t c = 0; c < 12; c++) {
        if (!((cols >> c) & 1)) continue;
        uint32_t lvl = fb[(uint8_t)(row * 12 + c)];
        uint32_t t = full * lvl / 255;
        if (!t) continue;                                                  /* too dim for this slot length: stays off */
        if (t < slot_us && o->n_events >= MATRIX_MAX_EVENTS) continue;     /* no room to schedule its switch-off (only if the supply sags below 3 V): leave it dark rather than stuck on */
        for (uint8_t p = 0; p < MATRIX_PORTS; p++) o->col_set[p] |= COL_MASK[c][p];
        if (t >= slot_us) continue;                                        /* on until the slot ends */
        uint8_t i = o->n_events;
        while (i > 0 && o->ev[i - 1].t > t) { o->ev[i] = o->ev[i - 1]; i--; }   /* insertion sort by switch-off time */
        o->ev[i].t = (uint16_t)t;
        for (uint8_t p = 0; p < MATRIX_PORTS; p++) o->ev[i].col_clr[p] = COL_MASK[c][p];
        o->n_events++;
    }
}
