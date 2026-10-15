# Executed inside build_power_workbook.py after build_spec_tabs.py. Adds: MCUs tab, Layout fit tab; datasheet-based fixes to Sensors / Lists / Inputs.
from openpyxl.styles import Font, Alignment

# ---------------------------------------------------------------- datasheet-based fixes
# LIS2DW12 numbers are now read from DS11811 rev 9 (Table 4, section 2.2)
for ref, v in (("D12", 0.05), ("D13", 1.0), ("D14", 1.0), ("D15", 5.0)):
    c = wsn[ref]; c.value = v
wsn["D10"].value = "No (boots by itself)"
wsn["D9"].value = "VDD 1.62-3.6 V, separate VDD_IO 1.62 V to VDD+0.1 V"
wsn["D11"].value = "Wake-up, activity/inactivity, free-fall, 6D/4D orientation, single/double tap, stationary/motion detect, 32-level FIFO, temperature sensor"
wsn["D5"].value = "3-axis accelerometer (no gyroscope)"
wsn["D6"].value = "LGA-12, 2.0 x 2.0 x 0.7 max"
wsn["D4"].value = "LIS2DW12 (ST, accelerometer) - CURRENT PICK"
wsn["D29"].value = ("Zero stock at DigiKey US (20-week lead time), but 19,712 at JLCPCB for $1.19. Datasheet DS11811 rev 9 is saved in datasheets/. "
                    "Interrupt output only reaches VDD_IO - 0.2 V (~3.1 V): the MCU input must be set to TTL level. Low-power-mode figures are at 1.8 V.")
wsn["D30"].value = "VERIFIED: ST datasheet DS11811 rev 9 (Table 4: 50 nA power-down, 1 uA @12.5 Hz, 0.38 uA @1.6 Hz, 5 uA @100 Hz low-power mode 1, 90 uA high-performance). DigiKey/JLCPCB pages VERIFIED."
# the game-mode current row in Lists
for row in range(2, 8):
    if wl[f"F{row}"].value == "LIS2DW12 normal mode":
        wl[f"G{row}"].value = 5.0
        wl[f"H{row}"].value = "VERIFIED: LIS2DW12 DS11811 Table 4, low-power mode 1, ODR 100 Hz = 5 uA (at 1.8 V)."
    if wl[f"A{row}"].value == "LIS2DW12 accelerometer wake":
        wl[f"B{row}"].value = 1.0
        wl[f"D{row}"].value = "VERIFIED: LIS2DW12 DS11811 Table 4, low-power mode 1 at 12.5 Hz = 1 uA typ (1.8 V; slightly higher at 3.3 V)."
# MCU pin drop is larger than 0.3 V (datasheet worst-case: 0.6 V sink + 0.7 V source at the rated 10 mA/6 mA)
ws["B12"].value = 0.5
ws["D12"].value = ("Worst case from the datasheets: AVR128DB sink 0.6 V at 10 mA and source 0.7 V at 6 mA, so about 0.2 V + 0.4 V = 0.6 V at 3-4 mA. "
                   "Typical is lower; 0.5 V used. The old 0.3 V was optimistic.")

