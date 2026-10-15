"""Column series resistor (R1-R12) for the single-colour watch: LED current vs battery voltage, LED forward voltage and resistor value.
Circuit (one lit LED): VDD (system rail, = battery 3.3-4.12 V in the solar variant) -> MCU source pin (drop) -> column resistor R -> LED anode ... LED cathode -> MCU sink pin (VOL) -> GND.
  I = (VDD - Vt) / (Rd + R_src + R_snk + R)         Vf(I) = Vt + Rd*I
Numbers and where they come from (ESTIMATES marked):
  VDD       3.3 V (BQ25570 BAT_OK falling threshold) / 3.7 V nominal / 4.12 V (BQ25570 over-voltage stop, resistors R50/R51)
  Vt, Rd    white LED knee 2.45 / 2.60 / 2.75 V (min / typ / max), dynamic resistance 30 ohm   ESTIMATE: Vf 2.6-3.3 V at 5-20 mA from the LCSC data sheets (Watch-Power-Calculator 'LED types');
            at 1-5 mA Vf is about 0.15-0.3 V lower, so the 'max' column is the dim, high-Vf LED
  R_src     source pin drop: AVR128DB data sheet VOH >= VDD - 0.7 V at IOH = 6 mA (VDD = 3 V)  -> 117 ohm worst case, ~60 ohm typical (graph 40-80)
  R_snk     sink pin drop: VOL <= 0.6 V at IOL = 10 mA (VDD = 3 V) -> 60 ohm worst case, ~35 ohm typical
Limits: source pin <= 6 mA (data sheet test point); 0201 LEDs are typically rated 5 mA max (ESTIMATE: the exact LED part is not chosen yet); a row sink carries every lit LED of that row (<= 10 mA).
"""
RD, RSRC, RSNK = 30.0, 60.0, 35.0
vdd = (3.3, 3.7, 4.12)
vt = {"low-Vf": 2.45, "typ-Vf": 2.60, "high-Vf": 2.75}
print("peak LED current in mA (typ pin drops)")
print(f'{"R":>5} | ' + " | ".join(f"{n} @{v:.2f} V" for n in vt for v in vdd))
for R in (100, 120, 150, 180, 220, 270, 330):
    row = []
    for n, t in vt.items():
        for v in vdd:
            row.append(f"{max(v - t, 0) / (RD + RSRC + RSNK + R) * 1000:5.1f}")
    print(f"{R:5d} | " + " | ".join(f"{x:>16}" for x in row))
print()
worst_hi = lambda R: (4.12 - 2.45) / (RD + RSRC + RSNK + R) * 1000
worst_lo = lambda R: (3.3 - 2.75) / (RD + 117 + 60 + R) * 1000
for R in (150, 180, 220, 270):
    print(f"R={R}: highest current (4.12 V, low-Vf LED, typical pins) {worst_hi(R):.1f} mA | lowest (3.3 V, high-Vf LED, worst pins) {worst_lo(R):.1f} mA")
need = (4.12 - 2.45) / 0.005 - (RD + RSRC + RSNK)
print(f"\nResistor needed to keep the worst case at <= 5 mA: {need:.0f} ohm -> next E24 value 220 ohm")
