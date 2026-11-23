def build(name, par, P, extra, title):
    W=[];F=[];S=[];T=[]
    def wire(a,b,c,d): W.append(f"WIRE {a} {b} {c} {d}")
    def flag(x,y,n): F.append(f"FLAG {x} {y} {n}")
    def two(kind,nm,x,y,top,bot,val,ex=None):
        p1,p2=((x+16,y),(x+16,y+64)) if kind=="cap" else ((x+16,y+16),(x+16,y+96))
        wire(*p1,p1[0],p1[1]-32); flag(p1[0],p1[1]-32,top); wire(*p2,p2[0],p2[1]+32); flag(p2[0],p2[1]+32,bot)
        S.append(f"SYMBOL {kind} {x} {y} R0\nSYMATTR InstName {nm}\nSYMATTR Value {val}"+(f"\nSYMATTR SpiceLine {ex}" if ex else ""))
    def src(kind,nm,x,y,top,bot,val):
        wire(x,y+16,x,y-16); flag(x,y-16,top); wire(x,y+96,x,y+128); flag(x,y+128,bot)
        S.append(f"SYMBOL {kind} {x} {y} R0\nSYMATTR InstName {nm}\nSYMATTR Value {val}")
    def nmos(nm,x,y,d,g,s):
        wire(x+48,y,x+48,y-32); flag(x+48,y-32,d); wire(x+48,y+96,x+48,y+128); flag(x+48,y+128,s)
        wire(x,y+80,x-32,y+80); flag(x-32,y+80,g)
        S.append(f"SYMBOL nmos {x} {y} R0\nSYMATTR InstName {nm}\nSYMATTR Value NFET")
    def note(x,y,s): T.append(f"TEXT {x} {y} Left 2 ;{s}")
    def sym(kind,nm,x,y,rot,val,ex=None):
        win=""
        if rot=="R270":
            win={"res":"WINDOW 0 32 56 VTop 2\nWINDOW 3 0 56 VBottom 2\n","ind":"WINDOW 0 32 56 VTop 2\nWINDOW 3 5 56 VBottom 2\n","cap":"WINDOW 0 32 32 VTop 2\nWINDOW 3 0 32 VBottom 2\n"}[kind]
            if ex: val=f"{val} {ex}"; ex=None
        S.append(f"SYMBOL {kind} {x} {y} {rot}\n{win}SYMATTR InstName {nm}\nSYMATTR Value {val}"+(f"\nSYMATTR SpiceLine {ex}" if ex else ""))
    def gnd(x,y): flag(x,y,"0")
    def path(*pts):
        for (p,q) in zip(pts[:-1],pts[1:]): wire(p[0],p[1],q[0],q[1])
    def hres(kind,nm,x0,y,val,ex=None):
        # horizontal 2-pin part on the line y, pin 1 on the left: occupies x0..x0+80 (res, ind) or x0..x0+64 (cap)
        sym(kind,nm,x0,y+16,"R270",val,ex) if kind=="cap" else sym(kind,nm,x0-16,y+16,"R270",val,ex)
    def vcap(nm,x,y,val,ex=None): sym("cap",nm,x-16,y,"R0",val,ex)      # pins (x,y) and (x,y+64)
    def vres(nm,x,y,val,ex=None): sym("res",nm,x-16,y-16,"R0",val,ex)   # pins (x,y) and (x,y+80)
    XB=1280; YL=272; cp,cm="X","Z"
    # ---- supply (left), wired to the VBUS rail at y = 0
    note(-1024,-112,"30 V SUPPLY (as on the PCB)")
    sym("voltage","V1",-992,160,"R0","{Vbus}"); path((-992,176),(-992,0),(-896,0)); path((-992,256),(-992,288)); gnd(-992,288)
    hres("ind","Lsup",-896,0,"{Lsup}","Rser={Rsup}"); flag(-944,0,"VIN")
    path((-816,0),(XB,0)); flag(-432,0,"VBUS")
    vcap("C307",-720,96,"{Cbulk}","Rser={ESRb}"); path((-720,0),(-720,96)); path((-720,160),(-720,208)); gnd(-720,208)
    vcap("C305",-624,96,"100n","Rser=5m"); path((-624,0),(-624,96)); path((-624,160),(-624,208)); gnd(-624,208)
    vres("R304",-528,64,"{RsV}"); path((-528,0),(-528,64)); vcap("C306",-528,160,"{CsV}"); path((-528,144),(-528,160)); path((-528,224),(-528,256)); gnd(-528,256)
    # ---- H-bridge: leg A at x = 0, leg B at x = XB, coil path between the two mid-points
    note(-208,-112,"H-BRIDGE (DRV8873 output stage)   M1/M2 = OUT A leg,  M3/M4 = OUT B leg")
    S.append("SYMBOL nmos -48 96 R0\nSYMATTR InstName M1\nSYMATTR Value NFET"); S.append("SYMBOL nmos -48 336 R0\nSYMATTR InstName M2\nSYMATTR Value NFET")
    path((0,0),(0,96)); path((0,192),(0,256)); path((0,256),(0,YL)); path((0,YL),(0,336)); path((0,432),(0,464)); path((0,464),(0,480)); gnd(0,480)
    sym("bv","BgA1",-288,112,"R0","V={Vg}*V(hA)"); path((-48,176),(-112,176),(-112,112),(-288,112),(-288,128)); path((-288,208),(-288,256),(0,256))
    sym("bv","BgA2",-288,352,"R0","V={Vg}*V(lA)"); path((-48,416),(-112,416),(-112,352),(-288,352),(-288,368)); path((-288,448),(-288,464),(0,464))
    S.append(f"SYMBOL nmos {XB+48} 96 M0\nSYMATTR InstName M3\nSYMATTR Value NFET"); S.append(f"SYMBOL nmos {XB+48} 336 M0\nSYMATTR InstName M4\nSYMATTR Value NFET")
    path((XB,0),(XB,96)); path((XB,192),(XB,256)); path((XB,256),(XB,YL)); path((XB,YL),(XB,336)); path((XB,432),(XB,464)); path((XB,464),(XB,480)); gnd(XB,480)
    sym("bv","BgB1",XB+288,112,"R0","V={Vg}*V(hB)"); path((XB+48,176),(XB+112,176),(XB+112,112),(XB+288,112),(XB+288,128)); path((XB+288,208),(XB+288,256),(XB,256))
    sym("bv","BgB2",XB+288,352,"R0","V={Vg}*V(lB)"); path((XB+48,416),(XB+112,416),(XB+112,352),(XB+288,352),(XB+288,368)); path((XB+288,448),(XB+288,464),(XB,464))
    # ---- coil path on the line y = YL:  A - Rsh - CP - Llead1 - X - Lcoil - Rcoil - Z - Llead2 - B
    note(560,YL-176,"COIL with its winding capacitance")
    path((0,YL),(96,YL)); flag(48,YL,"A"); hres("res","Rsh",96,YL,"{Rsh}")
    path((176,YL),(304,YL)); flag(208,YL,"CP"); hres("ind","Llead1",304,YL,"{Llead}","Rser={Rlead}")
    path((384,YL),(592,YL)); flag(528,YL,"X"); hres("ind","Lcoil",592,YL,"{Lc}")
    path((672,YL),(704,YL)); flag(688,YL,"M"); hres("res","Rcoil",704,YL,"{Rc}")
    path((784,YL),(992,YL)); flag(848,YL,"Z"); hres("ind","Llead2",992,YL,"{Llead}","Rser={Rlead}")
    path((1072,YL),(XB,YL)); flag(1216,YL,"B")
    # winding capacitance across the coil (above the line)
    path((448,YL),(448,176),(656,176)); hres("cap","Cw",656,176,"{Cw}"); path((720,176),(928,176),(928,YL))
    # snubber at the coil terminals (below the line)
    path((480,YL),(480,368),(544,368)); hres("res","RsE",544,368,"{RsE}"); path((624,368),(736,368)); hres("cap","CsE",736,368,"{CsE}"); path((800,368),(896,368),(896,YL))
    # coil terminals to ground
    path((416,YL),(416,400)); vcap("Ccm1",416,400,"{Ccm}"); path((416,464),(416,496)); gnd(416,496)
    path((960,YL),(960,400)); vcap("Ccm2",960,400,"{Ccm}"); path((960,464),(960,496)); gnd(960,496)
    # PCB snubbers at the connector: each terminal to ground, and across the terminals
    path((240,YL),(240,304)); vres("RcmP",240,304,"{RsCM}"); path((240,384),(240,400)); vcap("CcmP",240,400,"{CsCM}"); path((240,464),(240,496)); gnd(240,496)
    path((1136,YL),(1136,304)); vres("RcmN",1136,304,"{RsCM}"); path((1136,384),(1136,400)); vcap("CcmN",1136,400,"{CsCM}"); path((1136,464),(1136,496)); gnd(1136,496)
    path((272,YL),(272,592),(560,592)); hres("res","RsD",560,592,"{RsD}"); path((640,592),(752,592)); hres("cap","CsD",752,592,"{CsD}"); path((816,592),(1168,592),(1168,YL))
    note(-288,656,"RcmP/CcmP, RcmN/CcmN, RsD/CsD = PCB snubbers at the connector.   RsE/CsE = optional snubber at the coil.")
    note(-288,688,"Cw, Ccm1, Ccm2, Llead1, Llead2 = cable and winding parasitics (estimates).")
    # ---- control
    Y2=864; note(-1024,Y2-96,"PWM CONTROL (what the STM32 and the DRV8873 logic do). hA, lA, hB, lB drive the four gates above.")
    c1=[("voltage","Vtri","tri","PULSE(0 1 0 {T/2-1n} {T/2-1n} 1n {T})"),
        ("voltage","Vd","dcmd","PWL(0 {D0} {t1} {D0} {t1+tramp} {D1})"),
        ("bv","Bclamp","dcl","V=if({mode}==1,limit(V(dcmd),{Dmin},{Dmax}),limit(V(dcmd),-{Dmax},{Dmax}))"),
        ("bv","Bduty","duty","V=abs(V(dcl))"),
        ("bv","Bdir","dir","V=if(V(dcl)>=0,1,0)"),
        ("bv","Bsig1","sig1","V=if({mode}==1,if(V(dcl)>V(tri),3.3,0),if(V(duty)>V(tri),3.3,0))"),
        ("bv","Bsig2","sig2","V=if({mode}==1,if(1-V(dcl)>V(tri),3.3,0),3.3*V(dir))")]
    c2=[("BhA","hA","V=if({mode}==1,if(V(dcl)>V(tri)+{dd},1,0),if(V(dir)>0.5,if(V(duty)>V(tri)+{dd},1,0),0))"),
        ("BlA","lA","V=if({mode}==1,if(V(dcl)<V(tri)-{dd},1,0),if(V(dir)>0.5,if(V(duty)<V(tri)-{dd},1,0),1))"),
        ("BhB","hB","V=if({mode}==1,if(1-V(dcl)>V(tri)+{dd},1,0),if(V(dir)<0.5,if(V(duty)>V(tri)+{dd},1,0),0))"),
        ("BlB","lB","V=if({mode}==1,if(1-V(dcl)<V(tri)-{dd},1,0),if(V(dir)<0.5,if(V(duty)<V(tri)-{dd},1,0),1))")]
    for i,(k,nm,n,v) in enumerate(c1): src(k,nm,-992,Y2+i*176,n,"0",v)
    for i,(nm,n,v) in enumerate(c2): src("bv",nm,300,Y2+i*176,n,"0",v)
    # ---- directives
    tx=2000; ty=[-112]
    def t(s,d=32): T.append(f"TEXT {tx} {ty[0]} Left 2 {s}"); ty[0]+=d
    t(";"+title)
    t(";mode = 0: ONE SIDE HELD, OTHER SWITCHING. Command = signed duty d (-1..+1). dir = 1: M4 held on, leg A switches at |d|. dir = 0: M2 held on, leg B switches.")
    t(";mode = 1: UNIPOLAR. Command D (0.5 = 0 V). Leg A switches at D, leg B at 1-D.")
    t(";sig1/sig2 = STM32 pins.  mode 0: EN (PWM) and PH (direction).  mode 1: PWM_A and PWM_B.",48)
    t(";---- ADJUST THESE ----")
    for l in P: t(l)
    ty[0]+=16
    t(";---- DRV8873 values (150 mOhm HS+LS at 25 C, 250 mOhm at 150 C, RthJA 27.8 C/W, 53.2 V/us fastest slew, tPD ~1.5 us) ----")
    t("!.param Rds=75m td=300n Vg=5 Cgdx=0.1n RthJA=27.8 Pq=0.12 tmin=2u")
    t("!.param Ron={Rds*kT} Rtot={Rc+2*Ron+Rsh"+("+2*Rlead}" if par else "}"))
    t("!.param T={1/fsw} dd={td/T} Dmin={tmin*fsw} Dmax={1-tmin*fsw}")
    t(";tc = duty lost to the driver's switching delay and dead time (found from a first run). The command is raised by tc*fsw to make up for it; a closed current loop does this by itself.")
    t("!.param tc={if(fsw>50k,1.1u,1.5u)} u0={I0*Rtot/Vbus} u1={I1*Rtot/Vbus} tramp={abs(I1-I0)/Islew+1n}")
    t("!.param D0={mode*(0.5*(1+u0)+sgn(u0)*tc*fsw)+(1-mode)*(u0+sgn(u0)*tc*fsw)} D1={mode*(0.5*(1+u1)+sgn(u1)*tc*fsw)+(1-mode)*(u1+sgn(u1)*tc*fsw)}")
    t("!.param Rgs={(Vg-3.3)/(Cgdx*SR)}")
    t("!.model NFET VDMOS(Vto=3 Kp=40 Rd={Ron-2m-1/(40*(Vg-3))} Rs=2m Rg={Rgs} Cgdmax={Cgdx} Cgdmin={0.9*Cgdx} Cgs=2.5n Cjo=0.6n Is=1e-11 Rb=20m)")
    t("!.ic I(Lcoil)={I0}")
    t("!.tran 0 {tstop} {tsave} {dtmax}",48)
    vc=f"V({cp},{cm})"
    for l in ["!.meas TRAN Iavg AVG I(Lcoil) FROM {tstop-tsave-0.5m} TO {tstop-tsave}",
              "!.meas TRAN Iripple PP I(Lcoil) FROM {tstop-tsave-0.5m} TO {tstop-tsave}",
              f"!.meas TRAN Vcoil_max MAX {vc} FROM {{tstop-tsave-0.5m}} TO {{tstop-tsave}}",
              f"!.meas TRAN Vcoil_min MIN {vc} FROM {{tstop-tsave-0.5m}} TO {{tstop-tsave}}",
              "!.meas TRAN Vbus_pp PP V(VBUS) FROM {tstop-tsave-0.5m} TO {tstop-tsave}",
              "!.meas TRAN Pdrv AVG (V(VBUS)-V(A))*Id(M1)+V(A)*Id(M2)+(V(VBUS)-V(B))*Id(M3)+V(B)*Id(M4) FROM {tstop-tsave-0.5m} TO {tstop-tsave}",
              "!.meas TRAN Psnub_diff AVG I(RsD)*I(RsD)*{RsD} FROM {tstop-tsave-0.5m} TO {tstop-tsave}",
              "!.meas TRAN Psnub_cm AVG (I(RcmP)*I(RcmP)+I(RcmN)*I(RcmN))*{RsCM} FROM {tstop-tsave-0.5m} TO {tstop-tsave}",
              "!.meas TRAN Psnub_vm AVG I(R304)*I(R304)*{RsV} FROM {tstop-tsave-0.5m} TO {tstop-tsave}",
              "!.meas TRAN Psnub_coil AVG I(RsE)*I(RsE)*{RsE} FROM {tstop-tsave-0.5m} TO {tstop-tsave}","!.meas Tj PARAM {Tamb+RthJA*(Pdrv+Pq)}"]+extra: t(l)
    out="Version 4.1\nSHEET 1 5200 2700\n"+"\n".join(W+F+S+T)+"\n"
    open(f"/mnt/user-data/outputs/{name}.asc","w").write(out); return out