# ---------------------------------------------------------------- MCUs tab
wm = wb.create_sheet("MCUs")
put(wm, "A1", "Microcontroller comparison: one for the single-colour watch, one for the RGB watch", F_TITLE)
put(wm, "A2", f"Pin counts, limits and pin maps are from the datasheets saved in datasheets/ (AVR128DB DS40002247B; ATmega169P doc8018P: the 169P edition, the PA edition could not be downloaded). Stock/price from JLCPCB {AS_OF}.", F_NOTE, wrap=True)
wm.merge_cells("A2:E2"); wm.row_dimensions[2].height = 32
head(wm, 4, ["Attribute", "AVR128DB48 (single colour - CURRENT PICK)", "ATmega169PA (RGB - CURRENT PICK)", "AVR128DB64 (RGB alternative)", "ATmega1284P (single colour backup)"])
wm.row_dimensions[4].height = 44
mrows = [
    ("Package / body", "TQFP-48 7x7 (or VQFN-48 6x6)", "TQFP-64 14x14 (or QFN-64 9x9)", "QFN-64 9x9 (TQFP-64 10x10: 0 stock)", "TQFP-44 10x10"),
    ("Usable GPIO after crystal/reset/programming pins", 38, 53, 53, 32),
    ("GPIO this watch needs (matrix + extras)", 29, 48, 48, 29),
    ("Spare GPIO", "=B6-B7", "=C6-C7", "=D6-D7", "=E6-E7"),
    ("Sink current guaranteed per pin at 3 V (mA)", 10, "5 (Port B: 10)", 10, "n/a (not read)"),
    ("Source current guaranteed per pin at 3 V (mA)", 6, "5 (Port B: 10)", 6, "n/a (not read)"),
    ("Absolute maximum per pin (mA)", 50, 40, 50, "n/a (not read)"),
    ("Sleep with 32 kHz crystal running (uA, typ)", "about 3 (0.65 power-down + ~2.1 RTC)", 0.8, "about 3", "n/a (not read)"),
    ("Programming", "UPDI (1 pin)", "ISP/JTAG (shares row pins)", "UPDI", "ISP"),
    ("Max clock at 3-4.2 V", "24 MHz", "8 MHz", "24 MHz", "n/a (not read)"),
    ("32 kHz crystal pins", "PF0/PF1 (GPIO lost)", "pins 23/24 (dedicated XTAL1/XTAL2)", "PF0/PF1", "n/a (not read)"),
    ("Pin-change / wake limits", "any pin (LEVEL or BOTHEDGES)", "PB, PE (PCINT) and PD1 (INT0) only", "any pin", "n/a (not read)"),
    ("Hazards found in the datasheet", "Port C powered from VDDIO2 (tie to VDD, set fuse); INT input needs TTL level", "JTAG fuse on at the factory (PF4-PF7); crystal must be on pins 23/24", "same as AVR128DB48", "not read"),
    ("JLCPCB part / stock / price", "C1019766 / 60 / $5.38", "C9434 / 170 / $4.87 (also C507109 / 226 / $4.02)", "C1019767 / 11 / $5.55", "C33575 / 1,943 / $6.59"),
    ("DigiKey stock", "217 (AVR128DB48-I/PT)", "not checked", "not checked", "not checked"),
    ("Datasheet in folder", "yes: datasheets/AVR128DB28-32-48-64-DS40002247B.pdf", "169P edition only (PA not downloadable)", "same as AVR128DB48", "no"),
    ("Why pick it / why not", "UPDI, 1 pin to program, low sleep, enough pins. Weakness: low JLCPCB stock (60).", "Low sleep (0.8 uA), JLCPCB stocked, same family as the first board. Weakness: 14x14 mm body, 5 mA/pin on most ports.", "Same family as the single-colour chip; stock only 11.", "Big body, almost no spare pins, ISP."),
]
for i, row in enumerate(mrows):
    r = 5 + i
    put(wm, f"A{r}", row[0], bold=True, wrap=True)
    for j, v in enumerate(row[1:]):
        col = "BCDE"[j]
        isf = isinstance(v, str) and v.startswith("=")
        c = put(wm, f"{col}{r}", v, F_NORM, "0" if isinstance(v, (int, float)) or isf else None, wrap=True)
        if isf:
            c.fill = FILL_OUT
wm.column_dimensions["A"].width = 44
for col in "BCDE":
    wm.column_dimensions[col].width = 38
for r in (17, 18, 20, 21):
    wm.row_dimensions[r].height = 62
put(wm, "A22", "Row-pin check: single colour game mode (12 LEDs in one row, 'Power budget' tab uses the same peak current)", bold=True)
put(wm, "A23", "Peak current per lit LED (mA)"); put(wm, "B23", "=AVERAGE('LED types'!F5:F7)", fmt="0.00")
put(wm, "A24", "Sink current if all 12 LEDs of a row are lit at once (mA)"); put(wm, "B24", "=12*B23", fmt="0.0")
put(wm, "A25", "Guaranteed sink current per pin (mA)"); put(wm, "B25", "=B9", F_LINK, "0")
put(wm, "A26", "Most LEDs per slot a pin can take (software scheduling)"); put(wm, "B26", "=MAX(1,INT(B25/B23))", fmt="0", fill=FILL_OUT)
put(wm, "A27", "Verdict"); put(wm, "B27", '=IF(B24<=B25,"OK without drivers","TOO MUCH for one pin: schedule "&B26&" LEDs per slot (dimmer game) or add row driver transistors")', fill=FILL_OUT)
wm.merge_cells("B27:E27")

