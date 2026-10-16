# JLCPCB / LCSC in-stock alternatives for the LED Watch (RGB version)

Research date: 2026-10-05. Web/API research only; no KiCad files edited, no JLCPCB account/order/Chrome touched.

**How stock was checked.** JLCPCB's public parts-search endpoint (`jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`) and LCSC's product-detail endpoint (`wmsc.lcsc.com/ftps/wm/product/detail?productCode=Cxxxx`), queried with curl. Counts fluctuate hourly; JLC and LCSC sometimes differ by a few percent. "Library" = JLCPCB assembly library type (Basic = no extra feeder fee, Extended = per-part fee). Prices are USD at qty 1 (JLC API). Datasheets are the PDFs LCSC links for that C-number, plus Microchip/Atmel docs; pin text was extracted with Ghostscript `txtwrite` (and the LED land-pattern pages were read visually).

Tags: **VERIFIED** = read in the exact manufacturer datasheet (doc no. + section/page given). **UNVERIFIED** = not confirmed from a datasheet or not confirmable.

---------------------------------------------------------------------------------------------------

## 1. MCU: ATmega165PA-MU (QFN-64) replacement

### 1a. Key finding
Every ATmega165/325/645 -MU/-MUR/-MN variant on JLCPCB is **0 stock** (all 11 x 165, 10 x 325, 8 x 645 QFN-64 entries checked, incl. ATMEGA325PA-MUR C2055491, ATMEGA645P-MU C1337683, ATMEGA325A-MU C1339260, ATMEGA645A-MU C1342317). Those parts show `isPreSale=True` (JLC pre-order flag); what pre-sale lead time means for assembly was NOT checked (UNVERIFIED).

The only in-stock 64-pad 9x9 QFN parts in the same family are the **LCD siblings: ATmega169PA / 329PA / 649A**. They share the 165's 64M1 package and (verified below) the same pin on every pad, with one difference: pad 1 is `DNC` on the 165 family and `LCDCAP` on the 169 family.

### 1b. In-stock candidates

| MPN | LCSC / JLC C# | Stock (JLC / LCSC) | Unit price (qty 1) | Library | Flash / SRAM / EEPROM | Speed / Vcc | Footprint |
|---|---|---|---|---|---|---|---|
| **ATMEGA169PA-MU** | **C1339313** | 5 / 5 | $8.44 JLC ($8.18 LCSC) | Extended | 16 KB / 1 KB / 512 B (same as 165PA) | 16 MHz @ 1.8-5.5 V | QFN-64-EP 9x9, 0.5 mm, EP |
| ATMEGA329PA-MUR | C2053918 | 5 / 5 | $9.31 JLC ($9.02 LCSC) | Extended | 32 KB / 2 KB / 1 KB | 20 MHz @ 1.8-5.5 V | QFN-64 9x9 (JLC label "QFN-64(9x9)") |
| ATMEGA649A-MU | C1340148 | 10 / 10 | $10.90 JLC ($11.03 LCSC) | Extended | 64 KB / 4 KB / 2 KB | 16 MHz @ 1.8-5.5 V | QFN-64-EP 9x9 |

Source pages: https://jlcpcb.com/partdetail/C1339313 , https://jlcpcb.com/partdetail/C2053918 , https://jlcpcb.com/partdetail/C1340148 (the HTML pages did not show stock in a fetch; the stock numbers come from the two JSON endpoints above).

**Quantity caution:** stock is tiny (5 / 5 / 10). The earlier assembly attempt was "5 boards", i.e. 5 MCUs: ATmega169PA-MU is exactly enough, 649A-MU has 10. Re-check right before ordering. All other 169-family QFN entries (169A-MU C1339706, 169PA-MUR C1338947, 169P-16MU C1339770, 329A-MUR, 329P-20MU, 649P-MU C1342493 ...) are 0 stock. Do NOT use the `-MCH` / `-MCHR` entries (e.g. ATMEGA169PA-MCH C1340586): that is the 7x7 mm DRQFN (64MC) package, a different footprint.

Also seen in stock but NOT pin-compatible (different pinout; not datasheet-checked, listed only so nobody picks them by mistake): ATmega64A-MUR C2053133 (5), ATmega64L-8MU C1340114 (10).

