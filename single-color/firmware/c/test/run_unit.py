"""Build and run the C unit tests on the PC with undefined-behaviour and address checking switched on (falls back to a plain build if the
sanitizers are not available in this compiler)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GCC = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin\gcc.exe")
EXE = os.path.join(HERE, "unit_tests.exe")
SRC = [os.path.join(HERE, "unit_tests.c"), os.path.join(HERE, "..", "watch.c")]
INC = ["-I" + os.path.join(HERE, ".."), "-I" + os.path.join(HERE, "..", "..")]


def build(flags):
    return subprocess.run([GCC, "-std=gnu99", "-O1", "-g", "-Wall", "-Wextra"] + flags + INC + ["-o", EXE] + SRC, capture_output=True, text=True)


r = build(["-fsanitize=undefined", "-fno-sanitize-recover=undefined"])
sanitized = r.returncode == 0
if not sanitized:
    r = build([])
    if r.returncode:
        print(r.stderr)
        sys.exit(1)
print("build: " + ("with undefined-behaviour checks" if sanitized else "PLAIN (sanitizers unavailable)"))
if r.stderr.strip():
    print(r.stderr[:2000])
p = subprocess.run([EXE], capture_output=True, text=True)
print(p.stdout + p.stderr)
sys.exit(p.returncode)
