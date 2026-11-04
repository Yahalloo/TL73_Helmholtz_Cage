"""Fusion script: builds Rev B of the 40x40 Helmholtz cage as a PARAMETRIC (timeline) design.

Rev B is the Nov 2026 design-review simplification of HelmholtzCage4040_parametric.py (Rev A):
  * no base, column or cradle stand: 4 rail stubs on levelling feet under the bottom Y members;
  * no spacers, forks or struts: coil frames of neighbouring axes touch (gap = 0), and printed gauges
    set each pair's spacing during assembly;
  * one printed corner piece replaces the guide + the two laser-cut L-plates;
  * every bracket is a triangular gusset, and each coil-to-coil crossing has two of them, inline;
  * the 6U hangs in a printed tray, on a cord sling, from one beam between the X coils;
  * McMaster-Carr rail and hammer nuts, so the cross-section is the real 8 mm slot.

Run it once from Utilities > Scripts and Add-Ins, or through the Fusion MCP server. It creates a new
document. After that, edit through Modify > Change Parameters.

Notes for editors
  * Nesting: Y_F - prof - X_F and Z_F - prof - Y_F must stay equal to gap (0 mm).
  * Component names carry the cut length and are NOT updated when a length parameter changes.
  * The winding is 40 turns as five stacked rows (6, 8, 10, 12, 4 turns from the slot floor). Changing
    the turn count means changing WIND_ROWS here and rebuilding.
"""

import math

import adsk.core
import adsk.fusion

DOC_NAME = "Helmholtz Cage 4040 Rev B (parametric)"

# (name, expression, comment). All lengths in mm. Order matters: later ones reference earlier ones.
PARAMS = [
    ("prof", "40 mm", "Rail size (McMaster 6575N25, 8 mm slot)"),
    ("e_c", "7.75 mm", "Winding centroid depth below the outer rail face (row stack gives 7.77)"),
    ("gap", "0 mm", "Clearance between nested coil frames (frames touch)"),
    ("X_side", "1361 mm", "X coil mean-turn side (simulator)"),
    ("Y_side", "1441 mm", "Y coil mean-turn side (simulator)"),
    ("Z_side", "1521 mm", "Z coil mean-turn side (simulator)"),
    ("X_spacing", "722.5 mm", "X pair coil-centre spacing"),
    ("Y_spacing", "765 mm", "Y pair coil-centre spacing"),
    ("Z_spacing", "845.5 mm", "Z pair coil-centre spacing"),
    ("X_F", "X_side / 2 + e_c", "X coil outer face half-width"),
    ("Y_F", "Y_side / 2 + e_c", "Y coil outer face half-width"),
    ("Z_F", "Z_side / 2 + e_c", "Z coil outer face half-width"),
    # rail section, read from McMaster drawing 6575N187 (lip, taper and floor are measured, +/- 0.3 mm)
    ("slot_open", "8 mm", "Slot opening"),
    ("slot_lip", "4.5 mm", "Slot lip thickness (measured from drawing)"),
    ("slot_cav_w", "22 mm", "Slot cavity width"),
    ("slot_taper", "6.8 mm", "Depth where the cavity starts tapering (measured from drawing)"),
    ("slot_floor_w", "11.2 mm", "Slot floor width (measured from drawing)"),
    ("slot_cav_d", "12.2 mm", "Slot depth"),
    ("core_d", "7 mm", "Rail centre bore"),
    # winding
    ("wire_od", "1.72 mm", "AWG 14 heavy-build wire OD"),
    ("liner_t", "0.13 mm", "Nomex slot liner"),
    ("wind_floor", "slot_cav_d - liner_t", "Winding floor depth below the outer face"),
    ("r_floor", "12 mm", "Corner groove floor radius"),
    ("groove_clr", "0.5 mm", "Corner groove clearance per side"),
    ("groove_w", "12 * wire_od + 2 * groove_clr", "Corner groove width (widest row = 12 turns)"),
    # printed corner
    ("cheek_t", "8 mm", "Printed corner cheek thickness"),
    ("cheek_leg", "60 mm", "Printed corner cheek leg length"),
    # hardware
    ("brk_leg", "40 mm", "Gusset 5537T586 leg (check against McMaster drawing)"),
    ("brk_t", "6 mm", "Gusset wall thickness (check against McMaster drawing)"),
    ("brk_w", "35 mm", "Gusset width (check against McMaster drawing)"),
    ("hole_d", "9 mm", "Gusset mounting hole (check against McMaster drawing)"),
    ("hole_m6", "6.6 mm", "M6 clearance hole in printed parts"),
    ("clip_l", "60 mm", "Slot retainer clip length"),
    ("clip_d", "3 mm", "Slot retainer clip depth (wire top is 3.47 mm below the face)"),
    # satellite
    ("sat_x", "100 mm", "6U envelope x"),
    ("sat_y", "226.3 mm", "6U envelope y"),
    ("sat_z", "366 mm", "6U envelope z (long axis along cage Z)"),
    ("wv_margin", "10 mm", "Working volume margin around the 6U envelope"),
    ("cradle_t", "8 mm", "Printed satellite tray thickness"),
    ("sling_x", "66 mm", "Sling cord x (just outside the working volume)"),
    ("sling_y", "100 mm", "Sling cord y at the tray"),
    ("cord_d", "3 mm", "Sling cord width"),
    ("hanger_t", "12 mm", "Printed spreader thickness"),
    # stand
    ("leg_x", "560 mm", "Leg x position on the bottom Y members"),
    ("leg_l", "100 mm", "Rail stub length, cut from offcuts"),
    # derived
    ("L_mem_X", "2 * (X_F - prof)", "Cut length: X coil member"),
    ("L_mem_Y", "2 * (Y_F - prof)", "Cut length: Y coil member"),
    ("L_mem_Z", "2 * (Z_F - prof)", "Cut length: Z coil member"),
    ("L_beam", "X_spacing - prof", "Cut length: satellite beam between the X coils"),
    ("leg_z", "-(Y_F - prof) - leg_l", "Rail stub bottom (z)"),
    ("tray_z", "-sat_z / 2 - cradle_t", "Tray underside (z); tray top = 6U bottom face"),
    # assembly gauges: from a corner cheek's end to the nearest face of the coil being located
    ("L_g_X", "(Y_F - prof - cheek_leg) - (X_spacing / 2 + prof / 2)", "Gauge: X coil position on a Y member"),
    ("L_g_Y", "(Z_F - prof - cheek_leg) - (Y_spacing / 2 + prof / 2)", "Gauge: Y coil position on a Z member"),
    ("L_g_Z", "(Y_F - prof - cheek_leg) - (Z_spacing / 2 + prof / 2)", "Gauge: Z coil position on a Y member"),
    ("L_g_C", "(X_F - prof - cheek_leg) - (Y_spacing / 2 + prof / 2)", "Gauge: X coil centring on its own member"),
]

