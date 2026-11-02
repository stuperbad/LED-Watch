"""u1map.py SCH -> for every pin of U1: pin point, wire stub, label (text, position), no_connect.  Imported by repin.py too."""
import re, sys, math

def parse(s):
    stack = [[]]
    tok = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()"]+')
    spans = [[]]
    for m in tok.finditer(s):
        t = m.group(0)
        if t == "(":
            stack.append([]); spans.append([m.start()])
        elif t == ")":
            l = stack.pop(); sp = spans.pop(); sp.append(m.end()); l.append(("span", sp[0], sp[1])); stack[-1].append(l)
        else:
            stack[-1].append(t[1:-1] if t.startswith('"') else t)
    return stack[0][0]

def kids(n, key):
    return [c for c in n if isinstance(c, list) and c and c[0] == key]

def one(n, key):
    r = kids(n, key)
    return r[0] if r else None

def load(path):
    s = open(path, encoding="utf8", newline="").read()
    return s, parse(s)

def u1_pins(root, ref="U1"):
    """return (pin_points {num: (x, y, name)}, instance span)"""
    inst = None
    for c in kids(root, "symbol"):
        for p in kids(c, "property"):
            if p[1] == "Reference" and p[2] == ref:
                inst = c
    lib_id = one(inst, "lib_id")[1]
    at = one(inst, "at"); ix, iy, rot = float(at[1]), float(at[2]), int(float(at[3]))
    mir = one(inst, "mirror")
    libs = one(root, "lib_symbols")
    lib = [l for l in kids(libs, "symbol") if l[1] == lib_id][0]
    pins = {}
    def walk(n):
        for c in n:
            if isinstance(c, list) and c:
                if c[0] == "pin":
                    pat = one(c, "at"); num = one(c, "number")[1]; name = one(c, "name")[1]
                    px, py = float(pat[1]), float(pat[2])
                    pins[num] = (px, py, name)
                elif c[0] == "symbol":
                    walk(c)
    walk(lib)
    out = {}
    for num, (px, py, name) in pins.items():
        # lib y is up, schematic y is down
        x, y = px, -py
        if mir and mir[1] == "x": y = -y
        if mir and mir[1] == "y": x = -x
        a = math.radians(rot)
        rx = x * math.cos(a) + y * math.sin(a)
        ry = -x * math.sin(a) + y * math.cos(a)
        out[num] = (round(ix + rx, 3), round(iy + ry, 3), name)
    return out, inst

def r3(v): return round(float(v), 3)

def graph(root):
    wires = []
    for w in kids(root, "wire"):
        pts = one(one(w, "pts"), "xy") if False else kids(one(w, "pts"), "xy")
        a, b = pts[0], pts[1]
        wires.append(((r3(a[1]), r3(a[2])), (r3(b[1]), r3(b[2])), w))
    labels = []
    for l in kids(root, "label") + kids(root, "global_label"):
        at = one(l, "at"); labels.append((l[1], (r3(at[1]), r3(at[2])), l))
    ncs = []
    for n in kids(root, "no_connect"):
        at = one(n, "at"); ncs.append(((r3(at[1]), r3(at[2])), n))
    return wires, labels, ncs

if __name__ == "__main__":
    s, root = load(sys.argv[1])
    pins, inst = u1_pins(root)
    wires, labels, ncs = graph(root)
    for num in sorted(pins, key=lambda k: int(k) if k.isdigit() else 99):
        x, y, name = pins[num]
        pt = (x, y)
        w = [wi for wi in wires if pt in (wi[0], wi[1])]
        far = []
        for wi in w:
            far.append(wi[1] if wi[0] == pt else wi[0])
        lab = [(t, p) for (t, p, _) in labels if p == pt or p in far]
        nc = [p for (p, _) in ncs if p == pt or p in far]
        print(num, name, pt, "wires", len(w), "far", far, "labels", lab, "nc", nc)
