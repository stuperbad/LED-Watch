/* host_run.c - run the C watch core on a scenario file and print one line per step (for differential tests against the JS simulator).
 *
 * scenario commands:   SEED n | TIME h m s | DATE y m d | CFG idx v
 *                      ALARM h m on
 *                      R count dt btn ax ay az wake tap ff vdd_mv soc_pm bat solar chg ambient   (repeat a step `count` times)
 * output per step:     mode awake locked menu_on menu_sel ind_only n_slots <144 hex bytes of framebuffer> tone_hz
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../watch.h"

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: host_run scenario.scn\n"); return 2; }
    FILE *f = fopen(argv[1], "r"); if (!f) { perror("scenario"); return 2; }
    char line[256]; uint32_t seed = 1; int inited = 0;
    while (fgets(line, sizeof line, f)) {
        if (line[0] == '#' || line[0] == '\n') continue;
        char cmd[16]; int a, b, c;
        if (sscanf(line, "%15s", cmd) != 1) continue;
        if (!strcmp(cmd, "SEED")) { sscanf(line, "SEED %d", &a); seed = (uint32_t)a; watch_init(seed); inited = 1; }
        else if (!strcmp(cmd, "TIME")) { sscanf(line, "TIME %d %d %d", &a, &b, &c); watch_set_time((uint8_t)a, (uint8_t)b, (uint8_t)c); }
        else if (!strcmp(cmd, "DATE")) { sscanf(line, "DATE %d %d %d", &a, &b, &c); watch_set_date((uint16_t)a, (uint8_t)b, (uint8_t)c); }
        else if (!strcmp(cmd, "ALARM")) { sscanf(line, "ALARM %d %d %d", &a, &b, &c); watch_set_alarm((uint8_t)a, (uint8_t)b, (uint8_t)c); }
        else if (!strcmp(cmd, "CFG")) { sscanf(line, "CFG %d %d", &a, &b); watch_set_cfg((uint8_t)a, (uint8_t)b); }
        else if (!strcmp(cmd, "R")) {
            if (!inited) { watch_init(seed); inited = 1; }
            int n, dt, btn, ax, ay, az, wake, tap, ff, vdd, soc, bat, solar, chg, amb;
            if (sscanf(line, "R %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d", &n, &dt, &btn, &ax, &ay, &az, &wake, &tap, &ff, &vdd, &soc, &bat, &solar, &chg, &amb) != 15) { fprintf(stderr, "bad line: %s", line); return 2; }
            watch_io_t io = { (int16_t)ax, (int16_t)ay, (int16_t)az, (uint8_t)btn, (uint8_t)wake, (uint8_t)tap, (uint8_t)ff, (uint16_t)vdd, (uint16_t)soc, (uint8_t)bat, (uint8_t)solar, (uint8_t)chg, (uint8_t)amb };
            for (int i = 0; i < n; i++) {
                watch_step((uint16_t)dt, (uint32_t)dt, &io);
                const watch_t *w = watch_state(); const uint8_t *fb = watch_fb();
                printf("%d %d %d %d %d %d %d ", w->mode, w->awake, w->locked, w->menu_on, w->menu_sel, w->ind_only, watch_scan()->n);
                for (int k = 0; k < 144; k++) printf("%02x", fb[k]);
                printf(" %u\n", (unsigned)watch_tone_hz());
            }
        }
    }
    fclose(f); return 0;
}
