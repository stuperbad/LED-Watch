"""build.py out.kicad_pcb : first-pass mock-up of USB-C power+UPDI on the back at 3 o'clock (copy of the board)"""
import pcbnew, sys, json, math
mm=pcbnew.FromMM; V=pcbnew.VECTOR2I; tomm=pcbnew.ToMM
out=sys.argv[1]
b=pcbnew.LoadBoard("usbc/base_v.kicad_pcb")
LIB="C:/Program Files/KiCad/10.0/share/kicad/footprints/"
def load(lib,name): return pcbnew.FootprintLoad(LIB+lib+".pretty",name)
def net(name):
    n=b.FindNet(name)
    if n is None:
        n=pcbnew.NETINFO_ITEM(b,name); b.Add(n)
    return n
for nm in ("VBUS","CC1","CC2","SBU","ISET","TS"): net(nm)
# remove the pogo row
j2=b.FindFootprintByReference("J2"); b.Remove(j2)
# ---------------- USB-C receptacle on the back, mouth toward the +x edge
usb=load("Connector_USB","USB_C_Receptacle_GCT_USB4110"); usb.SetReference("J2"); usb.SetValue("USB-C power + UPDI (GCT USB4110)")
b.Add(usb); usb.Flip(usb.GetPosition(),True); usb.SetPosition(V(mm(116.35),mm(100.0))); usb.SetOrientationDegrees(270)
m={"A1":"GND","B12":"GND","A12":"GND","B1":"GND","SH":"GND","A4":"VBUS","B9":"VBUS","A9":"VBUS","B4":"VBUS","A5":"CC1","B5":"CC2","A8":"SBU","B8":"SBU"}
for p in usb.Pads():
    nm=m.get(p.GetNumber())
    if nm: p.SetNet(b.FindNet(nm))
# the four shell tabs get round notches around the ring vias that sit under them (notch.py)
N=json.load(open("usbc/notch.json"))
for p in usb.Pads():
    if p.GetNumber()!="SH": continue
    pos=p.GetPosition(); c=(tomm(pos.x),tomm(pos.y))
    n=min(N,key=lambda r:(r["c"][0]-c[0])**2+(r["c"][1]-c[1])**2)
    p.SetShape(pcbnew.PAD_SHAPE_CUSTOM); p.SetAnchorPadShape(pcbnew.F_Cu,pcbnew.PAD_SHAPE_CIRCLE)
    p.SetSize(V(mm(0.2),mm(0.2))); p.SetOrientationDegrees(0)
    p.AddPrimitivePoly(pcbnew.B_Cu,[V(mm(x-c[0]),mm(y-c[1])) for x,y in n["pts"]],0,True)
parts=[ # ref, lib, fp, value, nets by pad number, w, h
 ("U5","Package_TO_SOT_SMD","SOT-23-6","BQ21040DBV",{"1":"TS","2":"/BATT","4":"ISET","5":"GND","6":"VBUS"},3.0,1.9),
 ("C55","Capacitor_SMD","C_0402_1005Metric","1uF",{"1":"VBUS","2":"GND"},1.7,1.0),
 ("C56","Capacitor_SMD","C_0402_1005Metric","1uF",{"1":"/BATT","2":"GND"},1.7,1.0),
 ("R68","Resistor_SMD","R_0402_1005Metric","5.1k",{"1":"CC1","2":"GND"},1.7,1.0),
 ("R69","Resistor_SMD","R_0402_1005Metric","5.1k",{"1":"CC2","2":"GND"},1.7,1.0),
 ("R70","Resistor_SMD","R_0402_1005Metric","8.2k",{"1":"ISET","2":"GND"},1.7,1.0),
 ("R71","Resistor_SMD","R_0402_1005Metric","10k",{"1":"TS","2":"GND"},1.7,1.0),
 ("R72","Resistor_SMD","R_0402_1005Metric","1k",{"1":"SBU","2":"/UPDI"},1.7,1.0),
 ("D50","Diode_SMD","D_SOD-323","BAT54 (UPDI clamp)",{"1":"+3V3","2":"/UPDI"},2.7,1.2),
]
placement=json.load(open("usbc/place.json"))
for ref,lib,fpn,val,nets,w,h in parts:
    if ref not in placement: print("no spot",ref); continue
    x,y,ang=placement[ref]
    fp=load(lib,fpn); fp.SetReference(ref); fp.SetValue(val); b.Add(fp)
    fp.Flip(fp.GetPosition(),True); fp.SetPosition(V(mm(x),mm(y))); fp.SetOrientationDegrees(ang)
    for p in fp.Pads():
        nm=nets.get(p.GetNumber())
        if nm: p.SetNet(net(nm))
pcbnew.SaveBoard(out,b); print("saved",out)
