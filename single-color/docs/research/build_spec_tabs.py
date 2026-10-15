# Executed inside build_power_workbook.py (shares wb, ws, wl, wt, we, sw, wp and the style helpers).
# Adds: LEDs, Sensors, Batteries, Parts, Board size, Wear and stack, Shortcomings tabs and wires the picks into the model.
from openpyxl.styles import Font, Alignment

F_LNK = Font(name=ARIAL, size=10, color="0563C1", underline="single")
WRAP = Alignment(wrap_text=True, vertical="top")
AS_OF = "2026-10-08"


def link(ws_, ref, url, text="link"):
    c = ws_[ref]
    c.value = text
    c.hyperlink = url
    c.font = F_LNK
    c.alignment = Alignment(vertical="top")
    return c


def txt(ws_, ref, v, bold=False, fmt=None, wrap=True, color=None, italic=False):
    c = ws_[ref]
    c.value = v
    c.font = Font(name=ARIAL, size=10, bold=bold, italic=italic, color=color)
    if fmt:
        c.number_format = fmt
    c.alignment = Alignment(wrap_text=wrap, vertical="top")
    return c


def numinput(ws_, ref, v, fmt=None):
    c = inp(ws_, ref, v, fmt)
    c.alignment = Alignment(vertical="top")
    return c


def label_col(ws_, labels, start_row, col="A"):
    for i, l in enumerate(labels):
        c = ws_[f"{col}{start_row + i}"]
        c.value = l
        c.font = F_BOLD
        c.alignment = WRAP
        c.fill = FILL_SEC


# =============================================================== names used for dropdowns / lookups
LED_OPTS = ["0201 white - Xinglight XL-0201UWC", "0402 white - Xinglight XL-1005UWC", "0603 white - Kento KT-0603W",
            "0603 white - Dialight 5973904507F (DigiKey alt)", "0805 white - Kento KT-0805W", "0805 white - Lite-On LTW-170TK (DigiKey alt)",
            "RGB 0.83 mm - Harvatek B39D3RGB (original design)", "RGB 0.8 mm - Meihua MHPA0808RGBDT (JLCPCB alt)"]
BAT_OPTS = ["Renata ICP341018PM (35 mAh)", "Renata ICP331319PM (50 mAh)", "Renata ICP501022UPM (80 mAh)", "Renata ICP402025PC-01 (155 mAh)"]
SENS_OPTS = ["BMI270", "BMA400", "LIS2DW12"]
VARIANTS = ["A: pad-charged", "B: solar harvester"]
ROUTES = ["JLCPCB / LCSC", "DigiKey / Mouser"]

# =============================================================== LEDs tab
wd = wb.create_sheet("LEDs")
put(wd, "A1", "LED catalog: white options for the clock face, and the RGB parts from the first design", F_TITLE)
put(wd, "A2", f"Prices, stock and links checked live on {AS_OF} (DigiKey, JLCPCB) unless marked. VERIFIED = read from the distributor page or datasheet; ESTIMATE/UNVERIFIED = not confirmed. "
              "Pad length/width come from KiCad's stock footprints and drive the ring-size calculator on the 'Board size' tab. The first six columns can be picked on the Inputs tab.", F_NOTE, wrap=True)
wd.merge_cells("A2:I2"); wd.row_dimensions[2].height = 40
head(wd, 4, ["Attribute"] + LED_OPTS)
wd.row_dimensions[4].height = 62
labs = ["Role / why it is here", "Colour", "Package", "Body size (mm)", "Pad-axis length (mm, KiCad footprint)", "Pad width (mm, KiCad footprint)", "Height max (mm)",
        "Forward voltage typ (V)", "Test current for brightness (mA)", "Brightness at test current (mcd)", "Viewing angle (deg)", "Configuration",
        "DigiKey part number", "DigiKey stock", "DigiKey unit price at the minimum order (USD)", "DigiKey unit price at ~100 (USD)", "DigiKey minimum order (pieces)",
        "DigiKey cost of one minimum order (USD)", "DigiKey link", "JLCPCB / LCSC part", "JLCPCB library type (Basic = no extra fee)", "JLCPCB stock", "JLCPCB unit price at low quantity (USD)", "JLCPCB link",
        "Datasheet", "Status", "Cost of the 132 LEDs at DigiKey price (USD)", "Cost of the 132 LEDs at JLCPCB price (USD)", "Lowest battery voltage at which it lights (Vf + pin drop)",
        "Shortcomings", "How well verified"]
label_col(wd, labs, 5)
R_ = {n: 5 + i for i, n in enumerate(["role", "colour", "pkg", "body", "padL", "padW", "height", "vf", "itest", "mcd", "angle", "config", "dkpn", "dkstock", "dkp1", "dkp100", "dkmoq", "dkmoqcost", "dklink",
                                         "jlc", "jlctype", "jlcstock", "jlcprice", "jlclink", "ds", "status", "cost_dk", "cost_jlc", "vmin", "short", "verif"])}
