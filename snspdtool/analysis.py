"""Waveform measurements; definitions match the November 2026 audit."""
from pathlib import Path
import re
import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.signal import find_peaks
from PyLTSpice import RawRead

def read(path):
    p=Path(path)
    r=RawRead(str(p),[],dialect='ltspice')
    w={n.lower():np.asarray(r.get_wave(n),dtype=float) for n in r.get_trace_names()}
    h=p.open('rb').read(4096).decode('utf-16-le',errors='ignore')
    m=re.search(r'^Offset:\s*(\S+)',h,re.M)
    if m:w['time']+=float(m.group(1))
    return w

def crossing(t,y,level,start,direction):
    j=np.arange(start+1,len(y))
    yes=(y[j]<=level)&(y[j-1]>level) if direction=='down' else (y[j]>=level)&(y[j-1]<level)
    hits=j[yes]
    if not len(hits):return None
    j=hits[0]
    return float(t[j-1]+(level-y[j-1])*(t[j]-t[j-1])/(y[j]-y[j-1]))

def decay(t,y,post):
    peak=np.flatnonzero(post)[np.argmax(y[post])]
    if y[peak]<=1e-12:return None
    a=crossing(t,y,.9*y[peak],peak,'down');b=crossing(t,y,.1*y[peak],peak,'down')
    return float((b-a)*1e9) if a is not None and b is not None else None

def analyze(c, run_directory):
    root=Path(run_directory)
    name='case';log=(root/(name+'.log')).read_bytes().decode('utf-16-le',errors='replace')
    if 'Total elapsed time:' not in log:raise RuntimeError(name+' incomplete')
    w=read(root/'case.raw');g=lambda n:w[n.lower()]
    row=dict(c,finite=all(np.isfinite(x).all() for x in w.values()))
    if not row['finite']:return row
    t=g('time');tp=c['photon_ns']*1e-9
    pre=(t>tp-2e-9)&(t<tp-1e-9);post=t>=tp;tail=t>tp+30e-9;prepared=t>=tp-3e-9
    avg=lambda y,m:float(np.trapezoid(y[m],t[m])/(t[m][-1]-t[m][0]))
    I=g('I(wire:L_NBN4)');R=g('V(wire:NRwire4)');Rd=g('V(wire:NRdom4)')
    Te=g('V(wire:NTeUse4)');Tph=g('V(wire:NTphUse4)')
    out=g('V(N011)')-avg(g('V(N011)'),pre)
    rf=g('V(N013)')-avg(g('V(N013)'),pre)
    idx=np.flatnonzero(post)[np.argmax(out[post])]
    peak=float(out[idx]);ir=np.flatnonzero(post)[np.argmax(R[post])]
    suffix=np.maximum.accumulate(R[::-1])[::-1]
    resets=np.flatnonzero((np.arange(len(t))>=ir)&(suffix<1))
    ib=avg(I,pre);expected=c['bias']*c['Isw']
    eps=1.602176634e-19
    deposited=float(np.trapezoid(g('V(wire:NPph4)'),t)/eps)
    intended=.1*c['N']*1.9878e-25/532e-9/eps
    z=crossing(t,out,0,idx,'down') if c['N'] else None
    pm=post&(t<=z) if z is not None else post
    peaks,_=find_peaks(R,height=max(1,.2*float(max(R[post]))),prominence=max(.5,.1*float(max(R[post]))))
    peaks=peaks[t[peaks]>=tp]
    event_times=[]
    for j in peaks:
        if not event_times or t[j]-event_times[-1]>.5e-9:event_times.append(float(t[j]))
    ti=t[prepared]
    drive=g('V(N012)')-g('V(N024)')-(R+1e-5)*I
    kvl=38e-9*(I[prepared]-I[prepared][0])-cumulative_trapezoid(drive[prepared],ti,initial=0)
    vwire=g('V(wire:NET4)')-g('V(N024)')
    valid_pulse=bool(c['N'] and peak>1e-6 and max(R[post])>.01)
    row.update(Ipre_uA=ib*1e6,Itail_uA=avg(I,tail)*1e6,Imin_uA=float(min(I[post])*1e6),
        peak_mV=peak*1e3,rf_peak_uV=float(max(rf[post])*1e6),peak_time_ns=float((t[idx]-tp)*1e9),
        fall_90_10_ns=decay(t,out,post) if valid_pulse else None,
        positive_lobe_area_mV_ns=float(np.trapezoid(np.maximum(out[pm],0),t[pm])*1e12) if valid_pulse else None,
        Rpeak_ohm=float(max(R[post])),Rdomain_peak_ohm=float(max(Rd[post])),Rpre_max_ohm=float(max(R[pre])),
        Rtail_max_ohm=float(max(R[tail])),R_decay_90_10_ns=decay(t,R,post) if valid_pulse else None,
        reset_below_1ohm_ns=float((t[resets[0]]-tp)*1e9) if valid_pulse and len(resets) else None,
        Te_peak_K=float(max(Te[post])),Tph_peak_K=float(max(Tph[post])),Te_tail_K=avg(Te,tail),
        Te_decay_90_10_ns=decay(t,Te-c['Tb'],post) if valid_pulse else None,
        deposited_eV=deposited,deposited_relative_error=(deposited/intended-1) if intended else None,
        recovered=bool(max(R[tail])<1 and abs(avg(I,tail)/expected-1)<.01 and abs(avg(Te,tail)-c['Tb'])<.01),
        valid_pulse=valid_pulse,event_count=len(event_times),event_peak_times_ns=[(x-tp)*1e9 for x in event_times],
        kvl_integral_residual_fraction=float(max(abs(kvl))/(38e-9*expected)),
        resistor_voltage_error_V=float(max(abs(vwire-R*I)[prepared])),
        thermal_cap_hit=bool(max(Te[prepared])>=49.99 or max(Tph[prepared])>=49.99),
        domain_joule_eV=float(np.trapezoid(g('V(wire:NPjDomain4)'),t)/eps),
        wire_resistive_peak_uV=float(max((R*I)[post])*1e6))
    Ce=g('V(wire:NCe4)');Cp=g('V(wire:NCp4)')
    Pin=g('V(wire:NPph4)')+g('V(wire:NPjSeed4)');Pe=g('V(wire:NPeph4)');Pc=g('V(wire:NPcool4)');Pd=g('V(wire:NPdiff4)')
    norm=max(cumulative_trapezoid(Pin[prepared],ti,initial=0))
    for label,heat,temp,flux in [('electron',Ce,Te,Pin-Pe-Pd-Ce*(Te-c['Tb'])*1e-9),('phonon',Cp,Tph,Pe-Pc-Cp*(Tph-c['Tb'])*1e-9)]:
        u=cumulative_trapezoid(heat[prepared],temp[prepared],initial=0)
        f=cumulative_trapezoid(flux[prepared],ti,initial=0)
        row[label+'_seed_balance_residual_fraction']=float(max(abs(u-f))/norm) if norm>1e-30 else None
    return row
