/* matrix.c - the LED matrix scan driver (AVR128DB48 only).
 *
 * HOW IT WORKS, in plain words
 * ----------------------------
 * The 132 + 6 LEDs are wired as a grid of 12 rows x 12 columns. A row pin is the LEDs' shared "minus", a column pin is the "plus"
 * (through a 220 ohm resistor). An LED lights when its row pin is pulled LOW and its column pin is driven HIGH. Because the MCU can only sink
 * 10 mA per row pin, only a few LEDs on the same row can be lit at the same moment, so the picture is drawn one small piece at a time, very fast
 * (the eye blends it): each piece is a "slot" = one row plus up to m columns. watch_scan() (from the core) lists the slots.
 *
 * A hardware timer (TCA0) counts microseconds. When it overflows (the slot is over):
 *    1. everything is switched off (rows high, columns low);
 *    2. the next slot is switched on: its row low, its columns high;
 *    3. if some of its LEDs are dimmer than others, a second interrupt (the timer's compare match) switches each column off at the right moment
 *       (an LED at brightness 128/255 stays on for half as long as one at 255/255). That is the brightness control ("PWM").
 * The main program writes a new picture into a back buffer; the interrupt switches to it between two frames, so you never see a half-drawn picture.
 * When the display is off, the timer is stopped and every matrix pin is a high-impedance input (no current, nothing floating that could draw power).
 */
#include <avr/io.h>
#include <avr/interrupt.h>
#include <string.h>
#include "../watch.h"
#include "matrix.h"
#include "matrix_map.h"
#include "hw_config.h"

typedef struct {
    uint8_t  n;                                   /* slots in this frame; 0 = nothing to draw */
    uint16_t slot_us;                             /* timer ticks (microseconds) per slot */
    uint16_t on_q16;                              /* fraction of a slot a full-brightness LED is on, Q16 */
    uint8_t  row[WATCH_MAX_SLOTS];
    uint16_t cols[WATCH_MAX_SLOTS];
    uint8_t  fb[WATCH_ROWS * WATCH_COLS];
} frame_t;

static frame_t frames[2];
static volatile uint8_t front = 0;                /* the frame the interrupt is drawing */
static volatile uint8_t pending = 0;              /* the back frame is complete and should be used from the next frame */
static volatile uint8_t back_busy = 0;            /* the main program is writing the back frame: do not swap now */
static volatile uint8_t running = 0;
static uint8_t slot_idx = 0;

static matrix_slot_t cur;                         /* plan of the slot being displayed */
static uint8_t ev_i;

static PORT_t *const PORTS[MATRIX_PORTS] = { &PORTA, &PORTB, &PORTC, &PORTD };

static inline void all_off(void) {                /* rows idle HIGH, columns idle LOW: no LED has current */
    for (uint8_t p = 0; p < MATRIX_PORTS; p++) { PORTS[p]->OUTSET = MATRIX_ALL_ROWS[p]; PORTS[p]->OUTCLR = MATRIX_ALL_COLS[p]; }
}

static void pins_active(void) {
    for (uint8_t p = 0; p < MATRIX_PORTS; p++) {
        PORTS[p]->OUTSET = MATRIX_ALL_ROWS[p]; PORTS[p]->OUTCLR = MATRIX_ALL_COLS[p];
        PORTS[p]->DIRSET = (uint8_t)(MATRIX_ALL_ROWS[p] | MATRIX_ALL_COLS[p]);
        for (uint8_t b = 0; b < 8; b++) if ((MATRIX_ALL_ROWS[p] | MATRIX_ALL_COLS[p]) & (1u << b)) (&PORTS[p]->PIN0CTRL)[b] = PORT_ISC_INTDISABLE_gc;
    }
}
static void pins_hiz(void) {
    for (uint8_t p = 0; p < MATRIX_PORTS; p++) {
        PORTS[p]->DIRCLR = (uint8_t)(MATRIX_ALL_ROWS[p] | MATRIX_ALL_COLS[p]);
        for (uint8_t b = 0; b < 8; b++) if ((MATRIX_ALL_ROWS[p] | MATRIX_ALL_COLS[p]) & (1u << b)) (&PORTS[p]->PIN0CTRL)[b] = PORT_ISC_INPUT_DISABLE_gc;   /* input buffer off: a floating pin would otherwise leak current */
    }
}

