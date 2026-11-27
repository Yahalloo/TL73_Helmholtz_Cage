# LTspice results at 34 V and 20 kHz (2026-11-27)

**Which results go where (Adarsh, 27 Nov):**
- **Report.** The report's simulation section uses the **8 Ω / 3.12 A Z-coil runs at 34 V and 20 kHz** as its primary results, as originally run (bottom of this file, figures fig1 to fig6).
- **Power budget and field headroom.** These use the **Rev B coils, hot, at the 100 µT current** (next section, figures fig7 to fig10), with Z at 11.1 Ω.
- **Limits note.** The report mentions the 11.1 Ω result only in a short note in "Limits of the simulation".

## Coil data used (from TL73_M2_Design.docx, Table 7 and §6.5)

| Axis | R pair, 20 / 40 °C | L pair | k (µT/A) | I for 100 µT | Coil V at 40 °C | P | Source |
|---|---|---|---|---|---|---|---|
| X | 9.20 / **9.92 Ω** | 17.5 mH | 48.57 | **2.47 A** | 24.5 V | 60 W | Table 7 |
| Y | 9.76 / **10.53 Ω** | 18.8 mH | 45.75 | **2.46 A** | 25.9 V | 64 W | Table 7 |
| Z | 10.33 / **11.1 Ω** (Table 7: 11.14) | 20.1 mH | 42.09 | **3.27 A** | 36.4 V | 119 W | Table 7; §6.5 gives 10.3 / 11.1 Ω |

- Total coil power for the 100 µT worst case is 243 W (§6.5, Table 13, coils at 40 °C). LEO tests up to 60 µT need 103 W.
- The "I for 100 µT" values include a 10 % margin (Table 7 heading) and are the current for 100 µT **net**, against the ambient field in the worst direction. The coil pair alone then gives k × I: 120, 113 and 138 µT.

### Numbers that disagree
- **3.12 A design current.** The design current of 3.12 A used everywhere on the PCB side (power budget, the earlier LTspice runs, the report) does **not** match the 100 µT currents above: 2.47 / 2.46 / 3.27 A. The 3.12 A figure came from the earlier coil design. It is kept below only as a comparison.
- **Z inductance.** The earlier model used 21.0 mH and 8 Ω for Z. Table 7 gives 20.1 mH and 10.33 / 11.14 Ω.

## Power budget and headroom: 34 V, 20 kHz, single-side switching, hot coils at the 100 µT current

Duty needed = I × Rtot / 34 V + 1.5 µs × 20 kHz (dead-time correction), where Rtot = R + 0.237 Ω (two hot FETs, shunt and leads). The duty limit at 20 kHz is 96 % (2 µs minimum pulse).

| | X | Y | Z |
|---|---|---|---|
| Rtot (Ω) | 10.16 | 10.77 | 11.34 |
| L/Rtot (ms) | 1.72 | 1.75 | 1.77 |
| Duty needed for the 100 µT current | 77 % | 81 % | **112 % (not possible)** |
| Margin to the 96 % limit | 19 points | 15 points | **-16 points** |
| Current reached (A) | 2.49 | 2.48 | **2.81** (duty at the limit) |
| Field from the coil pair (µT) | 121 | 114 | **118**, against the 138 needed |
| Time from reversal to 90 % of the 100 µT current (ms) | 4.9 | 5.0 | not reached (90 % of the 2.81 A it reaches: 5.3) |
| Zero crossing after the reversal step (ms) | 1.15 | 1.16 | 1.24 |
| Ripple p-p | 18.2 mA = 0.88 µT | 15.0 mA = 0.69 µT | 4.8 mA = 0.20 µT |
| Driver loss (W) | 2.36 | 2.35 | 2.89 |
| **Junction estimate (°C)** | **99** | **99** | **114** |
| Supply current from 34 V (A) | 1.89 | 1.98 | 2.68 |
| Coil power (W) | 61.7 | 64.9 | 87.8 |
| **Maximum at 34 V** | 3.14 A = **153 µT** (scaled) | 2.96 A = **136 µT** (scaled) | 2.81 A = **118 µT** (simulated) |
| Headroom over the 100 µT current | +27 % | +20 % | **-14 %** |

- **All three axes together:** 6.55 A from 34 V and about 7.6 W of driver loss. Coil power is 214 W with Z limited to 2.81 A.
- **Unipolar switching** (comparison): same current, about 1 W more loss per driver, and junctions of 128 / 127 / 134 °C. Ripple is about half.
- **X and Y maximum:** taken from the Z run at the same clamped duty, scaled by 1 / Rtot. Their driver loss at maximum is the 100 µT loss plus the extra conduction loss.

