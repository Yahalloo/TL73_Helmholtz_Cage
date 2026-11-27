# Saves pictures of the open Fusion design (run after TL73_Enclosure.py) into Mechanical/enclosure_views
# 2026-11-27: views for the report (lid parked beside the box at x = 217 mm, control pod on the +x side).
# Fusion works in cm: box centre (0, 0), pod deck at x 7.5 .. 12.2, z 9.3; parked lid centre x 21.7.
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
shot("r34_iso_front_right", (40, -75, 55), (9, 0, 3))      # coil side, pod and parked lid with the fan
shot("r34_iso_back_right", (45, 75, 55), (9, 0, 3))        # supply side, pod deck, USB-C
shot("r34_top", (9, 0, 120), (9, 0, 0), (0, 1, 0))         # from above: inside of the box, pod deck, lid beside it
shot("r34_pod_close", (24, -22, 24), (9.7, -1.5, 8.5), fit=False)   # stop switch and LEDs on the pod deck
shot("r34_pod_inside", (-3, -14, 16), (9, -1.5, 6), fit=False)      # through the access window into the pod
