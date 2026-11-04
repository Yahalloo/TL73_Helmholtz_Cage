"""Layout of the 4040 T-slot Helmholtz cage (pure Python, no Fusion dependency).

The Fusion script (HelmholtzCage4040.py) turns this layout into components, and
running this file directly checks it without Fusion:

    python3 cage_layout.py            # interference + assembly-path checks, cut list, BOM.csv

Conventions (same as the simulator, helmholtz_cage/geometry.py)
------------------------------------------------------------------
* Global frame: cage centre at the origin, Z up. All lengths in mm.
* Each axis has one *pair*. A pair's local frame is (a, b, c) = (u, v, axis) with
  TRANSVERSE = X:(y,z), Y:(z,x), Z:(x,y), so a x b = c.
* The two coils of a pair are identical and are installed *translated* (never
  flipped) to c = +/- d/2, so the "+c" face of every coil faces +axis.
* Every winding sits in the radially OUTER slot of its 40x40 profile. If h is the
  simulator's mean-turn half side, the outer profile face is at F = h + E_C, where
  E_C is the depth of the winding centroid below that face.
* The gap between nested coils is (F_outer - 40) - F_inner = GAP.
"""

from __future__ import annotations

import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
AX = "XYZ"
TRANSVERSE = {0: (1, 2), 1: (2, 0), 2: (0, 1)}

# ------------------------------------------------------------------ profile + build constants [mm]
PROF = 40.0                      # 40x40 profile, 10 mm slot (MISUMI HFS8-4040 or equivalent)
SLOT_NECK_W, SLOT_NECK_D = 10.2, 4.0   # slot opening and lip thickness (simplified)
SLOT_CAV_W, SLOT_CAV_D = 16.0, 11.5    # simplified cavity width / floor depth below face
CORE_HOLE_D = 6.8
WIND_W = 15.5                    # winding pack, axial width
WIND_TOP, WIND_FLOOR = SLOT_NECK_D, SLOT_CAV_D   # pack fills the cavity (depth 4 .. 11.5)
E_C = 0.5 * (WIND_TOP + WIND_FLOOR)            # 7.75 mm: centroid depth below outer face
R_FLOOR = 12.0                   # corner groove floor radius (>= 7 x wire diameter)
GROOVE_CLR = 0.5
GAP = 10.0                       # clearance between nested coils = crossing spacer length
PLATE_T, PLATE_LEG = 6.35, 60.0  # 1/4" 6061 laser-cut corner plates
BRK_LEG, BRK_T, BRK_W = 40.0, 6.0, 35.0       # HBLFS8 envelope (simplified)
SPACER_OD, SPACER_ID = 16.0, 8.4
STRUT_INSET = 170.0              # strut centre distance from the coil's outer corner
RISER_H = 80.0                   # risers under the bottom Y struts
CLIP_L = 60.0
CUBESAT_6U = (100.0, 226.3, 366.0)            # long axis along cage Z (as optimised)
WV_MARGIN = 10.0
CRADLE_T = 8.0


# ------------------------------------------------------------------ small vector helpers
def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(k, s=1.0):
    v = [0.0, 0.0, 0.0]
    v[k] = float(s)
    return tuple(v)


IDENT = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))


def frame_z(origin, zdir):
    """Frame whose local +z points along ``zdir`` (an axis-aligned unit vector)."""
    k = max(range(3), key=lambda i: abs(zdir[i]))
    x = unit((k + 1) % 3)
    y = cross(zdir, x)
    return (tuple(origin), x, y)


def frame_xy(origin, x, y):
    return (tuple(origin), tuple(x), tuple(y))


def apply(frame, p):
    o, x, y = frame
    z = cross(x, y)
    return add(o, add(mul(x, p[0]), add(mul(y, p[1]), mul(z, p[2]))))


def rotate(frame, v):
    _, x, y = frame
    z = cross(x, y)
    return add(mul(x, v[0]), add(mul(y, v[1]), mul(z, v[2])))


def compose(parent, child):
    o, x, y = child
    return (apply(parent, o), rotate(parent, x), rotate(parent, y))