# ---------------------------------------------------------------- Layout fit tab
wf = wb.create_sheet("Layout fit")
put(wf, "A1", "Layout fit: does everything fit around / behind the solar cell?", F_TITLE)
put(wf, "A2", ("Picture: a round board. Outer band = the three LED rings. Inside the band, the front has a free round area; Variant B puts the rectangular solar cell in its middle, "
               "leaving four curved pockets (top, bottom, left, right) for chips and buttons. The BACK of the board carries the battery and whatever does not fit on the front. "
               "All areas are keep-out areas from the 'Board size' tab (courtyards x quantity), not exact placement."), F_NOTE, wrap=True)
wf.merge_cells("A2:G2"); wf.row_dimensions[2].height = 52
wf.column_dimensions["A"].width = 58
for col in "BCDEFG":
    wf.column_dimensions[col].width = 16
section(wf, 4, "Geometry (live from the Board size tab)", 7)
geo = [
    (5, "Board diameter (mm)", "='Board size'!B33", "0.0"),
    (6, "LED band thickness each side (mm)", "='Board size'!B19", "0.00"),
    (7, "Free inner circle radius (mm)", "=B5/2-B6", "0.00"),
    (8, "Cell picked on Inputs", "=Inputs!B37", None),
    (9, "Cell length (mm)", "=INDEX(Solar!$I$22:$I$24,MATCH(B8,Solar!$A$22:$A$24,0))", "0.0"),
    (10, "Cell width (mm)", "=INDEX(Solar!$J$22:$J$24,MATCH(B8,Solar!$A$22:$A$24,0))", "0.0"),
    (11, "Solar cell on the front? (Variant B)", '=IF(Inputs!B60="B: solar harvester","yes","no")', None),
    (12, "Cell half-diagonal (mm)", "=IF(B11=\"yes\",SQRT(B9^2+B10^2)/2,0)", "0.0"),
    (13, "Does the cell fit inside the free circle?", '=IF(B11="no","no cell",IF(B12<=B7,"yes","NO: cell corners hit the LED band"))', None),
    (14, "Free front area, circle minus cell (mm2)", "=PI()*B7^2-IF(B11=\"yes\",B9*B10,0)", "0"),
    (15, "Top pocket area (mm2)", "=IF(B11=\"yes\",MAX(0,B7^2*ACOS(MIN(1,B10/2/B7))-(B10/2)*SQRT(MAX(0,B7^2-(B10/2)^2))),PI()*B7^2/2)", "0"),
    (16, "Bottom pocket area (mm2)", "=B15", "0"),
    (17, "Left + right pockets area (mm2)", "=MAX(0,B14-B15-B16)", "0"),
    (18, "Fraction of a pocket parts can actually fill", "='Board size'!B11", "0.00"),
    (19, "Usable front area (mm2)", "=B14*B18", "0"),
]
for r, lab, f, fmt in geo:
    put(wf, f"A{r}", lab); put(wf, f"B{r}", f, F_LINK if "!" in f else F_NORM, fmt)
put(wf, "C15", "Cap above/below a rectangle that is as wide as the cell is long (rotate the cell in the layout to trade top/bottom for left/right).", F_NOTE)

section(wf, 21, "Where each part goes (1 = front pocket, 0 = back with the battery)", 7)
head(wf, 22, ["Part", "Area (mm2)", "On the front? (1/0)"])
placement = [0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1]
for i in range(len(comp)):
    r = 23 + i
    put(wf, f"A{r}", f"='Board size'!A{first + i}", F_LINK); put(wf, f"B{r}", f"='Board size'!E{first + i}", F_LINK, "0.0")
    inp(wf, f"C{r}", placement[i], "0")