WIND_ROWS = (6, 8, 10, 12, 4)                      # turns per row, from the slot floor outwards (40 turns)
AX = "XYZ"
TRANSVERSE = {0: (1, 2), 1: (2, 0), 2: (0, 1)}
UV = {0: (1, 2), 1: (0, 2), 2: (0, 1)}             # in-plane model axes of the plane normal to axis n
COLORS = {
    "aluminium": ((190, 194, 200), 1.0),
    "copper": ((196, 110, 50), 1.0),
    "printed": ((240, 130, 30), 1.0),
    "purchased": ((200, 30, 30), 1.0),
    "steel": ((90, 90, 95), 1.0),
    "cord": ((30, 110, 200), 1.0),
    "reference": ((60, 140, 230), 0.15),
}


def VI(expr):
    return adsk.core.ValueInput.createByString(expr)


# ------------------------------------------------------------------ linear expressions of parameters
class Lin:
    """sum(coef * parameter) + constant [mm]; renders as a Fusion expression."""

    def __init__(self, terms=None, c=0.0):
        self.t = {k: v for k, v in (terms or {}).items() if abs(v) > 1e-12}
        self.c = float(c)

    @staticmethod
    def of(x):
        return x if isinstance(x, Lin) else Lin(c=x)

    def __add__(self, o):
        o = Lin.of(o)
        t = dict(self.t)
        for k, v in o.t.items():
            t[k] = t.get(k, 0.0) + v
        return Lin(t, self.c + o.c)

    __radd__ = __add__

    def __neg__(self):
        return Lin({k: -v for k, v in self.t.items()}, -self.c)

    def __sub__(self, o):
        return self + (-Lin.of(o))

    def __rsub__(self, o):
        return Lin.of(o) - self

    def __mul__(self, s):
        return Lin({k: v * s for k, v in self.t.items()}, self.c * s)

    __rmul__ = __mul__

    def value(self, vals):
        return sum(v * vals[k] for k, v in self.t.items()) + self.c

    def expr(self):
        out = []
        for k, v in self.t.items():
            out.append(("-" if v < 0 else "+", k if abs(abs(v) - 1) < 1e-12 else f"{abs(v):.10g} * {k}"))
        if abs(self.c) > 1e-9 or not out:
            out.append(("-" if self.c < 0 else "+", f"{abs(self.c):.10g} mm"))
        s = " ".join(f"{sg} {tm}" for sg, tm in out)
        return s[2:] if s.startswith("+ ") else "-" + s[2:]


def P(name):
    return Lin({name: 1.0})


ZERO = Lin()
PROF = P("prof")
H = PROF * 0.5                      # half profile


# ------------------------------------------------------------------ frames (origin of Lin, axis-aligned unit axes)
def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(k, s=1):
    v = [0, 0, 0]
    v[k] = s
    return tuple(v)


def ivec(v):
    return tuple(int(round(c)) for c in v)


def frame_xy(origin, x, y):
    return (tuple(Lin.of(c) for c in origin), ivec(x), ivec(y))


def frame_z(origin, zdir):
    k = max(range(3), key=lambda i: abs(zdir[i]))
    x = unit((k + 1) % 3)
    return frame_xy(origin, x, cross(zdir, x))


IDENT = frame_xy((0, 0, 0), (1, 0, 0), (0, 1, 0))


def orient_table():
    """Measured: a joint origin with zAxisEntity = X/Y/Z axis, isFlipped, angle gives these local axes."""
    base = {"X": ((0, 0, 1), (0, -1, 0)), "Y": ((1, 0, 0), (0, 0, -1)), "Z": ((1, 0, 0), (0, 1, 0))}
    tab = {}
    for zn, (x0, y0) in base.items():
        for flip in (False, True):
            for ang in (0, 90, 180, 270):
                c, s = round(math.cos(math.radians(ang))), round(math.sin(math.radians(ang)))
                x = tuple(c * a + s * b for a, b in zip(x0, y0))
                y = tuple(-s * a + c * b for a, b in zip(x0, y0))
                if flip:
                    y = tuple(-v for v in y)
                tab[(ivec(x), ivec(y))] = (zn, flip, ang)
    assert len(tab) == 24
    return tab


ORIENT = orient_table()


def joint_spec(frame):
    """(z axis name, flip, angle, offsets) so that a joint origin on the parent origin reproduces ``frame``."""
    o, x, y = frame
    zn, flip, ang = ORIENT[(x, y)]
    z = cross(x, y)
    offs = [sum((Lin.of(o[j]) * a[j] for j in range(3) if a[j]), ZERO) for a in (x, y, z)]
    return zn, flip, ang, offs


# ------------------------------------------------------------------ assembly tree
class Node:
    def __init__(self, name):
        self.name = name
        self.children = []

    def add(self, child, frame=IDENT, tag=""):
        self.children.append((child, frame, tag))
        return child


