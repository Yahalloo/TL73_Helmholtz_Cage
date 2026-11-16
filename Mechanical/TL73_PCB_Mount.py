# TL73 Helmholtz Cage PCB - open mount (base plate drilled for off-the-shelf M3 standoffs)
# Fusion script. Geometry taken from TL_73_Helmholtz_Cage_PCB.kicad_pcb:
#   board 99 x 99 mm, USB notch 27 x 7.5 mm on the top edge,
#   4x M3 holes on a 92 x 68 mm pattern, morpho sockets (CN7/CN10) on the bottom side.
# Origin = centre of the shield PCB.  +Y = KiCad "up" (ST-LINK / USB end).  All values in mm.
import adsk.core, adsk.fusion, traceback, os, math

OUT_DIR = r"D:\GoogleDrive_Personal\Documents\Uni Courses\Final Year\T1\ELEC 491\Project_Design_Files\Repositry\PCB_V1.0\TL73_Helmholtz_Cage\Mechanical"

# ---------------- editable dimensions ----------------
PLATE_T      = 4.0     # base plate thickness
STANDOFF_H   = 25.0    # bought M3 hex standoff under the shield PCB (plate top -> PCB underside)
NUC_STANDOFF_H = 12.0  # bought M3 hex standoff under the Nucleo (leaves ~0.3 mm gap; add a washer)
HEX_AF       = 5.5     # standoff across-flats
M3_CLEAR_D   = 3.4     # M3 clearance hole through the plate
CBORE_D      = 6.5     # underside counterbore for pan/button/socket-cap M3 screw heads
CBORE_DEPTH  = 2.5
MARGIN       = 8.0     # plate margin around shield PCB / Nucleo
FOOT_HOLE_D  = 4.5     # M4 clearance holes in plate corners
FOOT_INSET   = 5.0
CORNER_R     = 5.0

# ---------------- from the KiCad board ----------------
PCB_HALF     = 49.5
PCB_T        = 1.6
NOTCH_HALF_W = 13.5
NOTCH_Y      = 42.0
HOLES        = [(-46.0, 45.5), (46.0, 45.5), (-46.0, -22.5), (46.0, -22.5)]
MORPHO_X     = 30.48           # centre of each 2-row header, +/- from board centre
MORPHO_Y_TOP = 42.76           # pin 1 row
MORPHO_Y_BOT = -2.96           # pin 37/38 row

# ---------------- Nucleo-64 (from ST MB1367 manufacturing package) ----------------
PCB_STEP     = "TL73_Shield_PCB_KiCad.step"   # File > Export > STEP from KiCad, "Board center origin"
NUC_STEP     = "NUCLEO_G474RE.step"           # optional real Nucleo model; placeholder is drawn if missing
NUC_W, NUC_L, NUC_T = 70.0, 82.5, 1.644
NUC_Y_TOP    = 74.5            # ST pick-and-place: morpho pin 1 row is 31.74 mm below the ST-LINK edge
STACK_GAP    = 11.04           # Nucleo top face -> shield underside (8.5 socket + 2.54 header body)
# Nucleo 3.2 mm mounting holes (ST drill file), Nucleo coords from its lower-left corner
NUC_HOLES    = [(43.89, 2.5), (10.87, 54.57), (59.13, 53.3)]
NUC_POST_D   = 6.5
PIN_TAIL     = 8.6             # TSW-119-09 tails under the Nucleo

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

def new_comp(root, name):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    return occ.component

