"""Build and run the PC tests of the hardware layer (pin map, scan planner, debounce, battery maths, accelerometer driver on a pretend sensor)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GCC = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin\gcc.exe")
EXE = os.path.join(HERE, "hw_tests.exe")
SRC = [os.path.join(HERE, "hw_tests.c")] + [os.path.join(HERE, "..", "hw", f) for f in ("matrix_map.c", "hw_pure.c", "imu.c")] + [os.path.join(HERE, "..", "watch.c")]
INC = ["-I" + os.path.join(HERE, ".."), "-I" + os.path.join(HERE, "..", ".."), "-I" + os.path.join(HERE, "..", "hw")]
r = subprocess.run([GCC, "-std=gnu99", "-O1", "-g", "-Wall", "-Wextra"] + INC + ["-o", EXE] + SRC, capture_output=True, text=True)
if r.returncode:
    print(r.stderr)
    sys.exit(1)
if r.stderr.strip():
    print(r.stderr[:2000])
p = subprocess.run([EXE], capture_output=True, text=True)
print(p.stdout + p.stderr)
sys.exit(p.returncode)
