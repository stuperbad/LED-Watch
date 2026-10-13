# LED Watch - Solar / Harvesting / Battery Research

Prepared 2026-10-05. Scope: 37 mm round LED watch, ~132 white LEDs on the front, small LiPo soldered on the back, optional miniature solar cell in the centre of the front face (free circle 12-18 mm, or ~12 mm square).

**Tag legend**
- **VERIFIED** = number read by me from the manufacturer datasheet/catalog PDF (document + section named), or from the live LCSC product page fetched on 2026-10-05.
- **UNVERIFIED** = from a search-engine excerpt, a reseller page, a mirror, my own estimate, or not found. Never inferred from a sibling part number unless explicitly labelled "sibling, do not rely".
- Tool limits: DigiKey, Mouser, octopart and analog.com were not fetchable by my tools (403 / timeout). DigiKey/Mouser stock and prices below are therefore undated search-engine snapshots (UNVERIFIED). LCSC stock was read live (VERIFIED for 2026-10-05). JLCPCB's own parts search page was not usable (it returned "0 found" even for a part LCSC lists), so JLCPCB stock is **UNVERIFIED**; JLCPCB shares C-numbers with LCSC, but its assembly-library stock can differ.

---

## Headline findings (read this first)

1. **There is no off-the-shelf, datasheet-backed PV cell that is 10-18 mm square.** Closest purchasable parts: Panasonic AM-1606C (15x15 mm amorphous, indoor-only, ~9 uW at 200 lux) and Anysolar KXOB25 (22x7 / 23x8 mm monocrystalline strips, up to 30.7 mW at 1 sun). The KXOB strips do **not** fit a 12-18 mm circle (diagonal 23 mm). A true 12x12 c-Si or a-Si cell means a custom order (Anysolar, Panasonic and Epishine all state they customise) or cutting your own.
2. **Solar will not sustain the watch indoors.** At 300-500 lux a 12x12 mm cell yields roughly 0.03-0.2 mWh/day against a 3-14 mWh/day load: 1-12 % coverage at best. It is a trickle.
3. **Solar only matters if the wearer is outdoors in sun.** One hour of real sun on the wrist (c-Si, ~40 % of 1 sun) gives ~8 mWh on a 12x12 mm cell, which roughly covers one day of medium use. So solar can *extend* battery life for outdoor people, not make the watch autonomous.
4. **Display bursts dominate the load**, not the sleep current. 60 wake-ups/day of 10 LEDs x 2 mA x 3 s is ~3.7 mWh/day vs ~1.6 mWh/day of always-on electronics.
5. **TI's cold-start voltage is 600 mV (typ), not the old 330 mV** in many web articles (BQ25504/BQ25570 datasheet revision history VERIFIED). e-peas AEM10300 starts at 275 mV, AEM10941 at 380 mV. This matters a lot for single-cell silicon (0.5-0.7 V Voc).
6. **Strong light can exceed IC input ratings**: KXOB25-01X8F/02X8F have Voc 5.53 V at 1 sun, above the 5.5 V absolute maximum on the e-peas SRC pins and BQ25570 VIN_DC. Choose lower-Voc cells or clamp.
7. **Most PV is not reflow-friendly, but the KXOB25 SolarBIT is the exception**: its datasheet allows reflow only with low-temperature Sn42/Bi58 paste (220 C peak), MSL3. A standard JLCPCB lead-free profile (~245 C) is outside that. Treat all PV as post-assembly hand/adhesive-mounted.

---

## 1. Miniature photovoltaic cells

### 1a. Candidate table

Area figures: "gross" = L x W of the part. Densities are Pmax / gross area.

