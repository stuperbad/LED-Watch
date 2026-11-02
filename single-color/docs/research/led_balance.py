"""led_balance.py : brightness balance of the three LED rings (hour 0603 / minute 0402 / second 0201) of the single-colour watch, 2026-11-02.
Circuit as in led_resistor.py: VDD -> MCU source pin (60 ohm) -> column resistor R -> LED -> MCU sink pin (35 ohm) -> GND, one lit LED per column.
LED model: Vf(I) = Vf_ref + 0.1 V * ln(I / I_ref)   (ESTIMATE: InGaN white, ideality about 4; the data sheets give Vf only at one current)
Light output: Iv(I) = Iv_ref * I / I_ref            (ESTIMATE: linear; real LEDs are a little better than linear at low current, so low-current numbers are slightly pessimistic)
Reference values: data sheets read on 2026-11-02 (Hubei KENTO CICADT 0603-0.6DT white, Xinglight XL-1005UWC and XL-0201UWC).  python led_balance.py"""
import math

RS, RK = 60.0, 35.0
VDDS = (3.3, 3.7, 4.12)


def current(vf_ref, i_ref, vdd, r):
    lo, hi = 0.0, 0.05
    for _ in range(60):
        i = (lo + hi) / 2
        vf = vf_ref + 0.1 * math.log(max(i, 1e-9) / i_ref)
        if vdd - vf - i * (RS + RK + r) > 0:
            lo = i
        else:
            hi = i
    return lo


# name: (Vf_ref min/typ/max at I_ref, I_ref [A], Iv_ref min/typ/max [mcd] at I_ref, CCT text)
LEDS = {
    "hour   0603 KT-0603W C2290":         ((2.60, 2.85, 3.10), 0.005, (145, 250, 360), "40,000 K to >100,000 K (x 0.21-0.25 y 0.16-0.23: deep blue-white)"),
    "minute 0402 XL-1005UWC C20613596":   ((2.60, 2.95, 3.30), 0.020, (350, 650, 1000), "15,000 K typ (x 0.245 y 0.248: blue-white)"),
    "second 0201 XL-0201UWC C965789":     ((2.60, 3.00, 3.40), 0.020, (550, 700, 900), "5,500-7,500 K (bins 5500-6000 / 6000-6500 / 6500-7000): cool white"),
}
if __name__ == "__main__":
    for r in (220, 330, 470):
        print(f"\n=== column resistor {r} ohm ===")
        print(f"{'LED':38} {'VDD':>5} | {'I typ mA':>8} {'(lowVf..hiVf)':>16} | {'mcd typ':>8} {'(worst..best bin)':>20}")
        for name, (vf, iref, iv, cct) in LEDS.items():
            for v in VDDS:
                it = current(vf[1], iref, v, r)
                ilo = current(vf[0], iref, v, r); ihi = current(vf[2], iref, v, r)
                m = lambda i, ivr: ivr * i / iref
                lo = m(ihi, iv[0]); hi = m(ilo, iv[2])        # least current x dimmest bin ... most current x brightest bin
                print(f"{name:38} {v:5.2f} | {it*1000:8.2f} ({ihi*1000:5.2f}..{ilo*1000:5.2f}) | {m(it, iv[1]):8.1f} ({lo:6.1f}..{hi:7.1f})")
            print()
    print("\nColour: " + "\n        ".join(f"{k}: {v[3]}" for k, v in LEDS.items()))
