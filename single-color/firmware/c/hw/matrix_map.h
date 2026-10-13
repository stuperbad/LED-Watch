/* matrix_map.h - how the 12 x 12 LED matrix is wired to the MCU pins, and the pure (hardware-free) helpers of the scan driver.
 *
 * The matrix: 12 ROW pins sink current (an LED lights when its row pin is LOW and its column pin is HIGH), 12 COLUMN pins source current through a
 * 220 ohm resistor. The pin numbers come from hwmap.h, which is generated from the schematic, so this file cannot disagree with the board.
 * Everything here is plain C so the PC tests can check it. */
#pragma once
#include <stdint.h>

#define MATRIX_PORTS 4                       /* the matrix uses ports A, B, C, D (index 0..3) */
#define MATRIX_MAX_EVENTS 8                  /* most columns that can be scheduled to switch off inside one slot (the row-sink limit allows 6 at 3.0 V) */

/* what to write to the four port registers for one slot, plus when to switch columns off again */
typedef struct {
    uint8_t  row_clr[MATRIX_PORTS];          /* OUTCLR: pulls the active row LOW (rows idle HIGH) */
    uint8_t  col_set[MATRIX_PORTS];          /* OUTSET: drives the active columns HIGH (columns idle LOW) */
    uint8_t  n_events;                       /* how many columns switch off before the slot ends */
    struct { uint16_t t; uint8_t col_clr[MATRIX_PORTS]; } ev[MATRIX_MAX_EVENTS];   /* sorted by time t (timer ticks = microseconds) */
} matrix_slot_t;

/* masks of every matrix pin per port (what to configure as output) */
extern const uint8_t MATRIX_ALL_ROWS[MATRIX_PORTS];
extern const uint8_t MATRIX_ALL_COLS[MATRIX_PORTS];

/* pure helpers */
uint16_t matrix_slot_us(uint8_t n_slots);                                    /* slot length for a frame of n slots */
void     matrix_plan_slot(const uint8_t *fb, uint8_t row, uint16_t cols, uint16_t slot_us, uint16_t on_q16, matrix_slot_t *out);
void     matrix_col_masks(uint8_t col, uint8_t out[MATRIX_PORTS]);           /* for tests */
void     matrix_row_masks(uint8_t row, uint8_t out[MATRIX_PORTS]);