# ------------------------------------------------------------------ parts and assembly tree
class Part:
    def __init__(self, key, name, kind, params, cls, source="", pn="", desc="", hw=None):
        self.key, self.name, self.kind, self.params = key, name, kind, params
        self.cls = cls          # aluminium | printed | copper | hardware | purchased | reference
        self.source, self.pn, self.desc = source, pn, desc
        self.hw = hw or {}      # fastener kit needed per instance


class Node:
    def __init__(self, name):
        self.name = name
        self.children = []      # (Node | part key, frame, tag)

    def add(self, child, frame=IDENT, tag=""):
        self.children.append((child, frame, tag))
        return child


class Layout:
    def __init__(self):
        self.parts: dict[str, Part] = {}
        self.root = Node("Helmholtz Cage 4040")
        self.info: dict = {}

    def part(self, key, **kw):
        if key not in self.parts:
            self.parts[key] = Part(key, **kw)
        return key


# ------------------------------------------------------------------ part definitions
M8_BRK = {"M8x20 SHCS 316": 2, "T-nut slot10 M8 stainless": 2}


def profile_part(lay: Layout, length: float) -> str:
    return lay.part(
        f"HFS8-4040-{length:g}", name=f"HFS8-4040 x {length:g} mm", kind="profile",
        params={"L": length}, cls="aluminium", source="MISUMI (cut to length, 0.5 mm steps)",
        pn=f"HFS8-4040-{length:g}", desc="40x40 aluminium extrusion, 8 series, 10 mm slot",
    )


def std_parts(lay: Layout):
    lay.part("BRACKET", name="Bracket HBLFS8", kind="bracket", params={}, cls="aluminium",
             source="MISUMI", pn="HBLFS8",
             desc="90 deg tabbed bracket, die-cast aluminium, 8 series (fasteners not included)", hw=M8_BRK)
    lay.part("BRACKET_X", name="Bracket HBLFS8 (crossing)", kind="bracket", params={}, cls="aluminium",
             source="MISUMI", pn="HBLFS8",
             desc="Same bracket; the screw through the 10 mm spacer is M8x30",
             hw={"M8x20 SHCS 316": 1, "M8x30 SHCS 316": 1, "T-nut slot10 M8 stainless": 2})
    lay.part("SPACER", name="Spacer 16OD x 10 for M8", kind="spacer", params={"L": GAP}, cls="aluminium",
             source="McMaster-Carr", pn="search: aluminum unthreaded spacer M8, 16 mm OD, 10 mm long",
             desc="Sets the 10 mm gap between nested coils")
    lay.part("PLATE", name="Corner plate (laser cut)", kind="plate", params={}, cls="aluminium",
             source="SendCutSend / OSH Cut (DXF exported by the script)", pn="6061-T6 0.250 in",
             desc="L-plate on both axial faces of each coil corner; sets squareness",
             hw={"M8x16 SHCS 316": 2, "T-nut slot10 M8 stainless": 2})
    lay.part("CORNER", name="Corner wire guide (print)", kind="corner", params={}, cls="printed",
             source="3D print, ASA or PETG", pn="PRT-CORNER",
             desc="Fills the corner cube, carries the winding around a 12 mm floor radius; keyed into both members",
             hw={"M8x65 SHCS 316": 1, "M8 nyloc nut 316": 1, "M8 washer 316": 2})
    lay.part("CLIP", name="Slot retainer clip (print)", kind="clip", params={}, cls="printed",
             source="3D print, PETG", pn="PRT-CLIP", desc="Snaps into the slot neck over the winding")
    lay.part("FORK", name="Crossing locator fork (print)", kind="fork", params={}, cls="printed",
             source="3D print, ASA or PETG", pn="PRT-FORK",
             desc="Keys into one coil's slot and straddles the crossing member of the next pair",
             hw={"M8x20 SHCS 316": 1, "T-nut slot10 M8 stainless": 1})
    lay.part("TERMINAL", name="Coil terminal block (print)", kind="terminal", params={}, cls="printed",
             source="3D print, PETG", pn="PRT-TERM", desc="Holds the coil's Powerpole pair + strain relief",
             hw={"M8x20 SHCS 316": 1, "T-nut slot10 M8 stainless": 1})
    lay.part("PP_RED", name="Powerpole PP30 housing red", kind="pp", params={}, cls="purchased",
             source="Powerwerx / DigiKey", pn="Anderson 1327G6 (+ 1331 contact)", desc="Coil + terminal")
    lay.part("PP_BLK", name="Powerpole PP30 housing black", kind="pp", params={}, cls="purchased",
             source="Powerwerx / DigiKey", pn="Anderson 1327 (+ 1331 contact)", desc="Coil - terminal")
    lay.part("CRADLE", name="6U cradle (print)", kind="cradle", params={}, cls="printed",
             source="3D print, PETG", pn="PRT-CRADLE", desc="Locates a 6U CubeSat long-axis-vertical",
             hw={"M8x20 SHCS 316": 1})
    lay.part("FOOT", name="Base foot pad (print)", kind="foot", params={}, cls="printed",
             source="3D print, TPU or PETG", pn="PRT-FOOT", desc="Non-magnetic foot under the base rails")
    lay.part("GAUGE50", name="Strut locator gauge 50 (print, tool)", kind="gauge", params={"L": 50.0},
             cls="printed", source="3D print, PETG", pn="PRT-GAUGE50",
             desc="Removable: sets X/Y strut position from the corner plate")
    lay.part("GAUGE100", name="Strut locator gauge 100 (print, tool)", kind="gauge", params={"L": 100.0},
             cls="printed", source="3D print, PETG", pn="PRT-GAUGE100",
             desc="Removable: sets Z strut / post position from the corner plate")
    lay.part("REF_6U", name="6U envelope (reference)", kind="refbox",
             params={"size": CUBESAT_6U}, cls="reference", desc="Not built")
    s = tuple(v + 2 * WV_MARGIN for v in CUBESAT_6U)
    lay.part("REF_WV", name="Working volume 6U+10 (reference)", kind="refbox",
             params={"size": s}, cls="reference", desc="Not built")


