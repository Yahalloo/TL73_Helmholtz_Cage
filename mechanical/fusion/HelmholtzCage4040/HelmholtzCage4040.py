"""Fusion 360 script: builds the 4040 T-slot Helmholtz cage assembly.

Run it from Utilities > Scripts and Add-Ins (see README.md). All geometry and
placements come from cage_layout.py, which reads design.json (the optimiser
output). To change the cage, edit design.json or the constants in
cage_layout.py and run the script again. It creates a new document each time.

Outputs in a new document:
  * Pair X/Y/Z, each with 2 identical Coil components (translated, not flipped) + struts
  * Crossing mounts, Base, CubeSat fixture, Reference volumes, Assembly tools
  * exports/stl/*.stl for every printed part, exports/dxf/corner_plate.dxf, exports/cage.step
"""

import importlib
import os
import sys
import traceback

import adsk.core
import adsk.fusion

HERE = os.path.dirname(os.path.realpath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import cage_layout as L  # noqa: E402

importlib.reload(L)

CM = 0.1  # Fusion API lengths are in cm
COLORS = {  # class -> RGB, opacity
    "aluminium": ((190, 194, 200), 1.0),
    "copper": ((196, 110, 50), 1.0),
    "printed": ((240, 130, 30), 1.0),
    "purchased": ((200, 30, 30), 1.0),
    "reference": ((60, 140, 230), 0.15),
}


def P(x, y, z):
    return adsk.core.Point3D.create(x * CM, y * CM, z * CM)


def V(v):
    return adsk.core.Vector3D.create(float(v[0]), float(v[1]), float(v[2]))


# ------------------------------------------------------------------ temporary B-rep helpers (mm)
class Geo:
    def __init__(self):
        self.tb = adsk.fusion.TemporaryBRepManager.get()

    def box(self, x0, x1, y0, y1, z0, z1):
        xa, xb = sorted((x0, x1))
        ya, yb = sorted((y0, y1))
        za, zb = sorted((z0, z1))
        obb = adsk.core.OrientedBoundingBox3D.create(
            P((xa + xb) / 2, (ya + yb) / 2, (za + zb) / 2), V((1, 0, 0)), V((0, 1, 0)),
            (xb - xa) * CM, (yb - ya) * CM, (zb - za) * CM)
        return self.tb.createBox(obb)

    def cyl(self, p1, p2, r):
        return self.tb.createCylinderOrCone(P(*p1), r * CM, P(*p2), r * CM)

    def _op(self, a, bs, kind):
        for b in bs:
            self.tb.booleanOperation(a, b, kind)
        return a

    def union(self, a, *bs):
        return self._op(a, bs, adsk.fusion.BooleanTypes.UnionBooleanType)

    def cut(self, a, *bs):
        return self._op(a, bs, adsk.fusion.BooleanTypes.DifferenceBooleanType)

    def inter(self, a, b):
        return self._op(a, [b], adsk.fusion.BooleanTypes.IntersectionBooleanType)

    # ---------------------------------------------------------------- part solids
    def profile(self, length):
        b = self.box(-20, 20, -20, 20, 0, length)
        for k in (0, 1):
            for s in (1, -1):
                for w, d0, d1 in ((L.SLOT_NECK_W, -1.0, L.SLOT_NECK_D + 0.5),
                                  (L.SLOT_CAV_W, L.SLOT_NECK_D, L.SLOT_CAV_D)):
                    n0, n1 = s * (20 - d1), s * (20 - d0)
                    if k == 0:
                        self.cut(b, self.box(n0, n1, -w / 2, w / 2, -1, length + 1))
                    else:
                        self.cut(b, self.box(-w / 2, w / 2, n0, n1, -1, length + 1))
        self.cut(b, self.cyl((0, 0, -1), (0, 0, length + 1), L.CORE_HOLE_D / 2))
        return [b]

    def bracket(self):
        w = L.BRK_W / 2
        b = self.box(0, L.BRK_LEG, 0, L.BRK_T, -w, w)
        self.union(b, self.box(0, L.BRK_T, 0, L.BRK_LEG, -w, w))
        self.cut(b, self.cyl((20, -1, 0), (20, L.BRK_T + 1, 0), 4.5),
                 self.cyl((-1, 20, 0), (L.BRK_T + 1, 20, 0), 4.5))
        return [b]

    def plate(self):
        t = L.PLATE_T / 2
        b = self.box(-40, 0, -40, 0, -t, t)
        self.union(b, self.box(-40, 0, -40 - L.PLATE_LEG, -40, -t, t),
                   self.box(-40 - L.PLATE_LEG, -40, -40, 0, -t, t))
        for x, y in ((-20, -70), (-70, -20), (-30, -30)):
            self.cut(b, self.cyl((x, y, -t - 1), (x, y, t + 1), 4.5))
        return [b]

    def corner(self):
        c0 = L.WIND_FLOOR + L.R_FLOOR          # arc centre offset from the outer corner
        w = L.WIND_W / 2 + L.GROOVE_CLR
        cube = self.box(-40, 0, -40, 0, -20, 20)
        groove = self.box(-41, 1, -41, 1, -w, w)
        floor = self.box(-41, -L.WIND_FLOOR, -41, -c0, -w - 1, w + 1)
        self.union(floor, self.box(-41, -c0, -41, -L.WIND_FLOOR, -w - 1, w + 1),
                   self.cyl((-c0, -c0, -w - 1), (-c0, -c0, w + 1), L.R_FLOOR))
        self.cut(groove, floor)
        self.cut(cube, groove)
        n0, n1 = 20 - L.SLOT_NECK_D + 0.3, 20.0     # tongues sit in the side-slot necks of both members
        h = L.SLOT_NECK_W / 2 - 0.2
        for z0, z1 in ((n0, n1), (-n1, -n0)):
            self.union(cube, self.box(-20 - h, -20 + h, -55, -40, z0, z1),
                       self.box(-55, -40, -20 - h, -20 + h, z0, z1))
        self.cut(cube, self.cyl((-30, -30, -21), (-30, -30, 21), 4.5))    # through-bolt for the two plates
        q = c0 - L.R_FLOOR / 1.4142 + 1.0                                  # thermistor pocket in the groove floor
        self.cut(cube, self.cyl((-q + 1.0, -q + 1.0, 0), (-q - 3.5, -q - 3.5, 0), 2.2))
        return [cube]

    def winding(self, F):
        a0, a1 = F - L.WIND_FLOOR, F - L.WIND_TOP
        cs = F - L.WIND_FLOOR - L.R_FLOOR
        w = L.WIND_W / 2
        body = self.box(-cs, cs, a0, a1, -w, w)
        self.union(body, self.box(-cs, cs, -a1, -a0, -w, w),
                   self.box(a0, a1, -cs, cs, -w, w), self.box(-a1, -a0, -cs, cs, -w, w))
        for sa in (1, -1):
            for sb in (1, -1):
                ring = self.cyl((sa * cs, sb * cs, -w), (sa * cs, sb * cs, w), a1 - cs)
                self.cut(ring, self.cyl((sa * cs, sb * cs, -w - 1), (sa * cs, sb * cs, w + 1), a0 - cs))
                self.inter(ring, self.box(sa * cs, sa * (a1 + 1), sb * cs, sb * (a1 + 1), -w - 1, w + 1))
                self.union(body, ring)
        return [body]

    def spacer(self, length):
        b = self.cyl((0, 0, 0), (0, 0, length), L.SPACER_OD / 2)
        self.cut(b, self.cyl((0, 0, -1), (0, 0, length + 1), L.SPACER_ID / 2))
        return [b]

    def clip(self):
        h = L.SLOT_NECK_W / 2 - 0.2
        return [self.box(-3.8, 0, -L.CLIP_L / 2, L.CLIP_L / 2, -h, h)]

    def fork(self):
        h = L.SLOT_NECK_W / 2 - 0.2
        b = self.box(0, 10, -30, 30, -15, 25)
        self.union(b, self.box(0, 10, -30, -20.2, 25, 50), self.box(0, 10, 20.2, 30, 25, 50),
                   self.box(-3.8, 0, -25, 25, -h, h))
        self.cut(b, self.cyl((-5, 0, 0), (11, 0, 0), 4.5))
        return [b]

    def terminal(self):
        h = L.SLOT_NECK_W / 2 - 0.2
        b = self.box(0, 12, -25, 25, -15, 15)
        self.union(b, self.box(-3.8, 0, -20, 20, -h, h))
        self.cut(b, self.cyl((-5, -17, 0), (13, -17, 0), 4.5),
                 self.box(3, 7, 21, 24, -16, 16))     # zip-tie slot for lead strain relief
        return [b]

    def pp(self):
        return [self.box(0, 7.9, 0, 24.6, -3.95, 3.95)]

    def cradle(self):
        t = L.CRADLE_T
        hx, hy = L.CUBESAT_6U[0] / 2 + 0.3, L.CUBESAT_6U[1] / 2 + 0.3
        b = self.box(-70, 70, -133, 133, 0, t)
        for sx in (1, -1):
            for sy in (1, -1):
                self.union(b, self.box(sx * hx, sx * (hx + 8), sy * (hy - 25), sy * (hy + 8), t, t + 40),
                           self.box(sx * (hx - 25), sx * (hx + 8), sy * hy, sy * (hy + 8), t, t + 40))
        self.cut(b, self.cyl((0, 0, -1), (0, 0, t + 1), 4.5))
        return [b]

    def foot(self):
        h = L.SLOT_NECK_W / 2 - 0.2
        b = self.box(-30, 30, -30, 30, 0, 10)
        self.union(b, self.box(-h, h, -25, 25, 10, 10 + 3.8))
        return [b]

    def gauge(self, length):
        h = L.SLOT_NECK_W / 2 - 0.2
        b = self.box(0, length, -20, 20, 0, 10)
        self.union(b, self.box(0, length, -h, h, -3.8, 0))
        return [b]

    def refbox(self, size):
        x, y, z = (s / 2 for s in size)
        return [self.box(-x, x, -y, y, -z, z)]

    def make(self, part):
        k, p = part.kind, part.params
        if k == "profile":
            return self.profile(p["L"])
        if k == "winding":
            return self.winding(p["F"])
        if k == "spacer":
            return self.spacer(p["L"])
        if k == "gauge":
            return self.gauge(p["L"])
        if k == "refbox":
            return self.refbox(p["size"])
        return getattr(self, k)()


# ------------------------------------------------------------------ assembly builder
class Builder:
    def __init__(self, app, design, lay):
        self.app, self.design, self.lay = app, design, lay
        self.geo = Geo()
        self.part_comps = {}
        self.node_comps = {}
        self.appearances = {}
        self.n_occ = 0

    def matrix(self, frame):
        o, x, y = frame
        m = adsk.core.Matrix3D.create()
        m.setWithCoordinateSystem(P(*o), V(x), V(y), V(L.cross(x, y)))
        return m

    def appearance(self, cls):
        if cls in self.appearances:
            return self.appearances[cls]
        app_ = None
        try:
            rgb, _ = COLORS[cls]
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
            if base:
                app_ = self.design.appearances.addByCopy(base, f"Cage {cls}")
                for prop in app_.appearanceProperties:
                    cp = adsk.core.ColorProperty.cast(prop)
                    if cp and cp.name in ("Color", "Colour"):
                        cp.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 0)
                        break
        except Exception:
            app_ = None
        self.appearances[cls] = app_
        return app_

    def part_component(self, key, parent, m):
        comp = self.part_comps.get(key)
        if comp is not None:
            parent.occurrences.addExistingComponent(comp, m)
            self.n_occ += 1
            return
        part = self.lay.parts[key]
        occ = parent.occurrences.addNewComponent(m)
        self.n_occ += 1
        comp = occ.component
        comp.name = part.name
        try:
            comp.partNumber = part.pn or part.key
            comp.description = f"{part.desc} | source: {part.source}"
        except Exception:
            pass
        ap = self.appearance(part.cls)
        for tb in self.geo.make(part):
            body = comp.bRepBodies.add(tb)
            body.name = part.name
            if ap:
                try:
                    body.appearance = ap
                except Exception:
                    pass
            if part.cls == "reference":
                try:
                    body.opacity = COLORS["reference"][1]
                except Exception:
                    pass
        self.part_comps[key] = comp
        adsk.doEvents()

    def place(self, node, comp):
        for child, frame, _tag in node.children:
            m = self.matrix(frame)
            if isinstance(child, L.Node):
                existing = self.node_comps.get(id(child))
                if existing is not None:
                    comp.occurrences.addExistingComponent(existing, m)
                    self.n_occ += 1
                    continue
                occ = comp.occurrences.addNewComponent(m)
                self.n_occ += 1
                occ.component.name = child.name
                self.node_comps[id(child)] = occ.component
                self.place(child, occ.component)
            else:
                self.part_component(child, comp, m)

    # ---------------------------------------------------------------- exports
    def export(self):
        em = self.design.exportManager
        out = os.path.join(HERE, "exports")
        notes = []
        stl_dir = os.path.join(out, "stl")
        os.makedirs(stl_dir, exist_ok=True)
        for key, comp in self.part_comps.items():
            part = self.lay.parts[key]
            if part.cls != "printed" or comp.bRepBodies.count == 0:
                continue
            try:
                path = os.path.join(stl_dir, f"{part.pn}.stl")
                opts = em.createSTLExportOptions(comp.bRepBodies.item(0), path)
                opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
                em.execute(opts)
            except Exception as e:
                notes.append(f"STL {part.pn}: {e}")
        try:
            comp = self.part_comps["PLATE"]
            body = comp.bRepBodies.item(0)
            top = max((f for f in body.faces if f.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType),
                      key=lambda f: f.pointOnFace.z)
            sk = comp.sketches.add(top)
            for e in top.edges:
                sk.project(e)
            os.makedirs(os.path.join(out, "dxf"), exist_ok=True)
            sk.saveAsDXF(os.path.join(out, "dxf", "corner_plate.dxf"))
        except Exception as e:
            notes.append(f"DXF: {e}")
        try:
            em.execute(em.createSTEPExportOptions(os.path.join(out, "cage.step"), self.design.rootComponent))
        except Exception as e:
            notes.append(f"STEP: {e}")
        return out, notes


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        lay = L.build(os.path.join(HERE, "design.json"))

        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.DirectDesignType
        root = design.rootComponent
        root.name = f"Helmholtz Cage 4040 ({lay.info.get('design', '')})"

        b = Builder(app, design, lay)
        b.place(lay.root, root)
        app.activeViewport.fit()
        out, notes = b.export()

        geo = lay.info["geo"]
        lines = [f"{L.AX[g['axis']]}: side {2 * g['h']:.1f} mm, spacing {g['d']:.1f} mm, {g['turns']} turns"
                 for g in geo]
        msg = (f"Built {b.n_occ} occurrences from {len(b.part_comps)} part definitions.\n\n" + "\n".join(lines)
               + f"\n\nExports: {out}" + ("\n\nExport notes:\n" + "\n".join(notes) if notes else ""))
        ui.messageBox(msg, "Helmholtz Cage 4040")
    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
