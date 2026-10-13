"""JLCPCB assembly files from a KiCad position export: usage make_bom_cpl.py pos_raw.csv out_dir
BOM: Comment, Designator, Footprint, LCSC Part #   CPL: Designator, Mid X, Mid Y, Layer, Rotation
Part numbers: LCSC (from JLCPCB's parts library, searched 2026-10-12) -- re-check stock on order day."""
import csv, sys, collections
pos, out = sys.argv[1], sys.argv[2]
LCSC = {
 ("LED white 0201", "LED_0201_0603Metric"): "C965789", ("LED white 0402", "LED_0402_1005Metric"): "C20613596", ("LED white 0603", "LED_0603_1608Metric"): "C2290",
 ("220", "R_0402_1005Metric"): "C25091", ("10k", "R_0402_1005Metric"): "C25744", ("6.49M", "R_0402_1005Metric"): "C172111", ("5.11M", "R_0402_1005Metric"): "C166448",
 ("1.47M", "R_0402_1005Metric"): "C477211", ("3.74M", "R_0402_1005Metric"): "C477705",
 ("100n", "C_0402_1005Metric"): "C1525", ("18p", "C_0402_1005Metric"): "C106202", ("10n", "C_0402_1005Metric"): "C15195", ("4u7", "C_0402_1005Metric"): "C23733",
 ("10u", "C_0402_1005Metric"): "C15525", ("22u", "C_0805_2012Metric"): "C109314",
 ("SW_Push", "SW_Push_1P1T_NO_CK_KMR2"): "C72443", ("LiPo", "JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal"): "C160402",
 ("32.768kHz", "Crystal_SMD_3215-2Pin_3.2x1.5mm"): "C97606", ("AVR128DB48-I/6LX", "QFN-48-1EP_6x6mm_P0.4mm_EP4.2x4.2mm"): "C1019768",
 ("LIS2DW12TR", "LGA-12_2x2mm_P0.5mm"): "C189624", ("BQ25570RGRR", "BQ25570RGR_VQFN-20_3.5x3.5mm_P0.5mm_EP2.05mm"): "C506250",
 ("10uH", "L_1210_3225Metric"): "C74563", ("22uH", "L_1210_3225Metric"): "C90320",
}
IND = {"SET", "TMR", "BAT", "FUN", "CFG", "LCK"}
rows = list(csv.DictReader(open(pos, encoding="utf8")))
bom = collections.OrderedDict()
cpl = []
missing = []
for r in rows:
    ref, val, pkg = r["Ref"], r["Val"], r["Package"]
    if val in IND:
        val = "LED white 0402"
    key = (val, pkg)
    if key not in LCSC:
        missing.append((ref, val, pkg))
        continue
    bom.setdefault(key, []).append(ref)
    cpl.append((ref, r["PosX"], r["PosY"], "Top" if r["Side"] == "top" else "Bottom", r["Rot"]))
with open(out + "/BOM.csv", "w", newline="", encoding="utf8") as f:
    w = csv.writer(f); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for (val, pkg), refs in bom.items():
        w.writerow([val, ",".join(sorted(refs)), pkg, LCSC[(val, pkg)]])
with open(out + "/CPL.csv", "w", newline="", encoding="utf8") as f:
    w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for c in cpl:
        w.writerow(c)
print("BOM lines", len(bom), "| placed parts", len(cpl), "| not in map:", missing)