LEDDATA = [
    dict(role="Option: smallest white LED (0201). Hardest to place and inspect.", colour="White (cool)", pkg="0201 (0603 metric)", body="0.65 x 0.35", padL=1.10, padW=0.40, height=0.65, vf=2.7, itest=5, mcd=185, angle=120, config="Single LED, 2 pads",
         dkpn="5962-XL-0201UWCTR-ND", dkstock=100000, dkp1=0.09375, dkp100=None, dkmoq=5000, dkl="https://www.digikey.com/en/products/detail/xinglight/XL-0201UWC/25672884",
         jlc="C965789", jtype="Extended", jstock=7966, jprice=0.07, jl="https://jlcpcb.com/partdetail/C965789", ds="https://datasheet.lcsc.com/lcsc/2012301032_XINGLIGHT-XL-0201UWC_C965789.pdf", status="Active",
         short="Tiny: hardest to place and rework. DigiKey sells it only as a 5,000-piece reel (marketplace, ships from the maker). 185 mcd at 5 mA is dim at the 0.3 mA we plan to use. Only ~8,000 at JLCPCB (Extended part: extra fee).",
         verif="DigiKey page VERIFIED (price, stock, Vf 2.7 V, 185 mcd). 5 mA test current from a search summary. Height 0.65 mm UNVERIFIED."),
    dict(role="Option: small white LED for the second and minute rings (0402).", colour="White (cool)", pkg="0402 (1005 metric)", body="1.10 x 0.55", padL=1.56, padW=0.64, height=0.70, vf=2.8, itest=20, mcd=690, angle=120, config="Single LED, 2 pads",
         dkpn="5962-XL-1005UWCTR-ND", dkstock=100000, dkp1=0.01563, dkp100=None, dkmoq=5000, dkl="https://www.digikey.com/en/products/detail/xinglight/XL-1005UWC/25672941",
         jlc="C20613596", jtype="Extended", jstock=337280, jprice=0.0113, jl="https://jlcpcb.com/partdetail/C20613596", ds="https://jlcpcb.com/partdetail/C20613596", status="Active",
         short="DigiKey: reel of 5,000 only (marketplace). JLCPCB has two listings of this part number; the other (C965796) shows 0 stock. Datasheet brightness spread is wide (350-1000 mcd at 20 mA); the DigiKey page says 690.",
         verif="DigiKey and JLCPCB pages VERIFIED. Datasheet range from the earlier research report (LCSC PDF)."),
    dict(role="CURRENT DESIGN default for the hour ring (0603).", colour="White", pkg="0603 (1608 metric)", body="1.6 x 0.8", padL=2.45, padW=0.95, height=0.65, vf=2.85, itest=5, mcd=250, angle=120, config="Single LED, 2 pads",
         dkpn="Not sold by DigiKey", dkstock=None, dkp1=None, dkp100=None, dkmoq=None, dkl=None,
         jlc="C2290", jtype="Basic", jstock=2096313, jprice=0.0122, jl="https://jlcpcb.com/partdetail/C2290", ds="https://jlcpcb.com/partdetail/C2290", status="Active",
         short="Not on DigiKey (JLCPCB/LCSC only). Brightness varies a lot unit to unit (145-360 mcd at 5 mA; JLCPCB lists up to 360). Vf range 2.6-3.1 V. Height is an estimate.",
         verif="JLCPCB page VERIFIED (stock, price, Basic). Vf/brightness from the JLCPCB listing and the earlier research report. Height ESTIMATE."),
    dict(role="DigiKey stand-in for the 0603 white LED (not the same part).", colour="White", pkg="0603 (1608 metric)", body="1.6 x 0.8", padL=2.45, padW=0.95, height=0.65, vf=2.9, itest=20, mcd=120, angle=None, config="Single LED, 2 pads",
         dkpn="350-4383-2-ND", dkstock=2053, dkp1=0.62, dkp100=0.3103, dkmoq=1, dkl="https://www.digikey.com/en/products/detail/dialight/5973904507F/9385438",
         jlc="n/a", jtype="n/a", jstock=None, jprice=None, jl=None, ds="https://s3-us-west-2.amazonaws.com/catsy.557/C18367A.pdf", status="Active",
         short="About 25x the price of the Kento 0603 ($0.31 vs ~$0.012). Only 2,053 in stock, 12-week lead time. Test current for the 120 mcd rating is not confirmed.",
         verif="DigiKey page VERIFIED (price, stock, 2.9 V, 120 mcd). Test current 20 mA is an ESTIMATE; height ESTIMATE."),
    dict(role="CURRENT DESIGN option for the hour ring if you want it brighter/larger (0805).", colour="White", pkg="0805 (2012 metric)", body="2.0 x 1.25", padL=2.85, padW=1.40, height=0.80, vf=2.9, itest=5, mcd=250, angle=120, config="Single LED, 2 pads",
         dkpn="Not sold by DigiKey", dkstock=None, dkp1=None, dkp100=None, dkmoq=None, dkl=None,
         jlc="C34499", jtype="Basic", jstock=482058, jprice=0.0202, jl="https://jlcpcb.com/partdetail/C34499", ds="https://jlcpcb.com/partdetail/C34499", status="Active",
         short="Not on DigiKey. Conflicting brightness data: the datasheet says 145-360 mcd at 5 mA, JLCPCB's listing says 350 mcd at 25 mA. The 0805 is the largest ring part, so it sets the board size.",
         verif="JLCPCB page VERIFIED (stock, price, Basic). Brightness conflict flagged. Height ESTIMATE."),
    dict(role="DigiKey stand-in for the 0805 white LED (the 4th size).", colour="White", pkg="0805 (2012 metric)", body="2.0 x 1.25", padL=2.85, padW=1.40, height=0.80, vf=3.3, itest=20, mcd=281, angle=None, config="Single LED, 2 pads",
         dkpn="160-1738-2-ND", dkstock=155071, dkp1=0.50, dkp100=0.2476, dkmoq=1, dkl="https://www.digikey.com/en/products/detail/liteon/LTW-170TK/758704",
         jlc="n/a", jtype="n/a", jstock=None, jprice=None, jl=None, ds="https://optoelectronics.liteon.com/upload/download/DS22-2004-078/LTW-170TK.pdf", status="Active",
         short="Highest forward voltage (3.3 V): on a LiPo it needs ~3.6 V before it lights at all, so it goes dark long before the battery is empty. ~12x the price of the Kento 0805.",
         verif="DigiKey page VERIFIED (price, stock, 3.3 V, 281 mcd, datasheet link). Test current 20 mA and height are ESTIMATES."),
    dict(role="RGB LED from the first (RGB) watch design.", colour="Red / green / blue", pkg="0.83 x 0.83 mm, 4 pads", body="0.83 x 0.83", padL=None, padW=None, height=0.75, vf=2.5, itest=5, mcd="R 26 / G 37 / B 7.5", angle=140, config="Common CATHODE",
         dkpn="3147-B39D3RGB-F6C0001HOU1930CT-ND", dkstock=20772, dkp1=0.40, dkp100=0.1969, dkmoq=1, dkl="https://www.digikey.com/en/products/detail/harvatek-corporation/B39D3RGB-F6C0001HOU1930/13588747",
         jlc="C6509069", jtype="Extended", jstock=0, jprice=None, jl="https://jlcpcb.com/partdetail/C6509069", ds="https://www.digikey.com/en/products/detail/harvatek-corporation/B39D3RGB-F6C0001HOU1930/13588747", status="OBSOLETE (stocked until sold out)",
         short="Obsolete at DigiKey. Zero stock at JLCPCB. 0.3 mm pads on a 0.5 mm pitch cannot be hand-soldered. Vf R 1.9 / G 2.5 / B 2.5 V.",
         verif="DigiKey page VERIFIED on 2026-10-06 (20,772 in stock). JLCPCB stock 0 as of 2026-10-05. Test current ~5.2 mA from the part alias (UNVERIFIED)."),
    dict(role="JLCPCB's in-stock stand-in for the RGB LED (common ANODE).", colour="Red / green / blue", pkg="0.8 x 0.8 mm, 4 pads", body="0.8 x 0.8", padL=None, padW=None, height=0.60, vf=2.5, itest=3, mcd="R 16-28 / G 28-47 / B 7.5-12.6", angle=120, config="Common ANODE",
         dkpn="Not checked at DigiKey", dkstock=None, dkp1=None, dkp100=None, dkmoq=None, dkl=None,
         jlc="C404279", jtype="Extended", jstock=14075, jprice=0.0472, jl="https://jlcpcb.com/partdetail/C404279", ds="https://datasheet.lcsc.com/datasheet/pdf/1674e4a9e1dec82609abb7eb7f417a05.pdf?productCode=C404279", status="Active",
         short="Common-anode (the first design is common-cathode), so matrix drive polarity must be reversed. Vf up to 3.5 V for green/blue. Same 0.5 mm pad pitch: still needs a fab to place.",
         verif="JLCPCB page VERIFIED (stock, price). Datasheet figures from the earlier JLCPCB research report."),
]
for j, d in enumerate(LEDDATA):
    col = "BCDEFGHI"[j]
    txt(wd, f"{col}{R_['role']}", d["role"]); txt(wd, f"{col}{R_['colour']}", d["colour"]); txt(wd, f"{col}{R_['pkg']}", d["pkg"]); txt(wd, f"{col}{R_['body']}", d["body"])
    for key, row, fmt in (("padL", "padL", "0.00"), ("padW", "padW", "0.00"), ("height", "height", "0.00"), ("vf", "vf", "0.00"), ("itest", "itest", "0"), ("angle", "angle", "0")):
        v = d[key]
        c = txt(wd, f"{col}{R_[row]}", v if v is not None else "n/a", fmt=fmt if v is not None else None, wrap=False)
        if v is not None:
            c.font = F_INPUT; c.fill = FILL_IN; c.border = BOX
    c = txt(wd, f"{col}{R_['mcd']}", d["mcd"], fmt="0", wrap=False)
    if isinstance(d["mcd"], (int, float)):
        c.font = F_INPUT; c.fill = FILL_IN; c.border = BOX
    txt(wd, f"{col}{R_['config']}", d["config"])
    txt(wd, f"{col}{R_['dkpn']}", d["dkpn"])
    for key, row, fmt in (("dkstock", "dkstock", "#,##0"), ("dkp1", "dkp1", "$0.0000"), ("dkp100", "dkp100", "$0.0000"), ("dkmoq", "dkmoq", "#,##0")):
        v = d[key]
        txt(wd, f"{col}{R_[row]}", v if v is not None else "n/a", fmt=fmt if v is not None else None, wrap=False)
    put(wd, f"{col}{R_['dkmoqcost']}", f'=IF(AND(ISNUMBER({col}{R_["dkp1"]}),ISNUMBER({col}{R_["dkmoq"]})),{col}{R_["dkp1"]}*{col}{R_["dkmoq"]},"n/a")', fmt="$#,##0.00")
    if d["dkl"]:
        link(wd, f"{col}{R_['dklink']}", d["dkl"], "DigiKey page")
    else:
        txt(wd, f"{col}{R_['dklink']}", "-")
    txt(wd, f"{col}{R_['jlc']}", d["jlc"]); txt(wd, f"{col}{R_['jlctype']}", d["jtype"])
    txt(wd, f"{col}{R_['jlcstock']}", d["jstock"] if d["jstock"] is not None else "n/a", fmt="#,##0" if d["jstock"] is not None else None, wrap=False)
    txt(wd, f"{col}{R_['jlcprice']}", d["jprice"] if d["jprice"] is not None else "n/a", fmt="$0.0000" if d["jprice"] is not None else None, wrap=False)
    if d["jl"]:
        link(wd, f"{col}{R_['jlclink']}", d["jl"], "JLCPCB page")
    else:
        txt(wd, f"{col}{R_['jlclink']}", "-")
    link(wd, f"{col}{R_['ds']}", d["ds"], "datasheet / listing")
    txt(wd, f"{col}{R_['status']}", d["status"])
    put(wd, f"{col}{R_['cost_dk']}", f'=IF(ISNUMBER({col}{R_["dkp100"]}),{col}{R_["dkp100"]}*132,IF(ISNUMBER({col}{R_["dkp1"]}),{col}{R_["dkp1"]}*132,"n/a"))', fmt="$#,##0.00")
    put(wd, f"{col}{R_['cost_jlc']}", f'=IF(ISNUMBER({col}{R_["jlcprice"]}),{col}{R_["jlcprice"]}*132,"n/a")', fmt="$#,##0.00")
    put(wd, f"{col}{R_['vmin']}", f'=IF(ISNUMBER({col}{R_["vf"]}),{col}{R_["vf"]}+Inputs!$B$12,"n/a")', fmt="0.00")
    txt(wd, f"{col}{R_['short']}", d["short"], color="9C0006")
    txt(wd, f"{col}{R_['verif']}", d["verif"], italic=True, color="555555")
wd.column_dimensions["A"].width = 34
for col in "BCDEFGHI":
    wd.column_dimensions[col].width = 30
for r in (R_["role"], R_["short"], R_["verif"]):
    wd.row_dimensions[r].height = 118 if r == R_["short"] else 62
wd.freeze_panes = "B5"

# =============================================================== Sensors tab
wsn = wb.create_sheet("Sensors")
put(wsn, "A1", "Motion sensors: the two being compared, plus a backup", F_TITLE)
put(wsn, "A2", f"Checked {AS_OF}. A gravity / tilt game only needs an accelerometer; the gyroscope in the BMI270 is not needed for it. Currents are at the supply voltages in the datasheets (BMI270 table: VDD = 1.8 V), so real values at 3.3 V are a little different.", F_NOTE, wrap=True)
wsn.merge_cells("A2:D2"); wsn.row_dimensions[2].height = 32
head(wsn, 4, ["Attribute", "BMI270 (Bosch, 6-axis IMU)", "BMA400 (Bosch, accelerometer)", "LIS2DW12 (ST, accelerometer) - backup"])
wsn.row_dimensions[4].height = 34
slabs = ["Type", "Package / body (mm)", "KiCad courtyard width (mm)", "KiCad courtyard height (mm)", "Supply range", "Needs a configuration file loaded at every power-up?", "Built-in features",
         "Sleep / suspend current (uA)", "Waiting for motion, lowest-power mode (uA)", "Wake-on-motion total used in the model (uA)", "Running a game, accelerometer only (uA)", "Running a game, accelerometer + gyroscope (uA)",
         "DigiKey part number", "DigiKey stock (US)", "DigiKey price at 1 (USD)", "DigiKey lead time", "DigiKey link", "JLCPCB / LCSC part", "JLCPCB library type", "JLCPCB stock", "JLCPCB price at low quantity (USD)", "JLCPCB link",
         "Datasheet", "Status", "Shortcomings", "How well verified"]
