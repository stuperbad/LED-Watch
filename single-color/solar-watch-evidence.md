# Is solar worth it for the LED watch? Evidence recheck

Date: 2026-10-06. Method: web research only; no KiCad files touched. Every number is tagged VERIFIED (source given and read on the page or in the PDF), UNVERIFIED (seen only in a search snippet, a forum, or a retailer page), or ESTIMATE (my assumption or derivation). The model is in `solar-energy-model.csv` (same folder), and the Python that produced it is trivially reproducible from the assumptions in section 4.

## 0. Bottom line

- Solar helps only if the face sees real daylight. In bright sun the cell is a major energy source; indoors it is almost nothing.
- Indoors under LED or fluorescent light, a 5.75 cm2 mono-Si cell harvests on the order of 10 to 100 microwatts, which is roughly 0.1 to 1 mWh over a whole 6-hour desk session (ESTIMATE, section 4).
- For an office worker the base case gives 0.6 to 2.4 mWh/day, about 4 to 71 percent of the three load levels. Partial cover at best, and only at the lowest load.
- A commuter with about 1 hour of sun on the wrist gets 1.5 to 5.7 mWh/day. A 5.75 cm2 cell roughly covers the 5.7 mWh/day load (100 percent) and the 3.3 mWh/day load (173 percent), but only 40 percent of the 14.4 mWh/day load.
- An outdoor enthusiast gets 9 to 35 mWh/day, which covers all loads with 3 cm2 or more.
- The result is dominated by how many hours of direct or bright-shade daylight the face sees, not by cell area or indoor performance. That is the number to measure.

## 1. Existing solar watches

### 1a. Citizen Eco-Drive (amorphous Si cell under the dial; cell area not published)

