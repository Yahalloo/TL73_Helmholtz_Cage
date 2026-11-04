"""Fusion script: builds the 4040 T-slot Helmholtz cage as a PARAMETRIC (timeline) design.

Same parts and placements as cage_layout.py / HelmholtzCage4040.py, but:
  * every dimension is a sketch dimension or feature extent whose expression uses the
    User Parameters (Modify > Change Parameters);
  * every placement is a joint origin whose offsets are expressions of the User Parameters,
    plus a rigid joint, so changing e.g. Z_spacing moves the Z coils, struts and posts;
  * every 40x40 extrusion is extruded from ONE cross-section sketch (component
    "HFS8-4040 cross-section"). Replace that sketch with the MISUMI profile to update all of them.

Run it once from Utilities > Scripts and Add-Ins, or through the Fusion MCP server. It creates a
new document. After that, edit the design by hand / through the parameters, not by re-running.

Notes for editors
  * Nesting: (Y_F - prof) - X_F and (Z_F - prof) - Y_F must stay equal to gap (10 mm), or the
    coils of neighbouring pairs collide / the crossing spacers no longer fit.
  * Component names carry the cut length (e.g. HFS8-4040-1296.5) and are NOT updated when a
    length parameter changes. Check the L_* parameters for the current cut lengths.
  * MISUMI cuts in 0.5 mm steps; keep X/Y/Z_side and *_spacing on that grid.
"""

import math

import adsk.core
import adsk.fusion

DOC_NAME = "Helmholtz Cage 4040 (parametric)"

# (name, expression, comment). All lengths in mm. Order matters: later ones reference earlier ones.
PARAMS = [
    ("prof", "40 mm", "Profile size (MISUMI HFS8-4040, 10 mm slot)"),
    ("e_c", "7.75 mm", "Winding centroid depth below the outer profile face"),
    ("gap", "10 mm", "Clearance between nested coils (= crossing spacer length)"),
    ("X_side", "1361 mm", "X coil mean-turn side (simulator)"),
    ("Y_side", "1461 mm", "Y coil mean-turn side (simulator)"),
    ("Z_side", "1561 mm", "Z coil mean-turn side (simulator)"),
    ("X_spacing", "722.5 mm", "X pair coil-centre spacing"),
    ("Y_spacing", "776 mm", "Y pair coil-centre spacing"),
    ("Z_spacing", "868.5 mm", "Z pair coil-centre spacing"),
    ("X_F", "X_side / 2 + e_c", "X coil outer face half-width"),
    ("Y_F", "Y_side / 2 + e_c", "Y coil outer face half-width"),
    ("Z_F", "Z_side / 2 + e_c", "Z coil outer face half-width"),
    ("plate_t", "6.35 mm", "Corner L-plate thickness (1/4 in 6061)"),
    ("plate_leg", "60 mm", "Corner L-plate leg length"),
    ("strut_inset", "170 mm", "Strut centre distance from the coil's outer corner"),
    ("riser_h", "80 mm", "Risers under the bottom Y struts"),
    ("wind_w", "15.5 mm", "Winding pack axial width"),
    ("wind_top", "4 mm", "Winding pack top depth below the outer face"),
    ("wind_floor", "11.5 mm", "Winding pack floor depth below the outer face"),
    ("r_floor", "12 mm", "Corner groove floor radius"),
    # constants of cage_layout.py, exposed so they can be edited too
    ("slot_neck_w", "10.2 mm", "Profile slot opening width (simplified section)"),
    ("slot_neck_d", "4 mm", "Profile slot lip thickness (simplified section)"),
    ("slot_cav_w", "16 mm", "Profile slot cavity width (simplified section)"),
    ("slot_cav_d", "11.5 mm", "Profile slot cavity floor depth below the face (simplified section)"),
    ("core_d", "6.8 mm", "Profile centre bore"),
    ("groove_clr", "0.5 mm", "Corner guide groove clearance per side of the winding"),
    ("brk_leg", "40 mm", "HBLFS8 bracket leg (simplified envelope)"),
    ("brk_t", "6 mm", "HBLFS8 bracket thickness (simplified envelope)"),
    ("brk_w", "35 mm", "HBLFS8 bracket width (simplified envelope)"),
    ("hole_d", "9 mm", "M8 clearance hole"),
    ("spacer_od", "16 mm", "Crossing spacer OD"),
    ("spacer_id", "8.4 mm", "Crossing spacer ID"),
    ("clip_l", "60 mm", "Slot retainer clip length"),
    ("cradle_t", "8 mm", "6U cradle base thickness"),
    ("sat_x", "100 mm", "6U envelope x"),
    ("sat_y", "226.3 mm", "6U envelope y"),
    ("sat_z", "366 mm", "6U envelope z (long axis along cage Z)"),
    ("wv_margin", "10 mm", "Working volume margin around the 6U envelope"),
    # derived
    ("L_mem_X", "2 * (X_F - prof)", "Cut length: X coil member"),
    ("L_mem_Y", "2 * (Y_F - prof)", "Cut length: Y coil member"),
    ("L_mem_Z", "2 * (Z_F - prof)", "Cut length: Z coil member"),
    ("L_strut_X", "X_spacing - prof", "Cut length: X pair strut"),
    ("L_strut_Y", "Y_spacing - prof", "Cut length: Y pair strut"),
    ("L_strut_Z", "Z_spacing - prof", "Cut length: Z pair strut"),
    ("xs", "Y_F - strut_inset", "Global x of the Y/Z struts and the base rails"),
    ("zt", "-Y_F - riser_h", "Base rail top (z)"),
    ("L_rail", "2 * Z_F + 80 mm", "Cut length: base rail (extends past the posts)"),
    ("L_cross", "2 * (xs - prof / 2)", "Cut length: base cross member"),
    ("L_riser", "riser_h", "Cut length: riser"),
    ("L_post", "-(Z_spacing / 2 + prof / 2) - zt", "Cut length: post under the bottom Z coil"),
    ("col_top", "zt + floor((-sat_z / 2 - cradle_t - zt) / (1 mm) * 2) / 2 * (1 mm)",
     "Centre column top = cradle base (0.5 mm grid)"),
    ("L_col", "col_top - zt", "Cut length: centre column"),
]