label_col(wsn, slabs, 5)
SD = {
    "B": ["6-axis IMU (accelerometer + gyroscope)", "LGA-14, 2.5 x 3.0 x 0.83", 3.79, 3.29, "VDD 1.71-3.6 V", "YES: an 8 KB file every power-up (about 6.6 ms at 10 MHz SPI, then up to 20 ms wait)",
          "Wrist-wear wake-up, wrist gesture, any-motion, no-motion, significant motion, step counting", 3.5, 10, 13, 210, 685,
          "828-1091-2-ND", 50792, 4.23, "16 weeks", "https://www.digikey.com/en/products/detail/bosch-sensortec/BMI270/9974486", "C2836813", "Extended", 7628, 2.64, "https://jlcpcb.com/partdetail/C2836813",
          "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf", "Active",
          "Wake mode costs ~13 uA all day (~1 mWh/day, about half the whole watch). Needs the 8 KB config upload at every power-up. 0.5 mm 14-pad LGA: the biggest sensor footprint. Costs ~$4 each.",
          "Datasheet currents VERIFIED (BST-BMI270-DS000-08, Table 6 and electrical table). DigiKey and JLCPCB pages VERIFIED."],
    "C": ["3-axis accelerometer (no gyroscope)", "LGA-12, 2.0 x 2.0 x 0.95", 2.59, 2.59, "VDD 1.71-3.6 V (DigiKey page)", "No (boots by itself)", "Wake-up, activity change, orientation, tap, step counter",
          0.16, 0.85, 0.85, 14.5, "n/a",
          "828-1081-2-ND", 0, 2.48, "16 weeks", "https://www.digikey.com/en/products/detail/bosch-sensortec/BMA400/8634935", "not checked", "-", None, None, None,
          "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bma400-ds000.pdf", "Active",
          "ZERO stock at DigiKey US on every listing (checked three). No gyroscope, so no rotation games. Not checked at JLCPCB. No built-in wrist-gesture classifier: raise-to-wake needs more firmware.",
          "Currents VERIFIED by the earlier research (BST-BMA400-DS000-09). DigiKey pages VERIFIED today (stock 0, $2.48)."],
    "D": ["3-axis accelerometer (no gyroscope)", "LGA-12, 2.0 x 2.0 x 0.7", 2.59, 2.59, "1.62-3.6 V (LCSC listing)", "Believed no (UNVERIFIED)", "Wake-up, activity, 6D orientation, tap, free-fall (UNVERIFIED listing)",
          0.05, 1.0, 1.0, "n/a", "n/a",
          "497-17718-2-ND", 0, 1.38, "20 weeks", "https://www.digikey.com/en/products/detail/stmicroelectronics/LIS2DW12TR/7914708", "C189624", "Extended", 19750, 1.19, "https://jlcpcb.com/partdetail/C189624",
          "https://www.digikey.com/en/products/detail/stmicroelectronics/LIS2DW12TR/7914708", "Active",
          "Zero stock at DigiKey US (20-week lead time) but 19,750 at JLCPCB. ST's datasheet could not be read: current figures are UNVERIFIED ESTIMATES.",
          "DigiKey and JLCPCB pages VERIFIED today. All electrical figures UNVERIFIED (ST datasheet not read)."],
}
keys = ["type", "pkg", "cw", "ch", "supply", "cfg", "feat", "sleep", "lp", "wake", "game_a", "game_ag", "dkpn", "dkstock", "dkp", "dklead", "dklink", "jlc", "jtype", "jstock", "jprice", "jlclink", "ds", "status", "short", "verif"]
S_ROW = {k: 5 + i for i, k in enumerate(keys)}
for col, vals in SD.items():
    for k, v in zip(keys, vals):
        ref = f"{col}{S_ROW[k]}"
        if k in ("dklink", "jlclink", "ds"):
            if v and v.startswith("http"):
                link(wsn, ref, v, "link")
            else:
                txt(wsn, ref, "-")
        elif k in ("cw", "ch", "sleep", "lp", "wake", "game_a", "game_ag", "dkstock", "dkp", "jstock", "jprice"):
            fmt = {"cw": "0.00", "ch": "0.00", "dkstock": "#,##0", "jstock": "#,##0", "dkp": "$0.00", "jprice": "$0.00"}.get(k, "0.00")
            c = txt(wsn, ref, v if v is not None else "n/a", fmt=fmt if isinstance(v, (int, float)) else None, wrap=False)
            if isinstance(v, (int, float)) and k in ("sleep", "lp", "wake", "game_a", "game_ag"):
                c.font = F_INPUT; c.fill = FILL_IN; c.border = BOX
        elif k == "short":
            txt(wsn, ref, v, color="9C0006")
        elif k == "verif":
            txt(wsn, ref, v, italic=True, color="555555")
        else:
            txt(wsn, ref, v)
wsn.column_dimensions["A"].width = 38
for col in "BCD":
    wsn.column_dimensions[col].width = 44
wsn.row_dimensions[S_ROW["short"]].height = 105; wsn.row_dimensions[S_ROW["verif"]].height = 62; wsn.row_dimensions[S_ROW["cfg"]].height = 44; wsn.row_dimensions[S_ROW["feat"]].height = 44
wsn.freeze_panes = "B5"

# =============================================================== Batteries tab
wbt = wb.create_sheet("Batteries")
put(wbt, "A1", "Battery options (single-cell protected LiPo, wire leads, soldered to the back of the board)", F_TITLE)
put(wbt, "A2", f"Mouser prices/stock checked {AS_OF}. All four are Renata ICP cells (3.7 V). Runtime rows use the live load from the 'Power budget' tab, so they change when you change the inputs. Other cheaper LiPo cells exist (hobby vendors) but their protection circuits and dimensions are unverified.", F_NOTE, wrap=True)
wbt.merge_cells("A2:E2"); wbt.row_dimensions[2].height = 36
head(wbt, 4, ["Attribute"] + BAT_OPTS)
wbt.row_dimensions[4].height = 34
blabs = ["Manufacturer part number", "Capacity (mAh)", "Nominal voltage (V)", "Energy (mWh)", "Length (mm)", "Width (mm)", "Thickness max (mm, includes swelling)", "Footprint area (mm2)", "Volume (cm3)",
         "Energy density (mWh per cm3)", "Diagonal (mm)", "Weight (g)", "Protection circuit", "Maximum charge current", "Termination", "Temperature limits", "Mouser part number", "Mouser stock", "Mouser price at 1 (USD)",
         "Mouser price at 100 (USD)", "Mouser link", "Datasheet", "Price per mWh at 1 (USD)", "Runtime with no solar, current inputs (days)", "Runtime including special mode (days)", "Fits inside the board size calculated on 'Board size'?", "Shortcomings", "How well verified"]
