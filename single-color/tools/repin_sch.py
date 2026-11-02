"""repin.py SCH [--apply]  -> move U1's matrix / I2C pins to the revision B assignment by editing labels, wires and no-connects in the saved schematic."""
import sys, uuid
sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])
import u1map as M

path = sys.argv[1]
apply = "--apply" in sys.argv
s, root = M.load(path)
pins, inst = M.u1_pins(root)
wires, labels, ncs = M.graph(root)

NEW = {}                                   # pin -> new net label (None = free)
cols = {44: 0, 45: 1, 46: 2, 47: 3, 48: 4, 1: 5, 2: 6, 3: 7, 4: 8, 5: 9, 6: 10, 7: 11}
for p, c in cols.items(): NEW[p] = f"COL{c}_MCU"
for i, p in enumerate([10, 11, 12, 13, 16, 17, 18, 19]): NEW[p] = f"ROW{i}"
for i, p in enumerate([20, 21, 22, 23]): NEW[p] = f"ROW{8 + i}"
NEW[24] = None; NEW[25] = None
NEW[36] = "SDA"; NEW[37] = "SCL"
NEW[46] = "COL2_MCU"; NEW[47] = "COL3_MCU"          # (kept for clarity: set by cols above)
NEW.update({p: f"COL{c}_MCU" for p, c in cols.items()})
FREE = {24, 25}
# pins 46/47 are columns now; SDA/SCL leave PA2/PA3.  Pins that become free: 24, 25.  Pins that become connected: 36, 37 (were no-connect).

edits = []        # (start, end, replacement) on the text
def uid(): return str(uuid.uuid4())

def pin_stub(num):
    x, y, _ = pins[str(num)]
    pt = (x, y)
    w = [wi for wi in wires if pt in (wi[0], wi[1])]
    far = [wi[1] if wi[0] == pt else wi[0] for wi in w]
    lab = [(t, p, l) for (t, p, l) in labels if p == pt or p in far]
    nc = [(p, n) for (p, n) in ncs if p == pt]
    return pt, w, far, lab, nc

log = []
for num in sorted(NEW):
    want = NEW[num]
    pt, w, far, lab, nc = pin_stub(num)
    cur = lab[0][0] if lab else None
    if want == cur and not (want is None and not nc):
        continue
    left_side = pins[str(num)][0] < 380
    if want is not None and lab:                         # rename
        t, p, l = lab[0]
        sp = [c for c in l if isinstance(c, tuple)][0]
        txt = s[sp[1]:sp[2]]
        new = txt.replace(f'(label "{t}"', f'(label "{want}"', 1)
        assert new != txt
        edits.append((sp[1], sp[2], new)); log.append(f"pin {num}: {cur} -> {want}")
    elif want is None and lab:                           # becomes free: drop wire + label, add no-connect
        for (t, p, l) in lab:
            sp = [c for c in l if isinstance(c, tuple)][0]; edits.append((sp[1], sp[2], ""))
        for wi in w:
            sp = [c for c in wi[2] if isinstance(c, tuple)][0]; edits.append((sp[1], sp[2], ""))
        edits.append((None, None, f'\r\n\t(no_connect\r\n\t\t(at {pt[0]} {pt[1]})\r\n\t\t(uuid "{uid()}")\r\n\t)'))
        log.append(f"pin {num}: {cur} -> free (no-connect)")
    elif want is not None and not lab:                   # was free: drop no-connect, add stub + label
        for (p, n) in nc:
            sp = [c for c in n if isinstance(c, tuple)][0]; edits.append((sp[1], sp[2], ""))
        fx = pt[0] - 2.54 if left_side else pt[0] + 2.54
        fx = round(fx, 3)
        ang, just = (180, "right bottom") if left_side else (0, "left bottom")
        edits.append((None, None, f'\r\n\t(wire\r\n\t\t(pts\r\n\t\t\t(xy {pt[0]} {pt[1]}) (xy {fx} {pt[1]})\r\n\t\t)\r\n\t\t(stroke\r\n\t\t\t(width 0)\r\n\t\t\t(type default)\r\n\t\t)\r\n\t\t(uuid "{uid()}")\r\n\t)'))
        edits.append((None, None, f'\r\n\t(label "{want}"\r\n\t\t(at {fx} {pt[1]} {ang})\r\n\t\t(effects\r\n\t\t\t(font\r\n\t\t\t\t(size 1.27 1.27)\r\n\t\t\t)\r\n\t\t\t(justify {just})\r\n\t\t)\r\n\t\t(uuid "{uid()}")\r\n\t)'))
        log.append(f"pin {num}: free -> {want}")

print("\n".join(log)); print(len(log), "pin changes")
if apply:
    cuts = sorted([e for e in edits if e[0] is not None], key=lambda e: -e[0])
    for a, b, r in cuts:
        s = s[:a] + r + s[b:]
    adds = "".join(e[2] for e in edits if e[0] is None)
    end = s.rstrip().rfind(")")                          # before the closing paren of kicad_sch
    # insert before "(sheet_instances" if present else before the final paren
    k = s.find("\r\n\t(sheet_instances")
    ins = k if k >= 0 else end
    s = s[:ins] + adds + s[ins:]
    open(path, "w", encoding="utf8", newline="").write(s)
    print("written")