AX = "XYZ"
TRANSVERSE = {0: (1, 2), 1: (2, 0), 2: (0, 1)}
UV = {0: (1, 2), 1: (0, 2), 2: (0, 1)}            # in-plane model axes of the plane normal to axis n
TURNS = {0: 43, 1: 38, 2: 41}                      # from design.json (all AWG 14)
COLORS = {
    "aluminium": ((190, 194, 200), 1.0),
    "copper": ((196, 110, 50), 1.0),
    "printed": ((240, 130, 30), 1.0),
    "purchased": ((200, 30, 30), 1.0),
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


def fork_frame(origin, n, r):
    return frame_xy(origin, n, cross(r, n))


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


# ------------------------------------------------------------------ assembly tree (same as cage_layout.build)
class Node:
    def __init__(self, name):
        self.name = name
        self.children = []

    def add(self, child, frame=IDENT, tag=""):
        self.children.append((child, frame, tag))
        return child


PART_INFO = {
    # key: (component name, part number, BOM item, class, source, description)
    "BRACKET": ("HBLFS8", "HBLFS8", "Bracket HBLFS8", "aluminium", "MISUMI",
                "90 deg tabbed bracket, die-cast aluminium, 8 series (fasteners not included)"),
    "BRACKET_X": ("HBLFS8 (crossing)", "HBLFS8", "Bracket HBLFS8 (crossing)", "aluminium", "MISUMI",
                  "Same bracket; the screw through the 10 mm spacer is M8x30"),
    "SPACER": ("Spacer 16OD x 10 for M8", "search: aluminum unthreaded spacer M8, 16 mm OD, 10 mm long",
               "Spacer 16OD x 10 for M8", "aluminium", "McMaster-Carr", "Sets the 10 mm gap between nested coils"),
    "PLATE": ("Corner plate (laser cut)", "6061-T6 0.250 in", "Corner plate (laser cut)", "aluminium",
              "SendCutSend / OSH Cut", "L-plate on both axial faces of each coil corner; sets squareness"),
    "CORNER": ("PRT-CORNER", "PRT-CORNER", "Corner wire guide (print)", "printed", "3D print, ASA or PETG",
               "Fills the corner cube, carries the winding around a 12 mm floor radius; keyed into both members"),
    "CLIP": ("PRT-CLIP", "PRT-CLIP", "Slot retainer clip (print)", "printed", "3D print, PETG",
             "Snaps into the slot neck over the winding"),
    "FORK": ("PRT-FORK", "PRT-FORK", "Crossing locator fork (print)", "printed", "3D print, ASA or PETG",
             "Keys into one coil's slot and straddles the crossing member of the next pair"),
    "TERMINAL": ("PRT-TERM", "PRT-TERM", "Coil terminal block (print)", "printed", "3D print, PETG",
                 "Holds the coil's Powerpole pair + strain relief"),
    "PP_RED": ("Anderson 1327G6", "Anderson 1327G6 (+ 1331 contact)", "Powerpole PP30 housing red", "purchased",
               "Powerwerx / DigiKey", "Coil + terminal"),
    "PP_BLK": ("Anderson 1327", "Anderson 1327 (+ 1331 contact)", "Powerpole PP30 housing black", "purchased",
               "Powerwerx / DigiKey", "Coil - terminal"),
    "CRADLE": ("PRT-CRADLE", "PRT-CRADLE", "6U cradle (print)", "printed", "3D print, PETG",
               "Locates a 6U CubeSat long-axis-vertical"),
    "FOOT": ("PRT-FOOT", "PRT-FOOT", "Base foot pad (print)", "printed", "3D print, TPU or PETG",
             "Non-magnetic foot under the base rails"),
    "GAUGE50": ("PRT-GAUGE50", "PRT-GAUGE50", "Strut locator gauge 50 (print, tool)", "printed", "3D print, PETG",
                "Removable: sets X/Y strut position from the corner plate"),
    "GAUGE100": ("PRT-GAUGE100", "PRT-GAUGE100", "Strut locator gauge 100 (print, tool)", "printed",
                 "3D print, PETG", "Removable: sets Z strut / post position from the corner plate"),
    "REF_6U": ("6U envelope (reference)", "", "6U envelope (reference)", "reference", "", "Not built"),
    "REF_WV": ("Working volume 6U+10 (reference)", "", "Working volume 6U+10 (reference)", "reference", "",
               "Not built"),
}
PROFILE_KEYS = {}                    # part key -> length parameter name


def profile_part(lparam):
    key = "PROFILE:" + lparam
    PROFILE_KEYS[key] = lparam
    return key


def bracket(node, corner, nB, nA, tag, key="BRACKET"):
    node.add(key, frame_xy(corner, nB, nA), tag)


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
            for sc in (1, -1):
                n.add("PLATE", frame_xy((sa * F, sb * F, sc * (H + P("plate_t") * 0.5)), (sa, 0, 0), (0, sb, 0)),
                      "plate")
            n.add("BRACKET", frame_xy((sa * (F - PROF), sb * (F - PROF), 0), (-sa, 0, 0), (0, -sb, 0)), "bracket")
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


def strut_positions():
    Fx, Fy, Fz = (P(a + "_F") for a in AX)
    xs, ins = P("xs"), P("strut_inset")
    return {
        0: [(sa * (Fx - ins), sb * (Fx - H), 0) for sa in (1, -1) for sb in (1, -1)],
        1: [(sa * (Fy - H), sb * xs, 1) for sa in (1, -1) for sb in (1, -1)],
        2: [(sa * xs, sb * (Fz - H), 0) for sa in (1, -1) for sb in (1, -1)],
    }


def build_pair(ax, coil, struts):
    A, d = AX[ax], P(AX[ax] + "_spacing")
    n = Node(f"Pair {A}")
    for s in (1, -1):
        n.add(coil, frame_xy((0, 0, s * d * 0.5), (1, 0, 0), (0, 1, 0)), f"coil{'+' if s > 0 else '-'}")
    pk = profile_part("L_strut_" + A)
    for a, b, k in struts:
        n.add(pk, frame_z((a, b, -(d * 0.5 - H)), (0, 0, 1)), "strut")
        for top in (True, False):
            ce = (d * 0.5 - H) if top else -(d * 0.5 - H)
            for s in (1, -1):
                p = [Lin.of(a), Lin.of(b), ce]
                p[k] = p[k] + s * H
                n.add("BRACKET", frame_xy(p, unit(k, s), (0, 0, -1 if top else 1)), "strut_bracket")
    return n


def build_tree():
    root = Node("root")
    Fx, Fy, Fz = (P(a + "_F") for a in AX)
    dX, dY, dZ = (P(a + "_spacing") for a in AX)
    xs, zt, col_top = P("xs"), P("zt"), P("col_top")
    struts = strut_positions()
    for ax in range(3):
        u, v = TRANSVERSE[ax]
        root.add(build_pair(ax, build_coil(ax), struts[ax]), frame_xy((0, 0, 0), unit(u), unit(v)), f"pair{AX[ax]}")

    xing = Node("Crossing mounts")
    for sx in (1, -1):
        for sy in (1, -1):
            for sz in (1, -1):
                bracket(xing, (sx * (dX * 0.5 + H), sy * dY * 0.5, sz * Fx), (sx, 0, 0), (0, 0, -sz), "xy_bracket",
                        "BRACKET_X")
                xing.add("SPACER", frame_z((sx * (dX * 0.5 + PROF), sy * dY * 0.5, sz * Fx), (0, 0, sz)), "xy_spacer")
                xing.add("FORK", fork_frame((sx * (dX * 0.5 - H), sy * dY * 0.5, sz * (Fx - H)), (-sx, 0, 0),
                                            (0, 0, sz)), "xy_fork")
                bracket(xing, (sx * Fy, sy * (dY * 0.5 + H), sz * dZ * 0.5), (0, sy, 0), (-sx, 0, 0), "yz_bracket",
                        "BRACKET_X")
                xing.add("SPACER", frame_z((sx * Fy, sy * (dY * 0.5 + PROF), sz * dZ * 0.5), (sx, 0, 0)), "yz_spacer")
                xing.add("FORK", fork_frame((sx * (Fz - H), sy * dY * 0.5, sz * (dZ * 0.5 + H)), (0, 0, sz),
                                            (-sx, 0, 0)), "yz_fork")
    root.add(xing, IDENT, "crossings")

    base = Node("Base")
    rail, xm = profile_part("L_rail"), profile_part("L_cross")
    riser, post, col = profile_part("L_riser"), profile_part("L_post"), profile_part("L_col")
    for sx in (1, -1):
        base.add(rail, frame_z((sx * xs, -(Fz + 40), zt - H), (0, 1, 0)), "rail")
        for yr in (250.0, -250.0):
            base.add(riser, frame_z((sx * xs, yr, zt), (0, 0, 1)), "riser")
            for s in (1, -1):
                bracket(base, (sx * xs, yr + s * H, zt), (0, s, 0), (0, 0, 1), "riser_bracket")
                bracket(base, (sx * xs, yr + s * H, -Fy), (0, s, 0), (0, 0, -1), "riser_bracket")
        for sy in (1, -1):
            px, py = sx * xs, sy * (Fz - H)
            base.add(post, frame_z((px, py, zt), (0, 0, 1)), "post")
            for s in (1, -1):
                bracket(base, (px, py + s * H, zt), (0, s, 0), (0, 0, 1), "post_bracket")
                bracket(base, (px + s * H, py, -(dZ * 0.5 + H)), (s, 0, 0), (0, 0, -1), "post_bracket")
            base.add("FOOT", frame_z((sx * xs, sy * (Fz + 10), zt - 50), (0, 0, 1)), "foot")
    for yc in (Fz - H, ZERO, -(Fz - H)):
        base.add(xm, frame_z((-(xs - H), yc, zt - H), (1, 0, 0)), "cross")
        for sx in (1, -1):
            for s in (1, -1):
                bracket(base, (sx * (xs - H), yc + s * H, zt - H), (-sx, 0, 0), (0, s, 0), "base_bracket")
    base.add(col, frame_z((0, 0, zt), (0, 0, 1)), "column")
    for s in (1, -1):
        bracket(base, (s * H, 0, zt), (s, 0, 0), (0, 0, 1), "column_bracket")
    root.add(base, IDENT, "base")

    fix = Node("CubeSat fixture")
    fix.add("CRADLE", frame_z((0, 0, col_top), (0, 0, 1)), "cradle")
    root.add(fix, IDENT, "fixture")
    ref = Node("Reference (not built)")
    ref.add("REF_6U", IDENT, "ref")
    ref.add("REF_WV", IDENT, "ref")
    root.add(ref, IDENT, "ref")
    tools = Node("Assembly tools (removable)")
    tools.add("GAUGE50", frame_z((Fz + 300, 0, zt), (0, 0, 1)), "tool")
    tools.add("GAUGE100", frame_z((Fz + 300, 100, zt), (0, 0, 1)), "tool")
    root.add(tools, IDENT, "tools")
    return root


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

    def poly(self, sk, n, pts):
        """Closed axis-aligned polygon; pts are (u, v) Lin pairs in the component frame."""
        lines, gc = sk.sketchCurves.sketchLines, sk.geometricConstraints
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
        x_is_u = self.sketch_x_is_u(sk, n)
        for ln, p, q in made:
            const_u = Lin.of(p[0]).expr() == Lin.of(q[0]).expr()
            const = Lin.of(p[0] if const_u else p[1])
            vertical = const_u == x_is_u          # constant sketch-x
            (gc.addVertical if vertical else gc.addHorizontal)(ln)
            self.dim_coord(sk, ln.startSketchPoint, const, vertical)

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
        L, T, w = P("brk_leg"), P("brk_t"), P("brk_w") * 0.5
        b = self.box(comp, (0, L, 0, T, -w, w))
        self.box(comp, (0, T, 0, L, -w, w), JOIN, b)
        self.cyl(comp, 1, (L * 0.5, 0), P("hole_d"), -1, T + 1, CUT, b)
        self.cyl(comp, 0, (L * 0.5, 0), P("hole_d"), -1, T + 1, CUT, b)

    def g_plate(self, comp):
        t, leg = P("plate_t") * 0.5, P("plate_leg")
        b = self.box(comp, (-PROF, 0, -PROF, 0, -t, t))
        self.box(comp, (-PROF, 0, -PROF - leg, -PROF, -t, t), JOIN, b)
        self.box(comp, (-PROF - leg, -PROF, -PROF, 0, -t, t), JOIN, b)
        for x, y in ((-H, -PROF - leg * 0.5), (-PROF - leg * 0.5, -H), (-PROF * 0.75, -PROF * 0.75)):
            self.cyl(comp, 2, (x, y), P("hole_d"), -t - 1, t + 1, CUT, b)

    def g_corner(self, comp):
        wf, w = P("wind_floor"), P("wind_w") * 0.5 + P("groove_clr")
        b = self.box(comp, (-PROF, 0, -PROF, 0, -H, H))
        self.box(comp, (-wf, 1, -PROF - 1, 1, -w, w), CUT, b)          # groove: the two straight runs
        self.box(comp, (-PROF - 1, 1, -wf, 1, -w, w), CUT, b)
        f = -self.v(wf)
        self.fillet_z_edges(comp, b, [(f, f)], "r_floor")              # groove floor radius at the corner
        h = P("slot_neck_w") * 0.5 - 0.2
        n0 = H - P("slot_neck_d") + 0.3
        for z0, z1 in ((n0, H), (-H, -n0)):                            # tongues in the side-slot necks
            self.box(comp, (-H - h, -H + h, -PROF - 15, -PROF, z0, z1), JOIN, b)
            self.box(comp, (-PROF - 15, -PROF, -H - h, -H + h, z0, z1), JOIN, b)
        self.cyl(comp, 2, (-PROF * 0.75, -PROF * 0.75), P("hole_d"), -H - 1, H + 1, CUT, b)
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
        a1, a0, w = F - P("wind_top"), F - P("wind_floor"), P("wind_w") * 0.5
        b = self.box(comp, (-a1, a1, -a1, a1, -w, w))
        self.box(comp, (-a0, a0, -a0, a0, -w - 1, w + 1), CUT, b)
        o, i = self.v(a1), self.v(a0)
        self.fillet_z_edges(comp, b, [(sx * o, sy * o) for sx in (1, -1) for sy in (1, -1)],
                            "r_floor + wind_floor - wind_top")
        self.fillet_z_edges(comp, b, [(sx * i, sy * i) for sx in (1, -1) for sy in (1, -1)], "r_floor")

    def g_spacer(self, comp):
        b = self.cyl(comp, 2, (0, 0), P("spacer_od"), 0, P("gap"))
        self.cyl(comp, 2, (0, 0), P("spacer_id"), -1, P("gap") + 1, CUT, b)

    def neck(self):
        return P("slot_neck_w") * 0.5 - 0.2

    def g_clip(self, comp):
        h = self.neck()
        self.box(comp, (-3.8, 0, -P("clip_l") * 0.5, P("clip_l") * 0.5, -h, h))

    def g_fork(self, comp):
        h = self.neck()
        b = self.box(comp, (0, 10, -30, 30, -15, 25))
        self.box(comp, (0, 10, -30, -(H + 0.2), 25, 50), JOIN, b)
        self.box(comp, (0, 10, H + 0.2, 30, 25, 50), JOIN, b)
        self.box(comp, (-3.8, 0, -25, 25, -h, h), JOIN, b)
        self.cyl(comp, 0, (0, 0), P("hole_d"), -5, 11, CUT, b)

    def g_terminal(self, comp):
        h = self.neck()
        b = self.box(comp, (0, 12, -25, 25, -15, 15))
        self.box(comp, (-3.8, 0, -20, 20, -h, h), JOIN, b)
        self.cyl(comp, 0, (-17, 0), P("hole_d"), -5, 13, CUT, b)
        self.box(comp, (3, 7, 21, 24, -16, 16), CUT, b)            # zip-tie slot for lead strain relief

    def g_pp(self, comp):
        self.box(comp, (0, 7.9, 0, 24.6, -3.95, 3.95))

    def g_cradle(self, comp):
        t = P("cradle_t")
        hx, hy = P("sat_x") * 0.5 + 0.3, P("sat_y") * 0.5 + 0.3
        b = self.box(comp, (-70, 70, -133, 133, 0, t))
        for sx in (1, -1):
            for sy in (1, -1):
                self.box(comp, (sx * hx, sx * (hx + 8), sy * (hy - 25), sy * (hy + 8), t, t + 40), JOIN, b)
                self.box(comp, (sx * (hx - 25), sx * (hx + 8), sy * hy, sy * (hy + 8), t, t + 40), JOIN, b)
        self.cyl(comp, 2, (0, 0), P("hole_d"), -1, t + 1, CUT, b)

    def g_foot(self, comp):
        h = self.neck()
        b = self.box(comp, (-30, 30, -30, 30, 0, 10))
        self.box(comp, (-h, h, -25, 25, 10, 13.8), JOIN, b)

    def g_gauge(self, comp, length):
        h = self.neck()
        b = self.box(comp, (0, length, -20, 20, 0, 10))
        self.box(comp, (0, length, -h, h, -3.8, 0), JOIN, b)

    def g_refbox(self, comp, sx, sy, sz):
        self.box(comp, (-sx * 0.5, sx * 0.5, -sy * 0.5, sy * 0.5, -sz * 0.5, sz * 0.5))

    def geometry(self, key, comp):
        if key in PROFILE_KEYS:
            return self.g_profile(comp, PROFILE_KEYS[key])
        if key.startswith("WIND_"):
            return self.g_winding(comp, P(key[-1] + "_F"))
        if key in ("GAUGE50", "GAUGE100"):
            return self.g_gauge(comp, 50.0 if key == "GAUGE50" else 100.0)
        if key == "REF_6U":
            return self.g_refbox(comp, P("sat_x"), P("sat_y"), P("sat_z"))
        if key == "REF_WV":
            m = P("wv_margin") * 2
            return self.g_refbox(comp, P("sat_x") + m, P("sat_y") + m, P("sat_z") + m)
        return {"BRACKET": self.g_bracket, "BRACKET_X": self.g_bracket, "PLATE": self.g_plate,
                "CORNER": self.g_corner, "SPACER": self.g_spacer, "CLIP": self.g_clip, "FORK": self.g_fork,
                "TERMINAL": self.g_terminal, "PP_RED": self.g_pp, "PP_BLK": self.g_pp, "CRADLE": self.g_cradle,
                "FOOT": self.g_foot}[key](comp)

    def info(self, key):
        """(name, part number, BOM item, class, source, description) of a part key, at the current parameters."""
        if key in PROFILE_KEYS:
            pn = f"HFS8-4040-{self.vals[PROFILE_KEYS[key]]:g}"
            return (pn, pn, f"HFS8-4040 x {self.vals[PROFILE_KEYS[key]]:g} mm", "aluminium",
                    "MISUMI (cut to length, 0.5 mm steps)",
                    f"40x40 aluminium extrusion, 8 series, 10 mm slot; length = parameter {PROFILE_KEYS[key]}")
        if key.startswith("WIND_"):
            ax = AX.index(key[-1])
            nm = f"Winding {key[-1]} ({TURNS[ax]} t AWG14)"
            side = 2 * (self.vals[key[-1] + "_F"] - self.vals["e_c"])
            return (nm, "", nm, "copper", "Magnet wire, heavy build",
                    f"{TURNS[ax]} turns, mean turn {side:.1f} mm (= {key[-1]}_side)")
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
        occ = self.new_occ(self.root, "HFS8-4040 cross-section")
        occ.isGroundToParent = True
        comp = occ.component
        comp.description = ("Simplified HFS8-4040 section driving every 40x40 extrusion. "
                            "Replace this sketch with the MISUMI CAD section (keep one closed outer profile).")
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.name = "HFS8-4040 section"
        a, nw, cw = H, P("slot_neck_w") * 0.5, P("slot_cav_w") * 0.5
        nd, cd = H - P("slot_neck_d"), H - P("slot_cav_d")
        top = [(a, a), (nw, a), (nw, nd), (cw, nd), (cw, cd), (-cw, cd), (-cw, nd), (-nw, nd), (-nw, a)]
        pts = []
        for k in range(4):                      # the top face's slot, rotated to each face (CCW)
            for x, y in top:
                for _ in range(k):
                    x, y = -y, x
                pts.append((x, y))
        self.poly(sk, 2, pts)
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
        self.group(t0, "HFS8-4040 cross-section")
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
    des.attributes.add("HelmholtzCage", "build", "parametric")
    b = Builder(app, des)
    b.build()
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