| # | Part (MPN) | Tech / appearance | Size (mm) | Test condition | Voc | Vmpp (Vope) | Impp (Iope) | Pmax | Bare / leads | Where to buy (price, stock) | Fits 12-18 mm circle? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Panasonic Amorton AM-1606C** (variants -DGK-E, -MEL) | a-Si on glass, indoor type | 15.0 x 15.0 x 0.7 (catalog) | 200 lx fluorescent, 25 C | 3.7 V | 2.6 V | 3.4 uA | ~8.8 uW (2.6 V x 3.4 uA, my calc) = 3.9 uW/cm2 | C-type terminal (conductive-paste pads, no lead). Catalog terminal table: C type allows lead wire to be attached with regular solder (my reading of extracted text; confirm) | DigiKey: 640 in stock on Panasonic stock-search page dated 2026-10-05 (VERIFIED as shown there). Mouser AM-1606C-MEL ~$2.64 @1 (search excerpt, UNVERIFIED) | **Yes (only real 15x15)** |
| 2 | Panasonic Amorton AM-1456 (AM-1456CA, DigiKey 869-1002-ND) | a-Si on glass, indoor | 25.0 x 10.0 x 1.1 | 200 lx fluorescent | 2.5 V | 1.5 V | 5.9 uA | ~8.9 uW = 3.5 uW/cm2 | CA = lead wires attached | DigiKey (listing seen in search, price/stock UNVERIFIED) | No (25 mm long) |
| 3 | Panasonic AM-1411 | a-Si indoor | 29.6 x 11.8 x 1.1 | 200 lx | 2.5 V | 1.5 V | 8.6 uA | ~12.9 uW | - | Catalog only (distributor not checked) | No |
| 4 | **Anysolar KXOB25-04X3F** (-TB/-TR) | Mono-Si SolarBIT, dark blue/grey | 22 x 7 x 1.8 | 1 sun (100 mW/cm2, AM1.5, 25 C) | 2.07 V | 1.67 V | 13.2 mA | 22.0 mW (Isc 14.0 mA) = 14.3 mW/cm2 | SMD body, no leads | LCSC C19077769 (live: **out of stock**, $4.72 @1, $1.79 @1000). DigiKey also lists -TB (stock UNVERIFIED) | No |
| 5 | **Anysolar KXOB25-05X3F** (-TB/-TR) | Mono-Si SolarBIT | 23 x 8 x 1.8 | 1 sun | 2.07 V | 1.67 V | 18.4 mA | 30.7 mW (Isc 19.5 mA) = 16.7 mW/cm2 | SMD | LCSC C5358484 (-TR, live: **out of stock**, $5.38 @1). DigiKey -TB ~$3.14 @1, 3,299 stock (excerpt, UNVERIFIED) | No |
| 6 | **Anysolar KXOB25-01X8F** | Mono-Si SolarBIT (8 cells in series) | 22 x 7 x 1.8 | 1 sun | **5.53 V** | 4.46 V | 5.5 mA | 24.5 mW = 15.9 mW/cm2 | SMD | DigiKey -TR ~$3.40, out of stock/backorder (excerpt, UNVERIFIED) | No |
| 7 | Anysolar KXOB25-02X8F | Mono-Si SolarBIT | 23 x 8 x 1.8 | 1 sun | **5.53 V** | 4.46 V | 5.9 mA | 26.3 mW | SMD | DigiKey -TB $3.40 @1, 325 stock (excerpt, UNVERIFIED) | No |
| 8 | Anysolar KXOB25-12X1F | Mono-Si SolarBIT (1 cell) | 22 x 7 x 1.8 | 1 sun | 0.69 V | 0.56 V | 43.9 mA | 24.5 mW | SMD | DigiKey -TB (listed); LCSC C21117290 reported by search but its page returned 404 (UNVERIFIED) | No |
| 9 | **Epishine LEH3 / MultiCell** (MC15-25x29-4, LEH3_50x20_6 ...) | Printed organic PV, flexible PET, 0.2 mm | smallest standard: 25 x 29 (7.3 cm2 aperture, 4 cells) | 500 lx warm-white LED | 2.59 V | 2.17 V | 57 uA | 124 uW (MC15-25x29-4) | Module with solder pads | epishine.com; Newark/Farnell stock distributor (search result). Price not found | No. Custom shape/size offered (VERIFIED, datasheet sec. 1) |
| 10 | PowerFilm LL200-3-37 | a-Si on PET, flexible, 0.22 mm | 114 x 36.5 | 200 lx / 1000 lx | Voc 2.9 V avg @200 lx | 2.1 V / 2.6 V | 79 uA / 419 uA | 0.166 mW / 1.089 mW (= 4.0 uW/cm2 @200 lx) | foil-tape contacts | powerfilmsolar.com page fetched | No (far too big) |

Sources/sections: AM-1606/1456/1411 - Panasonic "Amorphous Silicon Solar Cells, Amorphous Photosensors" catalog, Product List (glass substrate, indoor products). KXOB25-04X3F - Anysolar datasheet "KXOB25-04X3F" Rev. May 2025 (marked Preliminary), page 1 electrical table. KXOB25-05X3F - Anysolar datasheet Rev. Aug 2023, page 1. KXOB25-01X8F/02X8F - datasheets Rev. Jun 2026, page 1. KXOB25-12X1F - datasheet Rev. May 2025. Epishine - "Epishine MultiCell Data sheet v1.6.3", Tables 1-2. PowerFilm - product page.

### 1b. Indoor performance data actually available

| Source | Light | Density (per gross/cell area) | Tag |
|---|---|---|---|
| Panasonic AM-1606 (15 x 15 = 2.25 cm2) | 200 lx fluorescent | 3.9 uW/cm2 | VERIFIED (catalog) |
| Panasonic AM-1456 (2.5 cm2) | 200 lx fluorescent | 3.5 uW/cm2 | VERIFIED (catalog) |
| Epishine (cell-area basis) | 50 / 200 / 500 lx warm-white LED | mean 1.8 / 7.6 / 20.3 uW/cm2 (min-max 1.6-2.0 / 6.8-8.4 / 18.3-22.3) | VERIFIED (datasheet Table 2) |
| PowerFilm LL200-3-37 (41.6 cm2) | 200 / 1000 lx | 4.0 / 26 uW/cm2 | VERIFIED (page) |
| Anysolar KXOB25 mono-Si | any lux level | **not in datasheets** (only 1-sun data; text says indoor power may be ~100x lower than bright sun for incandescent/halogen, 200-500x lower for fluorescent, SM531K12L datasheet "Background") | indoor numbers UNVERIFIED; I assume 16-20 uW/cm2 at 400-500 lx |

Amorton states that an indoor-type cell should not be used where outdoor illumination is needed because output may not scale at high illuminance (catalog "Precautions", VERIFIED). So the AM-1606 is **not** a sun-harvesting part.

