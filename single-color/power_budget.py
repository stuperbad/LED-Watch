"""
Power budget + solar harvest comparison for the single-colour watch.  python power_budget.py
Everything is an assumption you can edit at the top; the same model feeds the table in power-budget.md.
Unit chain used everywhere:  lux --(÷ lux-per-W/m2)--> W/m2 --(÷10)--> mW/cm2 --(÷100 mW/cm2)--> suns
"""
# ---------------------------------------------------------------- light conditions
LIGHT = [  # name, lux, lux per W/m2 (spectrum)
    ("200 lux indoor LED/fluorescent", 200, 300),
    ("500 lux desk", 500, 300),
    ("1,000 lux window", 1000, 120),
    ("5,000 lux overcast/shade", 5000, 120),
    ("20,000 lux bright shade", 20000, 120),
    ("50,000 lux sunny", 50000, 120),
    ("1 sun (100 mW/cm2, ~120,000 lux)", 120000, 120),
]
# mono-Si low-light derating relative to its 1-sun efficiency (from solar-watch-evidence.md, UNVERIFIED snippets)
MONO_DERATE = {200: 4.4 / 18.4, 500: 7 / 18.4, 1000: 11 / 18.4, 5000: 15 / 18.4, 20000: 17 / 18.4, 50000: 18 / 18.4, 120000: 1.0}

# ---------------------------------------------------------------- cells
CELLS = {
    # name: dict(area_cm2 (footprint), kind, P1sun_mW or None, measured)
    "Panasonic AM-1606C (15x15x0.7 mm)": dict(area=1.5 * 1.5, kind="a-Si", measured_200lx_mW=2.6 * 3.4e-3, eff_sun=0.045),
    "Anysolar KXOB25-07X1TF (11.35x8x1.2 mm)": dict(area=1.135 * 0.8, kind="mono", P1sun=14.3),
    "Anysolar KXOB081K06TF (23x25x1.2 mm, yours)": dict(area=2.3 * 2.5, kind="mono", P1sun=105.9),
}

def irradiance_mW_cm2(lux, lpw):
    return lux / lpw / 10.0   # W/m2 -> mW/cm2

def cell_power_mW(cell, lux, lpw):
    irr = irradiance_mW_cm2(lux, lpw)                       # mW/cm2 of incident light
    if cell["kind"] == "a-Si":
        # measured: 200 lux fluorescent. a-Si output scales ~linearly with irradiance (UNVERIFIED for outdoors);
        # outdoors efficiency taken as ~4.5% of footprint (Panasonic outdoor table gives 3.6-5.4% for comparable AM cells)
        base_irr = irradiance_mW_cm2(200, 300)
        indoor = cell["measured_200lx_mW"] * irr / base_irr
        sun = cell["eff_sun"] * irr * cell["area"]
        return indoor if lux <= 1000 else min(indoor, sun) if lux < 5000 else sun
    ratio = MONO_DERATE[lux]
    return cell["P1sun"] * (irr / 100.0) * ratio

# ---------------------------------------------------------------- wearer profiles (hours/day at each ambient lux), from solar-watch-evidence.md
PROFILES = {
    "Office worker": dict(hours={200: 6, 500: 6, 1000: 1, 5000: 0.7, 20000: 0, 50000: 0, 30000: 0.3}, sleeve=0.7),
    "Commuter": dict(hours={200: 5, 500: 4, 1000: 1, 5000: 1.5, 20000: 0, 50000: 0, 30000: 1.0}, sleeve=0.6),
    "Outdoor enthusiast": dict(hours={200: 3, 500: 1, 1000: 0, 5000: 3, 20000: 3, 50000: 2, 30000: 0}, sleeve=0.8),
}
WRIST, OPTICAL, HARVESTER, CHARGE = 0.5, 0.85, 0.75, 0.95   # ESTIMATES (see solar-watch-evidence.md)
MONO_DERATE[30000] = 17.5 / 18.4

def harvest_mWh_day(cell, prof):
    total = 0.0
    for lux, h in prof["hours"].items():
        if not h:
            continue
        lpw = 300 if lux <= 500 else 120
        total += h * cell_power_mW(cell, lux, lpw)
    return total * WRIST * prof["sleeve"] * OPTICAL * HARVESTER * CHARGE

# ---------------------------------------------------------------- watch load
V = 3.7                     # LiPo nominal (V)
BATT_mWh = 100 * V          # 100 mAh cell
ALWAYS_ON = {               # microamps drawn from the supply, and the volts it is drawn at
    "MCU deep sleep + 32 kHz RTC": (3.3, V),
    "3.3 V regulator quiescent (LDO 1.6 uA / buck ~0.5 uA)": (1.6, V),
}
WAKE_SENSORS = {
    "button only (no motion sensor running)": 0.0,
    "BMI270 wake-on-motion (~13 uA @3.3 V)": 13 * 3.3,
    "BMA400 accelerometer wake (~0.85 uA @3.3 V)": 0.85 * 3.3,
}
SELF_DISCHARGE_MONTH = 0.02   # 2 %/month ESTIMATE
I_MCU_ACTIVE_mA = 1.5         # ESTIMATE while the display is up
N_LEDS = 3
def display_mWh(i_avg_led_mA, seconds=3.0):
    p_mW = (N_LEDS * i_avg_led_mA + I_MCU_ACTIVE_mA) * V       # LEDs run from the battery rail through resistors
    return p_mW * seconds / 3600.0

def always_on_mWh_day(sensor_uW):
    uW = sum(i * v for i, v in ALWAYS_ON.values()) + sensor_uW
    return uW * 24 / 1000.0 + BATT_mWh * SELF_DISCHARGE_MONTH / 30.0

if __name__ == "__main__":
    print("== light conversion")
    for n, lux, lpw in LIGHT:
        w = lux / lpw
        print(f"{n:36s} {lux:>7} lux = {w:8.2f} W/m2 = {w / 10:8.4f} mW/cm2 = {w / 1000:.5f} suns")
    print("\n== cell power (mW) at each light (footprint area)")
    for cn, c in CELLS.items():
        print(cn, f"(area {c['area']:.2f} cm2)")
        for n, lux, lpw in LIGHT:
            p = cell_power_mW(c, lux, lpw)
            print(f"   {n:36s} {p * 1000:10.1f} uW   = {p / c['area'] * 1000:9.1f} uW/cm2")
    print("\n== harvest mWh/day (wrist 0.5, sleeve per profile, optical 0.85, harvester 0.75, charge 0.95)")
    for cn, c in CELLS.items():
        print(cn, {pn: round(harvest_mWh_day(c, pr), 2) for pn, pr in PROFILES.items()})
    print("\n== display energy per wake (3 LEDs, 3 s, MCU 1.5 mA) in mWh")
    for i in (0.1, 0.3, 1.0):
        print(f"   {i} mA average per LED -> {display_mWh(i):.4f} mWh per wake;  20/60/200 wakes/day = " + "/".join(f"{display_mWh(i) * w:.2f}" for w in (20, 60, 200)))
    print("\n== always-on mWh/day (incl. 2%/month self-discharge of 100 mAh)")
    for n, uw in WAKE_SENSORS.items():
        print(f"   {n:46s} {always_on_mWh_day(uw):.2f}")
