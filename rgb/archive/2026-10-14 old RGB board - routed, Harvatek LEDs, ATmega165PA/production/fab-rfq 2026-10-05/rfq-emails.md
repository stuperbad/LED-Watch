# Quote-request emails — LED Watch (RGB prototype)
Drafts for Evan to review and send from his own email. Nothing has been sent.

Attach to every email (all in `Desktop\LED-Watch\fab-rfq\`):
- `LED-Watch-gerbers.zip` — fabrication files (4-layer, 42.87 x 50.28 mm)
- `LED-Watch-BOM.csv` — bill of materials with manufacturer part numbers and DigiKey numbers
- `LED-Watch-CPL-jlcpcb.csv` — placement coordinates (145 parts; Tag-Connect footprint J1 is not a part)

Before sending, fill the two TBD lines in the BOM if you've decided them (D1–D4 LED colour; C1/C2 value). Candidates are listed in the BOM.

Where to send (verify each on the company's own contact/quote page first; I did not look up direct email addresses):
- Bittele Electronics — https://www.7pcb.com (prototype turnkey + consigned, fine-pitch/0201 capable)
- Advanced Circuits — https://www.4pcb.com (quickturn prototype assembly)
- MacroFab — https://www.macrofab.com (US, buys from DigiKey, online RFQ portal)
- Screaming Circuits — https://www.screamingcircuits.com (US, prototype assembly, consigned/turnkey)
- PCBWay — https://www.pcbway.com (turnkey/kitted/combo)

---

## Email A — turnkey (they buy the parts)

**Subject:** Quote request: 4-layer prototype PCB + assembly, 5 pcs, fine-pitch LEDs (turnkey)

Hello,

I'm an artist/engineer building a small prototype LED watch and I'd like a quote for fabrication and assembly of 5 boards (a quote for 2 and for 10 would also be useful), turnkey if you can source the parts, or kitted if you can't.

**Board:** 4-layer FR-4, 1.6 mm, 42.87 x 50.28 mm single board (irregular outline with two strap lugs), ENIG, 0.1 mm trace/space, 0.2 mm via drill (0.4 mm pad). Gerbers attached.

**Assembly:** SMT, top side (132 small LEDs, one QFN-64, one LGA-14, 0201 passives, a 3.2x1.5 crystal, two tactile switches, one JST SH connector). The one bottom-side part is a Keystone 3034 coin-cell holder. I'm happy to hand-solder that one if two-sided assembly adds much cost.

**The hard part, so you can price it honestly:**
- 132 x Harvatek B39D3RGB-F6C0001HOU1930 — 0.83 x 0.83 mm RGB LED, 4 pads of 0.3 x 0.3 mm on a 0.5 mm pitch. DigiKey 3147-B39D3RGB-F6C0001HOU1930CT-ND (in stock, roughly 20,000; the part is marked obsolete but stocked).
- Several LEDs are rotated at 90-degree steps; the LEDs are polarity-sensitive. (A future revision may place LEDs at arbitrary angles in 5-degree steps around a ring: can your machines and your placement-data process handle non-90-degree rotations accurately, and is there any surcharge?)
- 0201 passives and 0.5 mm pitch QFN/LGA.

**Please tell me:** your price at 2 / 5 / 10 boards, setup/NRE and stencil costs, lead time, whether you'll source from DigiKey (and your parts-handling fee), whether you can place the 0.83 mm LED reliably, and any design-for-assembly changes you'd recommend (pad sizes, fiducials, paste aperture, panel/edge-rail requirements). I'd rather hear about a problem now than after the build.

Files attached: Gerbers (zip), BOM (csv, with manufacturer part numbers), centroid/placement (csv).

Thank you,
Evan Finkle
evanfinkle@gmail.com

---

## Email B — consigned (shorter; for houses that prefer to place parts you supply)

**Subject:** Assembly-only quote: 5 prototype boards, parts supplied by me

Hello,

Could you quote assembly only for 5 prototype boards (bare PCBs and parts supplied by me, with the usual attrition spares)? Details are above/attached: 132 x 0.83 mm RGB LEDs on a 0.5 mm pitch, one QFN-64, one LGA-14, 0201 passives. I'd like to know your setup fee, per-placement cost, stencil cost, lead time, and what you need from me (BOM format, spares, reel vs cut tape, how you want the coin-cell holder handled).

Thanks,
Evan Finkle
evanfinkle@gmail.com

---

## Notes for Evan
- If a house says they can't handle the 0.83 mm LED, that's useful: it's a reason to redesign around a larger LED (the single-color 0402/0603 direction), not a failure.
- The BOM still has candidate parts (flagged CANDIDATE). The BMI160 has been replaced with the BMI270 in the design.
- Parts availability at JLCPCB is a separate question being researched: see `jlc-alternatives.md` when it appears.
