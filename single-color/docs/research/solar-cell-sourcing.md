# Solar cell sourcing for the LED watch centre (research dated 2026-10-06)

Goal: a solar cell in the middle of the front face, with LED rings around it. Size target is a 12-20 mm circle or up to about 14 x 20 mm rectangle, no thicker than 2 mm. A 23 x 25 mm rectangle is acceptable only if nothing smaller exists.

Tags used throughout:
- **VERIFIED**: I read the manufacturer datasheet or catalog PDF, or a distributor page, and the source is cited.
- **UNVERIFIED**: from a search-result snippet, a reseller or aggregator page, or my own estimate. Treat as a lead.
- **ESTIMATE**: my own arithmetic, not a published number.

Limits of this research: DigiKey and Mouser block automated page fetches (HTTP 403 or Cloudflare), so I could not read live DigiKey/Mouser price tables directly. Prices and stock below come from regional DigiKey mirror pages, LCSC, resellers and Panasonic's stock-search page, and are tagged accordingly. Re-check them on the live site before ordering.

---

## 1. Bottom line

1. **Nothing round exists in the 12-20 mm range as a stock, individually purchasable part.** I looked at Anysolar, Panasonic, TDK, PowerFilm, Epishine, Exeger, Ricoh and Seeed, plus hobby sources. The only round stock parts I found are bigger:
   - Panasonic AL-2402, 27.2 mm diameter, 0.2 mm thick, stainless steel substrate (VERIFIED, Panasonic catalog).
   - Panasonic AM-2709B, 30.8 mm diameter, 0.7 mm thick, glass (VERIFIED, same catalog).
   - Anysolar SM101K04FR, 43.5 mm diameter.
   - Anysolar SM122K03FR, 82 mm diameter.
   - A 55 mm epoxy hobby panel.
2. **The best stock parts are small rectangles, not circles.**
   - The best fit for the 14 x 20 mm window is the Anysolar KXOB25-07X1TF (11.35 x 8 x 1.2 mm).
   - The best indoor-optimised part is the Panasonic AM-1606C (15 x 15 x 0.7 mm), which is in stock now.
3. **The realistic route to a round cell is a custom cut.** Panasonic says Amorton can be made in round or any other shape, and Epishine offers custom shape, size and contacts. Both are enquiry-only, and I could not find a published minimum order or price for either.
4. **A 14 x 20 mm cell cannot power a ring of LEDs in normal room light.** At 200-1000 lux, expect tens of microwatts, not milliwatts. Direct sun gives roughly 10-30 mW. Plan on a battery or supercap with the cell as a trickle charger. The cell and an energy-harvesting IC (BQ25504, AEM00300, AEM10941 or similar) will extend battery life but will not drive the LEDs directly.

---

## 2. Comparison of all real candidates

All Anysolar numbers below are at **1 sun (100 mW/cm², AM1.5, 25 C)** unless noted. Anysolar publishes no lux figures for the SolarBIT cells. Panasonic indoor numbers are at **200 lx fluorescent**.