PART_INFO = {
    # key: (component name, part number, BOM item, class, source, description)
    "BRACKET": ("5537T586", "5537T586", "Triangular gusset bracket, 40 mm", "aluminium", "McMaster-Carr",
                "Anodized aluminum gusset for 40 mm rail"),
    "CORNER": ("PRT-CORNER", "PRT-CORNER", "One-piece corner: wire guide + cheeks (print)", "printed",
               "3D print, ASA or PETG",
               "Slides into both members; carries the winding around the floor radius; replaces the L-plates"),
    "CLIP": ("PRT-CLIP", "PRT-CLIP", "Slot retainer clip (print)", "printed", "3D print, PETG",
             "Snaps into the slot neck over the winding"),
    "TERMINAL": ("PRT-TERM", "PRT-TERM", "Coil terminal block (print)", "printed", "3D print, PETG",
                 "Holds the coil's Powerpole pair + strain relief"),
    "PP_RED": ("Anderson 1327G6", "Anderson 1327G6 (+ 1331 contact)", "Powerpole PP30 housing red", "purchased",
               "Powerwerx / DigiKey", "Coil + terminal"),
    "PP_BLK": ("Anderson 1327", "Anderson 1327 (+ 1331 contact)", "Powerpole PP30 housing black", "purchased",
               "Powerwerx / DigiKey", "Coil - terminal"),
    "CRADLE": ("PRT-TRAY", "PRT-TRAY", "6U sling tray (print)", "printed", "3D print, PETG",
               "Carries a 6U CubeSat long-axis-vertical; four cord holes"),
    "HANGER": ("PRT-HANGER", "PRT-HANGER", "Beam spreader / centring piece (print)", "printed", "3D print, PETG",
               "Keys into the beam's lower slot; holds the two sling cords outside the working volume"),
    "CORD": ("Sling cord", "", "Sling cord set (4 legs)", "cord", "Non-magnetic cord (miscellaneous)",
             "Hangs the tray from the spreader; modelled as flat strips"),
    "FOOT": ("5537T983", "5537T983 + stem 8305A39", "Levelling mount with stem", "steel", "McMaster-Carr",
             "750 lb, zinc-plated steel, M8; screws into the rail stub's end"),
    "GAUGE_X": ("PRT-GAUGE-X", "PRT-GAUGE-X", "Gauge: X coil position on a Y member (print, tool)", "printed",
                "3D print, PETG", "Removable: sets X pair spacing"),
    "GAUGE_Y": ("PRT-GAUGE-Y", "PRT-GAUGE-Y", "Gauge: Y coil position on a Z member (print, tool)", "printed",
                "3D print, PETG", "Removable: sets Y pair spacing; print on the bed diagonal"),
    "GAUGE_Z": ("PRT-GAUGE-Z", "PRT-GAUGE-Z", "Gauge: Z coil position on a Y member (print, tool)", "printed",
                "3D print, PETG", "Removable: sets Z pair spacing"),
    "GAUGE_C": ("PRT-GAUGE-C", "PRT-GAUGE-C", "Gauge: X coil centring on its own member (print, tool)", "printed",
                "3D print, PETG", "Removable: centres the X coils in y"),
    "REF_6U": ("6U envelope (reference)", "", "6U envelope (reference)", "reference", "", "Not built"),
    "REF_WV": ("Working volume 6U+10 (reference)", "", "Working volume 6U+10 (reference)", "reference", "",
               "Not built"),
}
PROFILE_KEYS = {}                    # part key -> length parameter name
GAUGE_L = {"GAUGE_X": "L_g_X", "GAUGE_Y": "L_g_Y", "GAUGE_Z": "L_g_Z", "GAUGE_C": "L_g_C"}


def profile_part(lparam):
    key = "PROFILE:" + lparam
    PROFILE_KEYS[key] = lparam
    return key


def bracket(node, corner, nB, nA, tag):
    node.add("BRACKET", frame_xy(corner, nB, nA), tag)


def build_coil(ax):
    A, F = AX[ax], P(AX[ax] + "_F")
    Lm = P("L_mem_" + A)
    n = Node(f"Coil {A}")
    pk = profile_part("L_mem_" + A)
    for sb in (1, -1):
        n.add(pk, frame_z((-(F - PROF), sb * (F - H), 0), (1, 0, 0)), "member")
    for sa in (1, -1):
        n.add(pk, frame_z((sa * (F - H), -(F - PROF), 0), (0, 1, 0)), "member")
    for sa in (1, -1):
        for sb in (1, -1):
            n.add("CORNER", frame_xy((sa * F, sb * F, 0), (sa, 0, 0), (0, sb, 0)), "corner")
            bracket(n, (sa * (F - PROF), sb * (F - PROF), 0), (-sa, 0, 0), (0, -sb, 0), "corner_gusset")
    n.add("WIND_" + A, IDENT, "winding")
    for t in (-0.25, 0.0, 0.25):
        for sb in (1, -1):
            n.add("CLIP", frame_xy((t * Lm, sb * F, 0), (0, sb, 0), (1, 0, 0)), "clip")
        for sa in (1, -1):
            n.add("CLIP", frame_xy((sa * F, t * Lm, 0), (sa, 0, 0), (0, 1, 0)), "clip")
    term = Node(f"Terminal {A}")
    term.add("TERMINAL", IDENT, "terminal")
    term.add("PP_RED", frame_xy((12, -5, 4), (1, 0, 0), (0, 1, 0)), "pp")
    term.add("PP_BLK", frame_xy((12, -5, -4), (1, 0, 0), (0, 1, 0)), "pp")
    n.add(term, frame_xy((0, F - PROF, 0), (0, -1, 0), (1, 0, 0)), "terminal")
    return n


def build_pair(ax, coil):
    A, d = AX[ax], P(AX[ax] + "_spacing")
    n = Node(f"Pair {A}")
    for s in (1, -1):
        n.add(coil, frame_xy((0, 0, s * d * 0.5), (1, 0, 0), (0, 1, 0)), f"coil{'+' if s > 0 else '-'}")
    return n


