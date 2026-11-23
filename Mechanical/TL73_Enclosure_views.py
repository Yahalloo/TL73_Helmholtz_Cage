# Saves pictures of the open Fusion design (run after TL73_Enclosure.py) into Mechanical/enclosure_views
import adsk.core, os
OUT = r"D:\GoogleDrive_Personal\Documents\Uni Courses\Final Year\T1\ELEC 491\Project_Design_Files\Repositry\PCB_V1.0\TL73_Helmholtz_Cage\Mechanical\enclosure_views"
os.makedirs(OUT, exist_ok=True)
_app = adsk.core.Application.get()
_vp = _app.activeViewport
def shot(name, eye, target, up=(0, 0, 1), fit=True):
    c = _vp.camera
    c.isSmoothTransition = False
    c.eye = adsk.core.Point3D.create(*eye)
    c.target = adsk.core.Point3D.create(*target)
    c.upVector = adsk.core.Vector3D.create(*up)
    c.isFitView = fit
    _vp.camera = c
    adsk.doEvents()
    _vp.refresh()
    adsk.doEvents()
    _vp.saveAsImageFile(os.path.join(OUT, name + ".png"), 1800, 1100)
shot("iso_back_right", (75, 80, 55), (8, 0, 3))
shot("front", (0, -100, 4), (0, 0, 4))
shot("back", (0, 100, 4), (0, 0, 4))
shot("left", (-100, 0, 4), (0, 0, 4))
shot("right", (100, 0, 4), (0, 0, 4))
shot("top", (8, 0, 100), (8, 0, 0), (0, 1, 0))
shot("iso_front_left", (-50, -70, 55), (8, 0, 3))
shot("ntc_close", (-30, 14, 14), (-6.5, 1.5, 5.5), fit=False)
shot("inside", (4, -2, 60), (0, 0, 3), (0, 1, 0), fit=False)
shot("front_close", (-6, -30, 12), (0, -12.8, 5), fit=False)
shot("iso_front_left", (-50, -70, 55), (8, 0, 3))
