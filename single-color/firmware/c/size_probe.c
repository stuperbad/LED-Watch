/* size_probe.c - links the watch core with a trivial main so avr-size reports the REAL flash and RAM use of the logic (including the
 * libgcc helpers for 32/64-bit maths). Not the firmware: there is no hardware code here yet. */
#include <avr/io.h>
#include "watch.h"
static watch_io_t io = { 0, 0, 1000, 0, 0, 0, 0, 4000, 800, 1, 0, 0, 50 };
int main(void) {
    watch_init(1);
    for (;;) {
        io.btn = (uint8_t)(~PORTE.IN >> 1) & 3;             /* just so the compiler cannot discard the input path */
        watch_step(16, 16, &io);
        PORTA.OUT = watch_fb()[0] | watch_scan()->n;       /* keep the outputs alive */
    }
}