def build_tree():
    root = Node("root")
    Fx, Fy, Fz = (P(a + "_F") for a in AX)
    dX, dY, dZ = (P(a + "_spacing") for a in AX)
    for ax in range(3):
        u, v = TRANSVERSE[ax]
        root.add(build_pair(ax, build_coil(ax)), frame_xy((0, 0, 0), unit(u), unit(v)), f"pair{AX[ax]}")

    # two inline gussets per crossing, straddling the inner coil's member; frames touch (gap = 0)
    xing = Node("Crossing mounts")
    for sx in (1, -1):
        for sy in (1, -1):
            for sz in (1, -1):
                for s in (1, -1):
                    bracket(xing, (sx * dX * 0.5 + s * H, sy * dY * 0.5, sz * (Fx + P("gap"))),
                            (s, 0, 0), (0, 0, -sz), "xy_gusset")
                    bracket(xing, (sx * (Fy + P("gap")), sy * dY * 0.5 + s * H, sz * dZ * 0.5),
                            (0, s, 0), (-sx, 0, 0), "yz_gusset")
    root.add(xing, IDENT, "crossings")

    # legs: rail stubs against the outer axial faces of the bottom Y members (their radial slot holds the winding)
    stand = Node("Stand")
    stub, legx, legz = profile_part("L_leg"), P("leg_x"), P("leg_z")
    for sx in (1, -1):
        for sy in (1, -1):
            lx, ly = sx * legx, sy * (dY * 0.5 + PROF)
            stand.add(stub, frame_z((lx, ly, legz), (0, 0, 1)), "leg")
            stand.add("FOOT", frame_z((lx, ly, legz), (0, 0, 1)), "foot")
            for s in (1, -1):
                bracket(stand, (lx + s * H, sy * (dY * 0.5 + H), -(Fy - H)), (s, 0, 0), (0, sy, 0), "leg_gusset")
    root.add(stand, IDENT, "stand")

    # satellite: beam between the X coils' top members, spreader under it, cord sling, tray
    fix = Node("CubeSat hanger")
    fix.add(profile_part("L_beam"), frame_z((-(dX * 0.5 - H), 0, Fx - H), (1, 0, 0)), "beam")
    for sx in (1, -1):
        for s in (1, -1):
            bracket(fix, (sx * (dX * 0.5 - H), s * H, Fx - H), (0, s, 0), (-sx, 0, 0), "beam_gusset")
    fix.add("HANGER", frame_z((0, 0, Fx - PROF), (0, 0, 1)), "hanger")
    fix.add("CORD", IDENT, "cord")
    fix.add("CRADLE", frame_z((0, 0, P("tray_z")), (0, 0, 1)), "tray")
    root.add(fix, IDENT, "fixture")

    ref = Node("Reference (not built)")
    ref.add("REF_6U", IDENT, "ref")
    ref.add("REF_WV", IDENT, "ref")
    root.add(ref, IDENT, "ref")

    tools = Node("Assembly gauges (removable)")
    for i, g in enumerate(("GAUGE_X", "GAUGE_Y", "GAUGE_Z", "GAUGE_C")):
        tools.add(g, frame_z((Fz + 300, i * 100.0, P("leg_z") - 44), (0, 0, 1)), "tool")
    root.add(tools, IDENT, "tools")
    return root


PROFILE_KEYS.update({"PROFILE:L_leg": "L_leg"})


# ------------------------------------------------------------------ Fusion builder
NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation


def plane(comp, n):
    return (comp.yZConstructionPlane, comp.xZConstructionPlane, comp.xYConstructionPlane)[n]