Charging tables from the Citizen manual for the E81x/E82x family (VERIFIED, read from the PDF: https://www.citizenwatch-global.com/support/pdf/e81x_e820_e821/e.pdf). The manual has three tables for three movements. Minutes of light needed for one day of operation:

| Light | Lux | Movement A | Movement B | Movement C |
|---|---|---|---|---|
| Sunny outdoors | 100,000 | 3 min | 2 min | 2 min |
| Cloudy outdoors | 10,000 | 9 min | 11 min | 12 min |
| 20 cm from 30 W fluorescent | 3,000 | 32 min | 35 min | 40 min |
| Interior lighting | 500 | 3.2 h | 3.5 h | 4 h |

The same manual says (VERIFIED) that normal use is obtained in about 10 minutes per day in direct sunlight or 4 hours per day under indoor illumination. Time to full charge: 7 to 10 hours at 100,000 lux, 26 to 90 hours at 10,000 lux, and 810 hours at 500 lux for movement A (the other two show a dash at 500 lux).
A search result also quoted a 1.5 V titanium-lithium cell with a 180-day reserve (UNVERIFIED, retailer page).

Derived (ESTIMATE from the VERIFIED table): energy per hour of light scales as 1/(minutes needed). From 100 klux (2 to 3 min) to 500 lux (3.2 to 4 h) lux falls 200x while harvested energy rate falls only about 70 to 120x. So the a-Si cell is 1.7 to 3x more efficient per lux at 500 lux than at full sun. Note that sun lux is 100,000 but the watch's output saturates; the cell is not 100 percent efficient at any condition.

### 1b. Casio Tough Solar (amorphous Si cell; area not published)

Module 5454 manual (VERIFIED: https://support.casio.com/global/en/wat/manual/5454_en/VPCVSYfkxmgtjs.html). Charging time for 1 day of operation:

| Light | Lux | Time per day of operation |
|---|---|---|
| Outdoors, sunny | 50,000 | 8 min |
| Sunny, near window | 10,000 | 30 min |
| Overcast, near window | 5,000 | 48 min |
| Indoor fluorescent | 500 | 8 h |

Recovery times (VERIFIED, same page): from dead to start operating: 8 h at 50k lux, 26 h at 10k, 42 h at 5k, 469 h at 500 lux. From start to full: 38 h, 143 h, 232 h, and not stated at 500 lux.
Derived (ESTIMATE): 50k to 500 lux is 100x lux; the harvest rate falls only about 60x (8 h / 8 min = 60). The a-Si cell is again about 1.7x better per lux at 500 lux than at 50k.

Note that these watches are analog quartz with a load of order microwatts, not LED displays. They are not directly comparable in load, only in "light needed per day" and per-lux behaviour.

### 1c. Garmin solar (Power Glass; the cell is under the transparent screen)

- Garmin conditions for all battery claims: all-day wear plus 3 hours per day outside at 50,000 lux, i.e. 150,000 lux-hours/day (VERIFIED, Garmin blog https://www.garmin.com/en-US/blog/general/solar-charging-in-garmin-smartwatches/ states 50,000 lux and 3 h outdoors for the unlimited-battery claim).
- Garmin Fenix 7 Solar: 18 days smartwatch indoors, 22 days with solar (+4 days); GPS 57 h versus 73 h (+15 h) (UNVERIFIED, retailer snippets). Fenix 6 Pro Solar: 14 days + 2 days solar; fenix 6S Pro Solar: 9 days + 1.5 days (VERIFIED, Garmin press release https://www.garmin.com/en-PH/newsroom/press-release/news-2020-aug-solar/).
- Instinct 2 Solar: unlimited in smartwatch mode under the same assumptions, GPS 48 h with solar (UNVERIFIED, retailer/GSMArena snippets).
- Suunto Vertical Solar: +30 percent GPS battery at 50,000 lux (UNVERIFIED, retailer page). Battery mAh not found.
- Garmin Power Glass: 0.5 mm thick; the display-area cells are described as about 10 percent photovoltaic efficiency (meaning light transmission, one-tenth of the light reaches the cell) and the edge ring about 100 percent (UNVERIFIED, search result summaries of Garmin's solar minisite). Same source family: power 1 to 10 mW/cm2 and a curved panel reducing output by about 20 percent, and at 90 degrees to the sun output falls by a factor of about 6 (UNVERIFIED, the5krunner article https://the5krunner.com/2025/11/27/garmin-solar-technology-power-glass-unlimited-battery-mip).
- Real-world: one long-term Fenix 7S Pro user logged 16.9k lux-hours/day weekly average, 46.8k on his best day, 4k per day in a winter week, and 1.6k for an 8 mile forest-shade run; Garmin assumes 150k lux-hours/day. Measured gains: smartwatch +27 percent (11 to 14 days), GPS +7 percent, battery-saver +129 percent (VERIFIED as stated on the page https://runningwithrock.com/fenix-solar-charging-lux-hours/).
- Instinct 2 Solar forum users report about +1.5 percent in 30 min of sun and 1 to 2 percent net after 3 to 4 hours on a roof; the community consensus is that solar mostly slows discharge (UNVERIFIED, Garmin forum https://forums.garmin.com/outdoor-recreation/outdoor-recreation/f/instinct-2-series/303537/how-good-is-the-solar).
- Battery sizes: original Instinct Solar 200 mAh at 3.8 V (UNVERIFIED, battery retailer); Forerunner 955 Solar 220 to 342 mAh (UNVERIFIED, conflicting retailer data); fenix 6X 420 mAh (UNVERIFIED).
- Back-calculated harvest (ESTIMATE): Fenix 7 Solar +4 days on 18 means solar supplies about 1 percent of battery capacity per day at 150k lux-h. With an assumed 1.5 Wh battery (ESTIMATE, not verified) that is about 15 mWh/day, about 0.6 mW average. This is tiny relative to a bare cell because Power Glass passes only about 10 percent of light to the cell.

Reality check for your design: your opaque mono-Si cell sits under no screen, so it should out-harvest Garmin per cm2 by roughly 5 to 10x outdoors, but your face area is small and the cell competes with the LEDs for the face.

Not found: Seiko Solar and Samsung published cell areas or lux tables. Samsung does not appear to sell a solar wearable (not verified). Seiko solar manuals publish tables like Citizen's; I did not retrieve one.

## 2. Real-world wrist light exposure

Honest summary: published wrist data are measured by sensors that sit on the wrist and so already include sleeve occlusion and pose. I found no study that directly reports the fraction of the day a wrist sensor is covered by a sleeve (UNVERIFIED/none).

| Finding | Value | Status / source |
|---|---|---|
| Wrist sensor versus eye level | Wrist reads less than 0.5 of eye-level exposure | UNVERIFIED (search-result summary of review literature) |
| Wrist versus eye mean lux, real-life walk | 484 lux (wrist) versus 189 lux (eye), SD 1606 and 666 lux | UNVERIFIED snippet; shows wrist can read higher on average, so the ratio is highly pose-dependent |
| Indoors seated, device facing up | wrist sensors often overestimate ocular illuminance; facing down or sideways they underestimate | VERIFIED, PMC11100858 https://pmc.ncbi.nlm.nih.gov/articles/PMC11100858/ |
| Sleeve occlusion | named as a risk; not quantified | VERIFIED same paper |
| Time above 1000 lux, 7-day feasibility test (one wearer or small group) | 93.7 min/day overall; 194 min weekends; 43.6 min workdays; median 6.4 lux | VERIFIED, same paper (device may not be strictly wrist; treat as small-n) |
| Earlier San Diego cohort | median 58 min/day at 1000 lux or more | UNVERIFIED snippet (a ~1994 study, PubMed 8018787 would not load) |
| NHANES 2011 to 2014, wrist ActiGraph GT3X+, n=11,318 | for each 60 min of bright light (1000 lux or more) men get, women get 39.6 min | VERIFIED snippet, medRxiv https://www.medrxiv.org/content/10.1101/2024.04.28.24306495v1 (full text blocked, absolute minutes not read) |
| Sensor accuracy | GENEActiv read 78 percent of true at 1000 lux fluorescent, 80 percent under LED at 300 lux, and 93 percent at about 21,500 lux outdoors | VERIFIED, PMC7445795 |
| Actiwatch 2 under about 30,000 lux sun | reads about 46 percent of true | UNVERIFIED snippet |
| Actiwatch Spectrum PRO, outdoor classification | 1000 lux threshold misses 56.5 percent of outdoor events; the 6 participants wore sleeves rolled up on purpose | VERIFIED, PMC12558740 |
| Typical illuminance anchors I used | shade 2,000 to 3,000 lux (a runner's logs), 10,000 lux or less on a winter day, 120,000 lux peak sun | VERIFIED, runningwithrock.com (single user); 500 lux desk and 200 lux home are ESTIMATE |

Takeaways. (a) A typical adult sees roughly 1 hour/day of 1000+ lux at the wrist, with workdays much lower than weekends. (b) Because wrist data underread bright light, those hours could be modestly higher in truth, but sleeves can wipe out the outdoor hours entirely. (c) A dial-up cell sees whatever the wrist sees, so the shape of this distribution is the budget.

## 3. Lux to power conversion

Luminous efficacy of the irradiance reaching the cell (lux per W/m2):

| Source | lux per W/m2 | Status / source |
|---|---|---|
| Sunlight, 1 sun | about 116 to 122 (122 klux outdoors and 116 klux LED simulator at 1000 W/m2) | VERIFIED, P. Michael, IEEE DataPort, doi:10.21227/nyt0-xb17 |
| Published range across literature | 21 to 131 | VERIFIED, same dataset abstract |
| Daylight rule of thumb used here | 120 | ESTIMATE based on the above |
| White LED (4000 K) | about 300 | ESTIMATE (physics; consistent check below) |
| Fluorescent CFL | about 300 to 350 | ESTIMATE |
| Halogen/incandescent | about 15 to 20 (mostly IR) | ESTIMATE |

Consistency check (VERIFIED input): emerging indoor PV reaches 20 to 25 microwatt/cm2 at 200 lux and 120 to 150 microwatt/cm2 at 1000 lux at 35 to 45 percent efficiency (pv-magazine summary of a 2024 Nano Energy review https://www.pv-magazine.com/2024/07/17/all-indoor-pv-technologies-at-a-glance/). With 300 lux per W/m2: 200 lux is 66.7 microwatt/cm2 incident, times 0.35 = 23 microwatt/cm2. That matches, which supports using about 300 lux per W/m2 for LED.

Cell efficiency versus light level:

| Cell | Condition | Efficiency | Status / source |
|---|---|---|---|
| Poly-Si, 15 percent at 1 sun | LED 200 lux | 4.4 percent | UNVERIFIED snippet (search summary) |
| a-Si built for indoor | LED 200 lux | 7.5 percent | UNVERIFIED snippet |
| Mono-Si | LED 1000 lux | 9.3 percent | UNVERIFIED snippet |
| Mono/poly-Si | halogen 1000 lux | up to 20 percent | VERIFIED, IEEE TIM 2025 via pv-magazine https://www.pv-magazine.com/2025/05/01/artificial-light-tests-for-indoor-pv/ |
| OPV, perovskite, III-V | white LED/CFL 1000 lux | up to 14, 22, 39 percent | VERIFIED, same |
| Multi-Si cell | drops from 11 percent at 1 sun to under 2 percent at the lowest intensities | UNVERIFIED snippet |
| Reasoning | c-Si bandgap 1.12 eV is a poor match to visible-only LED light; a-Si (about 1.6 eV) matches better and holds Voc at low light; low shunt resistance kills fill factor at low light | UNVERIFIED snippet, consistent with the watch tables above |

Reusable table, power density per cm2 of active cell (mono-Si, using the efficiencies above; sun assumes 120 lux per W/m2, LED 300):

| Ambient lux | Source | Irradiance W/m2 | Assumed efficiency | mW per cm2 | mW on 5.75 cm2 (no losses) |
|---|---|---|---|---|---|
| 200 | LED | 0.67 | 4.4 % | 0.0029 | 0.017 |
| 500 | LED | 1.67 | 7 % (interpolated) | 0.0117 | 0.067 |
| 1,000 | window/daylight | 8.3 | 11 % | 0.092 | 0.53 |
| 5,000 | shade/overcast | 41.7 | 15 % | 0.625 | 3.6 |
| 20,000 | bright shade | 167 | 17 % | 2.83 | 16 |
| 30,000 | partial sun | 250 | 17.5 % | 4.38 | 25 |
| 50,000 | sun (Garmin spec) | 417 | 18 % | 7.5 | 43 |

Efficiency at 1 sun is 18.4 percent, taken from your own number: 105.9 mW / (5.75 cm2 x 100 mW/cm2). Note this conflicts with the stated 25 percent, which would give 144 mW. I used 105.9 mW (the lower, measured-looking value). Please confirm which is correct.

## 4. Revised energy model

Full numbers are in `solar-energy-model.csv` (columns: profile, cell_cm2, case, harvest_mWh_day, cover percent for each load, battery-days with 40 and 150 mAh).

Assumptions (all ESTIMATE unless marked):
- Cell: mono-Si, 18.4 percent at 1 sun (from your 105.9 mW). Efficiency per band as in the table in section 3.
- Hours per day at ambient lux (the rest of the 16 waking hours is under 50 lux and counts as zero; night is zero):

| Band | Office worker | Commuter | Outdoor enthusiast |
|---|---|---|---|
| 200 lux (home, dim) | 6 h | 5 h | 3 h |
| 500 lux (desk) | 6 h | 4 h | 1 h |
| 1,000 lux (window) | 1 h | 1 h | 0 |
| 5,000 lux (shade or overcast) | 0.7 h | 1.5 h | 3 h |
| 20,000 lux (bright shade) | 0 | 0 | 3 h |
| 30,000 lux (sun) | 0.3 h | 1.0 h | 0 |
| 50,000 lux (full sun) | 0 | 0 | 2 h |
| Hours at 1000 lux or more | 2.0 h | 3.5 h | 8 h |

Office hours at 1000 lux or more (2.0 h) are above the roughly 1 h/day the wrist studies report, so the office profile is generous. The outdoor profile is a deliberately active person (about 8 h at 1000 lux or more, 175k lux-hours of ambient light/day, close to Garmin's 150k assumption).
- Wrist factor: 0.5 applied to all ambient lux (face tilted, shadowed by the sleeve cuff, wrist reads under 0.5 of eye level per the UNVERIFIED snippet).
- Uncovered by a sleeve: 0.7 (office), 0.6 (commuter), 0.8 (outdoor). No published source; ESTIMATE.
- Optical/area factor 0.85 (bezel, cover glass, area lost to LEDs; ESTIMATE).
- Harvester (boost/charger) efficiency 0.75 (middle of 70 to 85 percent). At microwatt indoor levels real harvesters often do worse (UNVERIFIED), which would make the office case worse than shown.
- Charge efficiency 0.95.
- A "ceiling" case drops the wrist factor, sleeve factor and optical factor to 1 and uses 0.85 harvester efficiency, to show the best case.

Results, base case. Cover percent = harvest divided by load for three loads (3.3, 5.7, 14.4 mWh/day).

| Profile | Cell cm2 | Harvest mWh/day | Cover 3.3 | Cover 5.7 | Cover 14.4 |
|---|---|---|---|---|---|
| Office | 1.5 | 0.61 | 19 % | 11 % | 4 % |
| Office | 3 | 1.23 | 37 % | 22 % | 9 % |
| Office | 5.75 | 2.35 | 71 % | 41 % | 16 % |
| Commuter | 1.5 | 1.49 | 45 % | 26 % | 10 % |
| Commuter | 3 | 2.98 | 90 % | 52 % | 21 % |
| Commuter | 5.75 | 5.71 | 173 % | 100 % | 40 % |
| Outdoor | 1.5 | 9.23 | 280 % | 162 % | 64 % |
| Outdoor | 3 | 18.46 | 559 % | 324 % | 128 % |
| Outdoor | 5.75 | 35.37 | 1072 % | 621 % | 246 % |

Ceiling-case harvest (no sleeve or wrist penalty, 5.75 cm2): office 9.4, commuter 26.7, outdoor 124 mWh/day. Even this ceiling does not cover the 14.4 load for an office worker (65 percent).

Battery-days with solar (base case), versus no solar. Battery 40 mAh x 3.7 V = 148 mWh; 150 mAh = 555 mWh. No-solar life: 148 mWh gives 45, 26 and 10 days at the three loads; 555 mWh gives 168, 97 and 38 days. "inf" means harvest exceeds load.

| Profile, cell | 3.3 mWh/day, 40 mAh | 5.7, 40 mAh | 14.4, 40 mAh | 14.4, 150 mAh |
|---|---|---|---|---|
| Office 1.5 | 55 d (vs 45) | 29 (vs 26) | 11 (vs 10) | 40 (vs 38) |
| Office 5.75 | 156 (vs 45) | 44 (vs 26) | 12 (vs 10) | 46 (vs 38) |
| Commuter 3 | 463 | 54 | 13 | 49 |
| Commuter 5.75 | inf | inf | 17 | 64 |
| Outdoor 1.5 | inf | inf | 29 | 107 |
| Outdoor 3+ | inf | inf | inf | inf |

Verdict by profile:
- Office worker: partial at best (4 to 71 percent of load). Added battery life is 1 to 8 percent at the highest load and up to roughly 3x at the lowest load with the largest cell. Marginal; indoor light adds close to nothing (a full 6 h at 500 lux on 5.75 cm2 gives about 0.2 mWh before the other factors).
- Commuter: meaningful. 1 h of sun is the whole story. Full cover of the low and mid loads with 5.75 cm2, 40 percent of the high load.
- Outdoor enthusiast: covers everything with 3 cm2 or more; even 1.5 cm2 covers the low and mid loads.
- Sanity check against Garmin: Garmin's 150k lux-h/day gives about +22 percent energy on a smartwatch with a 10 percent transmission cell, which I back-calculated at about 15 mWh/day (ESTIMATE). My model's outdoor profile gives 9 to 35 mWh/day for a cell with no screen over it. That is the same order of magnitude, which is reassuring but not proof.

Also note the most uncertain inputs: the sleeve fraction, sun hours, and the wrist factor. Moving sun hours from 1 to 0.3 h/day roughly cuts the commuter result by two thirds.

## 5. Conclusions and design recommendations

Conclusions
1. Do not count indoor light. Under 500 lux the cell contributes well under 0.1 mW, which is less than the always-on load of about 0.07 mW (1.6 mWh/day) in most cases.
2. Solar is a bonus for people who spend time in sun with the wrist exposed. For desk workers it is a rounding error against a 40 to 150 mAh battery.
3. Cell area matters less than exposure hours. Going from 3 to 5.75 cm2 doubles harvest but also takes face area from the display.

Recommendations
1. Decide by wearer. If the watch is mostly a daily indoor display piece, skip solar and spend the face area on LEDs or a bigger battery (an extra 10 mAh costs less than the harvester IC and the cell). If you or your target users are outdoors for 1 h or more daily with bare wrists, include a 3 cm2 cell with a low-quiescent harvester (nA-class boost charger with a battery-protection path); the 1.5 cm2 option rarely beats the harvester's own overhead indoors.
2. Pick a wide, sun-weighted option, not an indoor-optimised one. Because mono-Si loses most of its efficiency indoors (4 to 9 percent versus 18 percent at 1 sun), either use mono-Si for sun and accept zero indoor gain, or use an indoor-optimised a-Si cell if indoor life matters (Casio and Citizen both do this).
3. Make solar optional in hardware: route the cell to a connector or footprint pads, add a footprint for a charge IC, and ship a version with it unpopulated. Include a current-sense path.

What to measure on a prototype
- Cell short-circuit current and Voc at 200, 500, 1000 lux (known LED lamp and a lux meter) and in a sunny window and outdoors, with the cell mounted behind the real cover glass and bezel. This replaces my efficiency table.
- Wear the watch (cell plus a logging photodiode or a coin-size logger such as a phone lux app on the wrist) for 2 weeks and log lux versus time to get your real hours per band and sleeve-occluded fraction.
- Harvester efficiency and quiescent current at 10, 100 and 1000 microamp inputs (a boost IC that needs more than 100 microamp to start would kill the indoor case).
- Real watch load: current in sleep, in a wake-up, and the self-discharge of the actual LiPo over a week.

## Sources

- Citizen manual: https://www.citizenwatch-global.com/support/pdf/e81x_e820_e821/e.pdf
- Casio module 5454: https://support.casio.com/global/en/wat/manual/5454_en/VPCVSYfkxmgtjs.html
- Garmin blog: https://www.garmin.com/en-US/blog/general/solar-charging-in-garmin-smartwatches/
- Garmin press release: https://www.garmin.com/en-PH/newsroom/press-release/news-2020-aug-solar/
- Fenix lux-hours review: https://runningwithrock.com/fenix-solar-charging-lux-hours/
- Garmin solar technology (the5krunner): https://the5krunner.com/2025/11/27/garmin-solar-technology-power-glass-unlimited-battery-mip
- Instinct 2 forum: https://forums.garmin.com/outdoor-recreation/outdoor-recreation/f/instinct-2-series/303537/how-good-is-the-solar
- Wrist-worn IoT light node: https://pmc.ncbi.nlm.nih.gov/articles/PMC11100858/
- GENEActiv accuracy: https://pmc.ncbi.nlm.nih.gov/articles/PMC7445795
- Actiwatch indoor/outdoor: https://pmc.ncbi.nlm.nih.gov/articles/PMC12558740/
- NHANES light: https://www.medrxiv.org/content/10.1101/2024.04.28.24306495v1
- Lux to irradiance: https://ieee-dataport.org/node/2380
- Indoor PV overview: https://www.pv-magazine.com/2024/07/17/all-indoor-pv-technologies-at-a-glance/
- Indoor PV tests: https://www.pv-magazine.com/2025/05/01/artificial-light-tests-for-indoor-pv/