# ------------------------------------------------------------------ geometry from the design JSON
def load_design(path):
    with open(path) as f:
        d = json.load(f)
    pairs = sorted(d["pairs"], key=lambda p: p["axis"])
    geo = []
    for p in pairs:
        h = 0.5 * p["width"] * 1e3
        F = round((h + E_C) * 4.0) / 4.0          # member length 2(F-40) on a 0.5 mm grid
        dd = round(p["spacing"] * 1e3 * 2.0) / 2.0  # strut length d-40 on a 0.5 mm grid
        geo.append({"axis": p["axis"], "h_sim": h, "F": F, "h": F - E_C, "d": dd, "d_sim": p["spacing"] * 1e3,
                    "turns": p["turns"], "awg": p["awg"]})
    return d, geo


# ------------------------------------------------------------------ builders
def build_coil(lay: Layout, g) -> Node:
    ax, F = g["axis"], g["F"]
    n = Node(f"Coil {AX[ax]}")
    Lm = 2.0 * (F - PROF)
    pk = profile_part(lay, Lm)
    for sb in (1, -1):   # members along a, at b = sb (F-20)
        n.add(pk, frame_z((-(F - PROF), sb * (F - 20), 0), (1, 0, 0)), "member")
    for sa in (1, -1):   # members along b, at a = sa (F-20)
        n.add(pk, frame_z((sa * (F - 20), -(F - PROF), 0), (0, 1, 0)), "member")
    for sa in (1, -1):
        for sb in (1, -1):
            n.add("CORNER", frame_xy((sa * F, sb * F, 0), (sa, 0, 0), (0, sb, 0)), "corner")
            for sc in (1, -1):
                n.add("PLATE", frame_xy((sa * F, sb * F, sc * (20 + PLATE_T / 2)), (sa, 0, 0), (0, sb, 0)), "plate")
            # inner-corner bracket: leg 1 on the a-member's inner face, leg 2 on the b-member's inner face
            n.add("BRACKET", frame_xy((sa * (F - PROF), sb * (F - PROF), 0), (-sa, 0, 0), (0, -sb, 0)), "bracket")
    # winding (one body per coil size)
    wk = lay.part(f"WIND_{AX[ax]}", name=f"Winding {AX[ax]} ({g['turns']} t AWG{g['awg']})", kind="winding",
                  params={"F": F}, cls="copper", source="Magnet wire, heavy build",
                  desc=f"{g['turns']} turns, mean turn {2 * g['h']:.1f} mm")
    n.add(wk, IDENT, "winding")
    # slot clips on the outer face, 3 per member
    for t in (-0.25, 0.0, 0.25):
        for sb in (1, -1):
            n.add("CLIP", frame_xy((t * Lm, sb * F, 0), (0, sb, 0), (1, 0, 0)), "clip")
        for sa in (1, -1):
            n.add("CLIP", frame_xy((sa * F, t * Lm, 0), (sa, 0, 0), (0, 1, 0)), "clip")
    # terminal block on the inner face of the +b member, at a = 0
    term = Node(f"Terminal {AX[ax]}")
    term.add("TERMINAL", IDENT, "terminal")
    term.add("PP_RED", frame_xy((12.0, -5.0, 4.0), (1, 0, 0), (0, 1, 0)), "pp")
    term.add("PP_BLK", frame_xy((12.0, -5.0, -4.0), (1, 0, 0), (0, 1, 0)), "pp")
    n.add(term, frame_xy((0, F - PROF, 0), (0, -1, 0), (1, 0, 0)), "terminal")
    return n


