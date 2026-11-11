# Data sheets for every part on the board (revision C)

Rule (owner, 2026-11-11): every part on the board has its data sheet, always. The PDFs are the manufacturers' files and are **not kept in git** (they sit on the author's disk; the section "Where to download them" below lists the sources). Only the table, the page snapshots and a few older files are tracked. The files below are the ones for the exact parts JLCPCB matched in the BOM (LCSC numbers), plus the chip data sheets.
Blocked sites: LCSC's PDF links only answer a real browser, so they are fetched through the owner's Chrome (open `https://www.lcsc.com/datasheet/Cxxxxx.pdf`, download button).

| Part (LCSC) | Where used | File |
|---|---|---|
| AVR128DB48 (C1019768) | U1 | `AVR128DB28-32-48-64-DS40002247B.pdf`, `AVR128DB.txt` |
| BQ25570 (C506250) | U4 | `bq25570.pdf`, `.txt` |
| BQ21040 (C202311) | U5 | `bq21040.pdf`, `.txt` |
| LIS2DW12 (C189624) | U2 | `LIS2DW12.pdf`, `.txt` |
| KXOB25-05X3TF | SC1 solar cell | `KXOB25-05X3TF-DATASHEET.pdf`, `.txt` |
| TinyCircuits ASR00011 | LiPo | `TinyCircuits-ASR00011-70mAh-datasheet.pdf`, `.txt` |
| GCT USB4110-GF-A (C5143397) | J2 | `GCT-USB4110.pdf` (GCT drawing; the STEP model is `hardware/3dmodels/usbc_gct_usb4110_gct.step`, not committed) |
| JST SM02B-SRSS-TB (C160402) | J1, J1B | `JST-SH.pdf`, `JST-SM02B-SRSS-TB-LCSC-sheet.pdf` |
| Murata PKMCS0909E4000-R1 (C910763) | BZ1 | `Murata-PKMCS0909E4000-R1.pdf`, `Murata-PKMCS0909E4000-R1-LCSC-sheet.pdf`; the full spec JGB40-1594B is not here yet: murata.com showed "under maintenance" on 2026-11-11, fetch it later |
| C&K / Littelfuse KMR221GLFS (C72443) | SW1, SW2 | `Littelfuse-CK-KMR2-datasheet.pdf`, `CK-KMR2.pdf`, `CK-KMR2-LCSC-contact-options.pdf` |
| Seiko SC-32S 12.5 pF (C97606) | Y1 | `Seiko-SC-32S-crystal.pdf` |
| Taiyo Yuden CBC3225T220MR (C90320) | L1 | `TaiyoYuden-CBC3225T220MR.pdf` |
| TDK NLCV32T-100K-PFR (C74563) | L2 | `TDK-NLCV32-inductor.pdf` |
| Panjit BAT54WS (C304155, "BAT54WS_R1_00001") | D50 | `Panjit-BAT54WS.pdf` (also `BAT54WS-Diodes-Inc.pdf`, another maker's) |
| UMW UDD32C05L01 (C19185929, JLCPCB's part is UMW's, not Yageo's) | D51 | `UMW-UDD32CxxL01-TVS.pdf` (also `Yageo-UDD32CxxL01.pdf`, the original maker's sheet for the same part name) |
| Xinglight XL-0201UWC (C965789), 0.65 x 0.35 x 0.4 mm | S0-S59 | `Xinglight-XL-0201UWC-LED-0201.pdf` |
| Xinglight XL-1005UWC (C20613596), 1.0 x 0.5 x 0.4 mm | M0-M59, IND1-7 | `Xinglight-XL-1005UWC-LED-0402.pdf` |
| Kento KT-0603W (C2290), 1.6 x 0.8 x 0.6 mm | H1-H12 | `Kento-KT-0603W-LED-0603.pdf` |
| Samsung CL05B104KO5NNNC, CL05A475MP5NRNC, CL05B103KB5NNNC, CL05A105KA5NQNC (C1525, C23733, C15195, C52923) | C10-12, C30-31, C50-53, C55-56 | `Samsung-MLCC-catalog-CL-series-2015.pdf` (the catalogue LCSC links for all four) |
| Samsung CL05A106MQ5NUNC (C15525) | C13 | `Samsung-CL05A106MQ5NUNC-10uF.pdf` |
| Yageo CC0402JRNPO9BN180 (C106202) | C20, C21 | `Yageo-NP0-ceramic-capacitors.pdf` |
| Yageo CC0805MKX5R6BB226 (C109314) | C54 | `Yageo-X5R-ceramic-capacitors.pdf` |
| UNI-ROYAL 0402WGF series (C25091, C25744, C423137, C423173, C25905, C11702) | R1-R12, R20, R21, R57-R59, R61-R67, R68-R72, R55, R56 | `UniRoyal-thick-film-chip-resistors.pdf` |
| Walsin WR04W6494FTL (C172111) | R50, R53 | `Walsin-WR04-chip-resistors.pdf` |
| Ralec RTT025114FTH (C166448) | R51 | `Ralec-RTT-chip-resistors.pdf` |
| Yageo RC0402FR-071M47L, -073M74L (C477211, C477705) | R52, R54 | `Yageo-RC_L-chip-resistors.pdf` |
| older / reference | | `ATmega169P-doc8018P-rev08-10.pdf`, `bq25504.pdf` |

Open: the Murata full spec (site down), and a check that each LCSC link still points at the part in the BOM when the BOM changes.

## Where to download them
Links collected while fetching the files on 2026-11-11 (not re-checked one by one; manufacturers move files, so if one is dead search the part number on the maker's site). The LCSC pattern `https://www.lcsc.com/datasheet/<LCSC number>.pdf` (for example `C1525`) only answers a real browser, not scripts.

| Part | Source |
|---|---|
| BQ25570 (revision G, March 2019, the one the layout notes quote) | https://www.ti.com/lit/ds/symlink/bq25570.pdf |
| BQ21040 | https://www.ti.com/lit/ds/symlink/bq21040.pdf |
| LIS2DW12 | https://www.st.com/resource/en/datasheet/lis2dw12.pdf |
| AVR128DB28/32/48/64 | https://www.microchip.com/content/dam/mchp/documents/MCU08/ProductDocuments/DataSheets/AVR128DB28-32-48-64-DataSheet-DS40002247.pdf |
| KXOB25-05X3TF solar cell | https://anysolar.biz/wp-content/uploads/2026/09/KXOB25-05X3TF-DATASHEET.pdf |
| TinyCircuits ASR00011 LiPo | https://www.mouser.com/datasheet/2/855/TinyCircuits_ASR00011-1323546.pdf |
| GCT USB4110 drawing | https://gct.co/files/drawings/usb4110.pdf |
| JST SH series | https://www.jst-mfg.com/product/pdf/eng/eSH.pdf |
| C&K KMR2 switch | https://www.ckswitches.com/media/1479/kmr2.pdf |
| Murata PKMCS0909E4000-R1 (flyer; the full spec link below was being fetched, check it) | https://www.murata.com/products/productdata/8796834160670/PKMCS0909E4000-R1.pdf and https://www.murata.com/products/productdata/8801054228510/SPEC-PKMCS0909E4000-R1.pdf |
| Seiko SC-32S crystal | https://www.sii.co.jp/hubfs/SC-32S_Leaflet_e_26.pdf (or LCSC C97606) |
| Xinglight XL-0201UWC (LCSC C965789) | https://www.lcsc.com/datasheet/C965789.pdf |
| Xinglight XL-1005UWC (LCSC C20613596) | https://www.lcsc.com/datasheet/C20613596.pdf |
| Kento KT-0603W (LCSC C2290) | https://www.lcsc.com/datasheet/C2290.pdf |
| Samsung CL05 capacitors (LCSC C1525, C23733, C15195, C52923, C15525) | https://www.lcsc.com/datasheet/C1525.pdf and the same pattern for the others |
| UMW UDD32C05L01 (LCSC C19185929) | https://www.lcsc.com/datasheet/C19185929.pdf |
| Walsin WR04 (LCSC C172111) | https://www.lcsc.com/datasheet/C172111.pdf |
| UNI-ROYAL 0402 resistors (LCSC C25091, C25744, C11702 and others) | https://www.lcsc.com/datasheet/C11702.pdf and the same pattern for the others |
| C&K KMR221 (LCSC C72443) | https://www.lcsc.com/datasheet/C72443.pdf |
| Panjit BAT54WS (LCSC C304155), Taiyo Yuden CBC3225T220MR (C90320), TDK NLCV32T-100K-PFR (C74563), Yageo capacitors and resistors, Ralec RTT025114FTH (C166448) | the LCSC pattern with the number from the table above |
