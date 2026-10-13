"""Generate scenario files for the differential test (C core vs JavaScript simulator).
Every scenario is a list of steps of 10 ms. Both cores see exactly the same inputs; run_diff.py compares what they draw."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))


class Sc:
    def __init__(s, name, seed=1):
        s.name = name
        s.lines = ["SEED %d" % seed]
        s.btn = 0
        s.acc = (0, 0, 1000)
        s.wake = 0
        s.tap = 0
        s.ff = 0
        s.vdd = 4000
        s.soc = 800
        s.bat = 1
        s.solar = 0
        s.chg = 0
        s.amb = 50

    def cmd(s, text):
        s.lines.append(text)

    def run(s, n, dt=10):
        if n > 0:
            s.lines.append("R %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d" % (n, dt, s.btn, *s.acc, s.wake, s.tap, s.ff, s.vdd, s.soc, s.bat, s.solar, s.chg, s.amb))

    def idle(s, ms):
        s.btn = 0
        s.run(ms // 10)

    def hold(s, btn, ms):
        s.btn = btn
        s.run(ms // 10)
        s.btn = 0
        s.run(10)

    def press(s, b, ms=100):                                      # b = 0 left, 1 right
        s.hold(1 << b, ms)

    def long(s, b):
        s.hold(1 << b, 1100)

    def chord(s, ms=2200):
        s.hold(3, ms)

    def event(s, **kw):                                           # one step with an event flag set (wake=..., tap=1, ff=1)
        old = (s.wake, s.tap, s.ff)
        for k, v in kw.items():
            setattr(s, k, v)
        s.run(1)
        s.wake, s.tap, s.ff = old
        s.run(5)

    def shake(s):
        for i in range(10):
            s.acc = (-2500 if i % 2 else 2500, 2000 if i % 2 else -2000, 1000)
            s.run(1)
        s.acc = (0, 0, 1000)
        s.run(20)

    def tilt(s, ax, ay, az):
        s.acc = (ax, ay, az)

    def goto(s, mode):                                            # via mode selection: hold Left, move Right until it blinks, then Right long
        s.long(0)
        for _ in range(mode):
            s.press(1)
        s.long(1)

    def game(s, g):
        s.goto(4)
        for _ in range(g):
            s.press(0)
        s.press(1)

    def save(s):
        with open(os.path.join(HERE, "scn", s.name + ".scn"), "w") as f:
            f.write("\n".join(s.lines) + "\n")


def build():
    os.makedirs(os.path.join(HERE, "scn"), exist_ok=True)
    out = []

    s = Sc("01_time_and_wake")
    s.idle(500); s.press(1); s.idle(1500); s.press(1); s.idle(2500); s.long(1); s.idle(3000)      # wake, date, battery
    s.idle(12000); s.event(wake=60); s.idle(11000); s.event(wake=20); s.idle(500); s.event(tap=1); s.idle(11000); s.shake(); s.idle(11000)
    s.event(ff=1); s.idle(500)
    out.append(s)

    s = Sc("02_menu")
    s.press(0); s.idle(300)
    s.long(0); s.idle(400); s.press(1); s.idle(400); s.press(1); s.idle(400); s.press(0); s.idle(400); s.long(1); s.idle(500)
    s.long(0); s.idle(400); s.press(0); s.idle(300); s.long(0); s.idle(300)                          # Left long in the menu -> Time
    s.long(0); s.press(1); s.press(1); s.idle(2700); s.idle(16000)                                    # auto-enter then decay back to Time
    out.append(s)

    s = Sc("03_set_time_date")
    s.press(1); s.goto(1)
    for i in range(3):
        s.press(1); s.idle(200)
    s.press(0)
    for i in range(4):
        s.press(1)
    s.press(0); s.hold(2, 3600); s.idle(300)                                                           # auto-repeat
    for f in range(4):
        s.press(0)
        for i in range(2):
            s.press(1)
        s.idle(300)
    s.cmd("DATE 2028 2 28"); s.press(0); s.press(0); s.press(0); s.press(1); s.idle(300)
    out.append(s)

    s = Sc("04_stopwatch")
    s.press(1); s.goto(2); s.idle(300); s.press(1); s.idle(2000); s.press(1); s.idle(300); s.press(0); s.idle(200)
    s.press(1); s.idle(95000); s.shake(); s.idle(1000); s.long(1); s.idle(500)
    out.append(s)

    s = Sc("05_battery")
    s.press(1); s.goto(3)
    for v, sol, chg in [(800, 0, 0), (50, 3, 1), (990, 30, 1), (0, 7, 0)]:
        s.soc = v; s.solar = sol; s.chg = chg; s.idle(300)
        for i in range(3):
            s.press(1); s.idle(900)
    s.soc = 100; s.bat = 0; s.idle(1500); s.soc = 20; s.idle(1200); s.idle(5000)
    out.append(s)

    s = Sc("06_config_and_wake_settings")
    s.press(1); s.goto(5)
    for k in range(10):
        s.idle(200)
        for i in range(3):
            s.press(1); s.idle(100)
        s.press(0)
    s.idle(16000); s.event(wake=60); s.idle(500)
    out.append(s)

    s = Sc("07_lock")
    s.press(1); s.idle(1000); s.chord(2400); s.idle(500); s.press(0); s.idle(500); s.press(1); s.idle(3000)
    s.idle(12000); s.press(0, 50); s.idle(2000); s.shake(); s.idle(500); s.cmd("CFG 9 1"); s.idle(12000); s.shake(); s.idle(500)
    s.cmd("CFG 9 2"); s.idle(500); s.chord(2400); s.chord(2400); s.chord(2400); s.idle(3000); s.chord(2400); s.idle(2000)
    out.append(s)

    s = Sc("08_button_wake_settings")
    s.cmd("CFG 8 3"); s.press(0); s.idle(500); s.press(1); s.idle(500); s.cmd("CFG 8 1"); s.idle(11000); s.press(1); s.idle(500); s.press(0); s.idle(500)
    s.cmd("CFG 5 1"); s.idle(11000); s.event(wake=90); s.idle(300); s.cmd("CFG 6 1"); s.idle(11000); s.shake(); s.cmd("CFG 7 1"); s.idle(11000); s.event(tap=1); s.idle(500)
    out.append(s)

    s = Sc("09_brightness_scan")
    s.cmd("CFG 2 1"); s.press(1)
    for vdd, bri in [(3000, 2), (3600, 0), (4200, 4), (4200, 0)]:
        s.vdd = vdd; s.cmd("CFG 0 %d" % bri); s.idle(400); s.press(1); s.idle(300); s.long(1); s.idle(300)
    s.soc = 1000; s.press(1); s.idle(200); s.cmd("CFG 3 1"); s.amb = 100; s.idle(300); s.amb = 0; s.idle(300)
    out.append(s)

    s = Sc("10_target")
    s.press(1); s.game(2); s.idle(3000)
    for i in range(14):
        s.press(i % 2, 40); s.idle(1000 + 130 * i)
    s.idle(2000); s.press(0); s.idle(500)
    out.append(s)

    s = Sc("11_random_modes", seed=7)
    s.press(1); s.game(5); s.idle(2500)
    for m in range(5):
        s.press(1); s.idle(2000); s.press(1); s.idle(2000); s.press(0); s.idle(300)
    s.shake(); s.idle(3000)
    out.append(s)

    s = Sc("12_pacer")
    s.press(1); s.game(6); s.idle(3000)
    for i in range(3):
        s.press(1); s.idle(2700); s.idle(1700)
    s.long(1); s.idle(3000); s.press(1); s.idle(2700); s.press(0); s.press(0); s.idle(12000)
    out.append(s)

    s = Sc("13_simon", seed=11)
    s.press(1); s.game(7); s.idle(6000)
    for i in range(12):
        s.press(i % 2, 40); s.idle(450)
    s.idle(9000); s.press(0); s.idle(1000)
    out.append(s)

    s = Sc("14_pong_two_players")
    s.press(1); s.game(8); s.idle(1500); s.press(1); s.idle(900)
    for i in range(30):
        s.press(i % 2, 30); s.idle(260)
    s.idle(30000)
    out.append(s)

    s = Sc("15_pong_solo")
    s.press(1); s.game(8); s.press(0); s.idle(600); s.press(1); s.idle(900)
    for i in range(10):
        s.press(1, 30); s.idle(500)
    s.idle(20000)
    out.append(s)

    s = Sc("16_quick_draw", seed=3)
    s.press(1); s.game(3); s.idle(800); s.hold(3, 800); s.idle(5000); s.press(1); s.idle(3500); s.hold(3, 800); s.idle(1000); s.press(0); s.idle(3500)
    out.append(s)

    s = Sc("17_orbit_patterns", seed=5)
    s.press(1); s.game(4); s.idle(1000)
    for p in range(6):
        s.idle(2500); s.press(1)
    s.tilt(300, -200, 900); s.idle(1000); s.press(0); s.idle(1000)
    out.append(s)

    for sc in out:
        sc.save()
    return [o.name for o in out]


if __name__ == "__main__":
    print("\n".join(build()))