def strut_positions(geo):
    """(A, B, member_dir) in each pair's local frame; member_dir is the local axis the strut's member runs along."""
    Fx, Fy, Fz = (g["F"] for g in geo)
    xs = Fy - STRUT_INSET                    # Y and Z struts share global x, so both sit above the base rails
    out = {}
    out[0] = [(sa * (Fx - STRUT_INSET), sb * (Fx - 20), 0) for sa in (1, -1) for sb in (1, -1)]
    out[1] = [(sa * (Fy - 20), sb * xs, 1) for sa in (1, -1) for sb in (1, -1)]
    out[2] = [(sa * xs, sb * (Fz - 20), 0) for sa in (1, -1) for sb in (1, -1)]
    return out, xs


def build_pair(lay: Layout, g, coil: Node, struts) -> Node:
    ax, d = g["axis"], g["d"]
    n = Node(f"Pair {AX[ax]}")
    for s in (1, -1):
        n.add(coil, ((0, 0, s * d / 2), (1, 0, 0), (0, 1, 0)), f"coil{'+' if s > 0 else '-'}")
    pk = profile_part(lay, d - PROF)
    for A, B, k in struts:
        n.add(pk, frame_z((A, B, -(d / 2 - 20)), (0, 0, 1)), "strut")
        for ce in (d / 2 - 20, -(d / 2 - 20)):
            for s in (1, -1):
                p = [A, B, ce]
                p[k] += s * 20
                nB = unit(k, s)
                nA = (0, 0, -1 if ce > 0 else 1)
                n.add("BRACKET", frame_xy(p, nB, nA), "strut_bracket")
    return n


def bracket(node, corner, nB, nA, tag, key="BRACKET"):
    node.add(key, frame_xy(corner, nB, nA), tag)