### 1c. Pin-by-pin comparison vs ATmega165PA — VERIFIED
Compared the two pinout figures:
- 165 family: Atmel doc **8285FS (08/2014)** "ATmega165A/PA/325A/PA/3250A/PA/645A/P/6450A/P datasheet summary", **Section 1.1, Figure 1-1 "64A (TQFP) and 64M1 (QFN/MLF) pinout"** (p.3). Covers 165A/165PA/325A/325PA/645A/645P.
- 169 family: Atmel doc **8284FS (07/2014)** "ATmega169A/PA/329A/PA/3290A/PA/649A/P/6490A/P datasheet summary", **Section 1.1, Figure 1-1** (p.3). Covers 169A/169PA/329A/329PA/649A/649P.
(Both PDFs are the ones LCSC links for these C-numbers: C2053871 -> 8285FS, C1339313/C2053918/C1340148 -> 8284FS.)

| Pad | ATmega165PA (8285 Fig 1-1) | ATmega169PA / 329PA / 649A (8284 Fig 1-1) | Same? |
|---|---|---|---|
| **1** | **DNC** | **LCDCAP** | **DIFFERENT** (see note) |
| 2-9 | PE0..PE7 (RXD, TXD, XCK/AIN0, AIN1, USCK/SCL, DI/SDA, DO, CLKO) | identical names | yes |
| 10-16 | PB0..PB6 | identical | yes |
| 17 | PB7 (OC2A) | identical | yes |
| 18-19 | PG3 (T1), PG4 (T0) | identical (also SEG24/SEG23 alt functions) | yes |
| 20 | RESET/PG5 | identical | yes |
| 21,22 | VCC, GND | identical | yes |
| 23,24 | XTAL2 (TOSC2), XTAL1 (TOSC1) | identical | yes |
| 25-32 | PD0..PD7 | identical (+SEG21..SEG15 alt) | yes |
| 33-34 | PG0, PG1 | identical (+SEG14/13) | yes |
| 35-42 | PC0..PC7 | identical (+SEG12..5) | yes |
| 43 | PG2 | identical (+SEG4) | yes |
| 44-48 | PA7..PA3 | identical (+SEG3..0, COM3) | yes |
| 49-51 | PA2, PA1, PA0 | identical (+COM2..0) | yes |
| 52,53 | VCC, GND | identical | yes |
| 54-61 | PF7..PF0 (ADC7..0, JTAG TDI/TDO/TMS/TCK on PF7-PF4) | identical | yes |
| 62 | AREF | identical | yes |
| 63 | GND | identical | yes |
| 64 | AVCC | identical | yes |
| EP | exposed pad = GND (note under Fig 1-1) | identical note | yes |

Package drawing: both datasheets carry **"64M1, 64-pad, 9 x 9 x 1.0 mm body, lead pitch 0.50 mm, QFN/MLF", drawing no. 64M1, rev H** — same package outline (VERIFIED by title block text; I did not compare the exposed-pad dimensions numerically).

**Note on pad 1:** 165-family pad 1 = DNC (do not connect). 169-family pad 1 = LCDCAP, which per 8284FS Section 2.3.17 needs an external capacitor (> 470 nF) **only if the LCD module is enabled with internal power**. With the LCD controller left disabled, leaving pad 1 unconnected is fine. (That the LCD is disabled out of reset is standard AVR behaviour but I did not find the reset-value table in the datasheet *summary* PDF — UNVERIFIED in that document; it is in the full 169 datasheet.) The existing board netlist (`fab-rfq/netlist.xml`, U135 pin 1) has pad 1 as `unconnected`, so existing traces stay valid.

**Other differences that matter (firmware/programming, not copper):**
- 169-family has an LCD controller; its COM/SEG functions are alternate functions on the same pins and are off unless enabled. Register map adds LCD registers (0xE5-0xE6 etc.; 8284 register summary) — 165 firmware needs recompiling for the new target (`-mmcu=atmega169pa` / `atmega329pa` / `atmega649`), and fuse/flash tools must select the new device.
- Device signature bytes differ between devices and between A/P/PA variants (8284FS and 8285FS revision-history notes both say "A, P, and PA devices have different signature (0x002) bytes"). Programmer config must match the chip actually fitted. Exact signature values were not extracted (UNVERIFIED here).
- Flash/RAM/EEPROM per table above. 169PA is a spec twin of 165PA (16K/1K/512B, 16 MHz, 1.8-5.5 V) — **best drop-in**. 329PA/649A just add memory (and 329PA is a 20 MHz grade).
- Speed/voltage grade: 165A/PA, 169A/PA, 649A/P: 0-16 MHz @ 1.8-5.5 V (8285FS and 8284FS feature lists).
- Temperature -40..85 C for all (the -MU suffix; -MN would be 105 C).