lastr = 23 + len(comp) - 1
section(wf, lastr + 2, "Result", 7)
r0 = lastr + 3
put(wf, f"A{r0}", "Front parts needing area (mm2, x routing overhead)"); put(wf, f"B{r0}", f"=SUMPRODUCT(B23:B{lastr},C23:C{lastr})*'Board size'!B10", fmt="0")
put(wf, f"A{r0 + 1}", "Usable front area (mm2)"); put(wf, f"B{r0 + 1}", "=B19", fmt="0")
put(wf, f"A{r0 + 2}", "FRONT VERDICT", bold=True); put(wf, f"B{r0 + 2}", f'=IF(B{r0}<=B{r0 + 1},"fits ("&TEXT(B{r0}/B{r0 + 1},"0%")&" full)","DOES NOT FIT: "&TEXT(B{r0}/B{r0 + 1},"0%")&" of the space")', fill=FILL_OUT)
put(wf, f"A{r0 + 3}", "Back parts + battery needing area (mm2, x routing overhead)"); put(wf, f"B{r0 + 3}", f"=(SUMPRODUCT(B23:B{lastr},1-C23:C{lastr})+'Board size'!B56)*'Board size'!B10", fmt="0")
put(wf, f"A{r0 + 4}", "Usable back area (whole circle, mm2)"); put(wf, f"B{r0 + 4}", "=PI()*(B5/2)^2*'Board size'!B11", fmt="0")
put(wf, f"A{r0 + 5}", "BACK VERDICT", bold=True); put(wf, f"B{r0 + 5}", f'=IF(B{r0 + 3}<=B{r0 + 4},"fits ("&TEXT(B{r0 + 3}/B{r0 + 4},"0%")&" full)","DOES NOT FIT: "&TEXT(B{r0 + 3}/B{r0 + 4},"0%")&" of the space")', fill=FILL_OUT)
put(wf, f"A{r0 + 7}", ("The MCU body (7x7 mm TQFP-48) plus its courtyard (10.4 mm square) is the biggest single block. The top and bottom pockets are the only ones wide enough for it; "
                        "left/right pockets are narrow slivers that suit buttons, the crystal and small passives."), F_NOTE, wrap=True)
wf.merge_cells(f"A{r0 + 7}:G{r0 + 7}"); wf.row_dimensions[r0 + 7].height = 40

# ---------------------------------------------------------------- Links tab: every hyperlink as plain, copyable text (the in-app preview cannot click links)
wlk = wb.create_sheet("Links")
put(wlk, "A1", "Every link in this workbook as plain text (copy and paste into a browser if the clickable links do not work in your viewer)", F_TITLE)
head(wlk, 3, ["Tab", "Cell", "Label", "Full URL"])
r_ = 4
for sh in wb.worksheets:
    if sh.title == "Links":
        continue
    for row in sh.iter_rows():
        for c in row:
            if c.hyperlink and c.hyperlink.target:
                put(wlk, f"A{r_}", sh.title); put(wlk, f"B{r_}", c.coordinate); put(wlk, f"C{r_}", str(c.value)); put(wlk, f"D{r_}", c.hyperlink.target)
                r_ += 1
wlk.column_dimensions["A"].width = 16; wlk.column_dimensions["B"].width = 8; wlk.column_dimensions["C"].width = 30; wlk.column_dimensions["D"].width = 120
wlk.freeze_panes = "A4"