def build(path=os.path.join(HERE, "design.json")) -> Layout:
    lay = Layout()
    std_parts(lay)
    raw, geo = load_design(path)
    gx, gy, gz = geo
    Fx, Fy, Fz = gx["F"], gy["F"], gz["F"]
    dX, dY, dZ = gx["d"], gy["d"], gz["d"]
    struts, xs = strut_positions(geo)
    lay.info = {"geo": geo, "xs": xs, "design": raw.get("name", "")}

    for g in geo:
        u, v = TRANSVERSE[g["axis"]]
        coil = build_coil(lay, g)
        pair = build_pair(lay, g, coil, struts[g["axis"]])
        lay.root.add(pair, frame_xy((0, 0, 0), unit(u), unit(v)), f"pair{AX[g['axis']]}")

    # ---------------- crossing mounts (global frame)
    xing = Node("Crossing mounts")
    for sx in (1, -1):
        for sy in (1, -1):
            for sz in (1, -1):
                # X-Y: bracket on the X coil's outer axial face, spacer under the Y top/bottom member
                bracket(xing, (sx * (dX / 2 + 20), sy * dY / 2, sz * Fx), (sx, 0, 0), (0, 0, -sz), "xy_bracket", "BRACKET_X")
                xing.add("SPACER", frame_z((sx * (dX / 2 + 40), sy * dY / 2, sz * Fx), (0, 0, sz)), "xy_spacer")
                xing.add("FORK", fork_frame((sx * (dX / 2 - 20), sy * dY / 2, sz * (Fx - 20)), (-sx, 0, 0), (0, 0, sz)),
                         "xy_fork")
                # Y-Z: bracket on the Y coil's outer axial face, spacer against the Z inner face
                bracket(xing, (sx * Fy, sy * (dY / 2 + 20), sz * dZ / 2), (0, sy, 0), (-sx, 0, 0), "yz_bracket", "BRACKET_X")
                xing.add("SPACER", frame_z((sx * Fy, sy * (dY / 2 + 40), sz * dZ / 2), (sx, 0, 0)), "yz_spacer")
                xing.add("FORK", fork_frame((sx * (Fz - 20), sy * dY / 2, sz * (dZ / 2 + 20)), (0, 0, sz), (-sx, 0, 0)),
                         "yz_fork")
    lay.root.add(xing, IDENT, "crossings")

    # ---------------- base (global frame)
    base = Node("Base")
    zt = -Fy - RISER_H                       # rail top
    rail = profile_part(lay, 2 * Fz + 80)          # extends past the posts so their brackets sit fully on it
    xm = profile_part(lay, 2 * (xs - 20))
    riser = profile_part(lay, RISER_H)
    post = profile_part(lay, -(dZ / 2 + 20) - zt)
    col_top = -CUBESAT_6U[2] / 2 - CRADLE_T     # cradle top = 6U bottom face (inside the 10 mm margin)
    col_top = zt + math.floor((col_top - zt) * 2.0) / 2.0
    col = profile_part(lay, col_top - zt)
    for sx in (1, -1):
        base.add(rail, frame_z((sx * xs, -(Fz + 40), zt - 20), (0, 1, 0)), "rail")
        for yr in (250.0, -250.0):
            base.add(riser, frame_z((sx * xs, yr, zt), (0, 0, 1)), "riser")
            for s in (1, -1):
                bracket(base, (sx * xs, yr + s * 20, zt), (0, s, 0), (0, 0, 1), "riser_bracket")
                bracket(base, (sx * xs, yr + s * 20, -Fy), (0, s, 0), (0, 0, -1), "riser_bracket")
        for sy in (1, -1):
            px, py = sx * xs, sy * (Fz - 20)
            base.add(post, frame_z((px, py, zt), (0, 0, 1)), "post")
            for s in (1, -1):
                bracket(base, (px, py + s * 20, zt), (0, s, 0), (0, 0, 1), "post_bracket")
                bracket(base, (px + s * 20, py, -(dZ / 2 + 20)), (s, 0, 0), (0, 0, -1), "post_bracket")
            base.add("FOOT", frame_z((sx * xs, sy * (Fz + 10), zt - 50), (0, 0, 1)), "foot")
    for yc in (Fz - 20, 0.0, -(Fz - 20)):
        base.add(xm, frame_z((-(xs - 20), yc, zt - 20), (1, 0, 0)), "cross")
        for sx in (1, -1):
            for s in (1, -1):
                bracket(base, (sx * (xs - 20), yc + s * 20, zt - 20), (-sx, 0, 0), (0, s, 0), "base_bracket")
    base.add(col, frame_z((0, 0, zt), (0, 0, 1)), "column")
    for s in (1, -1):
        bracket(base, (s * 20, 0, zt), (s, 0, 0), (0, 0, 1), "column_bracket")
    lay.root.add(base, IDENT, "base")

    # ---------------- fixture + references
    fix = Node("CubeSat fixture")
    fix.add("CRADLE", frame_z((0, 0, col_top), (0, 0, 1)), "cradle")
    lay.root.add(fix, IDENT, "fixture")
    ref = Node("Reference (not built)")
    ref.add("REF_6U", IDENT, "ref")
    ref.add("REF_WV", IDENT, "ref")
    lay.root.add(ref, IDENT, "ref")

    tools = Node("Assembly tools (removable)")
    tools.add("GAUGE50", frame_z((Fz + 300, 0, zt), (0, 0, 1)), "tool")
    tools.add("GAUGE100", frame_z((Fz + 300, 100, zt), (0, 0, 1)), "tool")
    lay.root.add(tools, IDENT, "tools")
    lay.info.update({"zt": zt, "col_top": col_top})
    return lay