**Aside about the existing netlist (not asked, but relevant to drop-in):** in `netlist.xml`, U135 pin 64 (AVCC) and pin 62 (AREF) are `unconnected`. 8284FS/8285FS Section 2.3 say AVCC "should be externally connected to VCC, even if the ADC is not used". This is independent of which chip is chosen. (netlist.xml may be older than the .kicad_pcb; check.)

**Recommendation (MCU): ATmega169PA-MU, C1339313** (spec twin; stock only 5, price $8.44). Fallback: ATmega649A-MU C1340148 (stock 10, 64 KB). Verdict: pin-compatible on all 64 pads + EP, pad 1 DNC -> LCDCAP left unconnected.

---------------------------------------------------------------------------------------------------

## 2. RGB LED replacement for Harvatek B39D3RGB-F6C0001HOU1930 (C6509069, 0 stock)

### 2a. The Harvatek reference (VERIFIED: Harvatek datasheet "B39D3RGB-F6C0001HOU1930", v1.0 01/09/2020, p.9 "Package Outline Dimension and Recommended Soldering Pattern")
- Package 0.83 x 0.83 mm, height 0.65 mm (0.75 max at DigiKey); 4 pads; **common cathode**.
- Pad numbers (top view of the part): Pin4 top-left, Pin1 top-right, Pin3 bottom-left, Pin2 bottom-right.
- Functions: **Pin1 = common cathode, Pin2 = R, Pin3 = G, Pin4 = B** (polarity diagram, p.9).
- Terminals 0.315 x 0.315 mm with 0.20 mm gap (about 0.515 mm pitch); recommended land: 4 pads 0.30 x 0.30, 0.24 mm gap (0.54 mm pitch).
- Vf typ/max: R 1.9/2.4 V, G 2.5/3.1 V, B 2.5/3.1 V; Iv at test current R 5 mA / G,B 2 mA: R 26, G 37, B 7.5 mcd.

### 2b. Headline: nothing in stock at JLCPCB is common CATHODE at <= 1.2 mm
Scanned ~3,900 JLC "RGB LED" entries. All in-stock RGB LEDs with a body <= 1.2 mm are **common ANODE** (or have a built-in driver IC, e.g. SK6805-EC10, WS2812-type: not usable here). The smallest common-cathode in-stock parts are 1.6 x 1.5 / 1.6 x 1.6 mm (e.g. TOGIALED TJ-S1615CY6TGLCCSRGB-A5 C601684, 38,337 in stock, $0.095; CHONGTIAN CT-1615URGBC-P6-1 C52676035; Yongyu SZYY1615RGB-A C3029072) — these need a bigger footprint. The one 1.0 mm common-cathode part found, Kingbright APGF1012GBRC-07 (C6506237), is 0 stock.

So: **there is no in-stock same-polarity drop-in.** The closest are common-anode parts with the same pad positions. Using a common-anode part means the polarity of every LED is reversed relative to the Harvatek (see 2d).

### 2c. In-stock candidates, closest footprint first
All JLC library type = Extended. Stock = JLC API 2026-10-05.

| MPN | C# | Stock | $/pc (qty 1) | Body | Polarity | Vf (R / G / B) | Pad map vs Harvatek |
|---|---|---|---|---|---|---|---|
| **Meihua MHPA0808RGBDT** | **C404279** | 14,080 | 0.047 | 0.80 x 0.80 x 0.60 | Common ANODE | 1.7-2.3 / 2.5-3.5 / 2.5-3.5 V (max, at 5/3/3 mA) | **Same pad numbers & positions as Harvatek** (VERIFIED) |
| Nationstar NCD0808RGB1 | C2917192 | 7,007 | 0.060 | 0.80 x 0.80 x 0.65 | Common ANODE | 1.9 typ / 2.5 / 2.6 V (JLC attrs) | Same physical positions (VERIFIED, no pad numbers) |
| Meihua MHPA0606RGBDT | C404278 | 39,973 | 0.060 | 0.69 x 0.69 x 0.48 | Common ANODE | 1.7-2.3 / 2.5-3.5 / 2.5-3.5 V | Same pin numbers, but part must be rotated 180 deg (VERIFIED) |
| Nationstar FC-B1010RGBT-HG | C158099 | 53,848 | 0.027 | 1.0 x 1.0 x 0.85 | Common ANODE | R 1.6-2.4 ... | bigger footprint |
| (other 1010s: Xinglight XL-B1010RGBT-HF C22464515 162,530; NH-B1010RGBT-HF C2874113 220,700; Meihua MHPA1010RGBDT C404280; all common anode, 1.0 mm) | | | | | | | need ~1.0 mm footprint |

