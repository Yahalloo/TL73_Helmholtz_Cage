# Imports NUCLEO_G474RE.step into a new Fusion design and saves it as one binary STL (mm).
import adsk.core, adsk.fusion, os, traceback
_D = r"D:\GoogleDrive_Personal\Documents\Uni Courses\Final Year\T1\ELEC 491\Project_Design_Files\Repositry\PCB_V1.0\TL73_Helmholtz_Cage\Mechanical"
_L = []
try:
    _app = adsk.core.Application.get()
    _doc = _app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    _des = adsk.fusion.Design.cast(_app.activeProduct)
    _im = _app.importManager
    _im.importToTarget(_im.createSTEPImportOptions(os.path.join(_D, "NUCLEO_G474RE.step")), _des.rootComponent)
    _em = _des.exportManager
    _o = _em.createSTLExportOptions(_des.rootComponent, os.path.join(_D, "NUCLEO_G474RE.stl"))
    _o.isBinaryFormat = True
    _o.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
    _em.execute(_o)
    bb = _des.rootComponent.boundingBox
    _L.append("ok size mm %.1f x %.1f x %.1f" % ((bb.maxPoint.x-bb.minPoint.x)*10, (bb.maxPoint.y-bb.minPoint.y)*10, (bb.maxPoint.z-bb.minPoint.z)*10))
    _doc.close(False)
except Exception:
    _L.append("FAILED " + traceback.format_exc())
open(os.path.join(_D, "_nucleo_stl_log.txt"), "w").write("\n".join(_L))