def fork_frame(origin, n, r):
    """Fork canonical frame: x = n (thickness, away from the mounting face), z = r (towards the other member)."""
    return frame_xy(origin, n, cross(r, n))


# ------------------------------------------------------------------ approximate solids (boxes) for checks
def part_boxes(p: Part):
    k, P = p.kind, p.params
    if k == "profile":
        return [(-20, 20, -20, 20, 0, P["L"])]
    if k == "bracket":
        w = BRK_W / 2
        return [(0, BRK_LEG, 0, BRK_T, -w, w), (0, BRK_T, 0, BRK_LEG, -w, w)]
    if k == "plate":
        t = PLATE_T / 2
        return [(-40, 0, -40, 0, -t, t), (-40, 0, -40 - PLATE_LEG, -40, -t, t), (-40 - PLATE_LEG, -40, -40, 0, -t, t)]
    if k == "corner":
        return [(-40, 0, -40, 0, -20, 20)]
    if k == "spacer":
        r = SPACER_OD / 2
        return [(-r, r, -r, r, 0, P["L"])]
    if k == "clip":
        return [(-3.8, 0, -CLIP_L / 2, CLIP_L / 2, -5, 5)]
    if k == "fork":
        return [(0, 10, -30, 30, -15, 25), (0, 10, -30, -20.2, 25, 50), (0, 10, 20.2, 30, 25, 50)]
    if k == "terminal":
        return [(0, 12, -25, 25, -15, 15)]
    if k == "pp":
        return [(0, 7.9, 0, 24.6, -3.95, 3.95)]
    if k == "winding":
        F = P["F"]
        a0, a1 = F - WIND_FLOOR, F - WIND_TOP
        w = WIND_W / 2
        return [(-a1, a1, a0, a1, -w, w), (-a1, a1, -a1, -a0, -w, w), (a0, a1, -a1, a1, -w, w), (-a1, -a0, -a1, a1, -w, w)]
    if k == "cradle":
        return [(-70, 70, -133, 133, 0, CRADLE_T)]
    if k == "foot":
        return [(-30, 30, -30, 30, 0, 10)]
    if k == "gauge":
        return [(0, P["L"], -20, 20, 0, 10)]
    return []


def flatten(lay: Layout):
    """List of (part key, global frame, path) where path is the tuple of (tag) from the root."""
    out = []

    def walk(node, frame, path):
        for child, fr, tag in node.children:
            g = compose(frame, fr)
            if isinstance(child, Node):
                walk(child, g, path + (tag,))
            else:
                out.append((child, g, path + (tag,)))

    walk(lay.root, IDENT, ())
    return out


def global_boxes(lay, inst):
    key, fr, path = inst
    res = []
    for b in part_boxes(lay.parts[key]):
        pts = [apply(fr, (x, y, z)) for x in b[0:2] for y in b[2:4] for z in b[4:6]]
        res.append(tuple(v for i in range(3) for v in (min(p[i] for p in pts), max(p[i] for p in pts))))
    return res


def overlap(b1, b2, tol=0.05):
    return all(min(b1[2 * i + 1], b2[2 * i + 1]) - max(b1[2 * i], b2[2 * i]) > tol for i in range(3))