label_col(wbt, blabs, 5)
B_ROW = {k: 5 + i for i, k in enumerate(["mpn", "mah", "v", "mwh", "L", "W", "T", "area", "vol", "dens", "diag", "wt", "prot", "chg", "term", "temp", "mpn2", "stock", "p1", "p100", "link", "ds", "ppm", "run", "run2", "fits", "short", "verif"])}
BD = [
    dict(mpn="ICP341018PM", mah=35, L=19.5, W=10.2, T=3.7, wt=1.7, prot="Yes (safety circuit)", chg="17.5 mA normal / 35 mA max (0.5C / 1C)", term="AWG30 wire leads", temp="Charge 0 to 45 C", m="614-ICP341018PM", stock=0, p1=13.87, p100=9.60,
         ml="https://www.mouser.com/ProductDetail/614-ICP341018PM", ds="https://asset.conrad.com/media10/add/160267/c1/-/en/001214022DS01/podatkovna-tablica-1214022-renata-icp341018pm-specijalni-akumulatori-prizmaticni-kabel-lipo-37-v-35-mah.pdf",
         short="Smallest and thinnest, but the least energy. NOT in stock at Mouser (factory order, lead time unknown). $13.87 each: the priciest per mWh.", verif="Dimensions, weight and charge limits VERIFIED (Renata datasheet via Conrad). Mouser price/stock VERIFIED today."),
    dict(mpn="ICP331319PM", mah=50, L=21.0, W=12.8, T=3.7, wt=2.0, prot="Yes (safety circuit)", chg="25 mA normal / 50 mA max", term="AWG30 wire leads", temp="Charge 0 to 45 C", m="614-ICP331319PM", stock=0, p1=12.21, p100=8.46,
         ml="https://www.mouser.com/ProductDetail/614-ICP331319PM", ds="https://asset.conrad.com/media10/add/160267/c1/-/gl/003015326DS00/tehnicni-podatki-3015326-renata-icp331319pm-specialni-akumulatorji-prismaticno-kabel-lipo-37-v-50-mah.pdf",
         short="Good thin option. NOT in stock at Mouser (factory order). The 21 x 12.8 mm size is the widest of the thin cells.", verif="Datasheet VERIFIED (Conrad copy). Mouser price/stock VERIFIED today."),
    dict(mpn="ICP501022UPM", mah=80, L=24.0, W=10.0, T=5.5, wt=2.6, prot="Yes (IEC62133 per search excerpt)", chg="40 mA normal / 80 mA max", term="Wire leads", temp="Charge 0 to 45 C", m="614-ICP501022UPM", stock=3, p1=12.22, p100=8.46,
         ml="https://www.mouser.com/ProductDetail/614-ICP501022UPM", ds="https://www.renata.com/fileadmin/downloads/productsheets/lithium_polymer/ICP501022UPM.pdf",
         short="Best energy for the size, but 5.5 mm thick (the thickest) and only 3 in stock at Mouser. 'Available in USA only' shipping flag.", verif="Mouser page VERIFIED today (3 in stock, $12.22, 24 x 10 x 5.5 mm, 0-45 C). Datasheet from Renata."),
    dict(mpn="ICP402025PC-01", mah=155, L=27.5, W=20.5, T=4.3, wt=4.0, prot="Yes (per datasheet excerpt)", chg="155 mA max", term="PC-01 connector version", temp="Charge 0 to 45 C", m="614-ICP402025PC-01", stock=0, p1=12.84, p100=8.89,
         ml="https://www.mouser.com/ProductDetail/614-ICP402025PC-01", ds="https://www.renata.com/fileadmin/downloads/productsheets/lithium_polymer/ICP402025PC-01.pdf",
         short="Most energy, but 27.5 x 20.5 mm: its diagonal is 34 mm, which forces a larger board. NOT in stock at Mouser. Connector version, not bare wires.", verif="Mouser price/stock VERIFIED today. Dimensions and charge limit are from an unopened datasheet excerpt (UNVERIFIED)."),
]
for j, d in enumerate(BD):
    col = "BCDE"[j]
    txt(wbt, f"{col}{B_ROW['mpn']}", d["mpn"], bold=True)
    c = txt(wbt, f"{col}{B_ROW['mah']}", d["mah"], fmt="0", wrap=False); c.font = F_INPUT; c.fill = FILL_IN; c.border = BOX
    c = txt(wbt, f"{col}{B_ROW['v']}", 3.7, fmt="0.0", wrap=False); c.font = F_INPUT; c.fill = FILL_IN; c.border = BOX
    put(wbt, f"{col}{B_ROW['mwh']}", f"={col}{B_ROW['mah']}*{col}{B_ROW['v']}", fmt="0.0", fill=FILL_OUT)
    for k, fmt in (("L", "0.0"), ("W", "0.0"), ("T", "0.0"), ("wt", "0.0")):
        c = txt(wbt, f"{col}{B_ROW[k]}", d[k], fmt=fmt, wrap=False); c.font = F_INPUT; c.fill = FILL_IN; c.border = BOX
    put(wbt, f"{col}{B_ROW['area']}", f"={col}{B_ROW['L']}*{col}{B_ROW['W']}", fmt="0")
    put(wbt, f"{col}{B_ROW['vol']}", f"={col}{B_ROW['area']}*{col}{B_ROW['T']}/1000", fmt="0.00")
    put(wbt, f"{col}{B_ROW['dens']}", f"={col}{B_ROW['mwh']}/{col}{B_ROW['vol']}", fmt="0")
    put(wbt, f"{col}{B_ROW['diag']}", f"=SQRT({col}{B_ROW['L']}^2+{col}{B_ROW['W']}^2)", fmt="0.0")
    txt(wbt, f"{col}{B_ROW['prot']}", d["prot"]); txt(wbt, f"{col}{B_ROW['chg']}", d["chg"]); txt(wbt, f"{col}{B_ROW['term']}", d["term"]); txt(wbt, f"{col}{B_ROW['temp']}", d["temp"])
    txt(wbt, f"{col}{B_ROW['mpn2']}", d["m"]); txt(wbt, f"{col}{B_ROW['stock']}", d["stock"], fmt="#,##0", wrap=False)
    txt(wbt, f"{col}{B_ROW['p1']}", d["p1"], fmt="$0.00", wrap=False); txt(wbt, f"{col}{B_ROW['p100']}", d["p100"], fmt="$0.00", wrap=False)
    link(wbt, f"{col}{B_ROW['link']}", d["ml"], "Mouser page"); link(wbt, f"{col}{B_ROW['ds']}", d["ds"], "datasheet")
    put(wbt, f"{col}{B_ROW['ppm']}", f"={col}{B_ROW['p1']}/{col}{B_ROW['mwh']}", fmt="$0.000")
    put(wbt, f"{col}{B_ROW['run']}", f"=IF('Power budget'!$B$22>0,{col}{B_ROW['mwh']}/'Power budget'!$B$22,0)", fmt="0", fill=FILL_OUT)
    put(wbt, f"{col}{B_ROW['run2']}", f"=IF('Power budget'!$B$61>0,{col}{B_ROW['mwh']}/'Power budget'!$B$61,0)", fmt="0", fill=FILL_OUT)
    put(wbt, f"{col}{B_ROW['fits']}", f"=IF('Board size'!$B$33>={col}{B_ROW['diag']}+2*'Board size'!$B$12,\"yes\",\"NO: too big\")")
    txt(wbt, f"{col}{B_ROW['short']}", d["short"], color="9C0006"); txt(wbt, f"{col}{B_ROW['verif']}", d["verif"], italic=True, color="555555")
wbt.column_dimensions["A"].width = 40
for col in "BCDE":
    wbt.column_dimensions[col].width = 34
wbt.row_dimensions[B_ROW["short"]].height = 92; wbt.row_dimensions[B_ROW["verif"]].height = 62; wbt.row_dimensions[B_ROW["chg"]].height = 30
wbt.freeze_panes = "B5"

# solar cell numeric dimensions (used by the board-size calculator)
head(sw, 21, ["Cell", "Footprint area (cm2)", "Type", "Power at 1 sun (mW)", "Measured at 200 lux (uW)", "Outdoor efficiency (a-Si only)", "Size (mm)", "Status", "Length (mm)", "Width (mm)", "Thickness (mm)", "Buy it"])
for r, (Lm, Wm, Tm, url, txtl) in zip((22, 23, 24), ((15.0, 15.0, 0.9, "https://www.digikey.com/en/products/detail/panasonic-energy/AM-1606C/25903138", "DigiKey (DISCONTINUED there, 640 left)"),
                                                     (11.35, 8.0, 1.2, "https://anysolar.biz/wp-content/uploads/2026/09/KXOB25-07X1TF-DATASHEET.pdf", "Anysolar datasheet (no live stock found)"),
                                                     (23.0, 25.0, 1.2, "https://www.digikey.com/en/products/detail/anysolar-ltd/KXOB081K06TF-TR/13999165", "DigiKey ($6.59, 2,754 on 10/06)"))):
    numinput(sw, f"I{r}", Lm, "0.00"); numinput(sw, f"J{r}", Wm, "0.00"); numinput(sw, f"K{r}", Tm, "0.00")
    link(sw, f"L{r}", url, txtl)
put(sw, "A25", "AM-1606C thickness: Panasonic's catalog says 0.7 mm, DigiKey's listing says 0.9 mm; the larger value is used here.", F_NOTE)
sw.column_dimensions["I"].width = 14; sw.column_dimensions["J"].width = 14; sw.column_dimensions["K"].width = 14; sw.column_dimensions["L"].width = 38

# =============================================================== Inputs: hardware choices
section(ws, 55, "8. Hardware choices (pick from the lists; other tabs update)")
put(ws, "A56", "Hour LED"); inp(ws, "B56", LED_OPTS[2])
put(ws, "A57", "Minute LED"); inp(ws, "B57", LED_OPTS[1])
put(ws, "A58", "Second LED"); inp(ws, "B58", LED_OPTS[1])
put(ws, "A59", "Battery"); inp(ws, "B59", BAT_OPTS[2])
put(ws, "A60", "Power variant"); inp(ws, "B60", VARIANTS[0])
put(ws, "A61", "Where to buy (for the cost on the Parts tab)"); inp(ws, "B61", ROUTES[0])
put(ws, "D56", "Options come from the 'LEDs' tab (white parts only).", F_NOTE)
put(ws, "D59", "Options come from the 'Batteries' tab; capacity feeds row 6.", F_NOTE)
put(ws, "D60", "A = charged through two pads (no solar). B = solar cell + harvester chip. B also puts the solar cell on the front for the board-size calculation.", F_NOTE)
for ref in ("B56", "B57", "B58", "B59", "B60", "B61"):
    ws[ref].alignment = Alignment(wrap_text=True, vertical="top")
ws.row_dimensions[56].height = 28; ws.row_dimensions[57].height = 28; ws.row_dimensions[58].height = 28; ws.row_dimensions[59].height = 28
ws.column_dimensions["B"].width = 46
dvl = DataValidation(type="list", formula1="=LEDs!$B$4:$G$4", allow_blank=False); ws.add_data_validation(dvl)
for ref in ("B56", "B57", "B58"):
    dvl.add(ref)
dvb = DataValidation(type="list", formula1="=Batteries!$B$4:$E$4", allow_blank=False); ws.add_data_validation(dvb); dvb.add("B59")
dvv = DataValidation(type="list", formula1='"A: pad-charged,B: solar harvester"', allow_blank=False); ws.add_data_validation(dvv); dvv.add("B60")
dvr = DataValidation(type="list", formula1='"JLCPCB / LCSC,DigiKey / Mouser"', allow_blank=False); ws.add_data_validation(dvr); dvr.add("B61")
# battery capacity now comes from the Batteries tab
c = ws["B6"]; c.value = "=INDEX(Batteries!$B$6:$E$6,MATCH(B59,Batteries!$B$4:$E$4,0))"; c.font = F_LINK; c.fill = PatternFill(fill_type=None); c.border = Border()
ws["D6"].value = "Comes from the battery you pick in row 59 (Batteries tab). To use a different cell, edit the capacity on the Batteries tab."