| Rank | Part | Maker | Shape and size (mm) | Thickness | Voc | Vmpp / Impp | Pmax | Light level | Tech | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | KXOB25-07X1TF | Anysolar | Rectangle 11.35 x 8 | 1.2 +/-0.3 | 0.69 V | 0.57 V / 25 mA | 14.3 mW | 1 sun | Mono-Si, 1 cell | VERIFIED, [datasheet](https://anysolar.biz/wp-content/uploads/2026/09/KXOB25-07X1TF-DATASHEET.pdf) |
| 2 | AM-1606C (also AM-1606C-MEL) | Panasonic | Square 15 x 15 | 0.7 | 3.7 V | Vop 2.6 V / Iop 3.4 uA (about 8.8 uW) | not listed | 200 lx fluorescent | a-Si on glass, 6 cells in series | VERIFIED, [Panasonic catalog](https://api.pim.na.industrial.panasonic.com/file_stream/main/fileversion/236089), plus a search-result snippet of the Mouser datasheet |
| 3 | KXOB25-04X1TF | Anysolar | Rectangle 9 x 7 | 1.2 +/-0.3 | 0.69 V | 0.56 V / 17.6 mA | 9.8 mW | 1 sun | Mono-Si, 1 cell | VERIFIED, [datasheet](https://anysolar.biz/wp-content/uploads/2026/09/KXOB25-04X1TF-DATASHEET.pdf) |
| 4 | KXOB25-05X3TF | Anysolar | Rectangle 23 x 8 | 1.2 | 2.07 V | 1.67 V / 18.4 mA | 30.7 mW | 1 sun | Mono-Si, 3 cells in series | VERIFIED, [Anysolar Gen3 table](https://anysolar.biz/products/gen3/) and [datasheet](https://anysolar.biz/wp-content/uploads/2026/09/KXOB25-05X3TF-DATASHEET.pdf) |
| 5 | KXOB25-14X1TF | Anysolar | Rectangle 23 x 8 | 1.2 | 0.69 V | 0.56 V / 55 mA | 30.7 mW | 1 sun | Mono-Si, 1 cell | VERIFIED, datasheet read, [datasheet](https://anysolar.biz/wp-content/uploads/2026/09/KXOB25-14X1TF-DATASHEET.pdf) |

Other KXOB25 variants from the same Anysolar tables (VERIFIED, [Gen3](https://anysolar.biz/products/gen3/) and [Gen2](https://anysolar.biz/products/gen2/)):

| Part | Size (mm) | Thickness | Voc | Vmpp / Impp | Pmax | Notes |
|---|---|---|---|---|---|---|
| KXOB25-03X4TF | 23 x 8 | 1.2 | 2.76 V | 2.23 V / 13.5 mA | 30 mW | 4 cells in series |
| KXOB25-02X8TF | 23 x 8 | 1.2 | 5.53 V | 4.46 V / 5.9 mA | 26.3 mW | 8 cells in series; best voltage for a boost IC |
| KXOB25-12X1F | 22 x 7 | 1.8 | 0.69 V | 0.56 V / 43.9 mA | 24.5 mW | Gen2, 1.8 mm thick |
| KXOB25-04X3F | 22 x 7 | 1.8 | 2.07 V | 1.67 V / 13.2 mA | 22.0 mW | Gen2 |
| KXOB25-01X8F | 22 x 7 | 1.8 | 5.53 V | 4.46 V / 5.5 mA | 24.5 mW | Gen2 |
| KXOB421K01TF | 22 x 22 | 1.2 | 0.69 V | 0.56 V / 161 mA | 90 mW | Too large to fit the centre target |
| KXOB081K06TF (your cell) | 23 x 25 | 1.2 | 4.15 V | 3.35 V / 31.6 mA | 105.9 mW | The part already on your board |

The "TF" suffix means 1.2 mm thick; the "F" parts are 1.8 mm. The three "preliminary" datasheets I read for the small TF parts are marked "Preliminary, Rev. Jun. 2026".

### Reading these numbers for a watch

- **Active area is smaller than the package.** For the KXOB25-04X1TF the front-side drawing shows an active window of about 8.0 x 5.83 mm inside the 9 x 7 mm body (VERIFIED, datasheet page 3). That is about 0.47 cm2.
- **Indoor power (ESTIMATE, not published).** Anysolar does not publish lux performance, only 1-sun numbers plus a Voc-versus-irradiance plot. Assuming roughly 8-12 uW per cm2 at 200 lux and roughly 40-60 uW per cm2 at 1000 lux for mono-Si under LED light (my own assumption, not a datasheet value):
  - The 9 x 7 mm cell gives about 4-6 uW at 200 lux.
  - The 11.35 x 8 mm cell gives about 6-9 uW at 200 lux.
  - Your 23 x 25 mm cell gives about 50 uW at 200 lux.
  - Do not rely on these. Measure a sample under your own lighting.
- **Panasonic AM-1606C indoor figure is measured.** It delivers about 8.8 uW at 200 lx fluorescent (2.6 V x 3.4 uA). That is in the same range as the small mono-Si cells but at a usable 2.6-3.7 V.
- **Low-voltage cells need the right boost IC.** The single-cell Anysolar parts (0.69 V Voc) work with the e-peas AEM00300 and the TI BQ25504, which Anysolar itself lists as recommended chargers (VERIFIED, Gen3 table). The Epishine evaluation kit datasheet states its harvesting IC needs at least 380 mV to cold-start (VERIFIED, [Epishine EK datasheet](https://www.farnell.com/datasheets/3624821.pdf)). A 0.69 V cell in dim light may sag below that, so consider two cells in series, or a 2.07 V / 2.76 V part.

### Termination and reflow

| Part family | Termination | Reflow | Source |
|---|---|---|---|
| Anysolar KXOB25 / KXOB1xx / SM series | SMD pads on the back (the 04X1TF drawing shows two end pads marked + and -) | Yes, but only with low-temperature solder. Anysolar recommends Sn42/Bi58 paste with a 220 C peak, above 175 C for about 50 s. Alternatively hand-solder for 5 s below 400 C. MSL 3, so bake if the bag is opened. Do not clean with IPA or chemical detergents; use lukewarm water. | VERIFIED, datasheet page 3 |
| Panasonic AM-1606C | "C" suffix means no lead wire (bare electrodes). Catalog states "A, CA, CAR" = with lead wire; "B, C, CS" = without. | Not stated. Glass amorphous cell; assume no reflow. Operating range on sibling Amorton listings is -10 to 60 C (UNVERIFIED for this specific part). | VERIFIED for the lead-wire code, UNVERIFIED for soldering |
| Epishine LEH3 / MultiCell | Solder pads on flexible PET foil | **No.** Datasheet says "NOT SUITABLE for infrared or hot-air reflow soldering." Use hand solder, hot bar, conductive adhesive, ultrasonic or laser welding. Do not cut or fold the modules. | VERIFIED, [datasheet](https://www.farnell.com/datasheets/4500869.pdf) |

For a PCB with LED rings, the Anysolar SMD parts are the only ones here that drop straight onto your board. You would need a SnBi paste pass or hand-solder the cell last.

---

## 3. Where to buy and what it costs

Prices below are single-piece unless stated. Because DigiKey and Mouser blocked live fetches, most figures are from mirrors or resellers.

| Part | Source | Stock / price I could see | Tag |
|---|---|---|---|
| KXOB25-02X8F-TB (23 x 8 x 1.8, 5.53 V) | DigiKey (EU site) | 895 in stock; EUR 3.62 at 1, 2.78 at 20, 2.42 at 100; lead time 15 weeks. [Link](https://www.digikey.es/en/products/detail/ixys/KXOB25-02X8F/9990458) | VERIFIED (page fetched) |
| KXOB25-14X1TF-TR (23 x 8 x 1.2) | DigiKey Canada mirror | 0 in stock; CAD 5.11 at 1, 4.17 at 10, 3.42 at 100; 2,500 expected 2027-01-20. [Link](https://punchouttest.digikey.ca/en/products/detail/anysolar-ltd/KXOB25-14X1TF-TR/13999166) | VERIFIED page, but a test/mirror host |
| KXOB25-14X1TF-TR | Dasenic (reseller) | 10,500 listed; USD 2.99 at 1. [Link](https://dasenic.com/product/anysolar-kxob25-14x1tf-tr-6790669) | UNVERIFIED (reseller) |
| KXOB25-04X3F-TB (22 x 7 x 1.8, 2.07 V) | LCSC | Out of stock; USD 4.72 at 1, 1.88 at 200. [Link](https://www.lcsc.com/product-detail/C19077769.html) | VERIFIED page |
| KXOB25-04X1TF, KXOB25-07X1TF (the two small cells) | Anysolar lists them as active; North America distributors per Anysolar are DigiKey, Arrow and Future. I could not find a live stock page. One search snippet mentioned a KXOB25-04X1TF-TB at about USD 2.66, source not confirmed. | **UNVERIFIED stock and price.** Datasheets are marked "Preliminary," so ask before designing around them. |
| AM-1606C / AM-1606C-DGK-E (Panasonic) | Panasonic stock-search page dated 2026-10-06 | 640 at DigiKey. [Link](https://na.industrial.panasonic.com/stock-search/AM-1606) | VERIFIED (Panasonic page) |
| AM-1606C | Findchips (Unikey Electronic) | USD 1.96-2.32 per unit, 640 units. [Link](https://www.findchips.com/search/AM-1606C) | UNVERIFIED (aggregator, price range only) |
| AM-1606C-MEL | Mouser | 301 in stock as of 2026-07-27 per a search snippet | UNVERIFIED |
| Epishine LEH3_50x50_6_10 (50 x 50 mm, too big) | Farnell | EUR 158.85 at 1 per a search snippet | UNVERIFIED |

Distributors that Anysolar names for North America (VERIFIED, [Anysolar sales page](https://anysolar.biz/sales-contacts/north-america/)): Arrow, DigiKey, Future Electronics. Direct contact: mjeong@anysolar.biz (the page says they are also seeking new distribution channels).

---

## 4. Other makers and technologies I checked

| Maker / product | What I found | Fits? | Tag |
|---|---|---|---|
| **Panasonic Amorton, small indoor cells** | AM-1456 (25 x 10 x 1.1, Voc 2.5 V, 1.5 V / 5.9 uA at 200 lx); AM-1411 (29.6 x 11.8); AM-1417 (35 x 13.9, 1.5 V / 13.3 uA); AM-1312 (38 x 12.5). All are too long for the centre. Source: Panasonic catalog. | Marginal | VERIFIED |
| **Panasonic AM-30-11** | Glass, 14 x 13 x 1.1 mm, 0.6 V, 17.7 uA. The catalog lists it under photosensors ("30" series) at fluorescent 200 lx. It is a sensor cell, so power is very low (about 10 uW at best). | Size fits, power poor | VERIFIED (catalog), part availability UNVERIFIED |
| **Panasonic AM-5610 (outdoor)** | 25 x 20 x 1.8 mm, 3.3 V at about 5.1 mA, 18 mW at 1 sun. Outdoor-type cell, so weak indoors. | Marginal, outdoor-only | VERIFIED (catalog); DigiKey/ChipDip listings seen |
| **Panasonic AL-2402 (round)** | 27.2 mm diameter, 0.2 mm thick, stainless-steel substrate, 1.5 V / 10.1 uA at 200 lx. Round, but 27 mm. A watch-grade standard part. | Too big by 7 mm | VERIFIED (catalog); availability UNVERIFIED |
| **Panasonic AM-2709B (round)** | 30.8 mm diameter, 0.7 mm, glass, 3.0 V / 3.3 uA at 200 lx. | Too big | VERIFIED (catalog) |
| **Panasonic custom shapes** | Catalog states Amorton can be made round, square or any complex shape, and every product table says "Designs may be customized based on requests." No minimum order or price published. Contact: Panasonic Solar Amorton, Tokyo. | The best route to a true 15-20 mm round, indoor-optimised cell | VERIFIED that custom is offered; MOQ and price UNVERIFIED |
| **TDK BCS4430B6** | Film a-Si, 44 x 30 mm, 4.2 V. Obsolete. | No | VERIFIED (DigiKey listing snippets) |
| **Epishine** | Standard modules are 50 x 50, 50 x 30, 50 x 20 mm (LEH3), plus MC15-25x29-4 (25 x 29 mm, 4 cells, Voc 2.59 V, 124 uW at 500 lux, 0.2 mm thick). Power density 7.6 uW/cm2 mean at 200 lux, 20.3 uW/cm2 at 500 lux. Epishine says it offers custom shape, size and contacting, and a sample ordering route via sales@epishine.com. Indoor-only, max 50 C, no reflow, may not be cut. | Flexible and very thin; custom cut is plausible for a round cell. 25 x 29 is larger than your acceptable maximum. | VERIFIED, [datasheet](https://www.farnell.com/datasheets/4500869.pdf) |
| **Exeger Powerfoyle** | Custom shape and print, but sizes start at 15 cm2 (about 44 mm diameter if round). Thickness from 1.3 mm. No public minimum order or sample route. | Too big | VERIFIED, [Exeger page](https://www.exeger.com/powerfoyle/customization/) |
| **PowerFilm** | Indoor series: INP1.2-12x34 (12 x 34 mm, Voc 0.8 V, 0.010 mW at 200 lux). Others are larger and low power. Industrial series (MP3-37, MPT3.6-75) are 114 x 36 mm and 74 x 73 mm. | 12 mm wide but 34 mm long; very low power | VERIFIED, [PowerFilm indoor series](https://www.powerfilmsolar.com/products/electronic-component-solar-panels/indoor-light-series) |
| **Ricoh solid-state DSSC (EH series)** | Largest module 52 x 84 mm, 230 uW. No small or round standard part found. | No | UNVERIFIED (press releases) |
| **SunPower / Maxeon C60 cells** | 125 x 125 mm, 0.58 V per cell, about 3.4 W. Sold for DIY panels on eBay and Tindie. I found nobody selling individual small cut pieces. You would have to laser-cut or scribe one yourself. A 15 mm circle would give roughly 0.58 V and, ESTIMATE, a few tens of mW at 1 sun. Fragile, bare cell, needs your own encapsulation and tabbing. | Possible DIY route to a round cell | UNVERIFIED |
| **Seeed, Kitronik, SparkFun hobby panels** | Seeed amorphous panels are 205 x 90 mm; Kitronik 3604 is 60 x 48 mm. Too large. | No | VERIFIED (DigiKey snippets) |
| **Tindie "miniature solar cell breakout"** | 5.8 x 9.85 mm cells on breakout boards, USD 2.50, "about 3.5 V (1 mA)" under a flashlight, only 10 left. Cell maker and technology not stated. | Tiny and cheap but unspecified | UNVERIFIED, [Tindie listing](https://www.tindie.com/products/questwise-ventures/miniature-solar-panel-cell-breakout-board/) |
| **Hobby epoxy round panel** | 55 mm diameter, 5 V, 40 mA (10 poly-Si cells). | Too big | UNVERIFIED |
| **GCell, Sundaya, Flexsolar, Solems, Solarbotics, Sunceco** | I found no public catalogue of small or round cells for these. Flexsolar's custom CIGS panels start at 50 W, so they are irrelevant. | No usable result | Not found |
| **Citizen Eco-Drive, Seiko, Casio** | Their cells are made in-house for their own watches. I found no evidence they sell cells to third parties. | Not purchasable | UNVERIFIED (absence of evidence) |
| **Voltaic Systems** | Builds custom-shaped panels (round, cutouts), laser-cut on FR4 with ETFE coating. Needs a quote; no published size floor or price. Contact: info@voltaicsystems.com, +1-212-401-1192. | Possible custom route, likely higher cost and a bigger minimum panel | VERIFIED, [Voltaic blog](https://blog.voltaicsystems.com/custom-shaped-solar-panels/) |

### Transparent or dial-printable photovoltaics under the LED rings

I found no purchasable semi-transparent PV in a size that suits a watch. The only relevant material was patents and watchmaker research (for example semi-transparent PV layers behind printed dials). Panasonic's catalog says Amorton can have regions that are transparent glass, made by etching, which would suit a see-through window, but that is custom-order only. Treat this as UNVERIFIED and a long shot. A more practical layout is a cell in the centre with LEDs on a ring outside it, as you are planning.

---

## 5. Top 5 for this application

1. **Anysolar KXOB25-07X1TF** (11.35 x 8 x 1.2 mm, 0.69 V, 14.3 mW at 1 sun). It is the smallest SMD cell with meaningful sun power and it fits well inside the 14 x 20 mm window, leaving room to wrap LED rings around it. Caveats: single 0.69 V cell needs a low-start boost IC; the datasheet is marked "Preliminary"; I could not confirm live stock.
2. **Panasonic AM-1606C** (15 x 15 x 0.7 mm, Voc 3.7 V, 2.6 V / 3.4 uA at 200 lx). It is the only part with a measured indoor figure and a boost-IC-friendly voltage. It is thin and in stock now (640 per Panasonic, 2026-10-06). Caveats: glass, bare electrodes, no reflow, only about 9 uW in a lit room.
3. **Anysolar KXOB25-04X1TF** (9 x 7 x 1.2 mm, 0.69 V, 9.8 mW). Smallest option; you could place two in series. Same caveats as #1.
4. **Anysolar KXOB25-05X3TF** (23 x 8 x 1.2 mm, 2.07 V, 30.7 mW). Higher voltage and about double the power, but 23 mm long, so it only works as a strip across the centre or under a ring segment. Stock exists on its siblings (KXOB25-05X3F and -02X8F) at DigiKey and Bristol.
5. **Anysolar KXOB25-02X8TF** (23 x 8 x 1.2 mm, 5.53 V, 26.3 mW). Same footprint as #4 with a very high voltage that suits boost ICs. Same length caveat.

**Best path to a round cell (not a stock part):** ask Panasonic Amorton for a custom round indoor a-Si cell (15-20 mm), or Epishine for a custom flexible round module. Both are enquiry-only and I could not confirm minimum orders or price.

---

## 6. How to buy these (beginner guide)

### Start here

1. **DigiKey (digikey.com).** It carries the widest range of small cells (Anysolar, Panasonic, TDK, Kitronik, SparkFun) and ships worldwide in single quantities. Anysolar lists it as an authorised North America distributor.
2. **Mouser (mouser.com).** Carries Panasonic Amorton (for example AM-1606C-MEL) and is a good second price check.
3. **LCSC (lcsc.com).** Cheaper Anysolar KXOB25 parts when in stock, with JLCPCB assembly integration, but stock is patchy (the KXOB25-04X3F was out of stock when I looked).
4. Direct from the maker if a part is not listed: Anysolar (mjeong@anysolar.biz), Epishine (sales@epishine.com).

### Searching DigiKey or Mouser

- Go to **Products, Sensors, Transducers, Solar Cells** (DigiKey category "Solar Cells"; Mouser "Solar Cells" under Sensors). Tick "In Stock" first.
- Search these terms: `KXOB25`, `KXOB25-07X1TF`, `KXOB25-04X1TF`, `IXOLAR`, `SolarBIT`, `Amorton`, `AM-1606`.
- Sort by **Size / Dimension** (smallest first) and use the **Type** filter: Monocrystalline for Anysolar, Amorphous for Panasonic and TDK.
- Filter **Open Circuit Voltage** to 1.5-5 V, or leave it open if you plan to series-connect.
- Check the **Packaging** column. "Tube" (TB) is the one to buy for single pieces; "Tape and Reel" (TR) parts are 1,300-2,500 per reel, although DigiKey lists some TR parts with a quantity-one price.
- Ignore the "Power" column when comparing indoor suitability: it is 1-sun power for crystalline cells and a much smaller, lux-based power for Panasonic indoor cells.
- Always check **Status** (Active versus Obsolete) and **Lead time**. Several Anysolar parts quote 10-15 weeks.

### Questions to ask a maker for a custom cut

1. Can you make a **round cell of 15 mm or 18 mm diameter**, no thicker than 1.2 mm? Do you also offer a 12 mm or 20 mm version?
2. What is the **minimum order quantity and price per piece**, and is there a sample or engineering lot (5 to 20 pieces)?
3. What is the **lead time** and the tooling or NRE fee?
4. What **voltage and series cell count** can fit in that area (one cell at 0.6 V, or several segments at 2-4 V)?
5. What are the **terminations**: SMD pads on the back, solder tabs, conductive-adhesive pads, or wires? On which side?
6. Is it **reflow-safe**? If not, what is the maximum temperature and the recommended attachment method (hand solder, conductive epoxy, hot bar)?
7. What is the **indoor performance** (uW per cm2 at 200 / 500 / 1000 lux, LED spectrum) and the **1-sun** rating?
8. What is the **top surface**: black, printed or coloured, and is a **semi-transparent or dial-printable** variant available?
9. What are the **operating and storage temperature limits** and the **humidity and UV** limits (relevant to a wrist-worn product)?
10. Do you provide a **drawing, a KiCad or STEP model, and a recommended boost IC** (for example e-peas AEM00300 or AEM10941, TI BQ25504)?

### Before you order

- Buy **two or three** of the 1.2 mm Anysolar TF parts and a pair of Panasonic AM-1606C, and measure them yourself at your real indoor light level with a boost IC. Anysolar publishes no lux data and Epishine itself warns not to rely on datasheets alone.
- Confirm that you can use **low-temperature SnBi paste** (220 C peak) on the board, or plan to hand-solder the cell last.

---

## 7. Source list

- Anysolar Gen3 table (all KXOB and SM parts): https://anysolar.biz/products/gen3/
- Anysolar Gen2 table: https://anysolar.biz/products/gen2/
- Anysolar datasheets (pattern `https://anysolar.biz/wp-content/uploads/2026/09/<PART>-DATASHEET.pdf`), read for KXOB25-04X1TF, -07X1TF, -14X1TF, -05X3TF, -02X8F
- Anysolar North America distributors: https://anysolar.biz/sales-contacts/north-america/
- Panasonic Amorton catalog (Apr 2019 edition, product tables): https://api.pim.na.industrial.panasonic.com/file_stream/main/fileversion/236089
- Panasonic stock search for AM-1606: https://na.industrial.panasonic.com/stock-search/AM-1606
- Epishine MultiCell / LEH3 datasheet: https://www.farnell.com/datasheets/4500869.pdf and https://www.farnell.com/datasheets/3624822.pdf
- Epishine evaluation kit: https://www.farnell.com/datasheets/3624821.pdf
- Exeger customization: https://www.exeger.com/powerfoyle/customization/
- PowerFilm indoor series: https://www.powerfilmsolar.com/products/electronic-component-solar-panels/indoor-light-series
- Voltaic custom panels: https://blog.voltaicsystems.com/custom-shaped-solar-panels/
- DigiKey (EU) KXOB25-02X8F: https://www.digikey.es/en/products/detail/ixys/KXOB25-02X8F/9990458
- LCSC KXOB25-04X3F-TB: https://www.lcsc.com/product-detail/C19077769.html
- Dasenic KXOB25-14X1TF-TR: https://dasenic.com/product/anysolar-kxob25-14x1tf-tr-6790669
- Findchips AM-1606C: https://www.findchips.com/search/AM-1606C
