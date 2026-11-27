# TL73 Helmholtz Cage coil driver - printed enclosure (box + vented lid) with panel connectors.
# Fusion script. Run from the Text Commands window (Py):  exec(open(r"<this file>").read())
#
# Idea: the shrouded jacks on the PCB are never touched in normal use. Short internal leads go from the
# PCB jacks to panel-mount shrouded jacks in the enclosure walls. Only the panel jacks see wear, and they
# can be replaced without touching the PCB.
#
# Origin = centre of the shield PCB, +Y = Nucleo USB end, floor underside at z = 0.  All values in mm.
# The floor keeps the hole pattern of TL73_PCB_Mount.py, so the same bought M3 standoffs are used.
import adsk.core, adsk.fusion, traceback, os, math

OUT_DIR = r"D:\GoogleDrive_Personal\Documents\Uni Courses\Final Year\T1\ELEC 491\Project_Design_Files\Repositry\PCB_V1.0\TL73_Helmholtz_Cage\Mechanical"

# ---------------- editable dimensions ----------------
WALL_T        = 3.0     # wall thickness
FLOOR_T       = 4.0     # floor thickness (same as the old base plate)
LID_T         = 3.0
X_IN          = 72.0    # inner half width  (PCB half width is 49.5: 22.5 mm each side for cables, fan and stop switch)
Y_FRONT_IN    = -125.0  # inner face of the front wall (coil side). PCB jack mouth is near y = -63:
                        # leaves about 60 mm for the internal plug and its cable bend
Y_BACK_IN     = 124.0   # inner face of the back wall (34 V supply side). PCB supply jacks CN1201 / CN1202 reach y = 62.2
                        # (board file of 27 Nov, after the 11.2 mm move): 61.8 mm left for the plug and its cable bend
Z_TOP         = 90.0    # top of the walls (lid sits on this)
CORNER_R      = 5.0
# Banana jacks: Cal Test CT4397-01-x, 4 mm sheathed (shrouded) panel jack with M4 stud. Datasheet CT4397 rev H.
# The jack goes in from outside, its round nut is tightened inside, and the internal lead is held on the M4 stud.
JACK_HOLE_D   = 12.2    # panel hole: 12.0 +0.1 on the datasheet, 0.2 mm extra for printing
JACK_FLAT     = 11.2    # across the two flats of the double-D hole (11.0 +0.1): stops the jack from turning
JACK_HEAD_D, JACK_HEAD_L = 14.6, 6.0     # collar that stays outside the wall
JACK_BODY_D, JACK_BODY_L = 12.0, 18.0    # M12x0.75 threaded body behind the collar
JACK_STUD_D, JACK_STUD_L = 4.0, 9.7      # M4 stud
JACK_STEP_URL = "https://as.caltestelectronics.com/public/attachment/810/CT4397-01_728afcd315c740528572acf29f3a184b.zip"
JACK_Z        = 72.0    # height of the panel jacks
JACK_PITCH    = 19.0    # + to - spacing of one pair
COIL_PAIR_X   = [-42.0, 0.0, 42.0]   # centre of the X, Y, Z pairs on the front wall
SUPPLY_X      = 19.0    # +34 V at +x, GND at -x on the back wall (same sides as on the PCB)
# USB feed-through: Adafruit 4259 round panel adapter, USB-C socket outside, USB-A socket inside
# (a short USB-A to micro-B cable goes from it to the Nucleo). Published sizes: about 30 mm lip, about 41 mm long.
# The thread / hole size is NOT published: USB_HOLE_D is an estimate, measure the part before printing.
USB_HOLE_D    = 24.5
USB_LIP_D, USB_LIP_T = 30.0, 3.0
USB_BODY_D, USB_LEN  = 24.0, 41.0
USB_Y, USB_Z  = 78.0, 62.0           # on the right wall, above and behind the Nucleo so the inner plug has room
# Sensor connectors: Switchcraft EN3 panel connectors with solder cups (EN3P2MX = 2 pin, EN3P6MX = 6 pin).
# Drawing EN3P_M: D-shaped hole 0.610 in diameter, 0.582 in across the flat. Flange and gasket inside, hex nut outside.
EN3_HOLE_D    = 15.8    # 15.49 + 0.3 clearance
EN3_FLAT      = 15.1    # 14.78 + 0.3: distance from the flat to the opposite side of the hole
EN3_FLANGE_D  = 20.62   # 0.812 in
EN3_THREAD_D  = 15.4    # threaded shell (5/8"-27 nominal, must pass the 15.49 mm hole)
EN3_FRONT_L   = 21.0    # 0.827 in from the flange to the mating end
EN3_REAR_L    = 5.6     # 0.22 in solder cups behind the flange
EN3_NUT_AF    = 22.2    # hex nut across flats (not dimensioned on the drawing: assumed 7/8 in)
EN3_Z         = 69.0
# left wall connectors: (label, y centre, number of pins)
EN3_LIST      = [("NTC X", 60.0, 2), ("NTC Y", 30.0, 2), ("NTC Z", 0.0, 2), ("MAG", -30.0, 6)]
VENT_W, VENT_H, VENT_Z0 = 4.0, 28.0, 12.0  # wall vent slots (all four walls)
VENT_Y        = list(range(-110, 101, 10))             # both side walls
FRONT_VENT_X  = list(range(-60, 61, 10))
BACK_VENT_X   = list(range(-60, 61, 10))
VENT_FB_H     = 18.0
LID_VENT_X    = list(range(-60, 61, 6))
LID_VENT_Y    = (-52.0, 34.0)        # lid slots over the drivers, the 5 V buck and the Nucleo
LID_VENT_W    = 3.0
LOGO_C        = (0.0, -89.0)         # team logo centre on the lid
LOGO_W        = 44.0                 # team logo width
LID_PARK_GAP  = 20.0                 # in the assembly the lid (with its fan and guard) is laid beside the box, this far
                                     # beyond the outer face of the control pod; LID_PARK is worked out below the pod parameters
POST          = 10.0    # lid screw posts: two in the back corners, two on the side walls near the front
# The posts are in the four corners again: with X_IN = 72 they start at x = 62, clear of the outer coil jacks
# (x = +/-51.5, body 12 mm, nut about 17 mm, so the nut ends near x = 60).
# ---- fan in the lid, directly above the three DRV8873S drivers (2026-11-27 layout) ----
# Fan: Sunon MF40100V1-1000U-A99, 40 x 40 x 10 mm, 5 V, 136 mA, under the lid blowing DOWN onto the drivers;
# Qualtek 08149 guard on top of the lid. M3 screws go through guard, lid and fan frame, nuts under the fan.
# Centre = centroid of U301 / U401 / U501 in TL_73_Helmholtz_Cage_PCB.kicad_pcb (board centre origin, +y = supply end):
# U301 (-31.6, -12.2), U401 (1.0, -12.2), U501 (33.6, -12.2). The drivers span 65 mm, so a 40 mm fan sits right over
# U401 and blows on the edges of U301 / U501; the wall vents are the exhaust (no lid vent slots any more).
FAN_X, FAN_Y  = 1.0, -12.2
FAN_SIZE, FAN_T = 40.0, 10.0
FAN_HOLE_D    = 38.0                 # air opening in the lid
FAN_SCREW_PITCH, FAN_SCREW_D = 32.0, 3.4   # M3 clearance on the standard 32 mm square
FAN_LEAD_MIN  = 250.0                # fan lead needed to reach J206 (-7.5, 26.0) with the lid lifted off and set beside the box
USE_LID_VENTS = False                # the lid slots of the old layout would short-circuit the fan inlet
# ---- control pod: an annex of the BASE on the right (+x) side, next to the LED headers J203 / J207 / J208 ----
# Its top is a fixed horizontal deck (part of the base, NOT the lid) that carries the stop switch and the three LEDs
# facing up. The pod is open to the main cavity through a window in the right wall, so the leads run straight to the
# headers; the lid covers only the main box and lifts off without touching them.
# Print: base floor-down. The deck rests on the right wall, the pod outer wall and the two end walls; 45 degree chamfers
# under its two long edges leave a POD_BRIDGE wide strip that bridges (no other horizontal overhang).
POD_Y0, POD_Y1 = -70.0, 40.0         # outer extent along y (clear of the wall-mount ears and of the USB adapter)
POD_W_IN      = 44.0                 # inside width (x) from the outer face of the right wall
POD_DECK_Z    = Z_TOP + LID_T        # top of the deck flush with the top of the lid (more visible); the deck is still base
# parked lid: its -x edge LID_PARK_GAP beyond the pod's outer face (the pod is the part of the base furthest out in +x,
# past the right mounting ears); raised by FAN_T so the fan hanging under it rests on the floor plane z = 0
LID_PARK      = ((X_IN + WALL_T) + POD_W_IN + WALL_T + LID_PARK_GAP + (X_IN + WALL_T), 0.0, FAN_T - Z_TOP)
GUARD_T       = 2.0                  # stand-in thickness of the Qualtek 08149 guard on top of the lid
LID_GAP       = 0.3                  # fit gap between the lid edge and the pod wall above the lid seam (lid lifts straight up)
DECK_T        = 4.5                  # deck thickness, stiff enough for a hard palm strike on the stop switch. The parts
                                     # need thinner panels, made by counterbores from below: EAO 1 to 3 mm (STOP_PANEL_T),
                                     # Lumex 2.5 mm max (LED_PANEL_T)