### 1c. Appearance / under-glass notes
- Mono-Si (Anysolar): "homogenous dark blue or dark grey" (Anysolar datasheet background, VERIFIED). Opaque, stable, UV-tolerant physically (UV claim UNVERIFIED - datasheet silent). Works well under a watch crystal; will look like a dark disc/rectangle in the dial centre.
- Panasonic a-Si on glass: colour/appearance not stated in the catalog (UNVERIFIED; typically brownish). Catalog warns static electricity damages cells and the light-receiving surface must be kept clean (VERIFIED).
- Epishine: datasheet says colours "might be subject to change"; designed for indoor use, "placing modules in direct sunlight for a prolonged time may result in degradation" (VERIFIED, sec. 8). **Poor fit under a watch crystal in sun.**
- Not found / not purchasable as small parts: Exeger Powerfoyle, GCell, Ambient Photonics (company says cells 5-225 cm2, no distributor found; UNVERIFIED), SunPower/Maxeon bare cells in <18 mm (none found), Flexsolar, Seiko (watch cells not sold as parts). Treat as unavailable.

### 1d. Practical conclusion for the 12-18 mm circle
- For *indoor* trickle: AM-1606C is the only genuinely stock part that fits, but ~9 uW at 200 lux is nearly worthless (see section 2).
- For *outdoor* contribution: you need a mono-Si cell, which means custom-cut (Anysolar will customise per their materials; UNVERIFIED for minimums) or an SMD strip placed elsewhere. A 22x7 mm KXOB strip has the same gross area (1.54 cm2) as a ~12.4 mm square, so power is equivalent; it simply doesn't fit a circle.
- For the voltage: a 3-cell strip (2.07 V Voc) is a good match for a boost harvester. Single-cell 0.69 V (12X1F) is below TI cold-start (600-700 mV) once indoors.

---

## 2. Energy budget model

All inputs are labelled. The model is a spreadsheet-style calc (Python script, not saved in the project).

### 2a. Constants and assumptions

| Item | Value | Tag |
|---|---|---|
| Battery nominal voltage | 3.7 V (energy = mAh x 3.7) | assumption |
| Usable fraction of capacity | 90 % (4.1 V down to ~3.3 V) | assumption |
| MCU sleep + RTC | 3.0 uA | UNVERIFIED (typical low-power MCU, 1-5 uA) |
| BMI270 wake-up mode | 13 uA = accel-only low-power @25 Hz 10 uA + advanced-feature engine 3 uA, at VDD 1.8 V | VERIFIED (BMI270 datasheet BST-BMI270-DS000-08 rev 1.6, Table 1 electrical characteristics). "Down to 4 uA" accel-only is also listed in the power-mode table. Wrist-wear-wakeup feature current itself is not separately tabulated. I treat 13 uA from the battery rail (LDO assumption). |
| Harvester/PMIC quiescent | 0.5 uA | VERIFIED range: AEM10941 400 nA (VBATT 3 V, LDOs off) / 600 nA (LDOs on); BQ25570 488 nA; BQ25504 <330 nA typ (all datasheets) |
| Other leakage (divider, regulator) | 2 uA | assumption |
| **Always-on total** | **18.5 uA -> 1.64 mWh/day** | derived |
| Battery self-discharge | 3 %/month of capacity | UNVERIFIED (typical LiPo; not in Renata datasheets read) |
| Display event | 10 LEDs lit x 2 mA each x 3 s, drawn from the battery rail at 3.7 V = 74 mW x 3 s = **0.0617 mWh per wake-up**. LED current is the battery current (constant-current/resistor drive), no boost | assumption (user brief: 1-5 mA/LED). Sensitivity below |
| PMIC harvest efficiency | 70 % indoor (uW level), 85 % outdoor | UNVERIFIED (TI states "up to 93 %" peak; real indoor efficiency at uW input is lower and is only shown as graphs) |
| Cell power densities | see 1b; indoor: a-Si 3.7 uW/cm2 per 200 lx scaled linearly (UNVERIFIED scaling), organic/c-Si-class 7.6 / ~12.5 / ~16.4 / 20.3 uW/cm2 at 200 / 300 / 400 / 500 lx (200 and 500 VERIFIED Epishine, 300-400 interpolated); c-Si outdoor 15.9 mW/cm2 at 1 sun (24.5 mW / 1.54 cm2, KXOB25-01X8F VERIFIED calc) | mixed |
| Cell areas (gross) | 10x10 = 1.00, 12x12 = 1.44, 15x15 = 2.25, 18x18 = 3.24 cm2 | the free circle of 12-18 mm is only 1.13-2.54 cm2, so 15x15 and 18x18 squares do not even fit a round hole; shown for scale |

### 2b. What the user's "30 %-70 % factor" is applied to
I apply it to **equivalent hours at the reference light level**, i.e. harvest hours = daylight hours (8-12 h) x factor. It is an availability/exposure factor (fraction of the day the cell sees the reference light, after sleeve, tilt, shadow, being asleep). It is *not* a cell-efficiency number; cell efficiency is already inside the W/cm2 densities. The result depends entirely on what the reference light is, so I show two references: S1 = 500 lx indoor-bright, and S1-sun = full 1 sun (an absurd upper bound for a wrist).

### 2c. Load per day (3 usage levels, fixed display event)

| Level | Wake-ups/day | Display mWh/day | Always-on mWh/day | Self-discharge (100 mAh) | **Total mWh/day** |
|---|---|---|---|---|---|
| Light | 20 | 1.23 | 1.64 | 0.37 | **3.25** |
| Medium | 60 | 3.70 | 1.64 | 0.37 | **5.71** |
| Heavy | 200 | 12.33 | 1.64 | 0.37 | **14.35** |

Display sensitivity (mWh/day for 20 / 60 / 200 wake-ups): 10 LEDs x 1 mA x 3 s = 0.6 / 1.9 / 6.2; 10 x 2 mA x 3 s = 1.2 / 3.7 / 12.3; 10 x 5 mA x 3 s = 3.1 / 9.3 / 30.8; 16 LEDs x 5 mA x 5 s = 8.2 / 24.7 / 82.2. Brightness-hungry usage can swamp everything.

