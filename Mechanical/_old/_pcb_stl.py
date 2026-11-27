# Exports the current board from KiCad as STEP, imports it into Fusion, moves the 3D models that KiCad's
# STEP export misplaces (same corrections as TL73_Enclosure.py), then saves a binary STL and two pictures.
import adsk.core, adsk.fusion, os, subprocess, traceback
_P = r"D:\GoogleDrive_Personal\Documents\Uni Courses\Final Year\T1\ELEC 491\Project_Design_Files\Repositry\PCB_V1.0\TL73_Helmholtz_Cage"
_M = os.path.join(_P, "Mechanical")
_K = r"C:\Users\adars\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe"
_FIX = {"ANT-TH_L33.0-W12.0": (-9.71, 0.0, 6.55), "CAP-TH_BD10.0-P5.00-D0.6-FD": (0.0, 0.0, 8.01), "CAP-TH_BD10.0-P5.00-D0.6-FD-A": (0.0, 0.0, 0.0)}
_L = []
try:
    _step = os.path.join(_M, "TL73_Coil_Driver_PCB.step")
    _p = subprocess.run([_K, "pcb", "export", "step", "--subst-models", "--force", "-o", _step, os.path.join(_P, "TL_73_Helmholtz_Cage_PCB.kicad_pcb")], capture_output=True, text=True, timeout=400, creationflags=0x08000000, cwd=_P)
    _L.append("kicad-cli rc %d %s %s" % (_p.returncode, _p.stdout[-600:], _p.stderr[-600:]))
    _app = adsk.core.Application.get()
    _doc = _app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    _des = adsk.fusion.Design.cast(_app.activeProduct)
    _root = _des.rootComponent
    _im = _app.importManager
    _im.importToTarget(_im.createSTEPImportOptions(_step), _root)
    _occ = _root.occurrences.item(_root.occurrences.count - 1)
    _names = {}
    _n = [0]
    def _fix(comp, ctx, depth=0):
        for native in comp.occurrences:
            o = native.createForAssemblyContext(ctx)
            nm = o.component.name
            _names[nm.split(":")[0][:40]] = _names.get(nm.split(":")[0][:40], 0) + 1
            hit = None
            for pre, off in _FIX.items():
                if nm.startswith(pre):
                    hit = off
            if hit:
                m = adsk.core.Matrix3D.create()
                m.translation = adsk.core.Vector3D.create(hit[0] * 0.1, hit[1] * 0.1, hit[2] * 0.1)
                m.transformBy(o.transform2)
                o.transform2 = m
                _n[0] += 1
            elif depth < 3:
                _fix(native.component, o, depth + 1)
    _fix(_occ.component, _occ)
    try:
        if _des.snapshots.hasPendingSnapshot:
            _des.snapshots.add()
    except Exception:
        pass
    _L.append("moved %d models" % _n[0])
    _L.append("components: " + ", ".join("%s x%d" % kv for kv in sorted(_names.items())))
    _em = _des.exportManager
    _o = _em.createSTLExportOptions(_root, os.path.join(_M, "TL73_Coil_Driver_PCB.stl"))
    _o.isBinaryFormat = True
    _o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
    _em.execute(_o)
    _vp = _app.activeViewport
    def _shot(name, eye, up):
        c = _vp.camera
        c.isSmoothTransition = False
        c.target = adsk.core.Point3D.create(0, 0, 0)
        c.eye = adsk.core.Point3D.create(*eye)
        c.upVector = adsk.core.Vector3D.create(*up)
        c.isFitView = True
        _vp.camera = c
        adsk.doEvents(); _vp.refresh(); adsk.doEvents()
        _vp.fit(); adsk.doEvents()
        _vp.saveAsImageFile(os.path.join(_M, "_old", name + ".png"), 1500, 1000)
    _shot("_pcb_iso", (-30, -50, 40), (0, 0, 1))
    _shot("_pcb_side", (-100, 0, 2), (0, 0, 1))
    bb = _root.boundingBox
    _L.append("ok size mm %.1f x %.1f x %.1f" % ((bb.maxPoint.x-bb.minPoint.x)*10, (bb.maxPoint.y-bb.minPoint.y)*10, (bb.maxPoint.z-bb.minPoint.z)*10))
except Exception:
    _L.append("FAILED " + traceback.format_exc())
open(os.path.join(_M, "_old", "_pcb_stl_log.txt"), "w").write("\n".join(_L))
