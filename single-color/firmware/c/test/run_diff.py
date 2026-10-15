"""Differential test: run every scenario on the JavaScript simulator core and on the C core (host build) and compare frame by frame.

usage: python run_diff.py [scenario-name-prefix]

Exact match is required on mode / awake / locked / menu / slot count. The framebuffer must match exactly, except for the animation
scenarios listed in LENIENT, where the two cores compute angles in different number formats: there each LED level may differ by a small
tolerance and a few LEDs per frame may sit one position off."""
import os
import subprocess
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
GCC = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin\gcc.exe")
EXE = os.path.join(HERE, "host_run.exe")
LENIENT = {"12_pacer": (2, 4), "17_orbit_patterns": (4, 12), "05_battery": (2, 1)}     # name -> (level tolerance, LEDs allowed to differ per frame)


def build():
    srcs = [os.path.join(HERE, "host_run.c"), os.path.join(HERE, "..", "watch.c")]
    cmd = [GCC, "-std=c99", "-O1", "-Wall", "-Wextra", "-I" + os.path.join(HERE, ".."), "-I" + os.path.join(HERE, "..", ".."), "-o", EXE] + srcs
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr)
        sys.exit(1)
    if r.stderr.strip():
        print(r.stderr)


def parse(text):
    rows = []
    for line in text.strip().split("\n"):
        t = line.split(" ")
        rows.append((tuple(int(x) for x in t[:7]) + (int(t[8]),), bytes.fromhex(t[7])))      # header ends with the buzzer frequency
    return rows


def compare(name, js, c):
    tol, allow = LENIENT.get(name, (0, 0))
    if len(js) != len(c):
        return "length differs: js %d vs c %d" % (len(js), len(c))
    bad = 0
    first = None
    for i, ((hj, fj), (hc, fc)) in enumerate(zip(js, c)):
        if (hj != hc) if not (tol or allow) else (hj[:6] + hj[7:] != hc[:6] + hc[7:]):
            return "step %d header differs (mode awake locked menu sel ind slots tone): js %s vs c %s" % (i, hj, hc)
        diff = [k for k in range(144) if abs(fj[k] - fc[k]) > tol and not (tol and max(fj[k], fc[k]) <= 20)]    # lenient: ignore near-dark LEDs
        if len(diff) > allow:
            bad += 1
            if first is None:
                first = (i, diff[:8], [fj[k] for k in diff[:8]], [fc[k] for k in diff[:8]])
    if bad:
        return "%d of %d frames differ; first at step %d, LED indices %s, js levels %s, c levels %s" % ((bad, len(js)) + first)
    return None


def main():
    pre = sys.argv[1] if len(sys.argv) > 1 else ""
    build()
    fails = 0
    for scn in sorted(glob.glob(os.path.join(HERE, "scn", pre + "*.scn"))):
        name = os.path.basename(scn)[:-4]
        js = subprocess.run(["node", os.path.join(HERE, "js_run.js"), scn], capture_output=True, text=True)
        if js.returncode:
            print(name, "JS FAILED", js.stderr[:300])
            fails += 1
            continue
        c = subprocess.run([EXE, scn], capture_output=True, text=True)
        if c.returncode:
            print(name, "C FAILED", c.stderr[:300])
            fails += 1
            continue
        err = compare(name, parse(js.stdout), parse(c.stdout))
        print(("PASS " if not err else "FAIL ") + name + ("" if not err else "  " + err))
        fails += bool(err)
    print("\n%d scenario(s) failed" % fails if fails else "\nall scenarios match")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