### 2d. Battery capacity vs runtime with no solar (90 % usable, self-discharge included)

| Capacity | Energy (mWh) | Light (20/day) | Medium (60/day) | Heavy (200/day) |
|---|---|---|---|---|
| 40 mAh | 148 | 44 days | 24 days | 9 days |
| 60 mAh | 222 | 65 | 36 | 14 |
| 100 mAh | 370 | 103 | 58 | 23 |
| 150 mAh | 555 | 146 | 85 | 34 |

Idle only (no display): 74 days (40 mAh), 165 (100 mAh), 227 (150 mAh). **A 40-150 mAh LiPo is a sensible range; 60-100 mAh is the sweet spot for a 37 mm watch.**

### 2e. Harvest, mWh/day (after PMIC efficiency)

| Scenario | Assumptions | 10x10 | 12x12 | 15x15 | 18x18 |
|---|---|---|---|---|---|
| S1a: brief low, indoor ref | 8 h x 30 % = 2.4 h eq at 500 lx, 20.3 uW/cm2 (organic/c-Si class) | 0.03 | 0.05 | 0.08 | 0.11 |
| S1b: brief high, indoor ref | 12 h x 70 % = 8.4 h eq at 500 lx | 0.12 | 0.17 | 0.27 | 0.39 |
| S1b with a-Si (9.2 uW/cm2) | same hours | 0.05 | 0.08 | 0.12 | 0.18 |
| S1-sun low (upper bound, unrealistic) | 2.4 h eq at full 1 sun, c-Si, 85 % | 32 | 47 | 73 | 105 |
| S1-sun high (upper bound, unrealistic) | 8.4 h eq at full 1 sun | 114 | 164 | 256 | 368 |
| R1: wrist, desk worker | 10 h at 400 lx x 50 % sleeve/shading = 5 h eq, 16.4 uW/cm2 | 0.06 | 0.08 | 0.13 | 0.19 |
| R1 with a-Si (7.4 uW/cm2) | same | 0.03 | 0.04 | 0.06 | 0.08 |
| R4: poor indoor | 4 h at 300 lx x 50 % = 2 h eq | 0.02 | 0.03 | 0.04 | 0.06 |
| R2: one outdoor hour | 1 h at 40 % of 1 sun (tilt, sleeve), c-Si, 85 % | 5.4 | 7.8 | 12.2 | 17.5 |
| R2 with outdoor-type a-Si | 1 h, 3.5 mW/cm2 x 40 % (gross density from Amorton AM-5815 12 mW / 3.37 cm2 at 1 sun) | 1.2 | 1.7 | 2.7 | 3.9 |
| R3: combined c-Si | R1 + R2 | 5.5 | 7.9 | 12.3 | 17.7 |

(Caution: "S1-sun" assumes the cell sees 2-8 h of direct sun, which a wrist under a sleeve does not. The 40 % outdoor factor is my assumption.)

### 2f. Coverage of load (12x12 mm cell; harvest / daily load)

| Scenario | Light 3.25 mWh | Medium 5.71 | Heavy 14.35 |
|---|---|---|---|
| S1a (indoor, low) | 1.5 % | 0.9 % | 0.3 % |
| S1b (indoor, high) | 5.3 % | 3.0 % | 1.2 % |
| R1 (desk worker) | 2.5 % | 1.4 % | 0.6 % |
| R2 (1 h outdoor sun, c-Si) | 240 % | 136 % | 54 % |

Outdoor hours per day needed to fully offset the load (c-Si, 40 % sun): 10x10: 0.6 / 1.1 / 2.7 h; 12x12: 0.4 / 0.7 / 1.8 h; 15x15: 0.3 / 0.5 / 1.2 h; 18x18: 0.2 / 0.3 / 0.8 h (light/medium/heavy). Indoor-only break-even would need ~57-250 cm2 of cell (impossible).

