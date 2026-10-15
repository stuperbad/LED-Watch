# Evaluation: Anysolar IXOLAR SolarBIT KXOB081K06TF (the cells Evan already owns)
2026-10-06. Source: Anysolar datasheet (Rev. Jun. 2026, marked "Preliminary") https://anysolar.biz/wp-content/uploads/2026/09/KXOB081K06TF-DATASHEET.pdf and the DigiKey listing (2994-KXOB081K06TF-TR-ND). Label on Evan's photo: "IXOLAR KXOB081K06TF R3.0".

## Datasheet facts (VERIFIED)
- Monocrystalline silicon, 6 cells in series (2 columns x 3 rows), efficiency typ. 25% (measured at wafer level), fill factor > 70%.
- Size **23 (W) x 25 (L) x 1.2 +/-0.3 mm**, 1.2 g. (DigiKey lists 1.5 mm.) Solder pads on the BACK: two 12 mm-wide pads, one at each 25 mm end (+ top, - bottom).
- At 1 sun (100 mW/cm2, AM1.5, 25 C): Voc 4.15 V, Isc 33.7 mA, Vmpp 3.35 V, Impp 31.6 mA, **Pmpp 105.9 mW**. Voc temp coeff -10.44 mV/K.
- Voc vs irradiance (graph, per cell): ~0.69 V at 1000 W/m2, ~0.61 V at 100 W/m2, still ~0.5 V near 1-3 W/m2 -> x6 cells ~ 3.0-3.7 V at dim light, so it can reach a LiPo-charging voltage with a boost/MPPT harvester even in modest light. (Power-vs-lux is NOT given in the datasheet.)
- Surface-mount, tape & reel (1,000/reel), MSL 3, operating -40 to +90 C.
- **Reflow:** only with LOW-temperature Sn42/Bi58 paste (e.g. Tamura TLF-401-11), 220 C peak, >175 C for ~50 s. Otherwise hand-solder: 5 s below 400 C. Cleaning: lukewarm water only; IPA and detergents can damage the film. A standard JLCPCB lead-free profile would exceed this -> treat as a hand/adhesive-attached part after assembly.
- DigiKey: $6.59 @1, 2,754 in stock, 15-week lead time (as seen 2026-10-06). Siblings: KXOB061K08TF (5.53 V, 105.8 mW), KXOB081K06F (non-thin), SM101K07TF (4.84 V, 154 mW), KXOB25-xx strips.

## Does it fit this watch?
No, not in the free centre. 23 x 25 mm needs a free circle ~34.6 mm across (its diagonal + clearance). With white-LED rings around it the board would be ~48-53 mm (0402/0402/0201: 48.3; 0603/0402/0402: 51.0; 0805/0603/0402: 53.5), far above the 30-37 mm boards under study. The largest square that fits the current free centres: 9.7 mm (13.7 mm free circle) up to 12.7 mm (18.0 mm free circle).

## Power perspective
Scaling by area, a ~12 mm square of the same cell technology would give roughly 25-30 mW at 1 sun (ESTIMATE; consistent with the KXOB25 strips at ~26 mW for ~16 cm2... see solar-power-research.md). Outdoors that is still far more than the watch needs; indoors mono-Si is weak (UNVERIFIED lux performance). The cell Evan owns would be dramatically oversized for energy, so the constraint is purely physical size.

## Ways forward
1. Use Evan's two cells for a MEASUREMENT experiment (outdoor/indoor charging of a LiPo through a harvester IC) to settle the real wrist-worn numbers.
2. Use a smaller cell: Anysolar KXOB25 strips (~22-23 x 7-8 mm) don't fit a circle either; a custom 12 mm cell would be a custom order (ask Anysolar techdevelop@anysolar.biz); other makers: Panasonic AM-1606C (15x15 mm indoor amorphous, in stock), Epishine (indoor OPV, min 25x29 mm module), Powerfilm (large), Seiko/Solems (indoor amorphous) - see solar-power-research.md.
3. Change the form factor: a non-round (rounded-square / rectangular) watch face where a 23x25 cell sits beside or inside the LED ring.
4. Put the cell on a strap section or a clip-on module instead of the face.
5. Keep solar optional: baseline pad/USB-charged LiPo, solar pads reserved.