STOP_PANEL_T  = 3.0                  # deck left at the stop switch: top of the EAO panel range, inside a STOP_NUT_POCKET_D counterbore
POD_CHAMFER   = 17.0                 # 45 degree support under both long edges -> bridge = POD_W_IN - 2 * POD_CHAMFER
RIB_T         = 3.0                  # ribs across the pod under the deck, either side of the stop switch, tying the deck
RIB_Y         = (-48.0, -12.0)       # to both pod walls; bottom edge is a 45 degree inverted V (prints without support)
RIB_DEPTH_MID = 6.0                  # rib depth under the deck centre line (it grows to 6 + half the pod width at the walls)
POD_WIN_W, POD_WIN_Z0, POD_WIN_Z1 = 80.0, 10.0, 20.0   # wire / hand-access window in the right wall: width, sill height,
                                     # top of its vertical sides (45 degree gable above, apex at POD_WIN_Z1 + POD_WIN_W / 2)
# Stop switch: EAO 51-256.025 (16 mm emergency stop, twist to unlock, 1 NC + 1 NO gold contacts, solder terminals).
# Datasheet in vendor_models. Cut-out: hole 16.2 +0.2 with an anti-rotation lug that sticks INTO the hole:
# 1.7 -0.1 wide, 15.0 +0.1 from the lug face to the far side of the hole. Panel 1 to 3 mm. Behind the panel 26.3 mm
# to the end of the solder terminals (drawing), head 19 mm above it, 30 mm minimum spacing to the next device.
STOP_Y        = -30.0                      # along the pod deck (x is the deck centre line)
STOP_NUT_POCKET_D, STOP_NUT_POCKET_H = 28.0, 6.0   # clear pocket under the deck for the fixing nut and fingers
STOP_HOLE_D   = 16.4                       # 16.2 + 0.2 for printing
STOP_LUG_W    = 1.5                        # 1.6 to 1.7 on the drawing, a little under so it can be filed to fit
STOP_LUG_GAP  = 15.2                       # lug face to the opposite side of the hole (15.0 + 0.2 for printing)
STOP_HEAD_D, STOP_HEAD_L, STOP_DEPTH = 24.5, 19.0, 26.3   # mushroom head; depth behind the panel incl. terminals
STOP_WIRE_BEND = 15.0                      # room under the terminals for the soldered leads
# Status LEDs: Lumex SSI-LXH312xD-150 snap-in indicators (3 mm LED, 150 mm leads). Distributor data: hole 0.170 to
# 0.174 in, panel 2.5 mm max. A recess under each hole leaves LED_PANEL_T. Check both numbers against the part.
LED_HOLE_D    = 4.4
LED_PANEL_T   = 2.0
LED_RECESS_D  = 10.0
LED_BODY_DEPTH = 12.0                      # clear space under each LED for the body and its leads
LED_Y         = [("FAULT", -2.0), ("RUN", 9.0), ("IDLE", 20.0)]   # same order as J208 / J207 / J203 on the board
# Lid screws: M3 machine screws into M3 heat-set brass inserts (standard 5.7 mm long, about 4.6 mm outside
# diameter) pressed into the posts with a soldering iron. Check INSERT_D against the insert maker's hole size.
INSERT_D      = 4.0     # hole for the insert
INSERT_L      = 7.0     # hole depth for a 5.7 mm insert
SCREW_RELIEF_D, SCREW_RELIEF_L = 3.2, 12.0   # narrower hole below the insert so an M3x8 or M3x10 screw has room
EAR_W, EAR_L  = 16.0, 22.0           # wall-mount ears
EAR_Y         = (-95.0, 85.0)
EAR_HOLE_D    = 4.5
TEXT_H        = 5.0
TEXT_DEPTH    = 0.6
FONT          = "Arial"
# per-face (horizontal flip, vertical flip) that makes the engraved text read correctly from outside
TEXT_FIX      = {"front": (0, 1), "back": (1, 1), "left": (1, 0), "right": (0, 0), "top": (0, 0)}

# ---------------- from TL73_PCB_Mount.py / the KiCad board ----------------
STANDOFF_H   = 25.0
NUC_STANDOFF_H = 12.0
HEX_AF       = 5.5
M3_CLEAR_D   = 3.4
CBORE_D      = 6.5
CBORE_DEPTH  = 2.5
HOLES        = [(-46.0, 45.5), (46.0, 45.5), (-46.0, -22.5), (46.0, -22.5)]
NUC_W, NUC_L, NUC_T = 70.0, 82.5, 1.644
NUC_Y_TOP    = 74.5
STACK_GAP    = 11.04
NUC_HOLES    = [(43.89, 2.5), (10.87, 54.57), (59.13, 53.3)]
MODEL_FIXES  = {"ANT-TH_L33.0-W12.0": (-9.71, 0.0, 6.55),
                "CAP-TH_BD10.0-P5.00-D0.6-FD": (0.0, 0.0, 8.01),
                "CAP-TH_BD10.0-P5.00-D0.6-FD-A": (0.0, 0.0, 0.0)}
# The buzzer BZ201 (EasyEDA model "BUZ-TH_BD9.0-P5.00-D0.6-L-FD") is new in the 27 Nov STEP. It sits on the board in
# KiCad's own 3D view; if Fusion shows it floating or sunk like the radial capacitors, add its offset here, e.g.
# MODEL_FIXES["BUZ-TH_BD9.0-P5.00-D0.6-L-FD"] = (0.0, 0.0, dz)
PCB_STEP     = "TL73_Shield_PCB_KiCad.step"
NUC_STEP     = "NUCLEO_G474RE.step"

mm = 0.1
VI = adsk.core.ValueInput
P3 = adsk.core.Point3D
NEW  = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT  = adsk.fusion.FeatureOperations.CutFeatureOperation
log = []

def profs(sk):
    c = adsk.core.ObjectCollection.create()
    for p in sk.profiles:
        c.add(p)
    return c

def extrude(comp, sk, z0, h, op, bodies=None):
    exts = comp.features.extrudeFeatures
    inp = exts.createInput(profs(sk), op)
    inp.startExtent = adsk.fusion.OffsetStartDefinition.create(VI.createByReal(z0 * mm))
    inp.setDistanceExtent(False, VI.createByReal(h * mm))
    if bodies:
        inp.participantBodies = bodies
    return exts.add(inp)

