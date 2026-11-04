# Handoff: build the parametric Helmholtz cage in Fusion (for Claude Desktop + Fusion MCP)

Paste everything below the line into a new Claude Desktop chat. Attach `cage_layout.py`, `HelmholtzCage4040.py`, `design.json` and `BOM.csv` from this folder. The chat must have the Autodesk Fusion connector enabled (Fusion open; Preferences > General > API > Fusion MCP Server on).

---

You are connected to my running Autodesk Fusion through the Fusion MCP server. Build a **parametric, timeline-based** Fusion design of a 3-axis Helmholtz cage made from 40x40 T-slot extrusion. My team will keep editing it by hand, so the model must be driven by **User Parameters** (Modify > Change Parameters): changing a parameter must update every dependent part. Use real sketches + extrudes (Capture Design History ON), not direct-modelling or base-feature solids.

The attached `cage_layout.py` is the verified reference layout. It is pure Python and passed an interference check (391 parts, 0 overlaps) and 4 assembly-path checks. `HelmholtzCage4040.py` is a non-parametric Fusion script that builds the same thing with temporary B-rep. Reproduce the same geometry and placements, but parametrically. Do not change the design. If something cannot be done parametrically, tell me before you deviate.

## Step 0: discover

List the Fusion MCP tools you have. If one runs Python/API scripts, write the model as one script that you run, read the errors from, and fix. Otherwise use the modelling tools directly. Show me the plan before building.

## User Parameters (mm unless noted)

| Name | Value | Meaning |
|---|---|---|
| prof | 40 | profile size (HFS8-4040, 10 mm slot) |
| e_c | 7.75 | winding centroid depth below the outer profile face |
| gap | 10 | clearance between nested coils (= crossing spacer length) |
| X_side / Y_side / Z_side | 1361 / 1461 / 1561 | mean-turn side (from the simulator) |
| X_spacing / Y_spacing / Z_spacing | 722.5 / 776 / 868.5 | coil-centre spacing of each pair |
| X_F | X_side/2 + e_c | outer face half-width (same pattern for Y_F, Z_F) |
| plate_t / plate_leg | 6.35 / 60 | laser-cut corner L-plates |
| strut_inset | 170 | strut centre distance from the coil's outer corner |
| riser_h | 80 | risers under the bottom Y struts |
| wind_w / wind_top / wind_floor / r_floor | 15.5 / 4 / 11.5 / 12 | winding pack in the slot, corner groove floor radius |

Constraint to report (not enforce): Y_F - prof - X_F = gap and Z_F - prof - Y_F = gap. These are 10 mm now. Changing a side without the next one breaks nesting; say so if it happens.

## Conventions

* Cage centre at the origin, Z up.
* Pair local frames: X coils lie in the YZ plane, Y coils in ZX, Z coils in XY.
* Both coils of a pair are the **same component**, placed at ±spacing/2 and **translated, never mirrored or flipped**.
* Every winding sits in the radially outer slot.

## Components to build (see `build()` in `cage_layout.py` for exact placements)

1. **Coil X/Y/Z** (one component each, 2 occurrences)
   * 4 identical members, length 2·(F − prof).
   * 4 printed corner guides: a 40 mm cube with a groove of radius r_floor.
   * 8 corner L-plates.
   * 4 inner-corner HBLFS8 brackets.
   * Winding body: a rounded rectangle at centroid half-width F − e_c, pack wind_w × 7.5.
   * 12 slot clips.
   * Terminal block with 2 Powerpole housings.
2. **Pair X/Y/Z**: 2 coil occurrences + 4 struts (length spacing − prof) + 4 brackets per strut end. Strut positions are in `strut_positions()`. The Y and Z struts share global x = Y_F − strut_inset.
3. **Crossing mounts**: 8 X–Y and 8 Y–Z, each a bracket + 10 mm spacer + printed fork. X–Z needs none (60 mm gap).
4. **Base**:
   * 2 rails along y at x = ±(Y_F − strut_inset), length 2·Z_F + 80.
   * 3 cross members, 4 risers (80 mm), 4 posts under the bottom Z coil.
   * Centre column, foot pads, brackets.
5. **CubeSat fixture**: printed 6U cradle, top at z = −183, 6U long axis along Z.
6. **Reference**: transparent 6U envelope and working-volume boxes (6U + 10 mm margin).
7. **Assembly tools**: strut locator gauges, 50 and 100 mm.

Part definitions, dimensions and hardware are in `part_boxes()`, in `HelmholtzCage4040.py` (class `Geo`), and in `BOM.csv`. Name each component with the part number from BOM.csv and set its description.

## Profile cross-section (simplified, until MISUMI CAD replaces it)

* 40 × 40 square.
* Each face has a 10.2 mm wide, 4 mm deep neck opening into a 16 mm wide cavity whose floor is 11.5 mm below the face.
* Ø6.8 mm centre bore.

Make the cross-section one sketch, referenced by every extrusion, so it can be swapped for the real HFS8-4040 profile later.

## Verify before you finish

* **Interference:** run Inspect > Interference on the whole assembly. The only expected overlaps are a winding with its own coil's members, corner guides and clips, and the clips with their members.
* **Section views:** check a section through one X–Y crossing and one Y–Z crossing. Each should show a 10 mm gap filled by the spacer.
* **Change test:** change Z_spacing to 900, check the Z coils, struts and posts follow, then set it back to 868.5.
* **Counts:** report the occurrence count of each part and compare it with BOM.csv.
* **Save** the design as "Helmholtz Cage 4040 (parametric)".