void matrix_init(void) { pins_hiz(); running = 0; frames[0].n = frames[1].n = 0; }

static void timer_start(void) {
    pins_active();
    slot_idx = 0;
    TCA0.SINGLE.CTRLB = TCA_SINGLE_WGMODE_NORMAL_gc;
    TCA0.SINGLE.PER = 1000;
    TCA0.SINGLE.CNT = 0;
    TCA0.SINGLE.INTFLAGS = TCA_SINGLE_OVF_bm | TCA_SINGLE_CMP0_bm;
    TCA0.SINGLE.INTCTRL = TCA_SINGLE_OVF_bm;
    TCA0.SINGLE.CTRLA = TCA_SINGLE_CLKSEL_DIV4_gc | TCA_SINGLE_ENABLE_bm;       /* 4 MHz / 4 = 1 MHz: one tick = one microsecond */
    running = 1;
}
static void timer_stop(void) {
    TCA0.SINGLE.CTRLA = 0;
    TCA0.SINGLE.INTCTRL = 0;
    running = 0;
    pins_hiz();
}

void matrix_off(void) {
    uint8_t sreg = SREG; cli();
    if (running) timer_stop();
    frames[0].n = frames[1].n = 0; pending = 0;
    SREG = sreg;
}

void matrix_update(const watch_scan_t *sc, const uint8_t *fb) {
    if (!sc->n) { matrix_off(); return; }
    frame_t *b = &frames[front ^ 1];
    back_busy = 1;
    b->n = sc->n; b->slot_us = matrix_slot_us(sc->n); b->on_q16 = sc->on_q16;
    for (uint8_t i = 0; i < sc->n; i++) { b->row[i] = sc->slot[i].row; b->cols[i] = sc->slot[i].cols; }
    memcpy(b->fb, fb, sizeof b->fb);
    pending = 1; back_busy = 0;
    if (!running) { uint8_t sreg = SREG; cli(); front ^= 1; pending = 0; timer_start(); SREG = sreg; }   /* first picture after the display was off */
}

/* ---- the interrupts ---- */
ISR(TCA0_OVF_vect) {
    TCA0.SINGLE.INTFLAGS = TCA_SINGLE_OVF_bm;
    all_off();                                                 /* the slot is over */
    if (slot_idx == 0 && pending && !back_busy) { front ^= 1; pending = 0; }   /* switch to the new picture only between frames */
    const frame_t *f = &frames[front];
    if (!f->n) { timer_stop(); return; }
    if (slot_idx >= f->n) slot_idx = 0;
    matrix_plan_slot(f->fb, f->row[slot_idx], f->cols[slot_idx], f->slot_us, f->on_q16, &cur);
    TCA0.SINGLE.PER = (uint16_t)(f->slot_us - 1);
    for (uint8_t p = 0; p < MATRIX_PORTS; p++) { PORTS[p]->OUTCLR = cur.row_clr[p]; PORTS[p]->OUTSET = cur.col_set[p]; }   /* next slot ON */
    ev_i = 0;
    if (cur.n_events) { TCA0.SINGLE.CMP0 = cur.ev[0].t; TCA0.SINGLE.INTFLAGS = TCA_SINGLE_CMP0_bm; TCA0.SINGLE.INTCTRL = TCA_SINGLE_OVF_bm | TCA_SINGLE_CMP0_bm; }
    else TCA0.SINGLE.INTCTRL = TCA_SINGLE_OVF_bm;
    slot_idx++;
}

ISR(TCA0_CMP0_vect) {                                           /* the dimmest LEDs of this slot are done: switch their columns off */
    TCA0.SINGLE.INTFLAGS = TCA_SINGLE_CMP0_bm;
    uint16_t now = cur.ev[ev_i].t;
    while (ev_i < cur.n_events && cur.ev[ev_i].t <= now + 1) {
        for (uint8_t p = 0; p < MATRIX_PORTS; p++) PORTS[p]->OUTCLR = cur.ev[ev_i].col_clr[p];
        ev_i++;
    }
    if (ev_i < cur.n_events) TCA0.SINGLE.CMP0 = cur.ev[ev_i].t;
    else TCA0.SINGLE.INTCTRL = TCA_SINGLE_OVF_bm;
}