def sketch(comp, name):
    sk = comp.sketches.add(comp.xYConstructionPlane)
    sk.name = name
    return sk

def circles(sk, pts, d):
    for (x, y) in pts:
        sk.sketchCurves.sketchCircles.addByCenterRadius(P3.create(x * mm, y * mm, 0), d / 2.0 * mm)

def rect(sk, x0, y0, x1, y1):
    sk.sketchCurves.sketchLines.addTwoPointRectangle(P3.create(x0 * mm, y0 * mm, 0), P3.create(x1 * mm, y1 * mm, 0))

def poly(sk, pts):
    L = sk.sketchCurves.sketchLines
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        L.addByTwoPoints(P3.create(a[0] * mm, a[1] * mm, 0), P3.create(b[0] * mm, b[1] * mm, 0))

OCC = {}
def new_comp(root, name):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    OCC[name] = occ
    return occ.component

# ---- sketches on a plane at x = v, y = v or z = v (used for wall openings and labels) ----
class WallSketch:
    def __init__(self, comp, axis, v, name):
        base = {"x": comp.yZConstructionPlane, "y": comp.xZConstructionPlane, "z": comp.xYConstructionPlane}[axis]
        idx = {"x": 0, "y": 1, "z": 2}[axis]
        self.sk = None
        for sign in (1, -1):
            pin = comp.constructionPlanes.createInput()
            pin.setByOffset(base, VI.createByReal(sign * v * mm))
            pl = comp.constructionPlanes.add(pin)
            sk = comp.sketches.add(pl)
            o = sk.sketchToModelSpace(P3.create(0, 0, 0)).asArray()
            if abs(o[idx] - v * mm) < 1e-6:
                self.sk = sk
                break
            sk.deleteMe(); pl.deleteMe()
        self.sk.name = name
        self.comp = comp
        self.plane = pl
    def again(self, name):
        # another empty sketch on the same plane
        w = WallSketch.__new__(WallSketch)
        w.comp, w.plane = self.comp, self.plane
        w.sk = self.comp.sketches.add(self.plane)
        w.sk.name = name
        return w
    def solid(self, total, name=None):
        exts = self.comp.features.extrudeFeatures
        inp = exts.createInput(profs(self.sk), NEW)
        inp.setSymmetricExtent(VI.createByReal(total * mm), True)
        f = exts.add(inp)
        if name:
            for i in range(f.bodies.count):
                f.bodies.item(i).name = name
        return f
    def p(self, x, y, z):
        q = self.sk.modelToSketchSpace(P3.create(x * mm, y * mm, z * mm))
        return P3.create(q.x, q.y, 0)
    def circle(self, c, d):
        self.sk.sketchCurves.sketchCircles.addByCenterRadius(self.p(*c), d / 2.0 * mm)
    def quad(self, pts):
        L = self.sk.sketchCurves.sketchLines
        q = [self.p(*a) for a in pts]
        for i in range(4):
            L.addByTwoPoints(q[i], q[(i + 1) % 4])
    def poly(self, pts):
        L = self.sk.sketchCurves.sketchLines
        q = [self.p(*a) for a in pts]
        n = len(q)
        for k in range(n):
            if q[k].distanceTo(q[(k + 1) % n]) > 1e-7:
                L.addByTwoPoints(q[k], q[(k + 1) % n])
    def join(self, body, total):
        exts = self.comp.features.extrudeFeatures
        inp = exts.createInput(profs(self.sk), JOIN)
        inp.setSymmetricExtent(VI.createByReal(total * mm), True)
        inp.participantBodies = [body]
        return exts.add(inp)
    def cut(self, body, total, what=None):
        exts = self.comp.features.extrudeFeatures
        inp = exts.createInput(what if what else profs(self.sk), CUT)
        inp.setSymmetricExtent(VI.createByReal(total * mm), True)
        inp.participantBodies = [body]
        return exts.add(inp)
    def chord(self, a, b):
        self.sk.sketchCurves.sketchLines.addByTwoPoints(self.p(*a), self.p(*b))
    def cut_big(self, body, total, min_area):
        # cut only the profiles larger than min_area (mm2): used for D-shaped holes drawn as circle + chord lines
        c = adsk.core.ObjectCollection.create()
        for pr in self.sk.profiles:
            if pr.areaProperties().area * 100.0 > min_area:
                c.add(pr)
        return self.cut(body, total, c)
    def label(self, body, text, a, b, key, outward, height=None):
        # text runs from a (left, as read from outside) to b (right); the points are the baseline
        try:
            sk = self.sk
            hf, vf = TEXT_FIX.get(key, (0, 0))
            if vf and abs(outward[2]) < 0.5:
                # a vertically flipped label hangs below its path: lift the path by the text height (wall labels only)
                hh = (height or TEXT_H)
                a = (a[0], a[1], a[2] + hh)
                b = (b[0], b[1], b[2] + hh)
            ln = sk.sketchCurves.sketchLines.addByTwoPoints(self.p(*a), self.p(*b))
            ln.isConstruction = True
            ti = sk.sketchTexts.createInput2(text, (height or TEXT_H) * mm)
            ti.setAsAlongPath(ln, True, adsk.core.HorizontalAlignments.CenterHorizontalAlignment, 0)
            ti.fontName = FONT
            ti.isHorizontalFlip = bool(hf)
            ti.isVerticalFlip = bool(vf)
            t = sk.sketchTexts.add(ti)
            self.cut(body, 2 * TEXT_DEPTH, t)
        except Exception:
            log.append("label '%s' failed: %s" % (text, traceback.format_exc()))

APPEAR = {}
def appearance(design, key):
    # key: "red", "black", "metal". Returns a design appearance or None.
    if key in APPEAR:
        return APPEAR[key]
    names = {"red": ["Paint - Enamel Glossy (Red)", "Plastic - Glossy (Red)"],
             "black": ["Paint - Enamel Glossy (Black)", "Plastic - Glossy (Black)"],
             "metal": ["Nickel - Polished", "Steel - Satin", "Aluminum - Satin"]}[key]
    app = adsk.core.Application.get()
    found = None
    for lib in app.materialLibraries:
        for nme in names:
            try:
                a = lib.appearances.itemByName(nme)
            except Exception:
                a = None
            if a:
                try:
                    found = design.appearances.addByCopy(a, "TL73_" + key)
                except Exception:
                    found = design.appearances.itemByName("TL73_" + key)
                break
        if found:
            break
    APPEAR[key] = found
    return found

def paint(design, feat, colour):
    ap = appearance(design, colour)
    if ap:
        for k in range(feat.bodies.count):
            try:
                feat.bodies.item(k).appearance = ap
            except Exception:
                pass

def jack_holes(comp, body, y_out, xs, z):
    # double-D holes for CT4397 jacks in an end wall (flats left and right)
    for x in xs:
        ws = WallSketch(comp, "y", y_out, "Jack_Hole")
        ws.circle((x, y_out, z), JACK_HOLE_D)
        r = JACK_HOLE_D / 2 + 1.0
        for s in (-1, 1):
            ws.chord((x + s * JACK_FLAT / 2, y_out, z - r), (x + s * JACK_FLAT / 2, y_out, z + r))
        ws.cut_big(body, 2 * WALL_T + 2, 40.0)

def fetch_jack_step(digit):
    # returns the path of the Cal Test STEP model CT4397-01-<digit> (0 = black, 2 = red), downloading the
    # manufacturer's zip (about 70 MB, one 46 MB STEP per colour) if the file is not there yet
    d = os.path.join(OUT_DIR, "vendor_models")
    os.makedirs(d, exist_ok=True)
    want = os.path.join(d, "CT4397-01-%d.STEP" % digit)
    if os.path.exists(want):
        return want
    import urllib.request, zipfile, io
    rq = urllib.request.Request(JACK_STEP_URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                                                        "Referer": "https://www.caltestelectronics.com/", "Accept": "*/*"})
    with urllib.request.urlopen(rq, timeout=120) as r:
        data = r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zz:
        for n in zz.namelist():
            if os.path.basename(n) in ("CT4397-01-0.STEP", "CT4397-01-2.STEP"):
                with open(os.path.join(d, os.path.basename(n)), "wb") as fh:
                    fh.write(zz.read(n))
    return want if os.path.exists(want) else None