#### MHPA0808RGBDT (C404279) — best match. Datasheet: Meihua/LYGMH LPDS-0002507 Rev.3 (2018/04/30), p.2 package dimensions
- Body 0.80 x 0.80 mm, 0.60 mm high (vs 0.83 x 0.83 x 0.65).
- Pad numbering viewed from the top: **4 top-left, 1 top-right, 3 bottom-left, 2 bottom-right** = exactly the Harvatek pattern (Pin4 TL, Pin1 TR, Pin3 BL, Pin2 BR).
- Functions: **Pin1 = common (anode "+"), Pin2 = RED, Pin3 = GREEN, Pin4 = BLUE** (polarity diagram) — identical to Harvatek's Pin1/R/G/B order except pin 1 is anode, not cathode.
- Terminals 0.30 x 0.30 mm, 0.20 mm gap -> **0.50 mm pitch**; recommended land 0.90 x 0.90 overall (pads about 0.35 x 0.35 with 0.20 gap). That is essentially the pitch/pad size the existing Harvatek land pattern already has (0.3 pads on 0.5 pitch) — I could not compare against the actual KiCad footprint (not opened), so treat "fits existing footprint" as UNVERIFIED until compared.
- Abs max: 20 mA continuous per colour, 2 kV / 1 kV / 1 kV HBM. Test conditions R 5 mA, G 3 mA, B 3 mA (comparable to Harvatek's 5/2/2). Luminous intensity from JLC attrs: R 16.5-27.8, G 27.7-46.8, B 7.5-12.6 mcd (Harvatek typ 26/37/7.5) — similar brightness. Black diffused lens (Harvatek: anti-reflection resin).
- Vf is allowed up to 3.5 V (G/B) vs Harvatek max 3.1 V: check headroom at the lowest supply voltage (design drives from a 3-4.2 V source per OPEN-ISSUES.md).

#### NCD0808RGB1 (C2917192). Datasheet: Foshan Nationstar spec NCD0808RGB1 version A, 2021-11-01, p.1/7
- 0.8 x 0.8 x 0.65 mm. Package pads 0.28 x 0.28, 0.24 gap (about 0.52 mm pitch); recommended land 0.4 x 0.4 pads with 0.2 gap (0.6 pitch; bigger than the existing 0.3 pads).
- Top view: B top-left, "+" (anode) top-right, G bottom-left, R bottom-right -> same positions as Harvatek (TL=B, TR=common, BL=G, BR=R). **Common anode.** No pad numbers printed.
- Vf typ: R 1.9 V, G 2.6 V, B 2.5 V (JLC attributes; test current 2 mA). Datasheet shows tiny test currents — brightness at your drive current not verified.

#### MHPA0606RGBDT (C404278). Datasheet: Meihua LPDS-0002503 V2 (2023/12/26), p.2
- 0.69 x 0.69 x 0.48 mm; pads 0.25 mm with 0.22 gap (0.47 pitch); land 0.25 pads, 0.85 x 0.85 overall.
- Top-view pad numbers: 2 TL, 3 TR, 1 BL, 4 BR; **1 = common anode, 2 = R, 3 = G, 4 = B**. Rotating the part 180 deg (CPL rotation +180 vs the Harvatek) puts 1 at TR, 2 at BR, 3 at BL, 4 at TL — i.e. the Harvatek pad->function map (VERIFIED by geometry). Smaller than the 0.83 package, so solder fillets will differ; probably fits the 0.3 mm pads (UNVERIFIED).

### 2d. What the common-anode swap implies (design consequence, UNVERIFIED against the schematic)
The Harvatek is common-cathode: R/G/B anodes are driven high, the common pad sits on the low side. A common-anode LED reverses current direction, so on the same board nets the LED would be reverse-biased (no light, ~10 V reverse rating though). It can only work if the board lets the MCU invert drive (common pad driven HIGH, colour pads driven LOW/sunk), which in a multiplexed matrix driven directly from MCU pins is a firmware polarity inversion only if the matrix wiring is symmetric. This needs a schematic check by Evan; I did not analyse the 132-LED matrix connectivity. If the topology can't be inverted, the only options are (a) a common-cathode 1.6 x 1.5 mm part with a new footprint (C601684 etc.), or (b) buy the Harvatek from DigiKey (20,772 in stock per OPEN-ISSUES.md) and consign it ("By Customer").

**Recommendation (LED):** best footprint/pin match = **Meihua MHPA0808RGBDT, C404279** (14,080 in stock, $0.047): identical pad numbering/positions/0.5 mm pitch, **but common ANODE**. Dealbreaker unless the matrix can run reversed. No in-stock common-cathode part at <= 1.2 mm exists at JLC today.

---------------------------------------------------------------------------------------------------

## 3. IMU: BMI270 and 14-pin LGA 2.5 x 3.0 alternatives

### 3a. BMI270 is in stock at JLC
| MPN | C# | Stock (JLC / LCSC) | $/pc | Library |
|---|---|---|---|---|
| **BMI270** (Bosch Sensortec) | **C2836813** | 8,007 / 7,328 | 2.63 JLC (2.66 LCSC) | Extended |
Page: https://jlcpcb.com/partdetail/C2836813 . Datasheet used: Bosch BST-BMI270-DS000-05, Rev 1.3 (11/2020), Section 7 "Pinout and Connection Diagram", Table 22 (pp.145-147). Package 2.5 x 3.0 x 0.83 mm, 14-LGA (datasheet feature list).

The project schematic currently uses **BMI160** (C94021, 0 stock at JLC/LCSC). VERIFIED identical pin list for BMI160 / BMI260 / BMI270 / BMI323 (the same-pinout Bosch family):
- BMI160: BST-BMI160-DS000-07 Rev 0.8 (02/2015), Table 30 "Pin-out and pin connections": 1 SDO, 2 ASDx, 3 ASCx, 4 INT1, 5 VDDIO, 6 GNDIO, 7 GND, 8 VDD, 9 INT2, 10 OCSB, 11 OSDO, 12 CSB, 13 SCx, 14 SDx — identical to BMI270 Table 22.
- BMI260: BST-BMI260-DS000-07 Rev 1.7 (03/2023), Table 32 — identical to BMI270.
- BMI323: Bosch flyer BST-BMI323-FL000-00 v1.0 (09/2022), pin table + note "BMI323 is pin to pin compatible to BMI160 and BMI270". Pins 2, 3, 10, 11 are "NC / Do not connect" (instead of ASDx/ASCx/OCSB/OSDO), so do not tie them to VDDIO/GND.

**Firmware warning (VERIFIED):** BMI270 datasheet (Section on initialization, around "Burst write 8 kB initialization data to Register INIT_DATA") requires an **8 kB config blob written at every power-up** before the sensor works. The BMI160 needs no blob. The ATmega165PA has only 16 KB flash / 1 KB SRAM (and the 169PA is the same), so the blob would eat half the flash (the blob can be streamed in chunks from flash; datasheet allows writing in smaller chunks). BMI160 -> BMI270 is pin-compatible but NOT driver-compatible. (BMI260 has the same style of config file; BMI323 not checked for it.)

### 3b. In-stock 14-pin LGA 2.5 x 3.0 alternatives
All library = Extended. Stock = JLC API (LCSC within a few %).

| MPN | C# | Stock | $/pc | Maker | Notes |
|---|---|---|---|---|---|
| BMI260 | C7544197 | 23,682 | 1.90 | Bosch | pin-identical to BMI270 |
| BMI323 | C5368700 | 3,299 | 3.23 | Bosch | pin-identical (NC on 2,3,10,11) |
| BMI320 / BMI325 | C22391148 / C41398783 | 3,473 / 5,051 | 1.10 / 2.28 | Bosch | pinout NOT checked (UNVERIFIED) |
| LSM6DS3TR-C | C967633 | 26,825 | 1.52 | ST | pin map below |
| LSM6DSL (TR) | C126672 | 9,833 | 2.59 | ST | pinout not read (same family, UNVERIFIED) |
| LSM6DSO (TR) | C2655100 | 5,011 | 3.88 | ST | pin map below |
| LSM6DSOX (TR) | C481766 | 3,978 | 3.87 | ST | same pinout as DSO family (UNVERIFIED for DSOX specifically) |
| LSM6DSR (TR) | C784817 | 6,651 | 3.05 | ST | pin map below |
| ICM-42688-P (TDK) | C1850418 | 4,662 (LCSC 3,794) | 19.44 | TDK | pin map below; expensive. Tokmas "ICM-42688-P(TOKMAS)" C54308212 (4,206, $3.21) is a third-party part, NOT TDK; datasheet not checked (UNVERIFIED) |
| ICM-42607-P | C5129967 | 10,310 | 2.15 | TDK | pin map below |
| ICM-42670-P | C3288646 | 6,692 | 2.28 | TDK | not checked (UNVERIFIED) |
| QMI8658A | C3021082 | 14,357 | 2.19 | QST | pin map below |
Not in stock now: BMI160 C94021 (0), BMX160 (0), ICM-42688-V (0), LSM6DSV-TR C5267399 (0).

### 3c. Pin mapping vs BMI270 (Bosch pin list from Table 22, BMI270 DS rev 1.3)
Legend: **=** electrically same function; **OK** = different name but works with the same BMI wiring; **!** = BMI-valid wiring that is NOT allowed on the alternative (needs rewiring).

| Pin | BMI270 | LSM6DS3TR-C (DocID030071 Rev 3, Sect 3 Table 2, p.20) | LSM6DSO (DS12140 Rev 2, Table 1) / LSM6DSR (DocID030186 Rev 1, Table 2, p.25) | ICM-42688-P (DS-000347 Rev 1.2, Sect 4.1 Table 9, p.18-19) | ICM-42607-P (DS-000417 Rev 1.2, p.17) | QMI8658A (13-52-25 Rev A, Table 3, p.8-9) |
|---|---|---|---|---|---|---|
| 1 | SDO | SDO/SA0 = | SDO/SA0 = | AP_SDO/AP_AD0 = | AP_SDO/AP_AD0 = | SDO/SA0 = |
| 2 | ASDx (VDDIO or DNC) | SDx: "Connect to VDDIO or GND" (**!** if left floating; ties to VDDIO OK) | SDx: connect to VDDIO or GND (**!** if floating) | RESV: NC or GND (**!** must NOT go to VDDIO) | RESV: NC / GND / VDDIO OK | SDx: VDDIO, GND or NC OK |
| 3 | ASCx (VDDIO or DNC) | SCx: connect to VDDIO or GND (**!** if floating) | SCx: same (**!** if floating) | RESV: NC or GND (**!** not VDDIO) | RESV: NC/GND/VDDIO OK | SCx: VDDIO/GND/NC OK |
| 4 | INT1 | INT1 = | INT1 = | INT1/INT = | INT1/INT = | INT1 = |
| 5 | VDDIO | VDDIO = | VDDIO = | VDDIO = | VDDIO = | VDDIO = |
| 6 | GNDIO | GND = | GND = | GND = | GND = | GND = |
| 7 | GND | GND = | GND = | RESV: connect to GND = | FSYNC: connect to GND if unused = | GND = |
| 8 | VDD | VDD = | VDD = | VDD = | VDD = | VDD = |
| 9 | INT2 | INT2 = | INT2 = | INT2/FSYNC/CLKIN (if INT2 unused, datasheet says tie to GND for FSYNC; **!** if left floating) | INT2 = | INT2 = |
| 10 | OCSB (DNC, or GND if OIS off) | NC "leave unconnected" (**!** if tied to GND) | OCS_Aux: leave unconnected (**!** if GND) | RESV: NC or GND OK | RESV: NC/GND/VDDIO OK | RESV: VDDIO or NC; **!** must NOT go to GND |
| 11 | OSDO (DNC, or GND if OIS off) | NC "leave unconnected" (**!** if GND) | SDO_Aux: VDDIO or NC (**!** if GND) | RESV: NC or GND OK | RESV: NC/GND/VDDIO OK | RESV-NC: output, leave floating (**!** don't drive/tie unless pin 10 -> VDDIO) |
| 12 | CSB (VDDIO for I2C) | CS = | CS = | AP_CS = (VDDIO for I2C/I3C) | AP_CS = | CS = (1 = I2C) |
| 13 | SCx (SCL/SCK) | SCL/SPC = | SCL/SPC = | AP_SCL/AP_SCLK = | AP_SCL/AP_SCLK = | SCL = |
| 14 | SDx (SDA/SDI) | SDA/SDI = | SDA/SDI = | AP_SDA/SDIO/SDI = | AP_SDA/SDIO/SDI = | SDA = |

**Reading it:** all of these are mapped pin-for-pin on the 14 pads in the same order (1 SDO, 4 INT1, 5 VDDIO, 8 VDD, 9 INT2, 12 CS, 13 SCL, 14 SDA, and the grounds on 6/7). Pin function names for 2, 3, 10, 11 differ, and several alternatives restrict what those pads may be tied to. Footprint land pattern equivalence (pad size/EP-less LGA 0.5 mm pitch) was NOT compared numerically between vendors (UNVERIFIED); all are listed as 2.5 x 3.0 mm, 14 pads, 0.5 mm pitch class.

**Pin-compatibility verdict:**
- Drop-in (VERIFIED, same pads, same functions): **BMI270, BMI260, BMI323 (from BMI160)**. BMI323 pads 2/3/10/11 "do not connect".
- Pin-compatible with at most a small wiring check: **ICM-42607-P** (most tolerant; pads 2,3,10,11 accept NC/GND/VDDIO; pin 7 = FSYNC wants GND, same as BMI GND pad), **QMI8658A** (pad 10 must not be GND), **LSM6DS3TR-C / LSM6DSO / LSM6DSR** (pads 2,3 must be tied to VDDIO or GND, not floating; pads 10/11 must not be grounded).
- ICM-42688-P: pads 2,3 must not be VDDIO; pad 9 should be GND if INT2 isn't used.
- Address note: BMI I2C address 0x68/0x69 (SDO pin). ST SA0: 0x6A/0x6B. QMI8658A: SA0=0 -> 0x6B, 1 -> 0x6A. ICM-426xx: AD0-selected (0x68/0x69) — check datasheets. All need new drivers.

**Existing board (aside, from `fab-rfq/netlist.xml`, may be stale vs .kicad_pcb):** U134 VDDIO(5), GNDIO(6), CSB(12) and SDO(1) are `unconnected`; INT2/OCSB/OSDO/ASDx/ASCx unconnected. The BMI160 datasheet (Table 30 / sect. 4.2) wants VDDIO powered and CSB tied to VDDIO for I2C; this is a board issue regardless of which IMU is chosen. For the ST/TDK parts, unconnected pins 2/3 would be non-compliant as per the table above.

**Recommendation (IMU):** **BMI270 C2836813** (8,007 in stock, $2.63) is a true drop-in, but needs the 8 kB init blob on a 16 KB MCU. If code space matters: **BMI260 C7544197** (same family, $1.90, 23k) has the same blob; non-blob choices that are pin-compatible with ~no copper change are **ICM-42607-P C5129967** ($2.15) or **LSM6DS3TR-C C967633** ($1.52, 26k stock; tie pads 2/3 to VDDIO/GND).

---------------------------------------------------------------------------------------------------

## 4. White LEDs for the future single-colour design (in stock at JLCPCB)

| Size | MPN | C# | Library | Stock (JLC) | $/pc (qty 1) | Vf | Luminous intensity | Test I | Source |
|---|---|---|---|---|---|---|---|---|---|
| **0603** | **Hubei KENTO KT-0603W** | **C2290** | **Basic** | 2,164,000 (LCSC 1,558,850) | 0.0122 | 2.6-3.1 V (VERIFIED, DS) | 145-360 mcd (DS) | 5 mA | https://jlcpcb.com/partdetail/C2290 |
| 0603 | Nationstar NCD0603W1 | C84265 | Extended | 700,202 | 0.020 | 2.6-3.6 V (JLC attr) | 300 mcd (JLC attr) | 20 mA | https://jlcpcb.com/partdetail/C84265 |
| 0603 | Xinglight XL-1608UWC-04 | C965808 | Extended | 339,741 | 0.0048 | 2.7 V | 130 mcd | 20 mA (JLC attr) | https://jlcpcb.com/partdetail/C965808 |
| **0805** | **Hubei KENTO KT-0805W** | **C34499** | **Basic** | 514,810 (LCSC 372,050) | 0.0202 | 2.6-3.1 V (DS) | 145-360 mcd (DS; JLC attr says 350) | 5 mA | https://jlcpcb.com/partdetail/C34499 |
| 0805 | Xinglight XL-2012UWC | C965818 | Extended | 302,932 | 0.0121 | 3.3 V | 660 mcd | 20 mA | https://jlcpcb.com/partdetail/C965818 |
| 0805 | Nationstar NCD0805W1 | C110099 | Extended | 34,852 | 0.0376 | 2.6-3.6 V | 750 mcd | 20 mA | https://jlcpcb.com/partdetail/C110099 |
| **0402** | **Xinglight XL-1005UWC** | **C20613596** | Extended | 337,851 (LCSC 337,850) | 0.0113 | 2.6-3.3 V (DS, 20 mA) | 350-1000 mcd (DS, 20 mA) | 20 mA | https://jlcpcb.com/partdetail/C20613596 |
| 0402 | Nationstar NCD0402W1 | C130725 | Extended | 15,669 | 0.0428 | 2.5/2.8/3.6 V min/typ/max (DS) | 60 / 100 / 180 mcd (DS) | 5 mA | https://jlcpcb.com/partdetail/C130725 |

- **Basic-library white LEDs exist for 0603 (C2290) and 0805 (C34499).** No Basic-library white 0402 LED turned up in the search (UNVERIFIED that none exists; the search is keyword-based) — the 0402 options above are Extended.
- Datasheets: KT-0603W / KT-0805W from LCSC PDFs (the extracted tables show identical values for both: Iv 145-360 mcd, Vf 2.6-3.1 V at 5 mA); XL-1005UWC and NCD0402W1 from LCSC PDFs. The C34499 JLC attribute "350 mcd @ 25 mA" conflicts with the datasheet (5 mA); trust the datasheet or measure.
- All white LEDs above are for a ~3 V supply with a series resistor; Vf up to ~3.1-3.6 V means a bare 3 V coin cell leaves little headroom for white.

---------------------------------------------------------------------------------------------------

## Summary table of picks

| Part | Pick | C# | Stock | Notes |
|---|---|---|---|---|
| MCU | ATmega169PA-MU | C1339313 | 5 | pin-for-pin with 165PA except pad 1 DNC -> LCDCAP (leave open); fallback ATmega649A-MU C1340148 (10) |
| RGB LED | MHPA0808RGBDT | C404279 | 14,080 | same pad numbering/positions/pitch as Harvatek, but common ANODE (polarity swap) |
| IMU | BMI270 | C2836813 | 8,007 | pin-identical to BMI160/BMI270 family; needs 8 kB init blob |
| White 0603 / 0805 | KT-0603W / KT-0805W | C2290 / C34499 | 2.1 M / 515 k | Basic |
| White 0402 | XL-1005UWC | C20613596 | 338 k | Extended |

## Sources
- JLCPCB parts search (JSON): https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList ; part pages https://jlcpcb.com/partdetail/<C#>
- LCSC product detail (JSON): https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=<C#>
- Atmel 8285FS (165/325/645): https://datasheet.lcsc.com/datasheet/pdf/af1d49a8d5cf00242f0566ee62873a0d.pdf?productCode=C2053871
- Atmel 8284FS (169/329/649): https://datasheet.lcsc.com/datasheet/pdf/46621f022f53df84e3c9acbbbf78b712.pdf?productCode=C1339313
- Harvatek B39D3RGB: https://cdn.components.ru/media/PDF/8019959.pdf (mirror of the DigiKey-linked datasheet)
- MHPA0808RGBDT: https://datasheet.lcsc.com/datasheet/pdf/1674e4a9e1dec82609abb7eb7f417a05.pdf?productCode=C404279 ; MHPA0606RGBDT: .../8062740a769b96b6cd9ee4e5a5a34ccc.pdf?productCode=C404278 ; NCD0808RGB1: .../acd0c889efc214f58d30c6b33310e894.pdf?productCode=C2917192
- BMI270: .../3a58504f6333c054470bbde99576876b.pdf?productCode=C2836813 ; BMI260: .../f9a2a5d18e4d5d2c585f223de1fb9cf9.pdf ; BMI323: .../ff79948038995216d66cbdb81c4944d1.pdf ; BMI160: .../f6ca2e3db627411a82c6c4b045622a0b.pdf
- LSM6DS3TR-C: .../176463bae17f4a667a4792d02c6297f0.pdf ; LSM6DSO: .../9b8183d12f183970849d8eecce406049.pdf ; LSM6DSR: .../9de199ce96f7ea5e7f92c28866be3be3.pdf ; ICM-42688-P: .../d5f9e170444ac167b391a8574fc574ca.pdf ; ICM-42607-P: .../34616b9eee2273d094e953ad8e62f71b.pdf ; QMI8658A: .../6d82261d3163ceec7c0a6ff46ab1f743.pdf (all under https://datasheet.lcsc.com/datasheet/pdf/)
- White LEDs: KT-0603W .../8238ae278d43fbd59fd57ef71ae67c27.pdf ; KT-0805W .../48953f05e6e6e0a517af2e319c9c297c.pdf ; NCD0402W1 .../e67d12309c54e877c904b98042342e9b.pdf ; XL-1005UWC .../85cfe3bba05d661319b34ccd12534d6b.pdf
