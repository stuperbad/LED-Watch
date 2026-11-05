# Questions for James (reviewer) - revision C, solar single-colour LED watch

Plain-language version of section 8 of `DESIGN-REVIEW-REV-C.md` (that file has the numbers and pictures). Written 2026-11-04.

## Who is who (the part labels on the board)

| Label | What it is |
|---|---|
| U1 | the microcontroller (AVR128DB48), the brain |
| U2 | the motion sensor (LIS2DW12) |
| U4 | the solar charger chip (BQ25570): takes the solar cell's tiny power, charges the battery, and also makes the 3.3 V supply |
| U5 | the USB charger chip (BQ21040) |
| L1, L2 | the two coils (inductors) next to U4: L1 for the solar side, L2 for the 3.3 V supply |
| C52 | the 4.7 uF "storage" capacitor right next to U4's battery pin |
| C53 | a small 10 nF "bypass" capacitor that should sit beside C52 (it does not, see question 1) |
| C50 | the 4.7 uF capacitor on U4's solar input |
| C54 | the 22 uF capacitor on the 3.3 V output |
| C10, C11, C13 | the capacitors at the microcontroller's three power pins |
| J2 | the USB-C connector (charging and programming) |
| D51 | static-protection diode on the USB 5 V pin; D50 clamp diode on the programming wire; R72 1 kohm in the programming wire; R68 / R69 5.1 kohm resistors that tell a charger "I am a device" |

## The four questions

Picture of where each one is on the board: `review-areas-top-and-bottom.png` (orange 1, green 2, purple 3 here = the USB-C corner), close-up of the back: `review-areas-back-zoom.png`.

**1. Are the solar-charger parts close enough to U4?**
TI's data sheet says "as close as possible" and gives no numbers. Ours: storage capacitor C52 1.3 mm (good), solar input capacitor C50 7.8 mm, bypass capacitor C53 8.1 mm (its copper is 20 mm, it loops round the chip), coil L1 5.7 mm, coil L2 9.4 mm. The back of the board is only a 4.8 mm strip between the two batteries and it is full; we tried moving things and each option broke something else (details in the design review, picture `cbyp-8p4mm.png`).
*Ask:* acceptable for a first board? If he would move one thing, which?
*Our answer if asked:* acceptable; measure the 3.3 V output and charging current on the bench.

**2. The microcontroller's three power capacitors are 1.4, 2.2 and 4.8 mm from their pins.**
His rule was about 1 mm with no via in between. The chip is boxed in by the crystal keep-out and the LED fan-out; at 4 MHz this is common practice.
*Ask:* acceptable, or does he want one moved?

**3. The USB-C corner: anything he would change?**
It holds the static diode on 5 V (D51), the two 5.1 kohm resistors, the 1 kohm in the programming wire with its clamp diode (D50), and the grounded shell. One small point to raise: the clamp diode D50 goes to the 3.3 V supply; the safer connection is the battery supply (a damaged cable putting 5 V on the programming wire could push current into the 3.3 V supply).
*Ask:* happy with the corner? Move the clamp to the battery supply?

**4. LED-ring pad exits that are not perfect.**
On the LED ring some parts sit at odd angles, so the first small trace piece cannot leave exactly along the part's axis and still end on a 45-degree line. About 20 pads are more than 25 degrees off the axis (mostly the ring LEDs, a few resistors, the coil L2 and the crystal). The owner has already redrawn the indicator row and the crystal capacitors.
*Ask:* close enough for a prototype, or does he want the first piece forced along the axis?

## Already decided (no need to ask)

- No extra static protection on the programming wires or the buttons for the prototype (owner's call, 2026-11-04). Revisit before boards go to other people.
- Inner ground-layer gap: set to 0.1 mm (JLCPCB can do 0.09 mm), as he suggested; checked in the file and in a picture (`in2-gap-before-after.png`): the clear ring around each via is visibly smaller.
- Vias: searched every non-ground, non-LED-ring net for vias that only hop over their own wire; the owner's hand clean-up had already removed the easy ones, 1 more hop and 1 leftover via were removed (345 -> 342); the other 119 vias are needed to cross other traces.
- No cut-out in the inner ground layer under the divider resistors (it would hurt other signals' return path; the data sheet's warning is about surface leakage).
- The crystal's two traces leave each pad sideways (both its capacitor and the chip pin are on the same pad side); the owner will redraw them to leave along the crystal's axis and fork afterwards.
- The crystal block sits 1.2 mm further from the chip than before; he can look at it.

## Not questions: things to do at the bench before power-up (BRING-UP-TESTS.md)

Meter the battery wires first (polarity is unknown until measured; no reverse protection). Plug the second battery in only at the same voltage as the first. Use a USB-C cable that carries the sideband wires (many charge-only cables do not) so the programming works.

**Smaller points, only if he has time** (details in the design review, section 7)
- The buck's switching node LBUCK used to run next to the high-impedance VOUT_SET divider tap; it is now on an inner layer with the ground plane in between.
- Vias in the exposed ground pads of the MCU (5) and the BQ25570 (1): fill them or leave them open?
- USB-C programming needs a cable with the SBU wires; there are no separate programming pads.
- Seven small parts overlap the battery outline; to be settled with a real battery.