def run(context):
    app = adsk.core.Application.get()
    try:
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent

        z_shield = PLATE_T + STANDOFF_H          # underside of shield PCB
        z_nuc_top = z_shield - STACK_GAP
        z_nuc_bot = z_nuc_top - NUC_T
        nuc_y_bot = NUC_Y_TOP - NUC_L

        # ---------- Mount ----------
        mount = new_comp(root, "PCB_Mount")
        px0, px1 = -PCB_HALF - MARGIN, PCB_HALF + MARGIN
        py0, py1 = -PCB_HALF - MARGIN, NUC_Y_TOP + MARGIN
        sk = sketch(mount, "Plate")
        rect(sk, px0, py0, px1, py1)
        base = extrude(mount, sk, 0, PLATE_T, NEW).bodies.item(0)
        base.name = "Mount"
        try:
            edges = adsk.core.ObjectCollection.create()
            for e in base.edges:
                a, b = e.startVertex.geometry, e.endVertex.geometry
                if abs(a.x - b.x) < 1e-6 and abs(a.y - b.y) < 1e-6 and abs(abs(a.z - b.z) - PLATE_T * mm) < 1e-6:
                    edges.add(e)
            fil = mount.features.filletFeatures
            fin = fil.createInput()
            try:
                fin.edgeSetInputs.addConstantRadiusEdgeSet(edges, VI.createByReal(CORNER_R * mm), True)
            except Exception:
                fin.addConstantRadiusEdgeSet(edges, VI.createByReal(CORNER_R * mm), True)
            fil.add(fin)
        except Exception:
            log.append("fillet skipped: " + traceback.format_exc())

        # M3 clearance holes + underside counterbores for off-the-shelf M3 standoffs
        nh = [(x - NUC_W / 2, y + nuc_y_bot) for (x, y) in NUC_HOLES]
        sk = sketch(mount, "M3_Clearance"); circles(sk, HOLES + nh, M3_CLEAR_D)
        extrude(mount, sk, 0, PLATE_T, CUT, [base])
        sk = sketch(mount, "M3_Counterbores"); circles(sk, HOLES + nh, CBORE_D)
        extrude(mount, sk, 0, CBORE_DEPTH, CUT, [base])

        # reference M3 hex standoffs (bought parts, not printed)
        so = new_comp(root, "M3_Standoffs_ref")
        def hexes(sk, pts):
            r = HEX_AF / math.sqrt(3.0)
            for (cx, cy) in pts:
                poly(sk, [(cx + r * math.cos(math.radians(60 * i)), cy + r * math.sin(math.radians(60 * i))) for i in range(6)])
        sk = sketch(so, "Shield_Standoffs"); hexes(sk, HOLES)
        f = extrude(so, sk, PLATE_T, STANDOFF_H, NEW)
        for i in range(f.bodies.count):
            f.bodies.item(i).name = "M3x%g_standoff_%d" % (STANDOFF_H, i + 1)
        sk = sketch(so, "Nucleo_Standoffs"); hexes(sk, nh)
        f = extrude(so, sk, PLATE_T, NUC_STANDOFF_H, NEW)
        for i in range(f.bodies.count):
            f.bodies.item(i).name = "M3x%g_standoff_nucleo_%d" % (NUC_STANDOFF_H, i + 1)

        feet = [(px0 + FOOT_INSET, py0 + FOOT_INSET), (px1 - FOOT_INSET, py0 + FOOT_INSET),
                (px0 + FOOT_INSET, py1 - FOOT_INSET), (px1 - FOOT_INSET, py1 - FOOT_INSET)]
        sk = sketch(mount, "Foot_Holes"); circles(sk, feet, FOOT_HOLE_D)
        extrude(mount, sk, 0, PLATE_T, CUT, [base])

        # ---------- Shield PCB: real model exported from KiCad (board-centre origin, underside at z=0) ----------
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
        pcb_step = os.path.join(OUT_DIR, PCB_STEP)
        if os.path.exists(pcb_step):
            import_step(pcb_step, "TL73_Shield_PCB_KiCad", 0, 0, z_shield)
            log.append("imported " + PCB_STEP)
        else:
            log.append("PCB STEP not found, skipped: " + pcb_step)

        # ---------- Nucleo-G474RE (simplified reference) ----------
        nuc_step = os.path.join(OUT_DIR, NUC_STEP)
        if os.path.exists(nuc_step):
            # ST model frame: origin at board lower-left corner, z=0 on the top face
            import_step(nuc_step, "NUCLEO_G474RE_MB1367", -NUC_W / 2, NUC_Y_TOP - NUC_L, z_nuc_top)
            log.append("imported " + NUC_STEP)
        else:
            nuc = new_comp(root, "NUCLEO_G474RE_ref")
            sk = sketch(nuc, "Board")
            rect(sk, -NUC_W / 2, nuc_y_bot, NUC_W / 2, NUC_Y_TOP)
            nb = extrude(nuc, sk, z_nuc_bot, NUC_T, NEW).bodies.item(0)
            nb.name = "Nucleo_PCB"
            sk = sketch(nuc, "Morpho")
            for s in (-1, 1):
                rect(sk, s * MORPHO_X - 2.54, MORPHO_Y_BOT - 1.27, s * MORPHO_X + 2.54, MORPHO_Y_TOP + 1.27)
            f = extrude(nuc, sk, z_nuc_top, STACK_GAP, NEW)
            for i in range(f.bodies.count):
                f.bodies.item(i).name = "Morpho_stack_%d" % (i + 1)
            f = extrude(nuc, sk, z_nuc_bot - PIN_TAIL, PIN_TAIL, NEW)
            for i in range(f.bodies.count):
                f.bodies.item(i).name = "Morpho_pin_tails_%d" % (i + 1)
            sk = sketch(nuc, "USB")
            rect(sk, -4.0, NUC_Y_TOP - 7.0, 4.0, NUC_Y_TOP + 1.0)
            extrude(nuc, sk, z_nuc_top, 3.0, NEW).bodies.item(0).name = "STLINK_USB"

        # ---------- exports ----------
        try:
            em = design.exportManager
            em.execute(em.createSTEPExportOptions(os.path.join(OUT_DIR, "TL73_PCB_Mount_Assembly.step"), root))
            em.execute(em.createSTEPExportOptions(os.path.join(OUT_DIR, "TL73_PCB_Mount.step"), mount))
            em.execute(em.createSTLExportOptions(base, os.path.join(OUT_DIR, "TL73_PCB_Mount.stl")))
            em.execute(em.createFusionArchiveExportOptions(os.path.join(OUT_DIR, "TL73_PCB_Mount.f3d")))
        except Exception:
            log.append("export problem: " + traceback.format_exc())

        try:
            app.activeViewport.goHome()
            app.activeViewport.fit()
        except Exception:
            pass
        bb = base.boundingBox
        log.append("OK mount bbox mm: %.1f x %.1f x %.1f, volume cm3 %.1f" % (
            (bb.maxPoint.x - bb.minPoint.x) * 10, (bb.maxPoint.y - bb.minPoint.y) * 10,
            (bb.maxPoint.z - bb.minPoint.z) * 10, base.volume))
    except Exception:
        log.append("FAILED: " + traceback.format_exc())
    try:
        with open(os.path.join(OUT_DIR, "build_log.txt"), "w") as fh:
            fh.write("\n".join(log))
    except Exception:
        pass

run(None)
