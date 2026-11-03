# Revision C in one page: what changed and why (notes for the design review, 2026-11-02)

## The one big change: USB-C replaces the pogo programming pads
- **Programming:** the chip is still programmed over UPDI, but now through the USB-C receptacle (J2, GCT USB4110, on the back at the rim, 3 o'clock). Both SBU pins are tied together and carry the UPDI wire: SBU -> R72 (1 k) -> the MCU's UPDI pin, with a BAT54WS clamp (D50) to +3V3, because VBUS sits right next to the SBU pins in the receptacle and a 5 V fault must not reach the MCU pin. Ground comes from the cable. USB data pins (D+ / D-) are not used.
- **Charging:** the same connector charges the battery. VBUS -> BQ21040 (U5) -> BATT, 54 mA (ISET 10 k), TS 10 k to ground (no thermistor), 1 uF in and out, CC1 / CC2 5.1 k pull-downs so any USB-C source gives 5 V. This is in addition to the solar harvester (BQ25570).
- **Why this and not pogo pads or a Tag-Connect footprint** (owner's reasoning, to say in your own words):
  - one connector for charging and programming, on the rim, nothing extra on the face of the watch;
  - a standard cable, no custom pogo jig and no dedicated programming cable / footprint with alignment holes;
  - the battery can be charged without bright light, which the solar cell alone cannot promise indoors;
  - the revision B pogo row was only 4 pads at 1.27 mm and needed a jig to hold it.
- **Honest trade-offs:** the cable must carry the SBU wires (not every charge-only cable does; checklist H4); the receptacle is a tall part on a watch rim and an open port (check part height and sweat / dust; ENIG finish helps); RESET is no longer wired out, so there is no high-voltage recovery if UPDI were ever disabled by a fuse (we do not do that; the firmware pulls PF6 up); 7 more BOM lines (26 -> 33).

## Other changes since the board the reviewer saw (revision B)
- **Fixed:** the solar cell pad was on a different net than the harvester input (found 2026-11-02 with the schematic parity check); now on `/SOLAR_IN`.
- **Layout:** outer LED-ring traces pulled in 0.29 mm from the board edge; the back-side area around the MCU and crystal cleaned up by hand; keep-out zones (crystal, MCU core, harvester core, IMU) now checked by a script, not by DRC; silkscreen reduced to numbers, weekday letters, mode labels, polarity marks and pin-1 marks (numerals 12 / 3 / 6 / 9 now 1.2 mm).
- **Checks:** DRC 0 errors / 0 unconnected, parity with the schematic: every connected pad matches; what it lists are pads the board leaves without a net (unused MCU / connector / IMU pins, and the far-side duplicate pads of each button, which carry no copper; checked against the C&K / Littelfuse KMR2 data sheet: its electrical diagram joins the two same-numbered terminals inside the switch, so wiring one pad of each pair is correct, see `DECISION-LOG.md` 2026-10-14), JLCDFM run (remaining red items are 0.10 mm track width and 0.15 mm via ring by design, and 229 pairs of traces at exactly 0.100 mm: JLCPCB's stated minimum for 4 layers is 0.09 mm).
- **Quote:** JLCPCB, 5 assembled boards, both sides, 3-4 day build, **$326.19 before shipping and duties** (quoted before D51 was added: one more extended part, to be re-quoted; nothing ordered, nothing in the cart for revision C).
- **LEDs:** the three LED parts were reviewed (`LED-SELECTION.md`) and kept; ring brightness will be balanced in firmware.

## Please look at (questions for the review)
1. **Power block:** two chargers on one battery net (BQ25570 from the solar cell, BQ21040 from USB): do they behave when both are active? Is the BQ25570 over-voltage setting above the BQ21040's 4.2 V termination?
2. **USB-C block:** CC pull-downs, SBU clamp and series resistor, VBUS -> charger path, ESD: one 5 V TVS diode (D51, UMW UDD32C05L01) now clamps VBUS to ground, next to D50 in the corner above the charger, on the VBUS line about 8.4 mm of 0.1 mm copper from the receptacle's pins; nothing on CC / SBU beyond the existing SBU clamp (is more wanted?).
3. **Crystal** (32.768 kHz, moved 1.2 mm from the MCU), **battery polarity** and the JST plugs.
4. **Programming day:** powering the board from the programmer while the battery is attached (`BRING-UP.md`).

Details: `DECISION-LOG.md` (2026-11-01 and 2026-11-02), `LAYOUT-AUDIT.md`, `PRE-ORDER-CHECKLIST.md` (section H), `../hardware/REVISIONS.md`.