# ---------------------------------------------------------------- Battery options tab (round 3)
wo = wb.create_sheet("Battery options")
put(wo, "A1", "Battery options, connections and retention (what we buy and install ourselves: JLCPCB does not sell LiPo cells)", F_TITLE)
put(wo, "A2", "Sources: Mouser/Conrad/Renata datasheets (VERIFIED where marked); hobby-shop listings found by web search 2026-10-09 (UNVERIFIED: sizes, stock and prices change and listings disagree). 'Smallest board' = result of plan_board.py with the medium (KXOB25) / 15 mm (AM-1606C) cell, VQFN MCU, 0.5 mm edge safety, cells soldered to pads.", F_NOTE, wrap=True)
wo.merge_cells("A2:L2"); wo.row_dimensions[2].height = 40
head(wo, 4, ["Option", "Cells", "Capacity total (mAh)", "Size each L x W x T (mm)", "Protected?", "Termination", "Price (USD each)", "Stock / source", "Smallest board, KXOB25 (MCU front / MCU back OK)", "Smallest board, AM-1606C (MCU front / MCU back OK)", "How well verified", "Shortcomings"])
wo.row_dimensions[4].height = 58
rows_b = [
 ("Renata ICP501022UPM", 1, 80, "24 x 10 x 5.5", "Yes", "Wire leads AWG30", 12.22, "Mouser 3 in stock", "36 mm", "40.5 mm (older run, TQFP MCU)", "Datasheet + Mouser page VERIFIED", "Thickest (5.5 mm); 3 in stock; single cell sits in the middle (rocking point)."),
 ("Renata ICP331319PM x2", 2, 100, "21 x 12.8 x 3.7", "Yes (each)", "Wire leads AWG30", 12.21, "Mouser 0 (factory order)", "37 / 37 mm", "43 / 42 mm", "Datasheet + Mouser VERIFIED", "Not stocked; about $24 for two; two cells to match and solder."),
 ("Renata ICP341018PM x2", 2, 70, "19.5 x 10.2 x 3.7", "Yes (each)", "Wire leads AWG30", 13.87, "Mouser 0 (factory order); Conrad ~EUR 14", "37 mm", "n/a", "Datasheet + Mouser VERIFIED", "Least energy; priciest per mAh."),
 ("Generic LP401230 x2", 2, 200, "30 x 12 x 4 (listing: 100-110 mAh each)", "Varies by seller", "Wires or JST-PH", None, "BerryBase / eBay DE (no US shipping on one listing)", "42 / 42 mm", "46 / 46 mm", "UNVERIFIED: capacity listings disagree", "Long cells need a wider board; two of them need 42 mm+; quality varies."),
 ("Generic LP401230 x1", 1, 100, "30 x 12 x 4", "Varies by seller", "Wires or JST-PH", None, "as above", "37 / 36 mm", "43 / 42 mm", "UNVERIFIED", "Single cell back in the middle."),
 ("Generic LP402025 (e.g. Adafruit 1317 150 mAh)", 1, 150, "27 x 20 x 4 (UNVERIFIED)", "Yes", "JST-PH plug (cut off or use)", 5.95, "Adafruit; one distributor shows stock conflicts", "37 / 37 mm", "43 / 42 mm", "UNVERIFIED (search snippets)", "Single big cell in the middle (rocking); two do not fit under 48 mm."),
 ("Adafruit 100 mAh (1570) / SparkFun 110 mAh (PRT-13853)", 1, 100, "about 30 x 12 x 4 (UNVERIFIED)", "Yes", "JST-PH plug", "11.60 / 7.53", "Marked retired or backorder by some sellers", "n/a", "n/a", "UNVERIFIED", "Stock unclear."),
 ("LIR2032 coin", 1, 40, "20 dia x 3.2", "NO", "Holder or solder tabs", None, "Many sellers (EEMB, RS, Loopacell...)", "about 40 mm", "about 44 mm", "Size/voltage VERIFIED in 3 datasheets; no protection found", "Half the energy; needs a protection part; holder adds bulk."),
 ("TinyCircuits 70 mAh (ASR00011)", 2, 140, "15 x 15 x 5 (+/-3, +/-2, +/-0.5)", "Yes", "JST SHR-02V-S-B plug, 25 mm wires (matches our header)", "n/a (not fetched)", "TinyCircuits shop; Mouser carries other TinyCircuits cells", "46 mm (strict)", "46 mm (strict)", "Size from a search summary; plug VERIFIED on the 150 mAh page", "Fat (5 mm); two of them are only 140 mAh."),
 ("TinyCircuits 150 mAh (ASR00003)", 1, 150, "20 x 20 x 5 (+/-3, +/-2, +/-0.5)", "Yes", "JST SHR-02V-S-B plug, 25 mm wires", 4.95, "TinyCircuits shop; Mouser datasheet exists", "single cell: fits", "single cell: fits", "TinyCircuits page VERIFIED (size, plug, price, protection, certs)", "Square 5 mm cell in the middle again; two do not fit under 48 mm."),
 ("Generic LP301030 x2 (3.0 x 10 x 30)", 2, 140, "30.5 x 10.2 x 3.2", "PCM included on some listings", "Wires (a seller can fit JST-SH to order: UNVERIFIED)", "about 2-3 (listings)", "Amazon, eBay, Alibaba makers", "45 mm (strict)", "45 mm (strict)", "UNVERIFIED: capacity 60-100 mAh depending on seller; no manufacturer datasheet found", "Thinnest option (3.2 mm); capacity and PCM vary by listing."),
 ("Generic LP401030 x2 (4.0 x 10 x 30)", 2, 180, "30 x 10 x 4", "Yes (PCM)", "Wires", "n/a", "LiPol and many makers", "44 mm (strict)", "44 mm (strict)", "LiPol datasheet exists (90 mAh, charge <= 45 mA); stock not checked", "Slow charge limit (45 mA)."),
 ("Electrokit 220 mAh with JST-SH", 1, 220, "36.5 x 21 x 4.5", "Yes", "150 mm AWG24 cable + JST-SH plug", None, "Electrokit (EU/Nordics only)", "does not fit", "does not fit", "UNVERIFIED", "Too big for the back."),
]
for i, r in enumerate(rows_b):
    rr = 5 + i
    for j, v in enumerate(r):
        c = put(wo, f"{'ABCDEFGHIJKL'[j]}{rr}", v if v is not None else "n/a", wrap=True, fmt="$0.00" if j == 6 and isinstance(v, float) else None)
    wo.row_dimensions[rr].height = 62
