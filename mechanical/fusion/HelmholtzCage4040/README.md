# Rev B (Nov 2026 design review): current design

Rev B replaces everything below for new work. The sections after this one describe Rev A and are kept for reference.

| File | Purpose |
|---|---|
| `HelmholtzCage4040_revB.py` | Fusion script. Run once to build the parametric design, then edit through Change Parameters. |
| `design_revB.json` | Simulator design for Rev B. |
| `BOM_revB.csv` | Rev B bill of materials with the prices checked so far. |
| `verification/revB/` | Rev B screenshots. |

Saved in Fusion as **Helmholtz Cage 4040 Rev B (parametric)**. `cage_layout.py`, `HelmholtzCage4040.py`, `HelmholtzCage4040_parametric.py` and `BOM.csv` are still Rev A.

| Axis | Side | Spacing | Turns | Member cut |
|---|---|---|---|---|
| X | 1361 mm | 722.5 mm | 40 | 8 x 1296.5 mm |
| Y | 1441 mm | 765 mm | 40 | 8 x 1376.5 mm |
| Z | 1521 mm | 845.5 mm | 40 | 8 x 1456.5 mm |

What changed from Rev A:
* **Stand:** no base. Four 100 mm rail stubs on levelling feet bolt to the outer side faces of the bottom Y members. The bottom faces hold the winding, so nothing can bolt there.
* **Coil spacing:** no spacers, forks or struts. Neighbouring coil frames touch, and printed gauges set each pair's spacing during assembly by butting between a corner cheek and the coil being located. The gauges are the precision parts, so check them with calipers.
* **Corners:** one printed piece combines the wire guide and the old L-plates. It slides into both members, with an M6 hammer nut through each of four cheek holes. A triangular gusset in the inside corner carries the load.
* **Brackets:** all triangular gussets (McMaster 5537T586). Each crossing has two, inline, either side of the inner coil's member.
* **Satellite:** a beam between the top X members, a printed spreader that holds the cords at x = +/-66 mm (outside the working volume), four cord legs and a printed tray under the satellite.
* **Fasteners:** M6 hammer nuts, which drop in at any time. Rail, brackets, nuts and feet are from McMaster-Carr.
* **Winding:** 40 turns as rows of 6, 8, 10, 12 and 4 from the slot floor. The wire tops out 3.47 mm below the face, leaving room for a 3 mm clip.

Check before ordering:
* Gusset 5537T586: leg, thickness, width and hole positions are assumed (holes 20 mm from the corner). Compare with McMaster's drawing.
* Slot shape: lip, taper and floor were measured from McMaster drawing 6575N187, to about +/-0.3 mm. Download the vendor CAD and wind a short offcut with 40 turns before ordering wire.
* Magnetic hardware: test a batch of the zinc-plated nuts with your magnetometer.
* Shorted turn: insulate one corner gusset per coil. Frames now touch at crossings, so check step response for extra lag from aluminium loops.

# 4040 T-slot Helmholtz cage: Fusion 360 model

This script builds the whole cage assembly in Fusion 360 from `design.json`. That file is the simulator output (`Optimized_cage/optimised_design_tslot4040.json`), and the script reproduces it exactly. Every part is either a standard catalogue item, a laser-cut aluminium plate, or a 3D print.

| File | Purpose |
|---|---|
| `HelmholtzCage4040.py` / `.manifest` | Fusion script. Builds the assembly and exports STL, DXF and STEP files. |
| `cage_layout.py` | All geometry and placements, in plain Python. Running `python3 cage_layout.py` checks the design without Fusion. |
| `design.json` | The simulator design. Edit this, then re-run the script. |
| `BOM.csv` | Bill of materials, regenerated each time `cage_layout.py` runs. |

## Run it

1. In Fusion, open **Utilities → Add-Ins → Scripts and Add-Ins**. Click **+** (Add script) and select this folder. Select **HelmholtzCage4040**, then click **Run**.
2. A new document opens with the assembly. When the run finishes, a message reports how many occurrences were built, and lists any export problems.
3. The script writes files to `exports/`:
   * `stl/PRT-*.stl`: one file per printed part, in its print orientation.
   * `dxf/corner_plate.dxf`: upload this to SendCutSend or OSH Cut as 6061-T6, 0.250 in thick.
   * `cage.step`: the whole cage.

The model is generated, not timeline-parametric. To change it, edit `design.json` (or the constants at the top of `cage_layout.py`) and run the script again.

Before every run of the script, run `python3 cage_layout.py`. If the numbers are right, it prints:

```
nesting gaps: X-Y 10.00 mm, Y-Z 10.00 mm, X-Z 60.00 mm
Interference check: 391 parts, 0 unexpected overlaps
1. Y pair lowered onto the base: clear
2. X coil slid in along y through the Y pair: clear
3. Z bottom coil lowered over X+Y: clear
4. Z top coil lowered onto the Z struts: clear
```

## Geometry (as modelled)

| Axis | Mean-turn side | Pair spacing | Turns | Coil member length (cut) | Strut length (cut) |
|---|---|---|---|---|---|
| X | 1361.0 mm | 722.5 mm | 43 | 4 × 1296.5 mm | 682.5 mm |
| Y | 1461.0 mm | 776.0 mm | 38 | 4 × 1396.5 mm | 736.0 mm |
| Z | 1561.0 mm | 868.5 mm | 41 | 4 × 1496.5 mm | 828.5 mm |

