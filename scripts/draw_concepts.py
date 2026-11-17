"""Audience-facing circuit and model figures, without simulation identifiers."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, Polygon, Rectangle

from draw_circuit import ROOT, INK, BLUE, MUTED, LIGHT, axes, wire, label, ground, element, NET
from snspdtool.core import selected


def node(ax, x, y):
    ax.plot(x, y, "o", color=INK, ms=3.5)


def amplifier_block(ax, x, y, w=2.2, h=1.5):
    ax.add_patch(Polygon([(x,y-h/2),(x,y+h/2),(x+w,y)],closed=True,
                         facecolor=LIGHT,edgecolor=INK,lw=1.5))
    label(ax,x+w*.36,y,"$A(\\omega)$",12)


def concept_overview():
    fig=plt.figure(figsize=(16,9),facecolor="white")
    fig.text(.04,.95,"External circuit and signal readout",fontsize=23,weight="bold",color=INK)
    fig.text(.04,.90,"The bias supplies current; a photon-induced resistance diverts current into the RF readout.",fontsize=12,color=MUTED)
    ax=axes(fig,[.035,.19,.93,.64],(0,18),(0,7.8))
    ax.add_patch(Circle((1.1,4.6),.38,fill=False,edgecolor=INK,lw=1.5))
    label(ax,1.1,4.77,"+",12);label(ax,1.1,4.44,"−",12)
    label(ax,.55,4.6,"$V_{bias}$",13,ha="right")
    wire(ax,[(1.1,4.98),(1.1,6.3),(1.8,6.3)])
    wire(ax,[(1.1,4.22),(1.1,3.2)]);ground(ax,1.1,3.2)
    element(ax,(1.8,6.3),(4.2,6.3),"R","Bias resistor\n10 kΩ",(3,6.95),size=10)
    element(ax,(4.2,6.3),(7.0,6.3),"L","Bias choke\n19.894 µH",(5.6,5.6),size=10)
    wire(ax,[(4.2,6.3),(4.2,7.25),(4.7,7.25)])
    element(ax,(4.7,7.25),(6.5,7.25),"C","1 pF",(5.6,7.68))
    wire(ax,[(6.5,7.25),(7,7.25),(7,6.3)])
    for x in [4.2,7]:node(ax,x,6.3)
    element(ax,(7,6.3),(9.1,6.3),"C","RF coupling\n7.957 nF",(8.05,6.95),size=10)
    element(ax,(9.1,6.3),(10.7,6.3),"R","1 Ω",(9.9,6.85),size=10)
    wire(ax,[(10.7,6.3),(15.0,6.3)])
    amplifier_block(ax,15,6.3,1.8,1.5)
    wire(ax,[(16.8,6.3),(17.65,6.3)])
    label(ax,17.15,6.88,"$V_{out}$",13)
    label(ax,15.9,5.1,"Amplifier chain",10,MUTED)
    for x,kind,text in [(11,"R","50 Ω"),(12.6,"R","50 Ω"),(14.2,"C","30 pF")]:
        node(ax,x,6.3)
        wire(ax,[(x,6.3),(x,4.95)])
        element(ax,(x,4.95),(x,3.05),kind,text,(x+.55,4),size=10)
        ground(ax,x,3.05)
    label(ax,12.6,2.25,"$50\\,\\Omega\\parallel50\\,\\Omega=25\\,\\Omega$\nResistive RF load",12,MUTED)
    # Reuse meander and photon-arrow strokes; omit the numerical gate branch.
    asset=json.loads((ROOT/'symbols/snspd_geometry.json').read_text())
    x0,y0,s=7,3.95,.026
    for x1,y1,x2,y2 in asset['lines']:
        if x1==x2==-64:continue
        wire(ax,[(x0+s*x1,y0-s*y1),(x0+s*x2,y0-s*y2)])
    wire(ax,[(7,6.3),(7,y0+48*s)])
    wire(ax,[(7,y0-48*s),(7,2.45)])
    label(ax,7.8,4.05,"SNSPD",13,ha="left",weight="bold")
    label(ax,5.45,4.7,"Photon energy\n$E_{dep}$",10,BLUE)
    ax.annotate("",(7,5.18),(7,5.65),arrowprops={"arrowstyle":"->","color":BLUE,"lw":1.3})
    label(ax,7.34,5.45,"$I(t)$",11,BLUE,ha="left")
    element(ax,(7,2.45),(7,.7),"R","Series return\n20 Ω",(8.1,1.7),size=10)
    ground(ax,7,.7)
    fig.text(.04,.108,"Bias tee",fontsize=12,weight="bold",color=INK)
    fig.text(.04,.067,"The choke supplies DC bias; the coupling capacitor passes the pulse to the readout.",fontsize=11,color=MUTED)
    fig.text(.54,.108,"Detector load",fontsize=12,weight="bold",color=INK)
    fig.text(.54,.067,"The full load depends on frequency and includes the 20 Ω return path.",fontsize=11,color=MUTED)
    fig.text(.04,.022,"Values shown: nominal 30 pF model configuration. The meander is a detector symbol, not a scale drawing.",fontsize=9.5,color=MUTED)
    return fig


def filter_panel(ax, title, highpass, rfeedback, gain=False):
    label(ax,.25,7.5,title,14,ha="left",weight="bold")
    series_kind,series_value=("C","52.88 pF") if highpass else ("R","10 Ω")
    feedback_kind,feedback_value=("R","1 kΩ") if highpass else ("C","1.59 pF")
    shunt_kind,shunt_value=feedback_kind,feedback_value
    element(ax,(.5,5.2),(3,5.2),series_kind,series_value,(1.75,5.8),size=10)
    element(ax,(3,5.2),(5.3,5.2),series_kind,series_value,(4.15,5.8),size=10)
    wire(ax,[(5.3,5.2),(6.35,5.2)])
    for x in [3,5.3]:node(ax,x,5.2)
    element(ax,(5.3,5.2),(5.3,2.65),shunt_kind,shunt_value,(4.4,3.8),size=10)
    ground(ax,5.3,2.65)
    ax.add_patch(Polygon([(6.35,5.85),(6.35,3.2),(8.45,4.5)],closed=True,
                         facecolor=LIGHT,edgecolor=INK,lw=1.45))
    label(ax,6.58,5.2,"+",13);label(ax,6.58,3.8,"−",13)
    wire(ax,[(8.45,4.5),(9.2,4.5)])
    node(ax,9.2,4.5)
    wire(ax,[(3,5.2),(3,6.4),(4,6.4)])
    element(ax,(4,6.4),(8.2,6.4),feedback_kind,feedback_value,(6.1,7),size=10)
    wire(ax,[(8.2,6.4),(9.2,6.4),(9.2,2)])
    element(ax,(9.2,2),(7,2),"R",rfeedback,(8.1,2.65),size=10)
    node(ax,7,2)
    wire(ax,[(7,2),(6,2),(6,3.8),(6.35,3.8)])
    element(ax,(7,2),(7,.55),"R","100 kΩ",(8,.95),size=10)
    ground(ax,7,.55)
    if gain:
        wire(ax,[(9.2,4.5),(10,4.5)])
        ax.add_patch(Rectangle((10,3.8),2.1,1.4,facecolor=LIGHT,edgecolor=INK,lw=1.4))
        label(ax,11.05,4.5,"Gain\n12.281",10)
        wire(ax,[(12.1,4.5),(12.5,4.5)])
    else:wire(ax,[(9.2,4.5),(12.5,4.5)])


def concept_amplifier():
    fig=plt.figure(figsize=(16,10.8),facecolor="white")
    fig.text(.035,.953,"Amplifier chain: filtering and gain",fontsize=23,weight="bold",color=INK)
    fig.text(.035,.909,"Signal order: two high-pass sections → gain → two low-pass sections → gain → output",fontsize=12,color=MUTED)
    for i,(title,hp,rf,gain) in enumerate([
        ("High-pass section 1",True,"15.2 kΩ",False),
        ("High-pass section 2 + gain",True,"123.5 kΩ",True),
        ("Low-pass section 1",False,"15.2 kΩ",False),
        ("Low-pass section 2 + gain",False,"123.5 kΩ",True)]):
        ax=axes(fig,[.025+(i%2)*.49,.5 if i<2 else .095,.47,.38],(0,13),(0,8))
        filter_panel(ax,title,hp,rf,gain)
    fig.text(.04,.055,"For each active section, the non-inverting gain is K = 1 + Rfeedback / Rground. The input and feedback networks set its frequency response.",fontsize=10,color=MUTED)
    fig.text(.04,.022,"The RF resistors terminate the detector readout. Gain blocks represent the nominal linear transfer model; final scalar calibration is case-dependent.",fontsize=9.5,color=MUTED)
    return fig


def box(ax,x,y,w,h,title,body):
    ax.add_patch(Rectangle((x,y),w,h,facecolor=LIGHT,edgecolor=MUTED,lw=1.3))
    label(ax,x+w/2,y+h-.3,title,12,weight="bold")
    label(ax,x+w/2,y+h/2-.16,body,11,linespacing=1.6)


def arrow(ax,points,text=None,xy=None):
    if len(points)>2:
        ax.plot([p[0] for p in points[:-1]],[p[1] for p in points[:-1]],color=BLUE,lw=1.4)
    ax.annotate("",points[-1],points[-2],arrowprops={"arrowstyle":"->","color":BLUE,"lw":1.4})
    if text:label(ax,*xy,text,10,BLUE,bbox={"facecolor":"white","edgecolor":"none","pad":2})


def concept_snspd():
    fig=plt.figure(figsize=(16,11.1),facecolor="white")
    fig.text(.04,.953,"SNSPD: electrical and thermal feedback",fontsize=23,weight="bold",color=INK)
    fig.text(.04,.909,"The same coupled equations describe both operating regimes; temperature, bias, and deposited energy set the response.",fontsize=12,color=MUTED)
    ax=axes(fig,[.03,.16,.94,.70],(0,16),(0,9.2))
    # Compact physical electrical equivalent, without numerical sensors or state capacitors.
    label(ax,.35,8.8,"Electrical response",13,ha="left",weight="bold")
    element(ax,(.6,7.55),(3,7.55),"L","$L_k=38$ nH",(1.8,8.2),size=11)
    element(ax,(3,7.55),(5.4,7.55),"R","$R_{wire}(t)$",(4.2,8.2),size=11)
    ax.annotate("",(4.55,7.9),(3.85,7.2),arrowprops={"arrowstyle":"->","color":INK,"lw":1.3})
    label(ax,.6,7.05,"$V_d$",11);label(ax,5.4,7.05,"$V_s$",11)
    ax.annotate("",(2.6,8.68),(1.1,8.68),arrowprops={"arrowstyle":"->","color":BLUE,"lw":1.3})
    label(ax,2.9,8.68,"$I(t)$",11,BLUE,ha="left")
    label(ax,10.8,8.2,"$L_k\\,dI/dt=V_d-V_s-I R_{wire}$",16)
    label(ax,10.8,7.34,"$R_{wire}=\\min[R_n,\\max(R_{seed}+R_d,0)]$",13)
    wire(ax,[(.35,6.55),(15.65,6.55)])
    # Two-temperature seed and resistance closure.
    box(ax,.35,3.65,6.0,2.1,"Seed electrons: $T_e$", "$C_e\\,\\dot T_e=P_{opt}+I^2R_{seed}$\n$-P_{e-ph}-P_{diff}$")
    box(ax,8.0,3.65,4.2,2.1,"Seed phonons: $T_{ph}$", "$C_{ph}\\,\\dot T_{ph}$\n$=P_{e-ph}-P_{sub}$")
    arrow(ax,[(6.35,4.7),(8,4.7)],"$P_{e-ph}$",(7.18,5.02))
    arrow(ax,[(12.2,4.7),(14,4.7)],"$P_{sub}$",(13.08,5.02))
    label(ax,14.8,4.7,"Bath\n$T_b$",12,MUTED)
    arrow(ax,[(1.4,6.45),(1.4,5.75)],"$P_{opt}$",(2,6.14))
    arrow(ax,[(5.5,5.75),(5.5,6.12),(14.8,6.12),(14.8,5.3)],"$P_{diff}$",(10.7,6.12))
    box(ax,.35,.5,6.0,1.95,"Resistance formation", "$R_{seed}=R_{seed,full} f_n(T_e,I)$\n$R_d$: formation, growth, and retraction")
    arrow(ax,[(3.35,3.65),(3.35,2.45)],"$T_e$",(3.75,3.05))
    arrow(ax,[(.8,2.45),(.8,3.65)],"$I^2R_{seed}$",(1.65,3.05))
    box(ax,8.0,.5,7.6,1.95,"Electrical feedback", "Higher resistance diverts detector current.\nLower current reduces Joule heating.\nCooling and domain retraction permit recovery.")
    arrow(ax,[(6.35,1.48),(8,1.48)],"$R_{wire}$",(7.17,1.85))
    arrow(ax,[(10.5,2.45),(10.5,3.1),(6,3.1),(6,3.65)],"$I$ changes heating",(8.7,3.1))
    # Heat-transfer laws are physical quantities, not SPICE element identifiers.
    fig.text(.04,.117,"Heat-transfer laws",fontsize=12,weight="bold",color=INK)
    fig.text(.04,.078,"$P_{e-ph}=\\Sigma V_{seed}(T_e^5-T_{ph}^5)$",fontsize=14,color=INK)
    fig.text(.53,.078,"$P_{sub}=\\beta A_{seed}(T_{ph}^4-T_b^4)$",fontsize=14,color=INK)
    fig.text(.04,.033,"Compact model: the seed has two temperatures; the propagated domain has a resistance state but no independent temperature or energy state.",fontsize=9.5,color=MUTED)
    fig.text(.04,.010,"Ce and Cph are seed heat capacities. The tiny numerical series resistance is omitted from the conceptual electrical equation.",fontsize=9,color=MUTED)
    return fig


def main():
    # Values must agree with the source netlists behind the technical figures.
    expected={'R1':'10k','L1':'19894n Cpar=1p','C1':'7.957n Rser=1','R3':'20','R2':'50',
              'C3':'52.88p','C4':'52.88p','C5':'52.88p','C6':'52.88p',
              'R4':'1k','R5':'1k','R8':'1k','R9':'1k','R6':'15.2k','R10':'123.5k',
              'R12':'10','R13':'10','R16':'10','R17':'10','R14':'15.2k','R18':'123.5k',
              'R7':'100k','R11':'100k','R15':'100k','R19':'100k',
              'C7':'1.59p','C8':'1.59p','C9':'1.59p','C10':'1.59p','E1':'12.281','E2':'{12.281*AmpGainCal}'}
    for name,value in expected.items():assert NET[name]['value']==value,(name,value)
    case=selected(['geiger_c30_high_dt005'])[0]
    assert (case['C_pF'],case['R20_ohm'])==(30,50)
    out=ROOT/'docs/figures'
    figures=[('concept_external_circuit',concept_overview()),('concept_amplifier',concept_amplifier()),('concept_snspd',concept_snspd())]
    with PdfPages(out/'model_concepts.pdf') as pdf:
        for name,fig in figures:
            svg=out/(name+'.svg')
            fig.savefig(svg,metadata={'Date':None})
            svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
            fig.savefig(out/(name+'.png'),dpi=180)
            pdf.savefig(fig)
            plt.close(fig)
    print('Rendered three conceptual figures without simulation node or element identifiers.')


if __name__=='__main__':main()