def all_bodies(comp, out):
    for b in comp.bRepBodies:
        out.append(b)
    for o in comp.occurrences:
        all_bodies(o.component, out)
    return out

def place_jacks(app, design, root, step, spots, colour, name):
    # imports the vendor STEP once and puts a copy at every spot = ((x, y, z) on the outer wall face, outward normal).
    # The model's own axes are not documented, so they are worked out from its size: long axis = jack axis,
    # heavier end = collar end.
    im = app.importManager
    im.importToTarget(im.createSTEPImportOptions(step), root)
    occ = root.occurrences.item(root.occurrences.count - 1)
    comp = occ.component
    comp.name = name
    bb = occ.boundingBox
    mn, mx = bb.minPoint.asArray(), bb.maxPoint.asArray()
    ext = [mx[i] - mn[i] for i in range(3)]
    ax = ext.index(max(ext))
    ctr = [(mn[i] + mx[i]) / 2 for i in range(3)]
    head = 1
    try:
        com = comp.getPhysicalProperties(adsk.fusion.CalculationAccuracy.LowCalculationAccuracy).centerOfMass.asArray()
        head = 1 if com[ax] > ctr[ax] else -1
    except Exception:
        log.append("jack centre of mass failed, collar direction assumed")
    log.append("%s model size mm %.1f x %.1f x %.1f, axis %s, collar towards %s" % (name, ext[0] * 10, ext[1] * 10, ext[2] * 10, "xyz"[ax], "+" if head > 0 else "-"))
    o = list(ctr)
    o[ax] = (mx[ax] if head > 0 else mn[ax]) - head * JACK_HEAD_L * mm     # plane under the collar = outer wall face
    V = adsk.core.Vector3D
    fx = [0, 0, 0]; fx[ax] = head
    fy = [0, 0, 0]; fy[(ax + 1) % 3] = 1
    fX, fY = V.create(*fx), V.create(*fy)
    fZ = fX.crossProduct(fY)
    first = True
    for (pt, n) in spots:
        tX = V.create(*n)
        tY = V.create(0, 0, 1)
        tZ = tX.crossProduct(tY)
        m = adsk.core.Matrix3D.create()
        m.setToAlignCoordinateSystems(P3.create(*o), fX, fY, fZ, P3.create(pt[0] * mm, pt[1] * mm, pt[2] * mm), tX, tY, tZ)
        if first:
            occ.transform = m
            first = False
        else:
            root.occurrences.addExistingComponent(comp, m)
        if design.snapshots.hasPendingSnapshot:
            design.snapshots.add()

def jack_standin(design, comp, y_out, outward, centres, name, colour):
    # used only if the vendor STEP cannot be downloaded: collar, threaded body and stud as cylinders (datasheet sizes)
    parts = [("collar", JACK_HEAD_D, 0.0, JACK_HEAD_L, colour), ("body", JACK_BODY_D, -JACK_BODY_L, 0.0, colour),
             ("stud", JACK_STUD_D, -JACK_BODY_L - JACK_STUD_L, -JACK_BODY_L, "metal")]
    for part, dia, a, b, col in parts:
        mid = y_out + outward * (a + b) / 2.0
        ws = WallSketch(comp, "y", mid, name + "_" + part)
        for (x, z) in centres:
            ws.circle((x, mid, z), dia)
        paint(design, ws.solid(abs(b - a), name + "_" + part), col)

def en3_model(design, comp, x_out, x_in, y, z, name):
    # Switchcraft EN3 panel connector drawn from its customer drawing (left wall: outside is -x)
    r = EN3_NUT_AF / math.sqrt(3.0)
    parts = [("flange", EN3_FLANGE_D, x_in, x_in + 2.5, "black"),
             ("solder_cups", 11.0, x_in + 2.5, x_in + 2.5 + EN3_REAR_L, "metal"),
             ("shell", EN3_THREAD_D, x_in + 2.5 - EN3_FRONT_L, x_in, "black")]
    for part, dia, a, b, col in parts:
        mid = (a + b) / 2.0
        ws = WallSketch(comp, "x", mid, name + "_" + part)
        ws.circle((mid, y, z), dia)
        paint(design, ws.solid(abs(b - a), name + "_" + part), col)
    mid = x_out - 2.0
    ws = WallSketch(comp, "x", mid, name + "_hex_nut")
    ws.poly([(mid, y + r * math.cos(math.radians(60 * k)), z + r * math.sin(math.radians(60 * k))) for k in range(6)])
    ws.circle((mid, y, z), EN3_THREAD_D)
    c = adsk.core.ObjectCollection.create()
    for pr in ws.sk.profiles:
        if pr.profileLoops.count > 1:
            c.add(pr)
    exts = comp.features.extrudeFeatures
    inp = exts.createInput(c, NEW)
    inp.setSymmetricExtent(VI.createByReal(4.0 * mm), True)
    f = exts.add(inp)
    for k in range(f.bodies.count):
        f.bodies.item(k).name = name + "_hex_nut"
    paint(design, f, "black")