CS = 5 + len(rows_b) + 1
section(wo, CS, "Connections (what joins the cell to the board)", 12)
head(wo, CS + 1, ["Option", "Part", "JLCPCB assembles it?", "Colour", "Size", "Pros", "Cons", "Verified?"])
conn = [
 ("JST-SH header (1 mm), our current choice", "SM02B-SRSS-TB(LF)(SN), JLCPCB C160402; mating plug JST SHR-02V-S-B", "YES: 27,798 in stock. (Use C160402; the plain listing C18337480 has 0 stock.)", "Not verified: check the JST drawing for the housing colour", "tiny, about 3 mm tall", "Smallest plug-in; assembler places it; TinyCircuits cells and Electrokit cells already ship with this plug; hand-swap with no soldering iron.", "Most hobby cells ship with PH plugs; generic sellers may fit SH to order (UNVERIFIED). Opening direction on the boards is unverified against the JST drawing.", "JLCPCB stock VERIFIED"),
 ("Screw or spring wire terminal (for swapping cells with no iron)", "Phoenix PTSM / 1771091 (2.5 mm pitch, SMD spring-cage, screwless); smallest screw terminals are 2.54 mm pitch", "yes (SMD) but height NOT verified", "typically black/green (UNVERIFIED)", "likely 6+ mm tall", "Tool-free swap of bare wires.", "Much bigger than the 3-4 mm JST-SH; needs bare wire ends; heavy for a watch.", "UNVERIFIED (datasheet blocked)"),
 ("Solder the cell wires to pads", "no part (2 small pads per cell, drawn on the boards)", "pads yes; wires are a manual step", "n/a", "flat", "Most elegant and thinnest; no plastic at all; no PH/SH mismatch.", "Hand soldering near a cell; needs strain relief (tape/foam).", "reasoning"),
 ("JST-PH header (2 mm)", "B2B-PH-SM4 family (not checked)", "likely yes (not checked)", "typically white/natural (UNVERIFIED); black variants exist (UNVERIFIED)", "about 6 mm tall", "Matches most hobby cells with no cutting.", "Bigger, taller, white by default.", "UNVERIFIED"),
]
for i, r in enumerate(conn):
    rr = CS + 2 + i
    for j, v in enumerate(r):
        put(wo, f"{'ABCDEFGH'[j]}{rr}", v, wrap=True)
    wo.row_dimensions[rr].height = 70
HS = CS + 2 + len(conn) + 1
section(wo, HS, "Holding the cells down", 12)
head(wo, HS + 1, ["Option", "How", "Interferes with the LED band / front parts?", "Verdict"])
hold = [
 ("Foam tape under each cell + polyimide (Kapton) tape over it", "Tape bridges onto bare board next to the cell (yellow dashed zone on the diagrams).", "No: nothing goes through the board.", "USE for prototypes."),
 ("Zip ties through board slots", "A tie needs a slot on each side of the cell; the outer slot would sit under the LED band.", "YES: slots land where the LEDs and their traces are.", "AVOID."),
 ("Thin metal shield over each cell (or both)", "Custom folded 0.2-0.3 mm stainless sheet or a standard soldered shield frame/lid, soldered to ground pads or glued; leaves a small gap over the cell (foam).", "No if its pads sit on the dashed zone.", "GOOD later; no specific product verified yet."),
 ("Case with a 1 mm bumper", "Wrap-under case; strap through the board slots.", "No.", "LATER (not for first prototypes)."),
]
for i, r in enumerate(hold):
    rr = HS + 2 + i
    for j, v in enumerate(r):
        put(wo, f"{'ABCD'[j]}{rr}", v, wrap=True)
    wo.row_dimensions[rr].height = 62
wo.column_dimensions["A"].width = 38
for col, w in zip("BCDEFGHIJKL", (10, 12, 22, 12, 22, 14, 30, 26, 26, 24, 40)):
    wo.column_dimensions[col].width = w
wb._sheets = [wb[n] for n in ["Inputs", "LEDs", "Sensors", "MCUs", "Batteries", "Battery options", "Solar", "Parts", "Board size", "Layout fit", "Wear and stack", "Shortcomings", "Power budget", "Every LED", "LED types", "Lists", "Notes", "Links"]]
