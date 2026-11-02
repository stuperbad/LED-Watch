# USB-C mock-up: assembly files (2026-11-02, from `LED Watch - USB-C.kicad_pcb` saved 04:21 plus the final clean-up)

| File | What |
|---|---|
| `assembly/BOM.csv` | 32 lines, 204 placed parts, JLCPCB / LCSC numbers (made by `tools/make_bom_cpl.py`) |
| `assembly/CPL.csv` | placement: 178 top, 26 bottom (the two cell pads SC1+ / SC1- are pads, not parts) |
| `assembly/pos_raw.csv` | the KiCad position export both are made from |
| `netlist.xml` | KiCad XML netlist of `LED Watch - USB-C.kicad_sch` (206 parts; the "annotation errors" warning of kicad-cli is the same as for rev B) |

| `gerbers/`, `LED Watch - USB-C - gerbers.zip` | gerbers + drill of the board saved 04:50 (4 copper layers, mask, silk, edge; protel names, no paste, same set as rev B), 42.1 x 51.28 mm |

**Not here yet:** a JLCPCB PCBA quote (needs a signed-in JLCPCB session). **Not verified:** the rotation of U5, D50 and J2 in JLCPCB's placement preview (`ROT_FIX` in `make_bom_cpl.py` only knows U2 and U4): check the pin-1 marks there. Stock on 2026-11-02 covers 5 boards for every line (lowest: AVR128DB48 33, BQ25570 494, 10 uH inductor 160, piezo 918).