# LED types now look up the picks
for i, r in enumerate((5, 6, 7)):
    sel = f"Inputs!$B${56 + i}"
    for col, row in (("C", R_["pkg"]), ("D", R_["vf"]), ("K", R_["mcd"]), ("L", R_["itest"])):
        cc = wt[f"{col}{r}"]
        cc.value = f"=INDEX(LEDs!$B${row}:$G${row},MATCH({sel},LEDs!$B$4:$G$4,0))"
        cc.font = F_LINK; cc.fill = PatternFill(fill_type=None); cc.border = Border()
        cc.number_format = "0.00" if col == "D" else ("0" if col in "KL" else "General")

# =============================================================== Board size tab
wz = wb.create_sheet("Board size")
put(wz, "A1", "How big does the board have to be? (round board with the LED rings outside the electronics)", F_TITLE)
put(wz, "A2", "The board is the largest of four demands: (1) the LED rings themselves, (2) a free centre on the FRONT big enough for the solar cell (Variant B), (3) enough BACK area for every component and the battery, (4) room for the battery's diagonal. The strap lugs sit outside this circle.", F_NOTE, wrap=True)
wz.merge_cells("A2:G2"); wz.row_dimensions[2].height = 44
wz.column_dimensions["A"].width = 56
for col in "BCDEFG":
    wz.column_dimensions[col].width = 17
section(wz, 4, "Rules you can change", 7)
rules = [(5, "LED spacing around a ring (copper gap between neighbours, mm)", 0.5, "0.00"), (6, "Gap between rings, for traces (mm)", 0.8, "0.00"), (7, "Outer LED edge to board edge (mm)", 1.0, "0.00"),
         (8, "Clearance around the solar cell inside the free centre (mm)", 0.3, "0.00"), (9, "Extra free centre wanted when there is no solar cell (mm diameter)", 0, "0.0"),
         (10, "Routing and keep-out overhead on the back (x the sum of courtyards)", 1.3, "0.00"), (11, "Fraction of the back circle that parts can actually fill", 0.6, "0.00"),
         (12, "Battery edge margin to the board edge (mm)", 1.5, "0.0")]
for r, lab, v, fmt in rules:
    put(wz, f"A{r}", lab); inp(wz, f"B{r}", v, fmt)
put(wz, "C5", "0.5 = the default used for the ring layouts.", F_NOTE)
put(wz, "C10", "ESTIMATES (back-side packing).", F_NOTE)

section(wz, 14, "1. The LED rings (closed-form version of the ring generator)", 7)
head(wz, 15, ["Ring", "LED pick", "Pad length (mm)", "Pad width (mm)", "LEDs in ring", "Min ring radius from LED spacing (mm)"])
wz.row_dimensions[15].height = 44
for i, (nm, n, sel) in enumerate((("Hour (inner)", 12, "Inputs!$B$56"), ("Minute (middle)", 60, "Inputs!$B$57"), ("Second (outer)", 60, "Inputs!$B$58"))):
    r = 16 + i
    put(wz, f"A{r}", nm, bold=True); put(wz, f"B{r}", f"={sel}", F_LINK, wrap=True)
    put(wz, f"C{r}", f"=INDEX(LEDs!$B${R_['padL']}:$G${R_['padL']},MATCH({sel},LEDs!$B$4:$G$4,0))", fmt="0.00")
    put(wz, f"D{r}", f"=INDEX(LEDs!$B${R_['padW']}:$G${R_['padW']},MATCH({sel},LEDs!$B$4:$G$4,0))", fmt="0.00")
    put(wz, f"E{r}", n, fmt="0")
    put(wz, f"F{r}", f"=(D{r}+$B$5)/(2*SIN(PI()/E{r}))", fmt="0.00")
    wz.row_dimensions[r].height = 28
put(wz, "A19", "Ring thickness on each side of the free centre (mm)"); put(wz, "B19", "=B7+C18+C17+C16+2*B6", fmt="0.00", fill=FILL_OUT)
put(wz, "A20", "Smallest board radius from ring 3 (seconds, outermost)"); put(wz, "B20", "=F18+B7+C18/2", fmt="0.00")
put(wz, "A21", "Smallest board radius from ring 2 (minutes)"); put(wz, "B21", "=F17+B7+C18+B6+C17/2", fmt="0.00")
put(wz, "A22", "Smallest board radius from ring 1 (hours)"); put(wz, "B22", "=F16+B7+C18+C17+2*B6+C16/2", fmt="0.00")
put(wz, "A23", "DEMAND 1: board diameter the LED rings need (mm)", bold=True); put(wz, "B23", "=2*MAX(B20,B21,B22,B19)", fmt="0.0", fill=FILL_OUT)

section(wz, 25, "2. The front free centre (solar cell)", 7)
put(wz, "A26", "Solar cell shown on the front?"); put(wz, "B26", '=IF(Inputs!B60="B: solar harvester","yes","no")')
put(wz, "A27", "Cell picked on the Inputs tab"); put(wz, "B27", "=Inputs!B37", F_LINK)
put(wz, "A28", "Cell diagonal (mm)"); put(wz, "B28", "=SQRT(INDEX(Solar!$I$22:$I$24,MATCH(B27,Solar!$A$22:$A$24,0))^2+INDEX(Solar!$J$22:$J$24,MATCH(B27,Solar!$A$22:$A$24,0))^2)", fmt="0.0")
put(wz, "A29", "Free centre diameter needed (mm)"); put(wz, "B29", '=IF(B26="yes",B28+2*B8,B9)', fmt="0.0")
put(wz, "A30", "DEMAND 2: board diameter for the front free centre (mm)", bold=True); put(wz, "B30", "=B29+2*B19", fmt="0.0", fill=FILL_OUT)

section(wz, 32, "Result", 7)
put(wz, "A33", "FINAL BOARD DIAMETER (mm)", bold=True); put(wz, "B33", "=MAX(B23,B30,B54,B57)", fmt="0.0", fill=FILL_OUT, bold=True)
put(wz, "A34", "What sets it"); put(wz, "B34", '=IF(B33=B23,"the LED rings",IF(B33=B30,"the solar cell in the centre",IF(B33=B54,"back-side parts area","the battery diagonal")))', fill=FILL_OUT)
put(wz, "A35", "Free centre left on the front (mm diameter)"); put(wz, "B35", "=B33-2*B19", fmt="0.0")
put(wz, "A36", "Board area (mm2)"); put(wz, "B36", "=PI()*(B33/2)^2", fmt="0")

section(wz, 38, "3. The back side: every component's keep-out area", 7)
head(wz, 39, ["Part", "Courtyard W (mm)", "Courtyard H (mm)", "Quantity in this build", "Counted area (mm2)", "Source"])
wz.row_dimensions[39].height = 30
V_A = 'Inputs!$B$60="A: pad-charged"'
V_B = 'Inputs!$B$60="B: solar harvester"'
sens_in = lambda nm: f'IF(ISNUMBER(SEARCH("{nm}",Inputs!$B$32&Inputs!$B$51)),1,0)'
comp = [
    ("MCU AVR128DB48 (TQFP-48)", 10.39, 10.39, "1", "KiCad courtyard (VERIFIED)"),
    ("Motion sensor BMI270 (LGA-14)", "=Sensors!B7", "=Sensors!B8", sens_in("BMI270"), "KiCad courtyard"),
    ("Motion sensor BMA400 (LGA-12)", "=Sensors!C7", "=Sensors!C8", sens_in("BMA400"), "KiCad courtyard"),
    ("Motion sensor LIS2DW12 (LGA-12)", "=Sensors!D7", "=Sensors!D8", sens_in("LIS2DW12"), "KiCad courtyard"),
    ("32.768 kHz crystal (3215)", 4.09, 2.39, "1", "KiCad courtyard"),
    ("Charger MCP73831 (SOT-23-5), Variant A", 4.19, 3.49, f"IF({V_A},1,0)", "KiCad courtyard"),
    ("3.3 V LDO (SOT-23), Variant A", 3.95, 3.49, f"IF({V_A},1,0)", "KiCad courtyard"),
    ("Harvester BQ25570 (VQFN-20), Variant B", 4.8, 4.8, f"IF({V_B},1,0)", "ESTIMATE: no KiCad footprint (3.5 mm body + margin)"),
    ("Inductors L1, L2 (1210), Variant B", 4.65, 3.25, f"IF({V_B},2,0)", "KiCad courtyard (placeholder size)"),
    ("JST SH battery connector", 5.89, 6.65, "1", "KiCad courtyard"),
    ("Buttons (KMR2)", 5.69, 3.69, "2", "KiCad courtyard"),
    ("UPDI header (1x3, 1.27 mm)", 3.19, 4.91, "1", "KiCad courtyard"),
    ("Charge pads TP1/TP2, Variant A", 3.09, 3.10, f"IF({V_A},2,0)", "KiCad courtyard"),
    ("Small passives (0402): decoupling, pull-ups, ladders", 1.95, 1.03, f"IF({V_A},20,34)", "ESTIMATE of count (schematic: ~20 in A, ~34 in B)"),
]
first = 40
for i, (nm, w, h, q, src) in enumerate(comp):
    r = first + i
    put(wz, f"A{r}", nm); put(wz, f"B{r}", w, F_LINK if isinstance(w, str) else F_NORM, "0.00"); put(wz, f"C{r}", h, F_LINK if isinstance(h, str) else F_NORM, "0.00")
    put(wz, f"D{r}", f"={q}", fmt="0"); put(wz, f"E{r}", f"=B{r}*C{r}*D{r}", fmt="0.0"); put(wz, f"F{r}", src, F_NOTE)
