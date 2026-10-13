/* matrix.h - LED matrix scan driver (AVR only). See matrix.c for how it works. */
#pragma once
#include <stdint.h>
#include "../watch.h"

void matrix_init(void);                                           /* all matrix pins high-impedance, timer stopped */
void matrix_update(const watch_scan_t *scan, const uint8_t *fb);  /* call after every watch_step(): starts, changes or stops the display */
void matrix_off(void);