class Builder:
    def __init__(self, app, des):
        self.app, self.des, self.root = app, des, des.rootComponent
        self.vals = {}
        self.part_comps = {}
        self.node_comps = {}
        self.places = []
        self.appearances = {}

    # ---------------------------------------------------------------- parameters
    def make_params(self):
        up = self.des.userParameters
        for name, expr, comment in PARAMS:
            p = up.add(name, VI(expr), "mm", comment)
            self.vals[name] = p.value * 10.0
        p = up.add("L_leg", VI("leg_l"), "mm", "Cut length: rail stub leg")
        self.vals["L_leg"] = p.value * 10.0

    def v(self, lin):
        return Lin.of(lin).value(self.vals)

    # ---------------------------------------------------------------- sketch helpers (all fully dimensioned)
    def sk_point(self, sk, n, u, v):
        p = [0.0, 0.0, 0.0]
        iu, iv = UV[n]
        p[iu], p[iv] = self.v(u) / 10.0, self.v(v) / 10.0
        return sk.modelToSketchSpace(adsk.core.Point3D.create(*p))

    def dim_coord(self, sk, pt, lin, horizontal):
        """Pin a sketch point's sketch-x (horizontal=True) or sketch-y to |lin| from the sketch origin."""
        gc, val = sk.geometricConstraints, self.v(lin)
        if abs(val) < 1e-6:
            (gc.addVerticalPoints if horizontal else gc.addHorizontalPoints)(sk.originPoint, pt)
            return
        g = pt.geometry
        tp = adsk.core.Point3D.create(g.x / 2 + (0 if horizontal else 0.5), g.y / 2 + (0.5 if horizontal else 0), 0)
        orient = (adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation if horizontal
                  else adsk.fusion.DimensionOrientations.VerticalDimensionOrientation)
        d = sk.sketchDimensions.addDistanceDimension(sk.originPoint, pt, orient, tp)
        d.parameter.expression = (lin if val > 0 else -lin).expr()

    def sketch_x_is_u(self, sk, n):
        xd = sk.xDirection
        return abs((xd.x, xd.y, xd.z)[UV[n][0]]) > 0.5

    def draw_loop(self, sk, n, pts):
        lines = sk.sketchCurves.sketchLines
        sp = [self.sk_point(sk, n, *p) for p in pts]
        first = prev = None
        made = []
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            ln = lines.addByTwoPoints(prev if prev is not None else sp[i], first if j == 0 else sp[j])
            if first is None:
                first = ln.startSketchPoint
            prev = ln.endSketchPoint
            made.append((ln, pts[i], pts[j]))
        return made

    def poly(self, sk, n, pts):
        """Closed axis-aligned polygon; pts are (u, v) Lin pairs in the component frame."""
        gc = sk.geometricConstraints
        x_is_u = self.sketch_x_is_u(sk, n)
        for ln, p, q in self.draw_loop(sk, n, pts):
            const_u = Lin.of(p[0]).expr() == Lin.of(q[0]).expr()
            const = Lin.of(p[0] if const_u else p[1])
            vertical = const_u == x_is_u          # constant sketch-x
            (gc.addVertical if vertical else gc.addHorizontal)(ln)
            self.dim_coord(sk, ln.startSketchPoint, const, vertical)

    def poly_free(self, sk, n, pts):
        """Closed polygon with any edge angles: axis-aligned edges as in poly(), then dimension what is still free."""
        gc = sk.geometricConstraints
        x_is_u = self.sketch_x_is_u(sk, n)
        made = self.draw_loop(sk, n, pts)
        pinned = [[False, False] for _ in pts]        # per vertex: model u, v already set by an axis-aligned edge
        for i, (ln, p, q) in enumerate(made):
            for c in (0, 1):
                if Lin.of(p[c]).expr() == Lin.of(q[c]).expr():
                    vertical = (c == 0) == x_is_u     # constant sketch-x
                    (gc.addVertical if vertical else gc.addHorizontal)(ln)
                    self.dim_coord(sk, ln.startSketchPoint, Lin.of(p[c]), vertical)
                    pinned[i][c] = pinned[(i + 1) % len(pts)][c] = True
        for i, (ln, p, _) in enumerate(made):
            for c in (0, 1):
                if not pinned[i][c]:
                    self.dim_coord(sk, ln.startSketchPoint, Lin.of(p[c]), (c == 0) == x_is_u)

    def circle(self, sk, n, center, dia):
        c = sk.sketchCurves.sketchCircles.addByCenterRadius(self.sk_point(sk, n, *center), self.v(dia) / 20.0)
        cu, cv = (Lin.of(center[0]), Lin.of(center[1]))
        lx, ly = (cu, cv) if self.sketch_x_is_u(sk, n) else (cv, cu)
        self.dim_coord(sk, c.centerSketchPoint, lx, True)
        self.dim_coord(sk, c.centerSketchPoint, ly, False)
        g = c.centerSketchPoint.geometry
        d = sk.sketchDimensions.addDiameterDimension(c, adsk.core.Point3D.create(g.x + 1, g.y + 1, 0))
        d.parameter.expression = Lin.of(dia).expr()
        return c

    def extrude(self, comp, sk, prof, n, lo, hi, op, body=None):
        ei = comp.features.extrudeFeatures.createInput(prof, op)
        nv = sk.xDirection.crossProduct(sk.yDirection)
        start = lo if (nv.x, nv.y, nv.z)[n] > 0 else -hi
        if abs(self.v(start)) > 1e-6:
            ei.startExtent = adsk.fusion.OffsetStartDefinition.create(VI(start.expr()))
        ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VI((hi - lo).expr())),
                            adsk.fusion.ExtentDirections.PositiveExtentDirection)
        if body is not None:
            ei.participantBodies = [body]
        return comp.features.extrudeFeatures.add(ei)

    def box(self, comp, b, op=NEW, body=None, n=2):
        lo, hi = [], []
        for i in range(3):
            a, c = Lin.of(b[2 * i]), Lin.of(b[2 * i + 1])
            if self.v(a) > self.v(c):
                a, c = c, a
            lo.append(a)
            hi.append(c)
        iu, iv = UV[n]
        sk = comp.sketches.add(plane(comp, n))
        self.poly(sk, n, [(lo[iu], lo[iv]), (hi[iu], lo[iv]), (hi[iu], hi[iv]), (lo[iu], hi[iv])])
        f = self.extrude(comp, sk, sk.profiles.item(0), n, lo[n], hi[n], op, body)
        return body if body is not None else f.bodies.item(0)

    def prism(self, comp, pts, n, lo, hi, op=NEW, body=None):
        sk = comp.sketches.add(plane(comp, n))
        self.poly_free(sk, n, pts)
        f = self.extrude(comp, sk, sk.profiles.item(0), n, Lin.of(lo), Lin.of(hi), op, body)
        return body if body is not None else f.bodies.item(0)

    def cyl(self, comp, n, center, dia, lo, hi, op=NEW, body=None):
        sk = comp.sketches.add(plane(comp, n))
        self.circle(sk, n, center, dia)
        f = self.extrude(comp, sk, sk.profiles.item(0), n, Lin.of(lo), Lin.of(hi), op, body)
        return body if body is not None else f.bodies.item(0)

    def fillet_z_edges(self, comp, body, corners, radius):
        """Fillet the edges parallel to z that pass through the given (x, y) [mm] points."""
        ec = adsk.core.ObjectCollection.create()
        for e in body.edges:
            a, b = e.startVertex.geometry, e.endVertex.geometry
            if abs(a.x - b.x) > 1e-6 or abs(a.y - b.y) > 1e-6:
                continue
            if any(abs(a.x * 10 - x) < 1e-3 and abs(a.y * 10 - y) < 1e-3 for x, y in corners):
                ec.add(e)
        assert ec.count == len(corners), f"fillet: found {ec.count} of {len(corners)} edges"
        fi = comp.features.filletFeatures.createInput()
        fi.edgeSetInputs.addConstantRadiusEdgeSet(ec, VI(radius), False)
        return comp.features.filletFeatures.add(fi)

    # ---------------------------------------------------------------- part geometry
    def g_profile(self, comp, lparam):
        prof = [p for p in self.section.profiles if p.profileLoops.count == 2][0]
        prof = prof.createForAssemblyContext(self.section_occ)
        ei = comp.features.extrudeFeatures.createInput(prof, NEW)
        ei.setDistanceExtent(False, VI(lparam))
        comp.features.extrudeFeatures.add(ei)

    def g_bracket(self, comp):
        """Open triangular gusset: L legs with two triangular side ribs. Holes 20 mm from the corner."""
        L, T, w = P("brk_leg"), P("brk_t"), P("brk_w") * 0.5
        b = self.prism(comp, [(ZERO, ZERO), (L, ZERO), (ZERO, L)], 2, -w, w)
        self.box(comp, (T, L + 1, T, L + 1, -(w - T), w - T), CUT, b)
        self.cyl(comp, 1, (L * 0.5, 0), P("hole_d"), -1, T + 1, CUT, b)
        self.cyl(comp, 0, (L * 0.5, 0), P("hole_d"), -1, T + 1, CUT, b)

    def g_corner(self, comp):
        """One printed piece: corner cube + wire groove + tongues into both members + cheeks on both axial faces."""
        wf, w, t, leg = P("wind_floor"), P("groove_w") * 0.5, P("cheek_t"), P("cheek_leg")
        b = self.box(comp, (-PROF, 0, -PROF, 0, -H, H))
        self.box(comp, (-wf, 1, -PROF - 1, 1, -w, w), CUT, b)          # groove: the two straight runs
        self.box(comp, (-PROF - 1, 1, -wf, 1, -w, w), CUT, b)
        f = -self.v(wf)
        self.fillet_z_edges(comp, b, [(f, f)], "r_floor")              # groove floor radius at the corner
        h = P("slot_open") * 0.5 - 0.2
        n0 = H - P("slot_lip") + 0.3
        for z0, z1 in ((n0, H), (-H, -n0)):                            # tongues slide into the side-slot necks
            self.box(comp, (-H - h, -H + h, -PROF - 15, -PROF, z0, z1), JOIN, b)
            self.box(comp, (-PROF - 15, -PROF, -H - h, -H + h, z0, z1), JOIN, b)
        for z0, z1 in ((H, H + t), (-H - t, -H)):                      # cheeks, where the L-plates used to be
            self.box(comp, (-PROF, 0, -PROF, 0, z0, z1), JOIN, b)
            self.box(comp, (-PROF, 0, -PROF - leg, -PROF, z0, z1), JOIN, b)
            self.box(comp, (-PROF - leg, -PROF, -PROF, 0, z0, z1), JOIN, b)
            for x, y in ((-H, -PROF - leg * 0.5), (-PROF - leg * 0.5, -H)):
                self.cyl(comp, 2, (x, y), P("hole_m6"), z0 - 1, z1 + 1, CUT, b)
        self.thermistor_pocket(comp, b)

    def thermistor_pocket(self, comp, body):
        """Cylinder r 2.2 along -(1,1,0) from (-(q-1), -(q-1), 0), q = wind_floor + r_floor (1 - 1/sqrt2) + 1."""
        planes = comp.constructionPlanes
        pi = planes.createInput()
        pi.setByAngle(comp.zConstructionAxis, VI("-45 deg"), comp.xZConstructionPlane)
        diag = planes.add(pi)
        nrm = diag.geometry.normal
        assert abs(abs(nrm.x) - abs(nrm.y)) < 1e-6 and nrm.x * nrm.y > 0, "diagonal plane has the wrong normal"
        sgn = 1 if nrm.x > 0 else -1
        qm1 = "(wind_floor + r_floor * (1 - 1 / sqrt(2)))"
        pi = planes.createInput()
        pi.setByOffset(diag, VI(f"{-sgn} * {qm1} * sqrt(2)"))
        start = planes.add(pi)
        start.name = "Thermistor pocket plane"
        sk = comp.sketches.add(start)
        qv = self.vals["wind_floor"] + self.vals["r_floor"] * (1 - 1 / math.sqrt(2))
        c = sk.modelToSketchSpace(adsk.core.Point3D.create(-qv / 10, -qv / 10, 0))
        circ = sk.sketchCurves.sketchCircles.addByCenterRadius(c, 0.22)
        if abs(c.x) < 1e-6 and abs(c.y) < 1e-6:
            sk.geometricConstraints.addCoincident(circ.centerSketchPoint, sk.originPoint)
        else:   # the sketch origin is not the projected model origin: pin by a distance from it
            self.dim_coord(sk, circ.centerSketchPoint, Lin(c=c.x * 10), True)
            self.dim_coord(sk, circ.centerSketchPoint, Lin(c=c.y * 10), False)
        sk.sketchDimensions.addDiameterDimension(circ, adsk.core.Point3D.create(c.x + 1, c.y + 1, 0)) \
            .parameter.expression = "4.4 mm"
        ei = comp.features.extrudeFeatures.createInput(sk.profiles.item(0), CUT)
        nv = sk.xDirection.crossProduct(sk.yDirection)
        toward_corner = (nv.x + nv.y) < 0
        ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(VI("4.5 mm * sqrt(2)")),
                            adsk.fusion.ExtentDirections.PositiveExtentDirection if toward_corner
                            else adsk.fusion.ExtentDirections.NegativeExtentDirection)
        ei.participantBodies = [body]
        comp.features.extrudeFeatures.add(ei)

    def g_winding(self, comp, F):
        """Stacked rows of wire; each row a rounded ring concentric with the corner floor radius."""
        wf, od = P("wind_floor"), P("wire_od")
        bodies = []
        for k, turns in enumerate(WIND_ROWS):
            a1, a0, w = F - wf + od * (k + 1), F - wf + od * k, od * (turns * 0.5)
            b = self.box(comp, (-a1, a1, -a1, a1, -w, w))
            self.box(comp, (-a0, a0, -a0, a0, -w - 1, w + 1), CUT, b)
            o, i = self.v(a1), self.v(a0)
            # inner first: the wall is thinner than the outer radius, so the outer fillet needs the inner material
            self.fillet_z_edges(comp, b, [(sx * i, sy * i) for sx in (1, -1) for sy in (1, -1)],
                                f"r_floor + {k} * wire_od" if k else "r_floor")
            self.fillet_z_edges(comp, b, [(sx * o, sy * o) for sx in (1, -1) for sy in (1, -1)],
                                f"r_floor + {k + 1} * wire_od")
            bodies.append(b)
        tools = adsk.core.ObjectCollection.create()
        for b in bodies[1:]:
            tools.add(b)
        ci = comp.features.combineFeatures.createInput(bodies[0], tools)
        ci.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        comp.features.combineFeatures.add(ci)

    def neck(self):
        return P("slot_open") * 0.5 - 0.2

    def g_clip(self, comp):
        h = self.neck()
        self.box(comp, (-P("clip_d"), 0, -P("clip_l") * 0.5, P("clip_l") * 0.5, -h, h))

    def g_terminal(self, comp):
        h = self.neck()
        b = self.box(comp, (0, 12, -25, 25, -15, 15))
        self.box(comp, (-3.8, 0, -20, 20, -h, h), JOIN, b)
        self.cyl(comp, 0, (-17, 0), P("hole_m6"), -5, 13, CUT, b)
        self.box(comp, (3, 7, 21, 24, -16, 16), CUT, b)            # zip-tie slot for lead strain relief

    def g_pp(self, comp):
        self.box(comp, (0, 7.9, 0, 24.6, -3.95, 3.95))

    def g_tray(self, comp):
        t = P("cradle_t")
        hx, hy = P("sat_x") * 0.5 + 0.3, P("sat_y") * 0.5 + 0.3
        b = self.box(comp, (-70, 70, -133, 133, 0, t))
        for sx in (1, -1):
            for sy in (1, -1):
                self.box(comp, (sx * hx, sx * (hx + 8), sy * (hy - 25), sy * (hy + 8), t, t + 40), JOIN, b)
                self.box(comp, (sx * (hx - 25), sx * (hx + 8), sy * hy, sy * (hy + 8), t, t + 40), JOIN, b)
                self.cyl(comp, 2, (sx * P("sling_x"), sy * P("sling_y")), P("cord_d") + 1, -1, t + 1, CUT, b)

    def g_hanger(self, comp):
        h, t = self.neck(), P("hanger_t")
        b = self.box(comp, (-80, 80, -15, 15, -t, 0))
        self.box(comp, (-30, 30, -h, h, 0, 3.8), JOIN, b)
        self.cyl(comp, 2, (0, 0), P("hole_m6"), -t - 1, 5, CUT, b)
        for sx in (1, -1):
            self.cyl(comp, 2, (sx * P("sling_x"), 0), P("cord_d") + 1, -t - 1, 1, CUT, b)

    def g_cords(self, comp):
        """Four legs from the spreader down to the tray, in the planes x = +/-sling_x."""
        top = P("X_F") - PROF - P("hanger_t")
        bot = P("tray_z") + P("cradle_t")
        c = P("cord_d") * 0.5
        for sx in (1, -1):
            xc = sx * P("sling_x")
            for sy in (1, -1):
                y = sy * P("sling_y")
                self.prism(comp, [(-c, top), (c, top), (y + c, bot), (y - c, bot)], 0, xc - c, xc + c)

    def g_foot(self, comp):
        """Levelling mount below the stub's end: M8 stem + pad (simplified from the catalogue entry)."""
        b = self.cyl(comp, 2, (0, 0), 8, -32, 0)
        self.cyl(comp, 2, (0, 0), 52, -44, -32, JOIN, b)

    def g_gauge(self, comp, lparam):
        """Bar that butts between a corner cheek and a coil face, keyed into the member's slot."""
        h, L = self.neck(), P(lparam)
        b = self.box(comp, (0, L, -20, 20, 0, 10))
        self.box(comp, (0, L, -h, h, -3.8, 0), JOIN, b)

    def g_refbox(self, comp, sx, sy, sz):
        self.box(comp, (-sx * 0.5, sx * 0.5, -sy * 0.5, sy * 0.5, -sz * 0.5, sz * 0.5))

    def geometry(self, key, comp):
        if key in PROFILE_KEYS:
            return self.g_profile(comp, PROFILE_KEYS[key])
        if key.startswith("WIND_"):
            return self.g_winding(comp, P(key[-1] + "_F"))
        if key in GAUGE_L:
            return self.g_gauge(comp, GAUGE_L[key])
        if key == "REF_6U":
            return self.g_refbox(comp, P("sat_x"), P("sat_y"), P("sat_z"))
        if key == "REF_WV":
            m = P("wv_margin") * 2
            return self.g_refbox(comp, P("sat_x") + m, P("sat_y") + m, P("sat_z") + m)
        return {"BRACKET": self.g_bracket, "CORNER": self.g_corner, "CLIP": self.g_clip, "TERMINAL": self.g_terminal,
                "PP_RED": self.g_pp, "PP_BLK": self.g_pp, "CRADLE": self.g_tray, "HANGER": self.g_hanger,
                "CORD": self.g_cords, "FOOT": self.g_foot}[key](comp)

    def info(self, key):
        """(name, part number, BOM item, class, source, description) of a part key, at the current parameters."""
        if key in PROFILE_KEYS:
            lp = PROFILE_KEYS[key]
            ln = self.vals[lp]
            return (f"6575N25 x {ln:g}", "6575N25", f"Rail 40 x 40 x {ln:g} mm", "aluminium",
                    "McMaster-Carr (10 ft stick, cut to length)",
                    f"Hollow silver anodized rail, 8 mm slot; length = parameter {lp}")
        if key.startswith("WIND_"):
            nm = f"Winding {key[-1]} (40 t AWG14)"
            side = 2 * (self.vals[key[-1] + "_F"] - self.vals["e_c"])
            return (nm, "", nm, "copper", "Magnet wire, heavy build",
                    f"40 turns as rows {WIND_ROWS} from the slot floor, mean turn {side:.1f} mm (= {key[-1]}_side)")
        return PART_INFO[key]

    # ---------------------------------------------------------------- appearance
    def appearance(self, cls):
        if cls in self.appearances:
            return self.appearances[cls]
        base = None
        for lib in self.app.materialLibraries:
            if "Appearance" not in lib.name:
                continue
            for i in range(lib.appearances.count):
                a = lib.appearances.item(i)
                if a.name.startswith("Plastic - Matte") or a.name.startswith("Paint - Enamel Glossy"):
                    base = a
                    break
            if base:
                break
        ap = None
        if base:
            ap = self.des.appearances.addByCopy(base, f"Cage {cls}")
            for prop in ap.appearanceProperties:
                cp = adsk.core.ColorProperty.cast(prop)
                if cp and cp.name in ("Color", "Colour"):
                    rgb = COLORS[cls][0]
                    cp.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 0)
                    break
        self.appearances[cls] = ap
        return ap

    # ---------------------------------------------------------------- components + occurrences
    def new_occ(self, parent, name):
        occ = parent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ.isGroundToParent = False
        occ.component.name = name
        return occ

    def make_section(self):
        occ = self.new_occ(self.root, "6575N25 cross-section")
        occ.isGroundToParent = True
        comp = occ.component
        comp.description = ("McMaster 6575N25 outline (from drawing 6575N187; internal corner chambers omitted). "
                            "Drives every 40x40 extrusion. Replace this sketch with the vendor CAD section if needed.")
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = "6575N25 section"
        a, ow, cw, fw = H, P("slot_open") * 0.5, P("slot_cav_w") * 0.5, P("slot_floor_w") * 0.5
        lip, tap, fl = H - P("slot_lip"), H - P("slot_taper"), H - P("slot_cav_d")
        top = [(a, a), (ow, a), (ow, lip), (cw, lip), (cw, tap), (fw, fl), (-fw, fl), (-cw, tap), (-cw, lip),
               (-ow, lip), (-ow, a)]
        pts = []
        for k in range(4):                      # the top face's slot, rotated to each face (CCW)
            for x, y in top:
                for _ in range(k):
                    x, y = -y, x
                pts.append((x, y))
        self.poly_free(sk, 2, pts)
        self.circle(sk, 2, (ZERO, ZERO), P("core_d"))
        assert sk.isFullyConstrained, "cross-section sketch is not fully constrained"
        self.section, self.section_occ = sk, occ

    def part_occ(self, parent, key):
        comp = self.part_comps.get(key)
        if comp is not None:
            occ = parent.occurrences.addExistingComponent(comp, adsk.core.Matrix3D.create())
            occ.isGroundToParent = False
            return occ
        name, pn, item, cls, source, desc = self.info(key)
        occ = self.new_occ(parent, name)
        comp = occ.component
        comp.partNumber = pn or name
        comp.description = f"{desc} | BOM: {item}" + (f" | source: {source}" if source else "")
        comp.attributes.add("HelmholtzCage", "key", key)
        self.geometry(key, comp)
        ap = self.appearance(cls)
        for body in comp.bRepBodies:
            body.name = name
            if ap:
                body.appearance = ap
            if cls == "reference":
                body.opacity = COLORS["reference"][1]
        self.part_comps[key] = comp
        adsk.doEvents()
        return occ

    def instantiate(self, node, comp):
        for child, frame, tag in node.children:
            if isinstance(child, Node):
                existing = self.node_comps.get(id(child))
                if existing is not None:
                    occ = comp.occurrences.addExistingComponent(existing, adsk.core.Matrix3D.create())
                    occ.isGroundToParent = False
                    self.places.append((comp, occ, frame, tag))
                    continue
                occ = self.new_occ(comp, child.name)
                self.node_comps[id(child)] = occ.component
                self.places.append((comp, occ, frame, tag))
                self.instantiate(child, occ.component)
            else:
                self.places.append((comp, self.part_occ(comp, child), frame, tag))

    def joint(self, parent, occ, frame, tag):
        zn, flip, ang, offs = joint_spec(frame)
        ji = parent.jointOrigins.createInput(adsk.fusion.JointGeometry.createByPoint(parent.originConstructionPoint))
        if zn == "X":
            ji.zAxisEntity = parent.xConstructionAxis
        elif zn == "Y":
            ji.zAxisEntity = parent.yConstructionAxis
        ji.isFlipped = flip
        if ang:
            ji.angle = VI(f"{ang} deg")
        ji.offsetX, ji.offsetY, ji.offsetZ = (VI(o.expr()) for o in offs)
        jo = parent.jointOrigins.add(ji)
        jo.name = f"at {tag} {occ.name}"
        g = adsk.fusion.JointGeometry.createByPoint(occ.component.originConstructionPoint.createForAssemblyContext(occ))
        jin = parent.joints.createInput(g, jo)
        jin.setAsRigidJointMotion()
        j = parent.joints.add(jin)
        j.name = f"{tag} {occ.name}"

    def group(self, start, name):
        tl = self.des.timeline
        if tl.count - 1 > start:
            tl.timelineGroups.add(start, tl.count - 1).name = name

    def build(self):
        tl = self.des.timeline
        self.make_params()
        t0 = tl.count
        self.make_section()
        self.group(t0, "6575N25 cross-section")
        t0 = tl.count
        self.instantiate(build_tree(), self.root)
        self.group(t0, "Parts")
        t0 = tl.count
        for i, (parent, occ, frame, tag) in enumerate(self.places):
            self.joint(parent, occ, frame, tag)
            if i % 25 == 0:
                adsk.doEvents()
        self.group(t0, "Placements (joint origins driven by User Parameters)")
        self.make_sections()

    def make_sections(self):
        """Section analyses through one X-Y and one Y-Z crossing (+,+,+), on planes that follow the spacings."""
        cps, sa = self.root.constructionPlanes, self.des.analyses.sectionAnalyses
        for name, base, expr in (("Section X-Y crossing (y = Y_spacing/2)", self.root.xZConstructionPlane, "Y_spacing / 2"),
                                 ("Section Y-Z crossing (z = Z_spacing/2)", self.root.xYConstructionPlane, "Z_spacing / 2")):
            pi = cps.createInput()
            pi.setByOffset(base, VI(expr))
            pl = cps.add(pi)
            pl.name = name
            s = sa.add(sa.createInput(pl, 0))
            s.name = name
            s.isLightBulbOn = False