last = first + len(comp) - 1          # 53
# (rows 54..57 hold the totals, kept right under the table)
put(wz, "A54", "DEMAND 3: board diameter for the back-side parts + battery (mm)", bold=True)
put(wz, "B54", f"=2*SQRT(((B55+B56)*B10)/(PI()*B11))", fmt="0.0", fill=FILL_OUT)
put(wz, "A55", "   (components alone, mm2)"); put(wz, "B55", f"=SUM(E{first}:E{last})", fmt="0")
put(wz, "A56", "   (battery footprint, mm2)"); put(wz, "B56", "=INDEX(Batteries!$B$12:$E$12,MATCH(Inputs!$B$59,Batteries!$B$4:$E$4,0))", fmt="0")
put(wz, "A57", "DEMAND 4: board diameter for the battery diagonal (mm)", bold=True); put(wz, "B57", "=INDEX(Batteries!$B$15:$E$15,MATCH(Inputs!$B$59,Batteries!$B$4:$E$4,0))+2*B12", fmt="0.0", fill=FILL_OUT)

section(wz, 59, "4. What if I group them differently? Board diameter (mm) for every battery x every front choice", 7)
head(wz, 60, ["Battery \\ front centre", "No solar cell", "AM-1606C", "KXOB25-07X1TF", "KXOB081K06TF (yours)"])
wz.row_dimensions[60].height = 30
put(wz, "A61", "Front-centre demand (mm)", F_NOTE)
put(wz, "B61", "=B9+2*B19", fmt="0.0")
for k, nm in enumerate(("AM-1606C", "KXOB25-07X1TF", "KXOB081K06TF (yours)")):
    col = "CDE"[k]
    put(wz, f"{col}61", f"=SQRT(INDEX(Solar!$I$22:$I$24,MATCH(\"{nm}\",Solar!$A$22:$A$24,0))^2+INDEX(Solar!$J$22:$J$24,MATCH(\"{nm}\",Solar!$A$22:$A$24,0))^2)+2*$B$8+2*$B$19", fmt="0.0")
for i, bn in enumerate(BAT_OPTS):
    r = 62 + i
    put(wz, f"A{r}", bn, bold=True)
    for col in "BCDE":
        put(wz, f"{col}{r}", f"=MAX($B$23,{col}$61,2*SQRT((($B$55+INDEX(Batteries!$B$12:$E$12,{i + 1}))*$B$10)/(PI()*$B$11)),INDEX(Batteries!$B$15:$E$15,{i + 1})+2*$B$12)", fmt="0.0", fill=FILL_OUT)
put(wz, "A66", "Each cell = the largest of: LED rings, that front choice, back-side area with that battery, and that battery's diagonal. Back-side parts use the current Variant/sensor picks on Inputs.", F_NOTE, wrap=True)
wz.merge_cells("A66:G66"); wz.row_dimensions[66].height = 30

# =============================================================== Wear and stack tab
wk = wb.create_sheet("Wear and stack")
put(wk, "A1", "Wearing it: thickness, the battery on the back, and the strap", F_TITLE)
put(wk, "A2", "Your assumption: no housing, strap through the board's slots, battery soldered to the back. This tab estimates the stack-up thickness and lists what could go wrong. Heights marked ESTIMATE are not from datasheets.", F_NOTE, wrap=True)
wk.merge_cells("A2:E2"); wk.row_dimensions[2].height = 32
wk.column_dimensions["A"].width = 58
for col in "BCDE":
    wk.column_dimensions[col].width = 40
section(wk, 4, "Stack-up from the front to the wrist (mm)", 5)
srows = [
    (5, "Front: tallest LED (mm)", "=MAX(INDEX(LEDs!$B$11:$G$11,MATCH(Inputs!B56,LEDs!$B$4:$G$4,0)),INDEX(LEDs!$B$11:$G$11,MATCH(Inputs!B57,LEDs!$B$4:$G$4,0)),INDEX(LEDs!$B$11:$G$11,MATCH(Inputs!B58,LEDs!$B$4:$G$4,0)))", "From the LEDs tab (heights are mostly ESTIMATES)."),
    (6, "Front: solar cell thickness (mm) if Variant B", '=IF(Inputs!B60="B: solar harvester",INDEX(Solar!$K$22:$K$24,MATCH(Inputs!B37,Solar!$A$22:$A$24,0)),0)', "From the Solar tab."),
    (7, "Front stack above the board (mm)", "=MAX(B5,B6)", "The cell sits in the middle; the LEDs are on the rings."),
    (8, "Board thickness (mm)", 1.6, "4-layer 1.6 mm FR-4 like the first design. A 1.0 mm board is possible but changes the quote."),
    (9, "Back: MCU height (mm)", 1.2, "ESTIMATE: TQFP-48 is about 1.2 mm; check the datasheet."),
    (10, "Back: battery thickness (mm, includes swelling)", "=INDEX(Batteries!$B$11:$E$11,MATCH(Inputs!B59,Batteries!$B$4:$E$4,0))", "From the Batteries tab."),
    (11, "Back stack below the board (mm)", "=MAX(B9,B10)", "The battery is the tallest thing on the back."),
    (12, "Protective film on the back, e.g. Kapton tape (mm)", 0.1, "Prevents skin contact with solder joints and the battery."),
    (13, "TOTAL THICKNESS without strap (mm)", "=B7+B8+B11+B12", "A typical wristwatch is roughly 8-12 mm thick (ESTIMATE)."),
]
for r, lab, v, note in srows:
    put(wk, f"A{r}", lab, bold=(r in (7, 11, 13)))
    if isinstance(v, str):
        put(wk, f"B{r}", v, fmt="0.00", fill=FILL_OUT if r in (7, 11, 13) else None)
    else:
        inp(wk, f"B{r}", v, "0.00")
    put(wk, f"C{r}", note, F_NOTE)
section(wk, 15, "Concerns with a bare board on the wrist (reasoning, not testing)", 5)
head(wk, 16, ["Concern", "Why it matters", "What to do", "How serious"])
cons = [
    ("Battery between board and strap, strap against the skin", "Your picture. The strap becomes the cushion and the barrier: skin never touches battery or solder joints. The strap must pass through the slots BEHIND the battery.", "Make the slots wide enough for the strap and keep the battery inside the circle so the strap cannot press on its edge.", "Good plan"),
    ("Battery directly against the skin", "Possible but not advisable: LiPo cells should not be bent, squeezed or pierced, and the pouch is soft. The Renata datasheet says charge only at 0-45 C (VERIFIED); skin plus a hot day can pass 45 C.", "Put a film or the strap between them. Do not charge the watch while wearing it.", "Avoid"),
    ("Sweat on exposed copper and solder", "ENIG pads and solder joints on the back will see sweat; salt water is conductive and corrosive. 3.7 V is low, but leakage drains the battery and corrodes pads.", "Conformal coat the back, or cover it with film. Keep LED front dry-ish; this is not waterproof.", "Medium"),
    ("Rough solder joints and wire leads against the wrist", "Sharp pins/leads are uncomfortable and can cut the film over time.", "Round the board edges, trim leads, film or tape over the back, and keep the strap between.", "Medium"),
    ("Cell swelling", "Renata's own datasheet lists maximum thickness above nominal (3.7 mm vs 3.4 mm) because cells swell (VERIFIED, ICP341018PM).", "Leave about 0.5 mm of space behind the cell; never glue it rigidly.", "Medium"),
    ("Charging temperature", "Cells charge only at 0-45 C; a watch in the sun can exceed 45 C. Neither the BQ25570 nor the MCP73831 has a battery-temperature input (research report).", "Avoid charging in direct sun; consider adding an NTC thermistor later.", "Medium (solar only)"),
    ("Thickness", "Board 1.6 mm + battery 3.7-5.5 mm + film + LEDs. See the total above.", "A thinner battery (35 or 50 mAh) saves about 2 mm; a thinner PCB saves up to 0.6 mm.", "Low"),
    ("No housing", "Bumps and static discharge reach the chip directly; the MCU pin protection is basic.", "Add small ESD protection on the buttons (TVS) if it gets worn daily.", "Low"),
    ("Nickel in ENIG", "ENIG has a nickel layer under the gold; a few people react to nickel if the gold wears through against skin.", "Film or coat the back so nothing metal touches skin.", "Low"),
]
for i, (a, b, c_, d_) in enumerate(cons):
    r = 17 + i
    txt(wk, f"A{r}", a, bold=True); txt(wk, f"B{r}", b); txt(wk, f"C{r}", c_); txt(wk, f"D{r}", d_)
    wk.row_dimensions[r].height = 76