Simulator results for the dimensions exactly as modelled:
* Field variation: 0.373 % (requirement R4 < 0.5 %)
* Centre accuracy (95th percentile): 3.2 % in magnitude and 2.2° in direction
* Envelope: 1.57 × 1.57 × 1.47 m

Rounding the corners of the winding (centroid radius about 16 mm) changes the field by less than 0.01 %.

## How the cage is put together

**Coil module.** Each coil is built and tested on its own:
* **Frame:** four identical HFS8-4040 members, with a printed corner wire guide filling each 40 mm corner cube.
* **Corner joints:** each corner is clamped between two laser-cut 6061 L-plates, one on each axial face, joined by an M8 through-bolt. The plates set the corner square. The guide is keyed into the side-slot necks of both members.
* **Inner-corner brackets:** an HBLFS8 bracket in each inner corner carries load. The printed guide carries none.
* **Winding:** it sits in the outward-facing slot, on a Nomex liner. Wire tension seats it, and printed clips in the slot opening keep it there. At the corners it runs around a 12 mm floor radius inside the guide. Each guide has a pocket in the floor for an NTC thermistor.
* **Terminal block:** a printed block on the inner face holds the coil's red and black Powerpole housings.

**Pairs.** The two coils of a pair are the same component. They are installed translated, never flipped, so the "+c" face of every coil faces +axis. Label that face on every coil.
* Four HFS8-4040 struts set the pair spacing. Their cut length is the precision feature.
* Each strut end has two HBLFS8 brackets.

**Between pairs** (the "Crossing mounts" component):
* **X–Y and Y–Z (8 crossings each):** each crossing has an HBLFS8 bracket on the inner coil's outer axial face and a 10 mm aluminium spacer against the outer coil's inner face. The spacer sets the 10 mm nesting gap.
* **Forks:** a printed fork at each crossing keys into one coil's slot and straddles the crossing member of the other pair. This locates the pairs relative to each other along the slot directions.
* **X–Z:** the gap is 60 mm and needs no mount.

**Base.** Two rails run along y under the Y and Z struts, with three cross members and printed foot pads.
* Four 80 mm risers carry the bottom Y struts, keeping the Y winding 80 mm above the rails.
* Four posts carry the bottom Z coil.
* A centre column carries the printed 6U cradle. The CubeSat sits long axis vertical, the orientation the uniformity result assumes.

## Assembly order (verified collision-free in `cage_layout.py`)

1. Build the base: rails, cross members, risers, posts and column.
2. Stand the two Y coils and bolt in the four Y struts. Lower the Y pair onto the risers.
3. Slide each X coil in along y, through the Y pair. Add the X struts, then the X–Y crossing brackets, spacers and forks. Measure to centre the X pair in x; a ±5 mm error is acceptable.
4. Lower the bottom Z coil from above, over everything, onto the four posts. Bolt in the Z struts.
5. Lower the top Z coil onto the struts. Fit the Y–Z crossing brackets, spacers and forks.
6. Connect each axis harness (coil A + → driver +, coil A − → coil B +, coil B − → driver −), then fit the cradle.

The heaviest single module is a Z coil at about 15 kg.

## Before ordering: check these

* **Profile cross-section.** The model uses a simplified slot-10 profile: 10.2 mm opening, 16 mm × 11.5 mm cavity. Download the real HFS8-4040 CAD from MISUMI and check that 38–43 turns of 14 AWG fit the real cavity. Wind a 30 cm offcut to be sure.
* **HBLFS8 bracket.** The model uses a 40 × 40 × 6 mm envelope with holes 20 mm from the corner. Compare that with MISUMI's drawing, and use MISUMI's recommended screw length (the BOM assumes M8 × 20, with M8 × 30 through each spacer).
* **Non-magnetic hardware.** Stainless T-nuts are often sintered or cold-worked, which can make them slightly magnetic. Hold a strong magnet to a sample of every batch of T-nuts, screws and brackets. Brackets are die-cast aluminium (ADC12).
* **Insulated corner.** One corner per coil is insulated, to break the aluminium loop (it would otherwise act as a shorted turn). On that corner, put Kapton film under the plate and bracket legs on one member, and nylon shoulder washers under those screws. The loops through struts and base are much weaker; add insulation there only if step-response tests show a lag.
* **Part numbers.** Check every part number in `BOM.csv` against the vendor before ordering, especially MISUMI HBLFS8, HNTRSN8 and the Anderson 1327, 1327G6 and 1331.
* **Chamber door.** The largest coil module is 1.58 m square, including the corner plates.

## Print settings

| Part | Material | Settings |
|---|---|---|
| Corner guides | ASA or PETG | 5 walls, 40 % gyroid infill, print with the groove facing up |
| Forks, terminal blocks, gauges | PETG | 4 walls, 30 % infill |
| Slot clips | PETG | Adjust the 9.8 mm width ±0.1 mm until they press-fit your printer's results |
| Foot pads | TPU (preferred) or PETG | |
| 6U cradle | PETG | 4 walls |

Don't use PLA anywhere: it creeps under bolt clamp load and near warm coils.