### Z is the limiting axis
- **3.27 A needs too much voltage.** The 100 µT current with the 10 % margin needs **39.9 V** from the bridge at the 96 % duty limit (36.4 V across the coil in Table 7). That is above the 36 V board rating (SMDJ36A stand-off, buck input) and above the DRV8873S 38 V maximum.
- **Without the margin it still falls short.** 2.97 A needs **36.2 V**, just over the 36 V rating.
- **What 34 V delivers.** Z reaches 2.81 A when hot, which is 95 % of the current without the margin. This agrees with §6.5 of the design document: 96 µT net at 40 °C, 105 µT at 20 °C.
- **Ways to close the gap:**
  - keep the Z coil cooler: the 20 °C resistance of 10.33 Ω gives about 3.0 A at 34 V;
  - shorten the leads or lower Rtot;
  - accept about 96 µT net in the single worst direction;
  - change the Z coil (fewer turns or heavier wire).

### Ringing at the Z coil (11.1 Ω, duty at its limit, about 2.9 µs low time)

| Case | Rising edge | Falling edge | Snubber dissipation |
|---|---|---|---|
| No snubber | 36.6 V peak, +3.3 V above 33.3 V, 5.1 MHz, does not die out | -7.6 V, 6.8 V below -0.8 V, 5.0 MHz | none |
| PCB snubber 33 Ω + 470 pF at the connector | 36.5 V, +3.2 V, 5.1 MHz (no change) | -7.5 V, 6.6 V, 5.0 MHz | 1.6 mW |
| 68 Ω + 1.5 nF at the coil | 35.1 V, +1.8 V, one overshoot | -5.4 V, one dip, settled within about 0.5 µs | 16 mW |

The conclusion is unchanged: leave the PCB snubbers unfitted, and fit 68 Ω + 1.5 nF at the coil terminals if the real coil rings.

### Figures (primary)
- fig7_100uT_reversal_XYZ_34V_20kHz.png: field reversal on X, Y and Z, with each axis's commanded field
- fig8_100uT_ripple_XYZ_34V_20kHz.png: ripple on each axis, single-side and unipolar
- fig9_100uT_junction_XYZ.png: junction estimate per axis
- fig10_100uT_Z_ringing_34V_20kHz.png: Z coil edges with and without snubbers
- results_100uT_34V_20kHz.json: all extracted numbers

### Decks (Simulation folder)
- sim_A_reversal_34V_20kHz_{X,Y,Z}_100uT.asc
- sim_D_steady_power_34V_20kHz_{X,Y,Z}_100uT.asc
- sim_D_steady_power_34V_20kHz_{X,Y,Z}_Imax.asc (X and Y Imax were not run, see above; Z ran)
- sim_C_snubber_34V_20kHz_Z_100uT.asc

The steady and snubber decks run for 15 ms and keep the last 1 ms, so the current settles from the `.ic` start. Their built-in `.meas` windows assume the old 2 ms run, so use the numbers here (from the raw files), not the logs.

---

## Report results: the 8 Ω / 3.12 A Z-coil model (34 V 20 kHz is primary, 30 V runs for comparison)

| Z coil, 3.12 A target, 8 Ω, 21 mH | 30 V 10 kHz | 30 V 100 kHz | 34 V 20 kHz | 34 V 10 kHz |
|---|---|---|---|---|
| Settled after reversal, held / unipolar (A) | 3.126 / 3.141 | 2.547 / 1.518 | 3.144 / 3.175 | n/a |
| Time to 90 % (ms) | 7.51 / 7.38 | not reached | 7.31 / 7.04 | n/a |
| Ripple p-p (mA) | 17.5 / 10.4 | 59 / 162 | 16.5 / 12.5 | 30.0 / 16.9 |
| Driver loss (W) | 2.70 / 3.21 | 6.29 / 8.30 | 3.45 / 4.74 | 2.82 / 3.45 |
| Junction (°C) | 108 / 123 | 208 / 264 | 129 / 165 | 112 / 129 |

- **Ringing (8 Ω, 34 V, 20 kHz):** +2.4 V / -7.5 V at 5 to 5.5 MHz with no snubber; the coil snubber damps it (15 mW).
- **Scaled 122 °C figure:** the "122 °C at 20 kHz" in the 30 V report was scaled from 10 kHz. At 34 V and 20 kHz the 8 Ω model gives 129 °C.
- **Junction temperature vs the thermistor limit:** the junction estimate cannot be compared directly with the 120 °C driver thermistor limit. The thermistor reads board copper, which runs cooler than the junction.
- **Figures and decks:** fig1 to fig6, with the `*_34V_20kHz.asc` and original 30 V decks.
- **Old-coil decks:** the helmholtz_drv8873_* decks (4.42 Ω) are superseded. One gave no data; the other reports an unrealistic 431 °C because of its slow gate model.