# =============================================================== Parts (BOM and cost) tab
wpa = wb.create_sheet("Parts")
put(wpa, "A1", "Parts list for the current picks, with cost and every link", F_TITLE)
put(wpa, "A2", f"Quantities follow your picks on Inputs. Unit price uses the 'Where to buy' choice (row 61). DigiKey/Mouser/JLCPCB data checked {AS_OF} unless noted. 'n/a' means I did not fetch it. Prices are at the quantity shown (1 watch); volume pricing is lower.", F_NOTE, wrap=True)
wpa.merge_cells("A2:L2"); wpa.row_dimensions[2].height = 34
head(wpa, 4, ["Part", "Qty", "DigiKey / Mouser part", "DigiKey / Mouser stock", "DigiKey / Mouser price (USD)", "JLCPCB part", "JLCPCB stock", "JLCPCB price (USD)", "Unit price used (USD)", "Line cost (USD)", "Links", "Notes"])
wpa.row_dimensions[4].height = 44
head(wpa, 4, ["JLCPCB link"], col0=13)
ROUTE = "Inputs!$B$61"
def ledrow(r, name, n, selref):
    put(wpa, f"A{r}", name, bold=True); put(wpa, f"B{r}", n, fmt="0")
    put(wpa, f"C{r}", f"=INDEX(LEDs!$B${R_['dkpn']}:$G${R_['dkpn']},MATCH({selref},LEDs!$B$4:$G$4,0))")
    put(wpa, f"D{r}", f"=INDEX(LEDs!$B${R_['dkstock']}:$G${R_['dkstock']},MATCH({selref},LEDs!$B$4:$G$4,0))", fmt="#,##0")
    put(wpa, f"E{r}", f"=IF(ISNUMBER(INDEX(LEDs!$B${R_['dkp100']}:$G${R_['dkp100']},MATCH({selref},LEDs!$B$4:$G$4,0))),INDEX(LEDs!$B${R_['dkp100']}:$G${R_['dkp100']},MATCH({selref},LEDs!$B$4:$G$4,0)),INDEX(LEDs!$B${R_['dkp1']}:$G${R_['dkp1']},MATCH({selref},LEDs!$B$4:$G$4,0)))", fmt="$0.0000")
    put(wpa, f"F{r}", f"=INDEX(LEDs!$B${R_['jlc']}:$G${R_['jlc']},MATCH({selref},LEDs!$B$4:$G$4,0))")
    put(wpa, f"G{r}", f"=INDEX(LEDs!$B${R_['jlcstock']}:$G${R_['jlcstock']},MATCH({selref},LEDs!$B$4:$G$4,0))", fmt="#,##0")
    put(wpa, f"H{r}", f"=INDEX(LEDs!$B${R_['jlcprice']}:$G${R_['jlcprice']},MATCH({selref},LEDs!$B$4:$G$4,0))", fmt="$0.0000")
    put(wpa, f"K{r}", "see the LEDs tab"); put(wpa, f"L{r}", f"=\"Pick: \"&{selref}", F_NOTE)
ledrow(5, "Hour LEDs", 12, "Inputs!$B$56"); ledrow(6, "Minute LEDs", 60, "Inputs!$B$57"); ledrow(7, "Second LEDs", 60, "Inputs!$B$58")
parts = [
    ("MCU AVR128DB48-I/PT", "1", "150-AVR128DB48-I/PT-ND", 217, 2.16, "C1019766", 60, 5.38, "https://www.digikey.com/en/products/detail/microchip-technology/AVR128DB48-I-PT/12807288", "https://jlcpcb.com/partdetail/C1019766", "Only 60 at JLCPCB and 217 at DigiKey: thin supply for a prototype run."),
    ("Motion sensor BMI270", f"=IF(ISNUMBER(SEARCH(\"BMI270\",Inputs!$B$32&Inputs!$B$51)),1,0)", "828-1091-2-ND", 50792, 4.23, "C2836813", 7628, 2.64, "https://www.digikey.com/en/products/detail/bosch-sensortec/BMI270/9974486", "https://jlcpcb.com/partdetail/C2836813", ""),
    ("Motion sensor BMA400", f"=IF(ISNUMBER(SEARCH(\"BMA400\",Inputs!$B$32&Inputs!$B$51)),1,0)", "828-1081-2-ND", 0, 2.48, "not checked", None, None, "https://www.digikey.com/en/products/detail/bosch-sensortec/BMA400/8634935", None, "ZERO stock at DigiKey US on every listing."),
    ("Motion sensor LIS2DW12", f"=IF(ISNUMBER(SEARCH(\"LIS2DW12\",Inputs!$B$32)),1,0)", "497-17718-2-ND", 0, 1.38, "C189624", 19750, 1.19, "https://www.digikey.com/en/products/detail/stmicroelectronics/LIS2DW12TR/7914708", "https://jlcpcb.com/partdetail/C189624", "In stock at JLCPCB only."),
    ("Charger MCP73831T-2ACI/OT (Variant A)", f"=IF({V_A},1,0)", "MCP73831T-2ACI/OTTR-ND", 33567, 0.76, "C424093", 5708, 0.79, "https://www.digikey.com/en/products/detail/microchip-technology/MCP73831T-2ACI-OT/964301", "https://jlcpcb.com/partdetail/C424093", "JLCPCB figures are from 2026-10-05 (not re-checked)."),
    ("3.3 V LDO MCP1700T-3302E/TT (Variant A)", f"=IF({V_A},1,0)", "MCP1700T3302ETTTR-ND", 0, 0.51, "C39051", None, None, "https://www.digikey.com/en/products/detail/microchip-technology/MCP1700T-3302E-TT/652676", "https://www.lcsc.com/product-image/C39051.html", "Zero stock at DigiKey; LCSC stock not checked."),
    ("Harvester BQ25570RGRR (Variant B)", f"=IF({V_B},1,0)", "296-39934-2-ND", 8455, 8.87, "C506250", 476, 5.82, "https://www.digikey.com/en/products/detail/texas-instruments/BQ25570RGRR/4384228", "https://jlcpcb.com/partdetail/C506250", "Needs a custom footprint (RGR package) and a protected LiPo (UV cut-off fixed at 1.95 V)."),
    ("32.768 kHz crystal ABS07-32.768KHZ-T", "1", "535-9542-2-ND", 525316, 0.61, "C130253", None, 0.73, "https://www.digikey.com/en/products/detail/abracon-llc/ABS07-32-768KHZ-T/1236858", "https://jlcpcb.com/partdetail/C130253", "JLCPCB price estimated from the 2026-10-05 BOM match; stock not re-checked."),
    ("JST SM02B-SRSS-TB(LF)(SN) battery connector", "1", "455-SM02B-SRSS-TBTR-ND", 66088, None, "C160402", 27798, None, "https://www.digikey.com/en/products/detail/jst-sales-america-inc/SM02B-SRSS-TB/926708", "https://jlcpcb.com/partdetail/C160402", "Use the (LF)(SN) listing C160402 (27,798 in stock 2026-10-09); the plain SM02B-SRSS-TB listing C18337480 has 0 stock."),
    ("Buttons TS21-34-035-BK-260-SMT-TR", "2", "2223-TS21-34-035-BK-260-SMT-TR-ND", 39050, None, "not matched", None, None, "https://www.digikey.com/en/products/detail/same-sky-formerly-cui-devices/TS21-34-035-BK-260-SMT-TR/21186457", None, "Price not fetched; stock from the 10/06 list page. KiCad footprint used is a generic KMR2."),
    ("Small passives (about $0.02 each)", f"=IF({V_A},20,34)", "generic", None, 0.02, "generic", None, 0.02, None, None, "ESTIMATE."),
]
for i, (nm, q, dkpn, dks, dkp, jc, js, jp, dkl, jl, note) in enumerate(parts):
    r = 8 + i
    put(wpa, f"A{r}", nm, bold=True); put(wpa, f"B{r}", q if q.startswith("=") else int(q), fmt="0")
    put(wpa, f"C{r}", dkpn); put(wpa, f"D{r}", dks if dks is not None else "n/a", fmt="#,##0"); put(wpa, f"E{r}", dkp if dkp is not None else "n/a", fmt="$0.00")
    put(wpa, f"F{r}", jc); put(wpa, f"G{r}", js if js is not None else "n/a", fmt="#,##0"); put(wpa, f"H{r}", jp if jp is not None else "n/a", fmt="$0.00")
    if dkl:
        link(wpa, f"K{r}", dkl, "DigiKey")
        if jl:
            link(wpa, f"M{r}", jl, "JLCPCB")
    elif jl:
        link(wpa, f"K{r}", jl, "JLCPCB")
    put(wpa, f"L{r}", note, F_NOTE, wrap=True)
nparts = 8 + len(parts)                       # next free row = 19
# solar cell and battery rows
rS, rB, rP = nparts, nparts + 1, nparts + 2    # 19, 20, 21
put(wpa, f"A{rS}", "Solar cell (Variant B)", bold=True); put(wpa, f"B{rS}", f"=IF({V_B},1,0)", fmt="0")
put(wpa, f"C{rS}", "=CHOOSE(MATCH(Inputs!B37,Solar!$A$22:$A$24,0),\"11-AM-1606C-ND\",\"not at DigiKey\",\"2994-KXOB081K06TF-TR-ND\")")
put(wpa, f"D{rS}", "=CHOOSE(MATCH(Inputs!B37,Solar!$A$22:$A$24,0),640,\"n/a\",2754)", fmt="#,##0")
put(wpa, f"E{rS}", "=CHOOSE(MATCH(Inputs!B37,Solar!$A$22:$A$24,0),3.14,\"n/a\",6.59)", fmt="$0.00")
put(wpa, f"F{rS}", "-"); put(wpa, f"G{rS}", "-"); put(wpa, f"H{rS}", "-"); put(wpa, f"L{rS}", "AM-1606C is discontinued at DigiKey; KXOB25-07X1TF has no live stock found (ask Anysolar); the price shown for it is n/a.", F_NOTE, wrap=True)
link(wpa, f"K{rS}", "https://www.digikey.com/en/products/detail/anysolar-ltd/KXOB081K06TF-TR/13999165", "see Solar tab for each cell")
put(wpa, f"A{rB}", "Battery (picked)", bold=True); put(wpa, f"B{rB}", 1, fmt="0")
put(wpa, f"C{rB}", "=INDEX(Batteries!$B$21:$E$21,MATCH(Inputs!B59,Batteries!$B$4:$E$4,0))")
put(wpa, f"D{rB}", "=INDEX(Batteries!$B$22:$E$22,MATCH(Inputs!B59,Batteries!$B$4:$E$4,0))", fmt="#,##0")
put(wpa, f"E{rB}", "=INDEX(Batteries!$B$23:$E$23,MATCH(Inputs!B59,Batteries!$B$4:$E$4,0))", fmt="$0.00")
put(wpa, f"F{rB}", "-"); put(wpa, f"G{rB}", "-"); put(wpa, f"H{rB}", "-"); put(wpa, f"L{rB}", "Mouser is the only source found; JLCPCB does not stock Renata cells.", F_NOTE, wrap=True)
link(wpa, f"K{rB}", "https://www.mouser.com/new/renata/renata-icp-series/", "Renata ICP at Mouser")
put(wpa, f"A{rP}", "Bare PCB, per watch (placeholder)", bold=True); put(wpa, f"B{rP}", 1, fmt="0")
for col in "CDEFG":
    put(wpa, f"{col}{rP}", "-")
