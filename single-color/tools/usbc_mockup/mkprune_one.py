s=open("C:/Users/evanf/Desktop/LED Watch/single-color/tools/prune_dangling_drc.py",encoding="utf8").read()
i=s.index("tried = set()")
head=s[:i].replace("HERE = os.path.dirname(os.path.abspath(__file__))","HERE = 'C:/Users/evanf/Desktop/LED Watch/single-color/tools'")
tail='''tried = set()
for rnd in range(6):
    todo = [(p, n) for p, n in dang if p not in tried]
    if not todo:
        break
    progress = False
    for p, n in todo:
        tried.add(p)
        nets = [n] if n else []
        open(os.path.join(w, "nets.txt"), "w").write("\n".join(nets))
        nxt = os.path.join(w, "next.kicad_pcb")
        r = subprocess.run([KPY, os.path.join(HERE, "prune_leaves.py"), cur, nxt, CX, CY, HALF, "--targets=" + repr([p]), "@" + os.path.join(w, "nets.txt")], capture_output=True, text=True)
        msgs = [l for l in r.stdout.splitlines() if l.strip() and not l.startswith("swig")]
        nch = int([l for l in msgs if l.startswith("changes:")][0].split()[1]) if any(l.startswith("changes:") for l in msgs) else 0
        if nch == 0:
            continue
        d2, unc, bad = drc(nxt)
        print("round %d %s %s: %d changes -> %d dangling, %d unconnected" % (rnd, n, p, nch, len(d2), unc), flush=True)
        if unc > unc0:
            print("    worse, undone", flush=True)
            continue
        shutil.copy(nxt, cur); dang, unc0, bad0 = d2, unc, bad; progress = True
    if not progress:
        break
shutil.copy(cur, dst)
print("wrote", dst, "| left: %d dangling, %d unconnected" % (len(dang), unc0))
'''
open("usbc/prune_one.py","w",encoding="utf8").write(head+tail)