sup="!.param Cbulk=330u ESRb=50m RsV=3.3 CsV=10n"
parl=[";Parasitics (estimates): inductance and resistance per coil lead, winding capacitance, each coil terminal to GND, supply lead",
      "!.param Llead=1u Rlead=1m Cw=400p Ccm=200p Lsup=0.5u Rsup=20m"]
allsave="I(Lcoil) V(A) V(B) V(CP) V(X) V(Z) V(VBUS) V(sig1) V(sig2) V(duty) V(dir) V(dcl) V(tri) Id(M1) Id(M2) Id(M3) Id(M4) I(RsD) I(RcmP) I(RcmN) I(R304) I(RsE)"
revP=lambda f:[f"!.param Vbus=30 fsw={f}","!.step param mode list 0 1","!.param Lc=21.0m Rc=8 Rsh=10m",
     "!.param I0=-3.12 I1=3.12 Islew=1e6 t1=2m","!.param tsave=0 tstop=30m dtmax={T/100}","!.param kT=1.5 Tamb=30 SR=53.2e6"]+parl+[
     "!.param RsD=33 CsD=470p RsCM=33 CsCM=470p RsE=68 CsE=1f",sup]
revX=lambda sv:["!.meas TRAN t90abs WHEN I(Lcoil)={0.9*I1} RISE=1","!.meas t90 PARAM {t90abs-t1}","!.save "+sv]
build("sim_A_reversal_10k",True,revP("10k"),revX(allsave),"---- DRV8873S, Z AXIS, NO OUTPUT FILTER: current reversal -3.12 A to +3.12 A at 10 kHz, both switching schemes ----")
build("sim_B_reversal_100k",True,revP("100k"),revX("I(Lcoil) V(A) V(B) V(X) V(Z) V(sig1) V(sig2)")+[";Only a few signals are saved here to keep the file small. Power and temperature come from sim_D_steady_power."],"---- DRV8873S, Z AXIS, NO OUTPUT FILTER: current reversal -3.12 A to +3.12 A at 100 kHz, both switching schemes ----")
build("sim_C_snubber_100k",True,["!.param mode=0 Vbus=30 fsw=100k","!.step param cfg list 0 1 2","!.param Lc=21.0m Rc=8 Rsh=10m",
     "!.param I0=3.12 I1=3.12 Islew=200 t1=0.3m","!.param tsave=0.5m tstop=1.5m dtmax=5n","!.param kT=1.5 Tamb=30 SR=53.2e6"]+parl+[
     ";cfg = 0: no coil snubbers.  cfg = 1: PCB snubbers fitted (33R + 470p at the connector).  cfg = 2: snubber at the coil terminals instead (68R + 1.5n).",
     "!.param RsD=33 CsD={if(cfg==1,470p,1f)} RsCM=33 CsCM={if(cfg==1,470p,1f)} RsE=68 CsE={if(cfg==2,1.5n,1f)}",sup],["!.save "+allsave],
     "---- DRV8873S, Z AXIS, NO OUTPUT FILTER: effect of the coil snubbers at 100 kHz, steady 3.12 A, one side held ----")
build("sim_D_steady_power",True,["!.param Vbus=30","!.step param mode list 0 1","!.step param fsw list 10k 100k","!.param Lc=21.0m Rc=8 Rsh=10m",
     "!.param I0=3.12 I1=3.12 Islew=200 t1=0.3m","!.param tsave=1m tstop=2m dtmax={T/200}","!.param kT=1.5 Tamb=30 SR=53.2e6"]+parl+[
     "!.param RsD=33 CsD=1f RsCM=33 CsCM=1f RsE=68 CsE=1f",sup],["!.save "+allsave],
     "---- DRV8873S, Z AXIS, NO OUTPUT FILTER: steady 3.12 A, driver loss and ripple for both schemes at 10 kHz and 100 kHz (coil snubbers not fitted) ----")