put(wpa, f"H{rP}", "=61.65/5", fmt="$0.00"); put(wpa, f"E{rP}", "=61.65/5", fmt="$0.00")
put(wpa, f"L{rP}", "ESTIMATE from the RGB board's JLCPCB quote ($61.65 for 5, shipping extra); the single-colour board has not been quoted.", F_NOTE, wrap=True)
for r in list(range(5, 8)) + list(range(8, rP + 1)):
    put(wpa, f"I{r}", f'=IF({ROUTE}="JLCPCB / LCSC",IF(ISNUMBER(H{r}),H{r},IF(ISNUMBER(E{r}),E{r},0)),IF(ISNUMBER(E{r}),E{r},IF(ISNUMBER(H{r}),H{r},0)))', fmt="$0.0000")
    put(wpa, f"J{r}", f"=B{r}*I{r}", fmt="$0.00", fill=FILL_OUT)
put(wpa, f"A{rP + 1}", "TOTAL for one watch (USD)", bold=True); put(wpa, f"J{rP + 1}", f"=SUM(J5:J{rP})", fmt="$0.00", fill=FILL_OUT, bold=True)
put(wpa, f"A{rP + 2}", "Same for 5 watches (USD, no volume discount)"); put(wpa, f"J{rP + 2}", f"=5*J{rP + 1}", fmt="$0.00")
put(wpa, f"A{rP + 3}", "Parts with no price fetched are counted as $0, so the total is a floor.", F_NOTE)
wpa.column_dimensions["A"].width = 40
for col, w in zip("BCDEFGHIJKLM", (7, 30, 14, 16, 16, 12, 16, 14, 14, 18, 60, 12)):
    wpa.column_dimensions[col].width = w
wpa.freeze_panes = "B5"

# =============================================================== Shortcomings tab
wh = wb.create_sheet("Shortcomings")
put(wh, "A1", "Every shortcoming in one place (what could go wrong with each choice)", F_TITLE)
put(wh, "A2", f"Verified on {AS_OF} unless marked. Severity: HIGH = could block the build or change the design; MEDIUM = cost/risk to manage; LOW = minor.", F_NOTE, wrap=True)
wh.merge_cells("A2:D2")
head(wh, 4, ["Choice", "Shortcoming", "Severity", "Evidence"])
rows_s = [
    ("LED: white 0201 (Xinglight XL-0201UWC)", "Tiny to place; DigiKey sells only 5,000-piece reels; 185 mcd is dim at 0.3 mA.", "MEDIUM", "DigiKey page, JLCPCB page"),
    ("LED: white 0402 (Xinglight XL-1005UWC)", "DigiKey reel-only (5,000); JLCPCB has a second listing for the same MPN with 0 stock.", "MEDIUM", "DigiKey, JLCPCB C20613596 and C965796"),
    ("LED: white 0603 / 0805 Kento (KT-0603W / KT-0805W)", "Not on DigiKey (JLCPCB/LCSC only); wide brightness spread; datasheet and listing disagree for the 0805.", "MEDIUM", "JLCPCB C2290, C34499"),
    ("LED: Dialight 0603 and Lite-On 0805 (DigiKey alternatives)", "25x and 12x the price of the Kento parts; Lite-On needs 3.3 V Vf, so it goes dark long before the battery is empty.", "MEDIUM", "DigiKey pages"),
    ("LED drive (all white LEDs on a LiPo)", "With a 150 ohm resistor the LED current falls from ~8 mA at 4.2 V to 0 at ~3.0 V; brightness will swing ~4x over the battery range.", "HIGH", "Calculated on 'LED types' tab"),
    ("RGB LED Harvatek B39D3RGB", "Obsolete, zero stock at JLCPCB; 0.3 mm pads cannot be hand-soldered.", "HIGH", "DigiKey 2026-10-06, JLCPCB 10/05"),
    ("RGB LED Meihua MHPA0808RGBDT", "Common anode: the original matrix needs reversed drive; Vf up to 3.5 V.", "MEDIUM", "JLCPCB / LCSC datasheet"),
    ("Sensor BMI270", "Always-on wake costs ~13 uA (~1 mWh/day, about half the watch); needs an 8 KB config upload at every power-up; priciest.", "MEDIUM", "BMI270 datasheet Table 6; DigiKey page"),
    ("Sensor BMA400", "ZERO stock at DigiKey US on every listing; not checked at JLCPCB; no gyroscope.", "HIGH", "DigiKey pages 8634935 / 8634944 / 8634941"),
    ("Sensor LIS2DW12", "Zero stock at DigiKey US (20-week lead time); datasheet figures not verified.", "MEDIUM", "DigiKey page; JLCPCB has 19,750"),
    ("MCU AVR128DB48", "Thin supply: 217 at DigiKey, 60 at JLCPCB. Crystal pins are dedicated (PF0/PF1). Row pins cannot carry a full 12-LED row in game mode.", "MEDIUM", "DigiKey and JLCPCB pages; calculator"),
    ("Solar cell: your KXOB081K06TF", "23 x 25 mm: forces a ~48-53 mm board with the LED rings around it.", "HIGH (size)", "Board size tab"),
    ("Solar cell: Anysolar KXOB25-07X1TF", "No live stock found; datasheet 'Preliminary'; one 0.57 V cell is marginal for a harvester's cold start.", "MEDIUM", "Anysolar datasheet"),
    ("Solar cell: Panasonic AM-1606C", "DISCONTINUED at DigiKey (640 left); thickness 0.7 mm (catalog) vs 0.9 mm (DigiKey); glass, bare electrodes, indoor-type (weak in sun).", "HIGH", "DigiKey page 25903138; Panasonic catalog"),
    ("Harvester BQ25570", "Needs a custom footprint; UV cut-off fixed at 1.95 V so it requires a protected cell; $8.87 at DigiKey ($5.82 JLCPCB).", "MEDIUM", "TI datasheet; DigiKey; JLCPCB"),
    ("Charger MCP73831 + LDO (Variant A)", "LDO has zero stock at DigiKey (LCSC not checked); charge pads need a charging dock or cable.", "LOW", "DigiKey pages"),
    ("Battery Renata ICP cells", "All $12-14 each; three of four not stocked at Mouser (80 mAh has 3); 'USA only' flag; 0-45 C charging.", "HIGH", "Mouser pages 2026-10-08"),
    ("Battery: 155 mAh", "27.5 x 20.5 mm: its diagonal forces a bigger board.", "MEDIUM", "Board size tab"),
    ("Wearing it bare", "No housing: sweat, rough solder joints, battery swelling, charging in the sun; thickness ~8-10 mm.", "MEDIUM", "Wear and stack tab (reasoning)"),
    ("Assembly of the whole board", "JLCPCB: LED rings with 0402/0603 are fine; fine-pitch 5-degree rotation is allowed as an extra service (not guaranteed).", "MEDIUM", "JLCPCB chat, 2026-10-05"),
]
for i, (a, b, s_, e) in enumerate(rows_s):
    r = 5 + i
    txt(wh, f"A{r}", a, bold=True); txt(wh, f"B{r}", b); c = txt(wh, f"C{r}", s_, bold=True)
    c.font = Font(name=ARIAL, size=10, bold=True, color="9C0006" if s_.startswith("HIGH") else ("9C5700" if s_.startswith("MEDIUM") else "006100"))
    txt(wh, f"D{r}", e, italic=True, color="555555")
    wh.row_dimensions[r].height = 46
wh.column_dimensions["A"].width = 42; wh.column_dimensions["B"].width = 90; wh.column_dimensions["C"].width = 14; wh.column_dimensions["D"].width = 44
wh.freeze_panes = "A5"

# =============================================================== update older formulas for the new picks
# harvest only counts for Variant B
wp["B30"].value = '=IF(Inputs!B60="B: solar harvester",INDEX(Solar!B28:D30,MATCH(Inputs!B37,Solar!A28:A30,0),MATCH(Inputs!B38,Solar!B27:D27,0)),0)'
wp["A30"].value = "Harvest per day (mWh), counted only for Variant B"

# =============================================================== tab order
order = ["Inputs", "LEDs", "Sensors", "Batteries", "Solar", "Parts", "Board size", "Wear and stack", "Shortcomings", "Power budget", "Every LED", "LED types", "Lists", "Notes"]
wb._sheets = [wb[n] for n in order]