def _expected(lay, i1, i2):
    """Overlaps that are by design (winding / clips inside the slot of the same coil)."""
    (k1, _, p1), (k2, _, p2) = i1, i2
    if p1[:-1] != p2[:-1]:
        return False
    kinds = {lay.parts[k1].kind, lay.parts[k2].kind}
    return ("winding" in kinds and kinds & {"profile", "corner", "clip"}) or kinds == {"clip", "profile"}


def interference(lay, insts=None):
    insts = insts if insts is not None else [i for i in flatten(lay) if lay.parts[i[0]].cls != "reference"]
    boxes = [(n, b) for n, inst in enumerate(insts) for b in global_boxes(lay, inst)]
    boxes.sort(key=lambda t: t[1][0])
    hits = []
    for i in range(len(boxes)):
        n1, b1 = boxes[i]
        for j in range(i + 1, len(boxes)):
            n2, b2 = boxes[j]
            if b2[0] >= b1[1]:
                break
            if n1 != n2 and overlap(b1, b2) and not _expected(lay, insts[n1], insts[n2]):
                hits.append((insts[n1], insts[n2]))
    return hits


def sweep(lay, moving, static, direction, start, stop, step=5.0):
    """Translate ``moving`` instances from ``start`` to ``stop`` (offsets along ``direction``); return first collision."""
    sb = [b for inst in static for b in global_boxes(lay, inst)]
    mb = [b for inst in moving for b in global_boxes(lay, inst)]
    n = int(abs(stop - start) / step) + 1
    for i in range(n + 1):
        s = start + (stop - start) * i / n
        off = mul(direction, s)
        for b in mb:
            bb = (b[0] + off[0], b[1] + off[0], b[2] + off[1], b[3] + off[1], b[4] + off[2], b[5] + off[2])
            for c in sb:
                if overlap(bb, c):
                    return s, bb, c
    return None


# ------------------------------------------------------------------ BOM
def bom(lay):
    counts = {}
    for key, _, _ in flatten(lay):
        counts[key] = counts.get(key, 0) + 1
    rows, hw = [], {}
    for key, q in counts.items():
        p = lay.parts[key]
        if p.cls == "reference":
            continue
        rows.append((p.cls, p.name, p.pn, p.source, q, p.desc))
        for h, m in p.hw.items():
            hw[h] = hw.get(h, 0) + m * q
    for h, q in hw.items():
        src = {"T-nut slot10 M8 stainless": ("MISUMI HNTRSN8 (SUS316 sintered) or FramingTech TN10M8SS",
                                              "MAGNET-TEST every batch")}.get(h, ("McMaster-Carr / Bolt Depot (316 / A4)",
                                                                                  "Non-magnetic grade only"))
        rows.append(("hardware", h, "", src[0], q, src[1]))
    geo = lay.info["geo"]
    wire = sum(2 * (4 * 2 * g["h"] * g["turns"] / 1000 + 2.0) for g in geo)
    rows += [
        ("consumable", "Magnet wire 14 AWG heavy build, 200 C, 25 lb spool", "e.g. Remington 14H200P / Essex GP/MR-200",
         "Remington / Essex distributor", 3, f"one spool per axis pair; ~{wire:.0f} m needed incl. 2 m leads per coil"),
        ("consumable", "Nomex 410 slot liner 0.13 mm, 20 mm strip", "", "McMaster-Carr", 1, f"~{4 * sum(2 * 2 * g['h'] for g in geo) / 1000:.0f} m"),
        ("consumable", "Kapton tape 25 mm", "", "McMaster-Carr / DigiKey", 2, "layer ties, insulated-corner film"),
        ("consumable", "RTV silicone (neutral cure)", "", "hardware store", 2, "seal winding in slot (optional)"),
        ("consumable", "Nylon shoulder washer M8", "", "McMaster-Carr", 30, "one insulated corner per coil + strut ends if needed"),
        ("consumable", "NTC thermistor 10k, epoxy bead", "", "DigiKey", 8, "one per coil in the corner-guide pocket"),
        ("consumable", "14 AWG stranded twisted pair (harness)", "", "DigiKey", 20, "metres, pair harnesses to drivers"),
        ("consumable", "Powerpole 1331 contacts (30 A)", "Anderson 1331", "Powerwerx / DigiKey", 50, "coils + harnesses + spares"),
        ("consumable", "ASA or PETG filament", "", "any", 3, "kg"),
    ]
    order = {"aluminium": 0, "copper": 1, "printed": 2, "purchased": 3, "hardware": 4, "consumable": 5}
    rows.sort(key=lambda r: (order.get(r[0], 9), r[1]))
    return rows