### 2g. Honest verdict
- **Sustain the watch:** only for an outdoorsy wearer with a mono-Si cell, and only for light/medium use.
- **Extend battery life:** yes outdoors (R2 can add 50-240 % of a day's load per sun-hour); marginal indoors (1-5 %).
- **Indoors (300-500 lx): trickle**, comparable to the always-on draw of the BMI270 alone (1.1 mWh/day at 13 uA vs 0.08-0.2 mWh/day harvested). Dropping the IMU to a 4-7 uA mode saves more energy than a 12 mm indoor cell can harvest.
- Where the money/effort goes: reduce display energy (fewer LEDs lit, lower mA, shorter bursts) and IMU current; solar is an optional outdoor bonus.
- Counter-intuitive: a bigger battery does not help the net budget, only runtime; solar area in the 12 mm circle is capped (1.1-2.5 cm2).

---

## 3. Energy-harvesting / power-management ICs

### 3a. Comparison

All specs in this table are from the datasheet noted unless tagged UNVERIFIED. LCSC data read live 2026-10-05.

| IC | Package | Cold-start | MPPT | Storage / charge setting | Iq | Battery protection built in? | Extra: charge from USB/pads? | LCSC / JLCPCB C-number, stock, price | DigiKey / Mouser (UNVERIFIED snapshots) |
|---|---|---|---|---|---|---|---|---|---|
| **TI BQ25504** | VQFN-16 3x3 (RGT) | **600 mV typ** (rev history: older 330 mV was changed to 600 mV) | Programmable, VOC sampling | OV and UV set by resistors (OV to 5.25 V); LiPo OV/UV freely programmable | <330 nA typ | Yes: programmable OV, programmable UV, VSTOR-VBAT PMOS opens below UV (load disconnect). No NTC. | No | **C2876746**, 154 in stock, $4.61 @1 / $3.49 @100 | DigiKey cross-listing seen, price UNVERIFIED |
| **TI BQ25570** | VQFN-20 3.5x3.5 (RGR) | **600 mV typ (700 max)**, 15 uW | Programmable VOC ratio (50/80 % or resistor) | OV programmable 2.2-5.5 V; **UV fixed 1.95 V**; buck out 1.8-3.3 V | 488 nA full operating | Partial: **UV 1.95 V is far too low for LiPo** (needs PCM'd cell or external UV logic via VBAT_OK) | No | **C506250**, 488 in stock, $5.87 @1 / $3.69 @1000 | DigiKey $7.32 @1, ~1.3K stock (UNVERIFIED) |
| TI BQ25505 | VQFN-20 3.5x3.5 | sibling - not read, do not rely | - | - | - | - | - | **C882746**, 733 in stock, $3.66 @1 / $2.40 @1000 (LCSC page VERIFIED; electrical specs UNVERIFIED) | - |
| **e-peas AEM10300** | QFN-28 4x4 | **275 mV, 3 uW** | VOC ratio 60-90 % selectable, programmable period | Config pins: preset LiPo "LiCoO2/Li-Po" = OVDIS 3.00 V / CHRDY 3.50 V / **OVCH 4.05 V** (another preset 4.35 V); custom via resistors | 5.9 nA on STO (EN_HP=L, VSTO 3.7 V) | Over-charge: yes (boost stops at OVCH). Over-discharge: **status pin ST_STO only**; no load switch described. LiPo's own PCM still needed | No | Not found on LCSC/JLCPCB (UNVERIFIED). Mouser carries EVK10300 | Mouser (EVK shown); IC stock not confirmed |
| **e-peas AEM10941** | QFN-28 5x5 | **380 mV, 3 uW** | VOC ratio 70/75/85/90 % | CFG presets: Li-ion OVCH 4.12 V, CHRDY 3.67 V, OVDIS 3.60 V (or 3.01 V variant); LiFePO4 etc.; custom via R | 400 nA (LDOs off) / 600 nA (LDOs on) at 3 V | Yes: over-charge stops boost; at OVDIS the LDOs are switched off (protects via load gating). Direct battery connections (e.g. LED rail) bypass it | No; has optional primary-battery input | Not found on LCSC (UNVERIFIED) | Mouser: AEM10941-QFN, 7,094 in stock (Indian Mouser page, price ~INR 295 = ~$3.5; undated, UNVERIFIED) |
| e-peas AEM10330 | QFN-40 5x5 | 275 mV | ratio 60-90 % | presets as 10300 + load 1.2-3.3 V up to 60 mA | 875 nA on STO | like 10300 + regulated load | No | not found | not checked |
| ADI **ADP5091** (also -5092) | LFCSP-24 (4x4) | 380 mV typ w/ charge pump | Yes | programmable; input range 0.08-3.3 V (cannot take >3.3 V PV) | 510 nA operating / 390 nA sleep | OV/UV programmable (mirror, not full read) | No | **C579259** (ADP5091ACPZ-2-R7), 74 in stock, $6.00 @1 | datasheet read only via third-party mirror of ADI Rev. A (ADI host unreachable) |
| ADI ADP5090 | LFCSP-16 3x3 | not read | - | - | - | - | No | not found | DigiKey listing only seen (UNVERIFIED) |
| ADI LTC3105 | DFN-10 3x3 / MSOP-12 | 250 mV start (0.25-0.4 V), operate 225 mV-5 V | MPPC (programmable) | **boost regulator only, not a battery charger** | 24 uA burst-mode | none | No | C684028 (DFN) 17 in stock $11.91; C684031 (MSOP) 60 in stock $12.03 | - |
| ADI LTC4070 | MSOP-8E / DFN-8 | n/a (shunt charger, not a harvester) | none | pin-selectable float | 450 nA to 50 mA operating (ADI web summary, UNVERIFIED) | Shunt over-charge only | No | C687241 **out of stock** | - |
| ADI LTC3331 | QFN 5x5 | harvester input 3.0-19 V (UNVERIFIED snippet) - will not start from small PV | - | 10 mA shunt charger, 3.45-4.2 V options | ~950 nA | - | - | not checked | not checked |
| ROHM BD70522GUL | VCSP50L1C 1.76 x 1.56 mm | n/a - a **buck**, not a harvester | - | - | 180 nA (UNVERIFIED snippet of ROHM DS) | - | - | not found | - |
| ABLIC S-8880A | SOT-23-5 / SNT-8A | 0.35 V (charge pump only; needs a boost behind it) | - | - | - | - | - | not checked | - |

Not evaluated: Nexperia NEH71x0 and any other parts; the user listed Nexperia, but I did not find a datasheet in time. Treat as open.

### 3b. Conventional pad/USB charger (if solar is dropped)

| IC | Package | Charge | Notes | LCSC |
|---|---|---|---|---|
| **MCP73831T-2ACI/OT** | SOT-23-5 (or 2x3 DFN-8) | 4.20 V CC/CV, 15-500 mA via one PROG resistor, +/-0.75 %, VDD 3.75-6 V, reverse leakage 0.15 uA typ (PROG floating) | Datasheet DS20001984H VERIFIED. Needs 4.7 uF in and 4.7 uF out, one PROG resistor, status LED optional. Selectable preconditioning/end-of-charge (variants) | **C424093**, 5,708 in stock, $0.79 @1, $0.42 @1000 |
| TP4054-42-SOT25R (TOP POWER ASIC) | SOT-23-5 | 4.2 V linear charger, C/10 termination, input 4-9 V, up to ~450 mA (LCSC summary) | Datasheet not read; LCSC page VERIFIED for stock/price | **C32574**, 22,740 in stock, $0.13 @5 |

For a 40-100 mAh cell set charge current to <=0.5C (e.g. 20-50 mA). Renata cells in 4a allow 0.5C normal, 1C maximum (VERIFIED, Renata datasheets).

### 3c. Recommendation

**First choice (best technical fit): e-peas AEM10300.** 275 mV cold-start suits a single or 3-cell mono-Si string indoors; QFN-28 4x4 mm; only 3 external power parts; built-in LiPo preset (3.00/3.50/4.05 V); 5.9 nA Iq. Weakness: no load disconnect (only ST_STO flag), and **not stocked at LCSC/JLCPCB** (UNVERIFIED), so it is a consigned/hand-assembled or Mouser-sourced part. Typical circuit (datasheet front page, VERIFIED): one 10 uH inductor, 10 uF + 22 uF capacitors (CSRC, CSTO), strap pins STO_CFG[3:0] and R_MPP[2:0]/T_MPP; optional resistors only in custom mode. Use a PCM-protected LiPo and have the MCU watch ST_STO.

**Second choice (assembly-friendly): TI BQ25504 (C2876746).** Verified datasheet, in stock at LCSC (154), 3x3 mm. Needs cell Voc > ~0.7 V when it must cold start, so use a >=2-series cell string (e.g. KXOB25-04X3F 2.07 V, or AM-1606 3.7 V at 200 lx) not a 0.69 V single cell. External parts from the datasheet: 22 uH boost inductor, ~4.7 uF on VIN_DC, VSTOR 4.7 uF, 0.01 uF low-leakage cap on VREF_SAMP, plus 1 % high-value resistor dividers for OV (~4.1 V), UV (~3.0 V) and OK thresholds, and the VOC-sample divider (MPPT). BQ25570 (C506250) adds a 1.8-3.3 V buck for the MCU but its UV is fixed at 1.95 V, so with a LiPo you rely on the cell's PCM.

If AEM10941 is wanted instead: it adds regulated 1.2/1.8 V and 1.8-4.1 V LDO outputs gated at OVDIS, but costs a 5x5 mm QFN, 2 inductors (22 uH + 10 uH) and 5 capacitors (CSRC 10 uF, CBOOST 10-22 uF, CBUCK 10 uF, CLV 10 uF, CHV 10 uF).

**Pad/USB charging alongside solar:** none of the harvesters accepts a 5 V USB source on the same node cleanly (AEM10941/10300 SRC abs max 5.5 V; BQ25570 recommended 5.1 V). Common approach: charge the LiPo with a separate MCP73831 (ORed to the cell through its own path) or just use MCP73831 alone.

---

## 4. Batteries

Naming convention VERIFIED against Renata datasheets (ICP341018 = 3.4 x 10 x 18 mm nominal; max dims in the datasheet include swelling, e.g. 3.7 x 10.2 x 19.5). Generic "401120"-style cells follow the same TTWWLL pattern (UNVERIFIED for non-Renata vendors).

| Cell | Capacity | Max dims T x W x L (mm) | Weight | PCM / safety circuit | Charge / discharge limits | Tag / source |
|---|---|---|---|---|---|---|
| Renata ICP341018PM | 35 mAh (33 min) | 3.7 x 10.2 x 19.5 | 1.7 g | Yes, AWG30 wires | 4.2 V CC/CV, 0.5C normal / 1C max charge (17.5/35 mA), cut-off 3.0 V, 1C continuous discharge 35 mA | VERIFIED, Renata datasheet (Conrad copy) |
| **Renata ICP331319PM** | 50 mAh (45 min) | 3.7 x 12.8 x 21.0 (after 500 cycles) | 2.0 g | Yes | 25 mA normal charge, 50 mA max; 50 mA continuous discharge | VERIFIED, ICP331319PM V01 11/2022 (Conrad copy) |
| **Renata ICP501022UPM** | 80 mAh (75 min) | 5.5 x 10.0 x 24.0 | 2.6 g | Yes, IEC62133 (search excerpt) | 40 mA normal charge, 80 mA max; 80 mA continuous | VERIFIED, datasheet (Rapid Electronics copy) |
| Renata ICP402025 (PC-01 connector version) | 155 mAh (150 min) | 4.3 x 20.5 x 27.5 | 4.0 g | Yes | 155 mA max charge | UNVERIFIED (search excerpt of datasheet copy, not opened) |
| Generic LiPo 401120 | 60 mAh | ~4.2 x 11.5 x 20 | - | usually yes (unspecified) | 30 mA charge | UNVERIFIED (uelectronics.com listing) |
| Generic 301014 / 501012 / 402025 | not verified (approx. 15-25 / ~30 / ~120-150 mAh, typical, my estimate) | nominal 3.0x10x14 / 5.0x10x12 / 4.0x20x25 | - | check each | - | UNVERIFIED |

- Wire-lead cells (AWG30) can be soldered to pads on the back of the board; the soldered-on requirement is consistent with Renata's "PM" wire-lead variants (VERIFIED). Many AliExpress cells have no PCM or poor PCMs; Renata PM cells advertise a safety circuit.
- **Fit under a 37 mm round board:** the board area is ~10.8 cm2 (diameter 37 mm). A 50 mAh cell footprint is 12.8 x 21 = 2.7 cm2; a 155 mAh cell is 20.5 x 27.5 = 5.6 cm2 (diagonal 34 mm, which just fits inside 37 mm but leaves almost no room for the case wall). Placing the cell flat on the back means total stack = PCB (~1.2-1.6) + back components (~1-2) + cell (3.7-5.5 mm) + case, i.e. a watch 8-10 mm thick. Because electronics are also on the back, practical choice: 50 mAh (21 x 12.8) or 80 mAh (24 x 10) strip beside the electronics, or put the cell on the opposite half. Use the 3.7 mm-thick cells to stay thin.
- Charge temperature window **0-45 C** (Renata, VERIFIED) matters: a wrist cell in direct sun plus ambient heat can exceed it; neither TI nor e-peas datasheets provide a battery NTC input (BQ25504 has only IC-die over-temp, OT_PROG; AEM10941 not found), so thermal protection is on you.

---

## 5. Risks and notes

| Topic | Finding | Tag |
|---|---|---|
| **Over-voltage under strong light** | Voc scales per series cell: KXOB25-01X8F/02X8F 5.53 V at 1 sun/25 C; the temperature coefficient is -13.9 mV/K for 01X8F, so a cold outdoor day pushes Voc higher. Abs max on AEM10941/10300 SRC pins and BQ25570 VIN_DC is 5.5 V, recommended VIN_DC to 5.1 V (BQ25570), SRC 5 V (AEM10941). A 3-cell strip (2.07 V) or single 0.69 V cell never gets near this. AM-1606 reached 3.7 V at only 200 lx; its 1-sun Voc is not given, expect higher; add a 5.1 V zener/TVS or an overvoltage shunt if Voc could approach the limit | VERIFIED for limits; Voc-at-sun for AM-1606 UNVERIFIED |
| **Reverse current when dark** | None of the datasheets I read (BQ25504/70, AEM10941/10300) specify battery-to-PV reverse leakage. PV cells themselves are reverse diodes; the boost-converter input stage generally blocks the battery. A Schottky or ideal-diode adds loss (0.2-0.3 V is unacceptable for sub-1 V cells), so do not add one unless measured. Measure dark-leak on a prototype | UNVERIFIED |
| **Over-discharge** | BQ25570 UV fixed 1.95 V (VERIFIED) - fatal for LiPo without the cell's PCM. BQ25504 UV programmable (set ~3.0 V; load on VSTOR is isolated below UV, VERIFIED). AEM10941 gates LDOs at OVDIS 3.01-3.60 V. AEM10300 only flags. LED rail connected straight to the battery bypasses any harvester gating, so the MCU must stop display below ~3.3 V | VERIFIED |
| **Charge voltage** | AEM10941 Li-ion preset stops at 4.12 V; AEM10300 LiPo preset 4.05 V; BQ programmable. Lower than 4.2 V = slightly less capacity, longer life | VERIFIED |
| **Fragility** | Amorton: don't press/scratch; static damages the generating element; keep surface clean (catalog handling, VERIFIED). Mono-Si SolarBIT is a laminated film body, 1.8 mm thick; do not clean with IPA (datasheet) | VERIFIED |
| **UV / appearance under a crystal** | Epishine degrades in prolonged direct sun and above ~30 C storage is discouraged (datasheet sec. 8). Mono-Si is opaque dark blue/grey and the most stable; a-Si indoor types not meant for sun | VERIFIED (Epishine, Amorton); UV on c-Si UNVERIFIED |
| **Reflow / assembly** | Anysolar KXOB25 (SolarBIT): reflow soldering allowed **only** with low-temp Sn42/Bi58 paste, peak ~220 C, >175 C for ~50 s, MSL3 (vacuum sealed; bake per J-STD-033C if the bag is open); manual: 5 s <400 C (04X3F rev May 2025) or 2 s <260 C (05X3F rev Aug 2023). The SolarMD film module (SM531K12L) is "not recommended for high temperature surface mount reflow". Epishine: **not suitable for IR or hot-air reflow**, hand-solder, hot-bar, conductive adhesive, ultrasonic or laser welding. Panasonic Amorton: lead wire or conductive-paste terminals, no reflow information | VERIFIED |
| **Decision for the PCB assembler** | Treat every PV part as post-assembly hand-soldered or conductive-adhesive mounted. Put a solder-pad pair (not a footprint the assembler populates) in the front centre, mark the part DNP in the BOM. Do not send MSL3 SolarBITs through a standard JLCPCB lead-free profile | recommendation |
| **Spectrum / lighting** | Warm-white LED lighting favours organic/a-Si; mono-Si needs more light (reported 100x-500x less than sun indoors per Anysolar background text). Sleeve shadowing, hand orientation and sleeping hours cut effective hours well below the 8-12 h daylight figure | VERIFIED text, effect estimated |
| **Cold start trap** | Indoors a single 0.69 V c-Si cell may sit at only ~0.4-0.5 V Voc: below TI's 600-700 mV, near AEM10941's 380 mV, comfortable for AEM10300's 275 mV | VERIFIED limits; indoor Voc UNVERIFIED |
| **MPPT sampling of tiny cells** | TI VOC_SAMP leaks into tiny cells; a 1.44 cm2 indoor cell produces only microwatts, so the 488 nA Iq and sampling losses eat a meaningful part (0.5 uA at 3 V = 0.036 mWh/day ~ same size as indoor harvest) | calc |

---

## 6. Suggested next steps (no files were modified)
1. Decide whether solar is worth it: for indoor-only wear, drop it and use MCP73831 (C424093) with pads/USB.
2. If kept for outdoor use: order 2-3 each of AM-1606C (15x15, ~$2.6, trial) and KXOB25-04X3F/12X1F strips, and ask Anysolar for a ~12x12 custom mono-Si cell quote (3 series cells ideally).
3. Pick BQ25504 (C2876746) for a JLCPCB-assembled prototype, or AEM10300 on a hand-assembled spin; measure dark leakage, cold-start in a 300 lx room, and Voc at 1 sun.
4. Reduce idle: put BMI270 to accel-only low-power (4-10 uA) and avoid always-on gyro; every uA is 0.09 mWh/day.

---

## Sources

Datasheets read (downloaded and parsed):
- Panasonic Amorton catalog "Amorphous Silicon Solar Cells / Amorphous Photosensors": https://api.pim.na.industrial.panasonic.com/file_stream/main/fileversion/236089
- Anysolar KXOB25-04X3F datasheet Rev. May 2025: https://anysolar.biz/wp-content/uploads/2026/09/KXOB25-04X3F-DATASHEET.pdf
- Anysolar KXOB25-05X3F datasheet Rev. Aug 2023: https://astrolkwx.com/wp-content/uploads/KXOB25-05X3F%20DATA%20SHEET%20202007.pdf
- Anysolar KXOB25-01X8F / 02X8F / 12X1F datasheets: https://anysolar.biz/wp-content/uploads/2026/09/KXOB25-01X8F-DATASHEET.pdf (same folder, -02X8F, -12X1F)
- Anysolar SM531K12L SolarMD datasheet (background/reflow text; sibling, used only for general statements): https://astrolkwx.com/wp-content/uploads/SM531K12L%20DATA%20SHEET%20202007.pdf
- Epishine MultiCell data sheet v1.6.3: https://farnell.com/datasheets/4500869.pdf (older LEH datasheet: https://www.farnell.com/datasheets/3624821.pdf)
- TI BQ25570 (SLUSBH2G): https://www.ti.com/lit/ds/symlink/bq25570.pdf ; TI BQ25504 (rev G): https://www.ti.com/lit/ds/symlink/bq25504.pdf
- e-peas AEM10941 DS v2.3: https://e-peas.com/documents/AEM10941/DS-AEM10941.pdf ; AEM10300 DS v1.5: https://e-peas.com/documents/AEM10300/DS-AEM10300.pdf ; AEM10330 DS v1.5: https://e-peas.com/documents/AEM10330/DS-AEM10330.pdf
- Linear/ADI LTC3105 (Farnell copy): https://www.farnell.com/datasheets/1769095.pdf
- Microchip MCP73831/2 DS20001984H: https://ww1.microchip.com/downloads/en/DeviceDoc/MCP73831-Family-Data-Sheet-DS20001984H.pdf
- Bosch BMI270 datasheet BST-BMI270-DS000-08 rev 1.6: https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf
- Renata ICP341018PM: https://asset.conrad.com/media10/add/160267/c1/-/en/001214022DS01/podatkovna-tablica-1214022-renata-icp341018pm-specijalni-akumulatori-prizmaticni-kabel-lipo-37-v-35-mah.pdf ; ICP331319PM: https://asset.conrad.com/media10/add/160267/c1/-/gl/003015326DS00/tehnicni-podatki-3015326-renata-icp331319pm-specialni-akumulatorji-prismaticno-kabel-lipo-37-v-50-mah.pdf ; ICP501022UPM: https://static.rapidonline.com/pdf/12-8368_v1.pdf

Live distributor pages (2026-10-05):
- LCSC: https://www.lcsc.com/product-image/C506250.html (BQ25570), https://www.lcsc.com/product-image/C2876746.html (BQ25504), https://www.lcsc.com/product-image/C882746.html (BQ25505), https://www.lcsc.com/product-image/C579259.html (ADP5091-2), https://www.lcsc.com/product-image/C424093.html (MCP73831), https://www.lcsc.com/product-detail/C32574.html (TP4054), https://www.lcsc.com/product-image/C684028.html and C684031 (LTC3105), https://www.lcsc.com/product-image/C687241.html (LTC4070), https://www.lcsc.com/product-image/C5358484.html and https://www.lcsc.com/product-detail/C19077769.html (KXOB25)
- Panasonic stock search for AM-1606: https://na.industrial.panasonic.com/stock-search/AM-1606
- PowerFilm LL200-3-37: https://www.powerfilmsolar.com/products/electronic-component-solar-panels/indoor-light-series/ll200-3-37

Search-engine excerpts only (UNVERIFIED): DigiKey/Mouser pages for KXOB25 and AEM10941 pricing/stock; Mouser AM-1606C-MEL price; ADP5091 mirror https://pdf.jiepei.com/adp5092-34924476.html; LTC4070/LTC3331 summaries; ROHM BD70522GUL (https://fscdn.rohm.com/en/products/databook/datasheet/ic/power/switching_regulator/bd70522gul-e.pdf, not opened); ABLIC S-8880A; Renata ICP402025 (https://www.manualsdir.com/manuals/258154/renata-sa-icp402025pc-01.html); generic 401120 (https://uelectronics.com/producto/bateria-lipo-3-7v-60mah-401120/).