def nesting_report(vals):
    xy = vals["Y_F"] - vals["prof"] - vals["X_F"]
    yz = vals["Z_F"] - vals["prof"] - vals["Y_F"]
    ok = abs(xy - vals["gap"]) < 1e-6 and abs(yz - vals["gap"]) < 1e-6
    return f"nesting gaps X-Y {xy:g} mm, Y-Z {yz:g} mm (gap = {vals['gap']:g}){'' if ok else '  <-- NOT EQUAL TO gap'}"


def run(_context: str):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    des = adsk.fusion.Design.cast(app.activeProduct)
    des.designType = adsk.fusion.DesignTypes.ParametricDesignType
    des.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    des.attributes.add("HelmholtzCage", "build", "revB")
    b = Builder(app, des)
    b.build()
    for c in des.allComponents:                 # hide the ~1000 joint / sketch glyphs
        c.isJointsFolderLightBulbOn = False
        c.isJointOriginsFolderLightBulbOn = False
        c.isSketchFolderLightBulbOn = False
        c.isConstructionFolderLightBulbOn = False
    app.activeViewport.fit()
    items = []
    for i in range(des.timeline.count):
        g = adsk.fusion.TimelineGroup.cast(des.timeline.item(i))
        items += [g.item(j) for j in range(g.count)] if g else [des.timeline.item(i)]
    bad = [it for it in items if it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    print(f"parts: {len(b.part_comps)} definitions, {len(b.places)} placements, timeline {len(items)} items")
    print(nesting_report(b.vals))
    print(f"unhealthy timeline items: {len(bad)}")
    for it in bad[:20]:
        print("  ", it.name, it.errorOrWarningMessage.splitlines()[0] if it.errorOrWarningMessage else "")