def main():
    lay = build()
    geo = lay.info["geo"]
    print("Coil geometry (simulator mean turn -> as-modelled):")
    for g in geo:
        print(f"  {AX[g['axis']]}: side {2 * g['h_sim']:.2f} -> {2 * g['h']:.2f} mm, spacing {g['d_sim']:.2f} -> "
              f"{g['d']:.1f} mm, outer face F = {g['F']:.2f}, member {2 * (g['F'] - PROF):g}, strut {g['d'] - PROF:g}")
    Fx, Fy, Fz = (g["F"] for g in geo)
    print(f"  nesting gaps: X-Y {Fy - PROF - Fx:.2f} mm, Y-Z {Fz - PROF - Fy:.2f} mm, X-Z {Fz - PROF - Fx:.2f} mm")

    insts = [i for i in flatten(lay) if lay.parts[i[0]].cls != "reference"]
    hits = interference(lay, insts)
    print(f"\nInterference check: {len(insts)} parts, {len(hits)} unexpected overlaps")
    for a, b in hits[:20]:
        print("  ", lay.parts[a[0]].name, a[2], "<->", lay.parts[b[0]].name, b[2])

    # assembly paths
    def sel(pred):
        return [i for i in insts if pred(i[2])]

    base = sel(lambda p: p[0] == "base")
    ypair = sel(lambda p: p[0] == "pairY")
    xpair = sel(lambda p: p[0] == "pairX")
    xcoil = sel(lambda p: p[0] == "pairX" and p[1] == "coil+")
    zbot = sel(lambda p: p[0] == "pairZ" and p[1] == "coil-")
    ztop = sel(lambda p: p[0] == "pairZ" and p[1] == "coil+")
    zstr = sel(lambda p: p[0] == "pairZ" and p[1] in ("strut", "strut_bracket") and True)
    xy = sel(lambda p: p[0] == "crossings" and p[1].startswith("xy"))
    print("\nAssembly path checks (5 mm steps):")
    checks = [
        ("1. Y pair lowered onto the base", ypair, base, (0, 0, 1), 1500, 0),
        ("2. X coil slid in along y through the Y pair", xcoil, ypair + base, (0, 1, 0), -1600, 0),
        ("3. Z bottom coil lowered over X+Y", zbot, base + ypair + xpair + xy, (0, 0, 1), 2000, 0),
        ("4. Z top coil lowered onto the Z struts", ztop, base + ypair + xpair + xy + zbot + zstr, (0, 0, 1), 1500, 0),
    ]
    for name, mv, st, dirn, a, b in checks:
        r = sweep(lay, mv, st, dirn, a, b)
        print(f"  {name}: {'clear' if r is None else 'COLLISION at offset %.0f mm' % r[0]}")

    rows = bom(lay)
    path = os.path.join(HERE, "BOM.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["class", "item", "part number", "source", "qty", "notes"])
        w.writerows(rows)
    print(f"\nBOM written to {path}")
    for r in rows:
        print(f"  {r[4]:4d}  {r[0]:9s} {r[1]:42s} {r[2]}")
    tot = sum(lay.parts[k].params["L"] * q for k, q in
              ((k, sum(1 for i in insts if i[0] == k)) for k in lay.parts) if lay.parts[k].kind == "profile")
    print(f"\nTotal HFS8-4040: {tot / 1000:.2f} m (~{tot / 1000 * 1.63:.0f} kg)")


if __name__ == "__main__":
    main()