def stroke_quads(pts, w, closed=False):
    # thick line through pts as one quad per segment (ends extended a little so the joints overlap)
    out = []
    n = len(pts)
    for i in range(n if closed else n - 1):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        ux, uy = dx / L, dy / L
        e = 0.35 * w
        ax, ay, bx, by = x0 - ux * e, y0 - uy * e, x1 + ux * e, y1 + uy * e
        nx, ny = -uy * w / 2, ux * w / 2
        out.append([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
    return out

def logo_quads():
    # TL-73 team logo redrawn as strokes: wire cube (the cage), small cube (the CubeSat), two rings.
    # Coordinates in the logo's own pixels (720 x 660, y down), scaled to LOGO_W and centred on LOGO_C.
    s = LOGO_W / 720.0
    def T(p):
        return (LOGO_C[0] + (p[0] - 360.0) * s, LOGO_C[1] - (p[1] - 330.0) * s)
    groups = []   # each group = list of quads that do not enclose an area together
    top, ul, ur, ll, lr, bot, front, back = (360, 95), (118, 185), (602, 185), (118, 510), (602, 510), (360, 600), (360, 270), (360, 425)
    edges = [(top, ul), (top, ur), (ul, ll), (ur, lr), (ll, bot), (lr, bot), (front, ul), (front, ur), (front, bot), (back, top), (back, ll), (back, lr)]
    for a, b in edges:
        groups.append(stroke_quads([T(a), T(b)], 1.0))
    c = [(345, 300), (277, 330), (277, 408), (345, 440), (413, 408), (413, 330)]   # small cube outline
    for i in range(6):
        groups.append(stroke_quads([T(c[i]), T(c[(i + 1) % 6])], 0.8))
    for a in ((277, 330), (413, 330), (345, 440)):
        groups.append(stroke_quads([T((345, 362)), T(a)], 0.8))
    for (cx, cy, rx, ry) in ((360, 360, 345, 105), (360, 330, 115, 315)):
        N = 72
        ring = [T((cx + rx * math.cos(2 * math.pi * i / N), cy + ry * math.sin(2 * math.pi * i / N))) for i in range(N)]
        q = stroke_quads(ring, 1.5, True)
        for k in range(3):
            groups.append(q[k::3])
    return groups

def fillet_vertical(comp, body, height, radius):
    try:
        edges = adsk.core.ObjectCollection.create()
        for e in body.edges:
            a, b = e.startVertex.geometry, e.endVertex.geometry
            if abs(a.x - b.x) < 1e-6 and abs(a.y - b.y) < 1e-6 and abs(abs(a.z - b.z) - height * mm) < 1e-6:
                edges.add(e)
        fil = comp.features.filletFeatures
        fin = fil.createInput()
        try:
            fin.edgeSetInputs.addConstantRadiusEdgeSet(edges, VI.createByReal(radius * mm), True)
        except Exception:
            fin.addConstantRadiusEdgeSet(edges, VI.createByReal(radius * mm), True)
        fil.add(fin)
    except Exception:
        log.append("fillet skipped: " + traceback.format_exc())

def run(context):
    app = adsk.core.Application.get()
    try:
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent

        xo = X_IN + WALL_T
        yf, yb = Y_FRONT_IN - WALL_T, Y_BACK_IN + WALL_T      # outer faces
        z_shield = FLOOR_T + STANDOFF_H
        z_nuc_top = z_shield - STACK_GAP
        nuc_y_bot = NUC_Y_TOP - NUC_L
        nh = [(x - NUC_W / 2, y + nuc_y_bot) for (x, y) in NUC_HOLES]

        # ================= BASE =================
        basec = new_comp(root, "Enclosure_Base")
        sk = sketch(basec, "Outer"); rect(sk, -xo, yf, xo, yb)
        base = extrude(basec, sk, 0, Z_TOP, NEW).bodies.item(0)
        base.name = "Enclosure_Base"
        fillet_vertical(basec, base, Z_TOP, CORNER_R)
        sk = sketch(basec, "Pocket"); rect(sk, -X_IN, Y_FRONT_IN, X_IN, Y_BACK_IN)
        extrude(basec, sk, FLOOR_T, Z_TOP - FLOOR_T, CUT, [base])

        # lid screw posts in the four inner corners
        y_back_post = Y_BACK_IN - POST / 2
        y_front_post = Y_FRONT_IN + POST / 2
        posts = [(sx * (X_IN - POST / 2), y) for sx in (-1, 1) for y in (y_front_post, y_back_post)]
        sk = sketch(basec, "Lid_Posts")
        for (cx, cy) in posts:
            x0 = cx - POST / 2 - (1.0 if cx < 0 else 0.0)   # overlap 1 mm into the walls so the join is solid
            x1 = cx + POST / 2 + (1.0 if cx > 0 else 0.0)
            y0 = cy - POST / 2 - (1.0 if cy == y_front_post else 0.0)
            y1 = cy + POST / 2 + (1.0 if cy == y_back_post else 0.0)
            rect(sk, x0, y0, x1, y1)
        extrude(basec, sk, FLOOR_T - 1.0, Z_TOP - FLOOR_T + 1.0, JOIN, [base])
        sk = sketch(basec, "Lid_Screw_Relief"); circles(sk, posts, SCREW_RELIEF_D)
        extrude(basec, sk, Z_TOP - SCREW_RELIEF_L, SCREW_RELIEF_L, CUT, [base])
        sk = sketch(basec, "Lid_Insert_Holes"); circles(sk, posts, INSERT_D)
        extrude(basec, sk, Z_TOP - INSERT_L, INSERT_L, CUT, [base])

        # floor: M3 clearance + underside counterbores (same pattern as the open mount)
        sk = sketch(basec, "M3_Clearance"); circles(sk, HOLES + nh, M3_CLEAR_D)
        extrude(basec, sk, 0, FLOOR_T, CUT, [base])
        sk = sketch(basec, "M3_Counterbores"); circles(sk, HOLES + nh, CBORE_D)
        extrude(basec, sk, 0, CBORE_DEPTH, CUT, [base])

        # wall-mount ears
        sk = sketch(basec, "Ears")
        ears = []
        for sx in (-1, 1):
            for ey in EAR_Y:
                xa, xb2 = sx * (xo - 1.0), sx * (xo + EAR_W)
                rect(sk, min(xa, xb2), ey - EAR_L / 2, max(xa, xb2), ey + EAR_L / 2)
                ears.append((sx * (xo + EAR_W / 2 + 1.0), ey))
        extrude(basec, sk, 0, FLOOR_T, JOIN, [base])
        sk = sketch(basec, "Ear_Holes"); circles(sk, ears, EAR_HOLE_D)
        extrude(basec, sk, 0, FLOOR_T, CUT, [base])

        # ---- front wall: six coil jacks ----
        try:
            jx = []
            for cx in COIL_PAIR_X:
                jx += [cx - JACK_PITCH / 2, cx + JACK_PITCH / 2]
            jack_holes(basec, base, yf, jx, JACK_Z)
            wt = WallSketch(basec, "y", yf, "Front_Text")
            names = ["X+", "X-", "Y+", "Y-", "Z+", "Z-"]
            zt = JACK_Z + 10.5
            for x, nme in zip(jx, names):
                wt.label(base, nme, (x - 8, yf, zt), (x + 8, yf, zt), "front", (0, -1, 0))
            for cx, nme in zip(COIL_PAIR_X, ["COIL X", "COIL Y", "COIL Z"]):
                wt.label(base, nme, (cx - 19, yf, JACK_Z - 20), (cx + 19, yf, JACK_Z - 20), "front", (0, -1, 0))
            wv = WallSketch(basec, "y", yf, "Front_Vents")
            for vx in FRONT_VENT_X:
                wv.quad([(vx - VENT_W / 2, yf, VENT_Z0), (vx + VENT_W / 2, yf, VENT_Z0),
                         (vx + VENT_W / 2, yf, VENT_Z0 + VENT_FB_H), (vx - VENT_W / 2, yf, VENT_Z0 + VENT_FB_H)])
            wv.cut(base, 2 * WALL_T + 2)
        except Exception:
            log.append("front wall failed: " + traceback.format_exc())

        # ---- back wall: 34 V input jacks ----
        try:
            ws = WallSketch(basec, "y", yb, "Back_Openings")
            jack_holes(basec, base, yb, [SUPPLY_X, -SUPPLY_X], JACK_Z)
            for vx in BACK_VENT_X:
                ws.quad([(vx - VENT_W / 2, yb, VENT_Z0), (vx + VENT_W / 2, yb, VENT_Z0),
                         (vx + VENT_W / 2, yb, VENT_Z0 + VENT_FB_H), (vx - VENT_W / 2, yb, VENT_Z0 + VENT_FB_H)])
            ws.cut(base, 2 * WALL_T + 2)
            wt = WallSketch(basec, "y", yb, "Back_Text")
            zt = JACK_Z + 10.5
            # seen from behind, +x is on the left
            wt.label(base, "+34V", (SUPPLY_X + 10, yb, zt), (SUPPLY_X - 10, yb, zt), "back", (0, 1, 0))
            wt.label(base, "GND", (-SUPPLY_X + 10, yb, zt), (-SUPPLY_X - 10, yb, zt), "back", (0, 1, 0))
            wt.label(base, "34 V IN   36 V MAX", (40, yb, JACK_Z - 20), (-40, yb, JACK_Z - 20), "back", (0, 1, 0))
        except Exception:
            log.append("back wall failed: " + traceback.format_exc())

        # ---- left wall (-x): Switchcraft EN3 solder-cup connectors for the three NTCs and the magnetometer, vents ----
        try:
            for (nme, ny, n) in EN3_LIST:
                wp = WallSketch(basec, "x", -xo, "EN3_Hole")
                wp.circle((-xo, ny, EN3_Z), EN3_HOLE_D)
                zf = EN3_Z - EN3_HOLE_D / 2 + EN3_FLAT      # flat at the top of the hole
                wp.chord((-xo, ny - EN3_HOLE_D / 2 - 1, zf), (-xo, ny + EN3_HOLE_D / 2 + 1, zf))
                wp.cut_big(base, 2 * WALL_T + 2, 60.0)
            ws = WallSketch(basec, "x", -xo, "Left_Vents")
            for vy in VENT_Y:
                ws.quad([(-xo, vy - VENT_W / 2, VENT_Z0), (-xo, vy + VENT_W / 2, VENT_Z0),
                         (-xo, vy + VENT_W / 2, VENT_Z0 + VENT_H), (-xo, vy - VENT_W / 2, VENT_Z0 + VENT_H)])
            ws.cut(base, 2 * WALL_T + 2)
            wt = WallSketch(basec, "x", -xo, "Left_Text")
            # seen from the left (-x side), +y is on the left
            for (nme, ny, n) in EN3_LIST:
                wt.label(base, nme, (-xo, ny + 10, EN3_Z + 14.5), (-xo, ny - 10, EN3_Z + 14.5), "left", (-1, 0, 0), 4.0)
        except Exception:
            log.append("left wall failed: " + traceback.format_exc())

        # ---- right wall (+x): USB adapter, wire window into the control pod, vents ----
        try:
            wu = WallSketch(basec, "x", xo, "USB_Hole")
            wu.circle((xo, USB_Y, USB_Z), USB_HOLE_D)
            wu.cut(base, 2 * WALL_T + 2)
            wt = WallSketch(basec, "x", xo, "Right_Text")
            # seen from the right (+x side), -y is on the left
            wt.label(base, "USB-C", (xo, USB_Y - 14, USB_Z + 17), (xo, USB_Y + 14, USB_Z + 17), "right", (1, 0, 0), 4.5)
            ws = WallSketch(basec, "x", xo, "Right_Vents")
            for vy in VENT_Y:
                if abs(vy - USB_Y) < USB_LIP_D / 2 + 4:
                    continue          # no vents under the USB adapter
                if POD_Y0 - VENT_W < vy < POD_Y1 + VENT_W:
                    continue          # this part of the wall is inside the control pod
                ws.quad([(xo, vy - VENT_W / 2, VENT_Z0), (xo, vy + VENT_W / 2, VENT_Z0),
                         (xo, vy + VENT_W / 2, VENT_Z0 + VENT_H), (xo, vy - VENT_W / 2, VENT_Z0 + VENT_H)])
            ws.cut(base, 2 * WALL_T + 2)
        except Exception:
            log.append("right wall failed: " + traceback.format_exc())

        # ================= CONTROL POD (stop switch and status LEDs facing up) =================
        try:
            px0 = xo                                  # outer face of the right wall
            pxi = xo + POD_W_IN                       # inner face of the pod outer wall
            px1 = pxi + WALL_T                        # outer face of the pod
            zd = POD_DECK_Z
            zu = zd - DECK_T                          # underside of the deck
            yi0, yi1 = POD_Y0 + WALL_T, POD_Y1 - WALL_T
            ym = (POD_Y0 + POD_Y1) / 2.0
            # solid block from the floor to the deck top, 1 mm into the right wall so the join is solid
            sk = sketch(basec, "Pod_Block"); rect(sk, px0 - 1.0, POD_Y0, px1, POD_Y1)
            extrude(basec, sk, 0, zd, JOIN, [base])
            # hollow it out between the floor and the deck (the right wall itself is not touched)
            sk = sketch(basec, "Pod_Cavity"); rect(sk, px0, yi0, pxi, yi1)
            extrude(basec, sk, FLOOR_T, zu - FLOOR_T, CUT, [base])
            # wire window through the right wall: vertical sides, 45 degree gable on top (prints without support)
            xw = X_IN + WALL_T / 2.0
            ww = WallSketch(basec, "x", xw, "Pod_Wire_Window")
            h = POD_WIN_W / 2.0
            ww.poly([(xw, ym - h, POD_WIN_Z0), (xw, ym + h, POD_WIN_Z0), (xw, ym + h, POD_WIN_Z1),
                     (xw, ym, POD_WIN_Z1 + h), (xw, ym - h, POD_WIN_Z1)])
            ww.cut(base, WALL_T + 2.0)
            # 45 degree supports under the deck: along both long edges and both ends
            c = POD_CHAMFER
            wc = WallSketch(basec, "y", ym, "Pod_Deck_Support_Long")
            wc.poly([(px0 - 0.5, ym, zu + 0.5), (px0 + c, ym, zu + 0.5), (px0 + c, ym, zu), (px0 - 0.5, ym, zu - c - 0.5)])
            wc.join(base, yi1 - yi0 + 1.0)
            wc2 = wc.again("Pod_Deck_Support_Long_2")
            wc2.poly([(pxi + 0.5, ym, zu + 0.5), (pxi - c, ym, zu + 0.5), (pxi - c, ym, zu), (pxi + 0.5, ym, zu - c - 0.5)])
            wc2.join(base, yi1 - yi0 + 1.0)
            xm = (px0 + pxi) / 2.0
            we = WallSketch(basec, "x", xm, "Pod_Deck_Support_Ends")
            for (yw, sgn) in ((yi0, 1), (yi1, -1)):
                we.poly([(xm, yw - sgn * 0.5, zu + 0.5), (xm, yw + sgn * c, zu + 0.5), (xm, yw + sgn * c, zu),
                         (xm, yw - sgn * 0.5, zu - c - 0.5)])
            we.join(base, pxi - px0 + 1.0)
            # above the lid seam the lid edge sits at x = xo: clear everything up to xo + LID_GAP over the pod length so
            # the lid lifts straight up past the pod wall (below the seam the right wall and the chamfer stay joined)
            sk = sketch(basec, "Lid_Gap_At_Pod"); rect(sk, X_IN - 1.0, POD_Y0 - 0.5, xo + LID_GAP, POD_Y1 + 0.5)
            extrude(basec, sk, Z_TOP, zd - Z_TOP + 1.0, CUT, [base])
            xc = (px0 + pxi) / 2.0                    # deck centre line
            # ribs across the pod under the deck: full width between the walls, bottom edge rising at 45 degrees from
            # each wall to RIB_DEPTH_MID under the centre line (inverted V), joined 0.5 mm into deck and walls
            hw = (pxi - px0) / 2.0
            for k, yr in enumerate(RIB_Y):
                wr = WallSketch(basec, "y", yr, "Pod_Deck_Rib_%d" % k)
                wr.poly([(px0 - 0.5, yr, zu + 0.5), (pxi + 0.5, yr, zu + 0.5), (pxi + 0.5, yr, zu - RIB_DEPTH_MID - hw - 0.5),
                         (xc, yr, zu - RIB_DEPTH_MID), (px0 - 0.5, yr, zu - RIB_DEPTH_MID - hw - 0.5)])
                wr.join(base, RIB_T)
            # stop switch: clear space for the body, terminals and leads, the nut pocket, the panel hole, the lug
            sk = sketch(basec, "Stop_Body_Clearance"); circles(sk, [(xc, STOP_Y)], STOP_HOLE_D + 0.6)
            z_body = zd - STOP_DEPTH - 1.0
            extrude(basec, sk, z_body, zu - z_body, CUT, [base])
            sk = sketch(basec, "Stop_Nut_Pocket"); circles(sk, [(xc, STOP_Y)], STOP_NUT_POCKET_D)
            # the pocket reaches up into the deck so the switch sees a STOP_PANEL_T panel (counterbore from below)
            z_pk = zu - STOP_NUT_POCKET_H
            extrude(basec, sk, z_pk, (zd - STOP_PANEL_T) - z_pk, CUT, [base])
            sk = sketch(basec, "Stop_Switch_Hole"); circles(sk, [(xc, STOP_Y)], STOP_HOLE_D)
            extrude(basec, sk, zu - 0.1, DECK_T + 0.2, CUT, [base])
            # anti-rotation lug on the +x side of the hole (towards the pod outer wall), deck thickness only
            x_face = xc - STOP_HOLE_D / 2 + STOP_LUG_GAP
            sk = sketch(basec, "Stop_Switch_Lug")
            rect(sk, x_face, STOP_Y - STOP_LUG_W / 2, xc + STOP_HOLE_D / 2 + 0.6, STOP_Y + STOP_LUG_W / 2)
            extrude(basec, sk, zd - STOP_PANEL_T, STOP_PANEL_T, JOIN, [base])
            # status LEDs: space for the body under the deck, recess to LED_PANEL_T, then the hole
            pts = [(xc, ly) for (nme, ly) in LED_Y]
            sk = sketch(basec, "LED_Body_Clearance"); circles(sk, pts, LED_RECESS_D)
            extrude(basec, sk, zu - LED_BODY_DEPTH, LED_BODY_DEPTH + (DECK_T - LED_PANEL_T), CUT, [base])
            sk = sketch(basec, "LED_Holes"); circles(sk, pts, LED_HOLE_D)
            extrude(basec, sk, zu - 0.1, DECK_T + 0.2, CUT, [base])
            # engraved labels on the deck, read from the coil (front, -y) side like the lid text
            wt = WallSketch(basec, "z", zd, "Pod_Text")
            wt.label(base, "STOP", (xc - 12, STOP_Y - 20, zd), (xc + 12, STOP_Y - 20, zd), "top", (0, 0, 1), 5.0)
            for (nme, ly) in LED_Y:
                wt.label(base, nme, (xc + 5.5, ly - 1.75, zd), (pxi, ly - 1.75, zd), "top", (0, 0, 1), 3.5)
            log.append("control pod: deck z %.1f, %d LEDs, stop switch at y %.1f" % (zd, len(LED_Y), STOP_Y))
        except Exception:
            log.append("control pod failed: " + traceback.format_exc())

        # ================= LID =================
        lidc = new_comp(root, "Enclosure_Lid")
        sk = sketch(lidc, "Lid"); rect(sk, -xo, yf, xo, yb)
        lid = extrude(lidc, sk, Z_TOP, LID_T, NEW).bodies.item(0)
        lid.name = "Enclosure_Lid"
        fillet_vertical(lidc, lid, LID_T, CORNER_R)
        sk = sketch(lidc, "Lid_Screws"); circles(sk, posts, M3_CLEAR_D)
        extrude(lidc, sk, Z_TOP, LID_T, CUT, [lid])
        if USE_LID_VENTS:
            sk = sketch(lidc, "Lid_Vents")
            for vx in LID_VENT_X:
                rect(sk, vx - LID_VENT_W / 2, LID_VENT_Y[0], vx + LID_VENT_W / 2, LID_VENT_Y[1])
            extrude(lidc, sk, Z_TOP, LID_T, CUT, [lid])
        # fan over the drivers: air opening and the four M3 holes on the 32 mm square
        sk = sketch(lidc, "Fan_Opening")
        circles(sk, [(FAN_X, FAN_Y)], FAN_HOLE_D)
        circles(sk, [(FAN_X + sx * FAN_SCREW_PITCH / 2, FAN_Y + sy * FAN_SCREW_PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)], FAN_SCREW_D)
        extrude(lidc, sk, Z_TOP, LID_T, CUT, [lid])
        try:
            zt = Z_TOP + LID_T
            wt = WallSketch(lidc, "z", zt, "Lid_Text")
            wt.label(lid, "TL-73 HELMHOLTZ CAGE", (-52, 78, zt), (52, 78, zt), "top", (0, 0, 1), 6.5)
            wt.label(lid, "3-AXIS COIL DRIVER", (-52, 64, zt), (52, 64, zt), "top", (0, 0, 1), 6.5)
            wt.label(lid, "34 V IN  -  36 V MAX", (-52, 46, zt), (52, 46, zt), "top", (0, 0, 1))
            wt.label(lid, "34 V IN AT THIS END", (-52, 100, zt), (52, 100, zt), "top", (0, 0, 1), 4.0)
            wt.label(lid, "COILS X  Y  Z AT THIS END", (-52, -119, zt), (52, -119, zt), "top", (0, 0, 1), 4.0)
            wt.label(lid, "FAN INTAKE  KEEP CLEAR", (FAN_X - 40, FAN_Y - FAN_SIZE / 2 - 10, zt), (FAN_X + 40, FAN_Y - FAN_SIZE / 2 - 10, zt), "top", (0, 0, 1), 4.0)
        except Exception:
            log.append("lid text failed: " + traceback.format_exc())
        try:
            zt = Z_TOP + LID_T
            w0 = WallSketch(lidc, "z", zt, "Logo_0")
            for gi, quads in enumerate(logo_quads()):
                w = w0 if gi == 0 else w0.again("Logo_%d" % gi)
                for q in quads:
                    w.quad([(p[0], p[1], zt) for p in q])
                w.cut(lid, 2 * TEXT_DEPTH)
        except Exception:
            log.append("logo failed: " + traceback.format_exc())

        # ================= reference parts =================
        so = new_comp(root, "M3_Standoffs_ref")
        def hexes(sk, pts):
            r = HEX_AF / math.sqrt(3.0)
            for (cx, cy) in pts:
                poly(sk, [(cx + r * math.cos(math.radians(60 * i)), cy + r * math.sin(math.radians(60 * i))) for i in range(6)])
        sk = sketch(so, "Shield_Standoffs"); hexes(sk, HOLES)
        extrude(so, sk, FLOOR_T, STANDOFF_H, NEW)
        sk = sketch(so, "Nucleo_Standoffs"); hexes(sk, nh)
        extrude(so, sk, FLOOR_T, NUC_STANDOFF_H, NEW)

        try:
            red = [((x, yf, JACK_Z), (0, -1, 0)) for x in jx[0::2]] + [((SUPPLY_X, yb, JACK_Z), (0, 1, 0))]      # X+ Y+ Z+ and +34V
            blk = [((x, yf, JACK_Z), (0, -1, 0)) for x in jx[1::2]] + [((-SUPPLY_X, yb, JACK_Z), (0, 1, 0))]     # X- Y- Z- and GND
            sr = sb = None
            try:
                sr, sb = fetch_jack_step(2), fetch_jack_step(0)
            except Exception:
                log.append("CT4397 STEP download failed: " + traceback.format_exc())
            if sr and sb:
                place_jacks(app, design, root, sr, red, "red", "CalTest_CT4397-01-2_red")
                place_jacks(app, design, root, sb, blk, "black", "CalTest_CT4397-01-0_black")
                log.append("placed 8 CT4397-01 jacks from the Cal Test STEP models")
            else:
                jr = new_comp(root, "CalTest_CT4397-01_standin")
                for spots, col in ((red, "red"), (blk, "black")):
                    for (pt, n) in spots:
                        jack_standin(design, jr, pt[1], n[1], [(pt[0], pt[2])], "CT4397-01_" + col, col)
                log.append("CT4397 drawn as stand-in cylinders (no vendor STEP)")
        except Exception:
            log.append("jacks failed: " + traceback.format_exc())
        try:
            uc = new_comp(root, "USB_Adafruit_4259_approx")
            for part, dia, a, b, col in (("lip", USB_LIP_D, xo, xo + USB_LIP_T, "black"),
                                         ("body", USB_BODY_D, xo + USB_LIP_T - USB_LEN, xo, "black"),
                                         ("usb_c_socket", 9.0, xo + USB_LIP_T, xo + USB_LIP_T + 0.6, "metal")):
                mid = (a + b) / 2.0
                wsu = WallSketch(uc, "x", mid, "USB_" + part)
                wsu.circle((mid, USB_Y, USB_Z), dia)
                paint(design, wsu.solid(abs(b - a), "Adafruit_4259_" + part), col)
            log.append("drew the Adafruit 4259 USB adapter from its published sizes (approximate)")
        except Exception:
            log.append("USB adapter failed: " + traceback.format_exc())
        try:
            # stand-in models (published sizes, not vendor CAD). The fan and its guard are their own component so they
            # move with the lid when it is parked; the stop switch and LEDs stay on the pod deck.
            fc = new_comp(root, "Fan_lid_mounted_approx")
            hs = FAN_SIZE / 2
            for nm, z0, h, hole in (("Fan_40x40x10_frame", Z_TOP - FAN_T, FAN_T, FAN_HOLE_D - 1.0),
                                    ("Fan_guard_Qualtek_08149", Z_TOP + LID_T, GUARD_T, FAN_HOLE_D)):
                sk = sketch(fc, nm)
                rect(sk, FAN_X - hs, FAN_Y - hs, FAN_X + hs, FAN_Y + hs)
                circles(sk, [(FAN_X, FAN_Y)], hole)
                c = adsk.core.ObjectCollection.create()
                for pr in sk.profiles:
                    if pr.profileLoops.count > 1:
                        c.add(pr)
                inp = fc.features.extrudeFeatures.createInput(c, NEW)
                inp.startExtent = adsk.fusion.OffsetStartDefinition.create(VI.createByReal(z0 * mm))
                inp.setDistanceExtent(False, VI.createByReal(h * mm))
                f = fc.features.extrudeFeatures.add(inp)
                for k in range(f.bodies.count):
                    f.bodies.item(k).name = nm
                paint(design, f, "black" if nm.startswith("Fan_40") else "metal")
            pc = new_comp(root, "Control_pod_parts_approx")
            xc = xo + POD_W_IN / 2.0
            zd = POD_DECK_Z
            for part, dia, z0, h, col in (("head", STOP_HEAD_D, zd + 3.0, STOP_HEAD_L - 3.0, "red"),
                                          ("bezel", 20.0, zd, 3.0, "black"),
                                          ("body", 16.0, zd - STOP_DEPTH, STOP_DEPTH - DECK_T, "black")):
                sk = sketch(pc, "Stop_" + part); circles(sk, [(xc, STOP_Y)], dia)
                f = extrude(pc, sk, z0, h, NEW)
                for k in range(f.bodies.count):
                    f.bodies.item(k).name = "Stop_switch_" + part
                paint(design, f, col)
            for (nme, ly) in LED_Y:
                for part, dia, z0, h in (("bezel", LED_HOLE_D + 2.5, zd, 1.5), ("body", LED_HOLE_D - 0.2, zd - 12.0, 12.0 - DECK_T)):
                    sk = sketch(pc, "LED_%s_%s" % (nme, part)); circles(sk, [(xc, ly)], dia)
                    f = extrude(pc, sk, z0, h, NEW)
                    for k in range(f.bodies.count):
                        f.bodies.item(k).name = "LED_%s_%s" % (nme, part)
                    paint(design, f, "black")
            log.append("drew the lid fan, the stop switch and 3 status LEDs as stand-in models")
        except Exception:
            log.append("fan / pod parts failed: " + traceback.format_exc())
        en3c = None
        try:
            en3c = new_comp(root, "Switchcraft_EN3_from_drawing")
            for (nme, ny, n) in EN3_LIST:
                en3_model(design, en3c, -xo, -X_IN, ny, EN3_Z, "EN3P%dMX_%s" % (n, nme.replace(" ", "_")))
            log.append("drew %d Switchcraft EN3 connectors from the customer drawing" % len(EN3_LIST))
        except Exception:
            log.append("EN3 connectors failed: " + traceback.format_exc())

        def import_step(path, name, dx, dy, dz):
            im = app.importManager
            im.importToTarget(im.createSTEPImportOptions(path), root)
            occ = root.occurrences.item(root.occurrences.count - 1)
            occ.component.name = name
            t = occ.transform
            t.translation = adsk.core.Vector3D.create(dx * mm, dy * mm, dz * mm)
            occ.transform = t
            try:
                if design.snapshots.hasPendingSnapshot:
                    design.snapshots.add()
            except Exception:
                pass
            return occ
        try:
            pcb_step = os.path.join(OUT_DIR, PCB_STEP)
            if os.path.exists(pcb_step):
                shield_occ = import_step(pcb_step, "TL73_Shield_PCB_KiCad", 0, 0, z_shield)
                fixed = [0]
                def fix_models(comp, ctx, depth=0):
                    for native in comp.occurrences:
                        o = native.createForAssemblyContext(ctx)
                        hit = None
                        for prefix, off in MODEL_FIXES.items():
                            if o.component.name.startswith(prefix):
                                hit = off
                        if hit:
                            try:
                                m = adsk.core.Matrix3D.create()
                                m.translation = adsk.core.Vector3D.create(hit[0] * mm, hit[1] * mm, hit[2] * mm)
                                m.transformBy(o.transform2)
                                o.transform2 = m
                                fixed[0] += 1
                            except Exception:
                                log.append("model fix failed for " + o.name)
                        elif depth < 3:
                            fix_models(native.component, o, depth + 1)
                fix_models(shield_occ.component, shield_occ)
                try:
                    if design.snapshots.hasPendingSnapshot:
                        design.snapshots.add()
                except Exception:
                    pass
                log.append("imported %s, repositioned %d models" % (PCB_STEP, fixed[0]))
            nuc_step = os.path.join(OUT_DIR, NUC_STEP)
            if os.path.exists(nuc_step):
                import_step(nuc_step, "NUCLEO_G474RE_MB1367", -NUC_W / 2, NUC_Y_TOP - NUC_L, z_nuc_top)
                log.append("imported " + NUC_STEP)
        except Exception:
            log.append("reference import problem: " + traceback.format_exc())

        # ================= exports =================
        try:
            em = design.exportManager
            em.execute(em.createSTLExportOptions(base, os.path.join(OUT_DIR, "TL73_Enclosure_Base.stl")))
            em.execute(em.createSTLExportOptions(lid, os.path.join(OUT_DIR, "TL73_Enclosure_Lid.stl")))
            em.execute(em.createSTEPExportOptions(os.path.join(OUT_DIR, "TL73_Enclosure_Base.step"), basec))
            em.execute(em.createSTEPExportOptions(os.path.join(OUT_DIR, "TL73_Enclosure_Lid.step"), lidc))
            if en3c:
                em.execute(em.createSTEPExportOptions(os.path.join(OUT_DIR, "vendor_models", "Switchcraft_EN3P_from_drawing.step"), en3c))
            # lay the lid beside the box (text up) so the inside is visible in the assembly; the fan and its guard get
            # the same move so they stay on the lid at the fan hole
            try:
                for key in ("Enclosure_Lid", "Fan_lid_mounted_approx"):
                    if key not in OCC:
                        continue
                    lo = OCC[key]
                    t = lo.transform
                    t.translation = adsk.core.Vector3D.create(LID_PARK[0] * mm, LID_PARK[1] * mm, LID_PARK[2] * mm)
                    lo.transform = t
                if design.snapshots.hasPendingSnapshot:
                    design.snapshots.add()
            except Exception:
                log.append("lid move failed: " + traceback.format_exc())
            em.execute(em.createSTEPExportOptions(os.path.join(OUT_DIR, "TL73_Enclosure_Assembly.step"), root))
            em.execute(em.createFusionArchiveExportOptions(os.path.join(OUT_DIR, "TL73_Enclosure.f3d")))
        except Exception:
            log.append("export problem: " + traceback.format_exc())
        try:
            app.activeViewport.goHome()
            app.activeViewport.fit()
        except Exception:
            pass
        for b in (base, lid):
            bb = b.boundingBox
            log.append("OK %s bbox mm: %.1f x %.1f x %.1f, volume cm3 %.1f" % (b.name,
                (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10,
                (bb.maxPoint.z - bb.minPoint.z) * 10, b.volume))
    except Exception:
        log.append("FAILED: " + traceback.format_exc())
    try:
        with open(os.path.join(OUT_DIR, "enclosure_build_log.txt"), "w") as fh:
            fh.write("\n".join(log))
    except Exception:
        pass

run(None)
