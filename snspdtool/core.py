"""Case definitions, portable LTspice deck generation, and reference checks."""
from pathlib import Path
import hashlib,json,os,shutil

ROOT=Path(__file__).resolve().parents[1]
SMOKE_IDS=[
    'geiger_c30_high_dt005',
    'calorimetric_c30_b90_n1',
    'calorimetric_c30_b90_n4',
    'calorimetric_c30_b60_n10',
    'calorimetric_c30_b90_n10',
    'calorimetric_c30_b96_n10',
    'calorimetric_asc120_b90_n10',
]

def cases():
    return [c for p in sorted((ROOT/'cases').glob('*.json')) for c in json.loads(p.read_text())]

def selected(ids=None,group=None,smoke=False):
    all_cases=cases();wanted=set(SMOKE_IDS if smoke else ids or [])
    unknown=wanted-{c['id'] for c in all_cases}
    if unknown:raise ValueError('Unknown case IDs: '+', '.join(sorted(unknown)))
    return [c for c in all_cases if (not wanted or c['id'] in wanted) and (not group or c['group']==group)]

def references():
    out={}
    for group in ['geiger','calorimetric']:
        for r in json.loads((ROOT/f'results/reference/{group}_metrics.json').read_text()):
            out[group+'_'+r['name']]=r
    return out

def locate_ltspice(explicit=None):
    candidates=[explicit,os.environ.get('LTSPICE_EXECUTABLE'),'/Applications/LTspice.app/Contents/MacOS/LTspice',shutil.which('LTspice'),shutil.which('LTspice.exe')]
    for env in ['LOCALAPPDATA','ProgramFiles']:
        if os.environ.get(env):
            candidates.extend(str(Path(os.environ[env])/p) for p in ['Programs/ADI/LTspice/LTspice.exe','ADI/LTspice/LTspice.exe','LTC/LTspiceXVII/XVIIx64.exe'])
    for p in candidates:
        if p and Path(p).is_file():return Path(p).resolve()
    raise FileNotFoundError('LTspice executable not found. Use --ltspice PATH or LTSPICE_EXECUTABLE.')

def locate_opamp(explicit=None):
    h=Path.home()
    candidates=[explicit,os.environ.get('LTSPICE_OPAMP_SUB'),h/'Library/Application Support/LTspice/lib/sub/opamp.sub',h/'Documents/LTspice/lib/sub/opamp.sub',h/'Documents/LTspiceXVII/lib/sub/opamp.sub']
    if os.environ.get('LOCALAPPDATA'):candidates.append(Path(os.environ['LOCALAPPDATA'])/'LTspice/lib/sub/opamp.sub')
    for p in candidates:
        if p and Path(p).is_file():return Path(p).resolve()
    raise FileNotFoundError('Installed LTspice opamp.sub not found. Use --opamp PATH or LTSPICE_OPAMP_SUB.')

def deck(c,opamp):
    def inc(p):return '.include "'+Path(p).resolve().as_posix()+'"'
    bias='1' if c['bias_voltage_V'] is not None else '{I_bias*(10000+20)}'
    if c['bias_voltage_V'] is not None:bias=format(c['bias_voltage_V'],'.15g')
    return f'''* SNSPD_simulation 0.1.0: {c['id']}
{inc(ROOT/'models/snspd_nbn_v5c.lib')}
{inc(opamp)}
.param TsubCase={c['Tb']:.15g} TcCase={c['Tc']:.15g} IswCase={c['Isw']:.15g}
.param biasFrac={c['bias']:.15g} photonCount={c['N']} AmpGainCal={c['gain_calibration']:.15g}
.param I_bias={{biasFrac*IswCase}} Cshunt={c['C_pF']}p Rextra={c['R20_ohm']}
Xwire N020 0 N012 N024 nanowireElectrothermal_NbN_v5c
+ Tsub={{TsubCase}} Tc={{TcCase}} IswBath={{IswCase}}
+ Nphoton={{photonCount}} etaAbs=0.1 tPhotonNorm=5p Iinit4={{I_bias}}
+ criticalBiasFraction={{biasFrac}} criticalCoreFactor=2
+ finiteSizePenalty0=10 penaltyExponent=1
I1 0 N020 PULSE(0 1u {c['photon_ns']}n 1p 1p 4p 4000n)
V1 N001 0 {bias}
{inc(ROOT/'circuits/amplifier_chain.inc')}
{inc(ROOT/'circuits/bias_tee_and_load.inc')}
.ic V(wire:NdTe4)=0 V(wire:NdTph4)=0 V(wire:NRdom4)=0
.tran 0 {c['stop_ns']}n 0 {c['dt']}
.options plotwinsize=0 numdgt=15 method=gear reltol=1e-5 abstol=1e-13 vntol=1e-8
.save V(N011) V(N012) V(N013) V(N024) V(wire:NET4)
+ I(wire:L_NBN4) V(wire:NRwire4) V(wire:NRseed4) V(wire:NRdom4)
+ V(wire:NTeUse4) V(wire:NTphUse4) V(wire:NPph4)
+ V(wire:NPjSeed4) V(wire:NPjDomain4) V(wire:NPeph4) V(wire:NPcool4)
+ V(wire:NPdiff4) V(wire:NCe4) V(wire:NCp4)
.end
'''

def build(c,output,opamp):
    d=Path(output)/c['id'];d.mkdir(parents=True,exist_ok=True)
    (d/'case.cir').write_text(deck(c,opamp))
    (d/'case.json').write_text(json.dumps(c,indent=2)+'\n')
    return d

def compare(result,reference):
    """Regression bounds preserve observed behavior, including no-trigger cases."""
    failures=[]
    if not result['finite']:return ['non-finite trace']
    for key in ['recovered']:
        if result[key]!=reference[key]:failures.append(key+' classification changed')
    expected_events=reference.get('event_count',reference.get('resistance_pulse_count'))
    if result['event_count']!=expected_events:failures.append('event count changed')
    if result['thermal_cap_hit']:failures.append('thermal cap reached')
    if expected_events:
        # A 0.2% amplitude bound is larger than the observed 0.0083% step effect.
        if abs(result['peak_mV']-reference['peak_mV'])>max(.002,.002*abs(reference['peak_mV'])):failures.append('peak differs by >0.2% (or 2 microvolt)')
        expected_reset=reference.get('reset_below_1ohm_ns',reference.get('reset_ns'))
        if expected_reset is not None and (result['reset_below_1ohm_ns'] is None or abs(result['reset_below_1ohm_ns']-expected_reset)>.002):failures.append('resistance reset differs by >2 ps')
        if reference.get('fall_90_10_ns') is not None and (result['fall_90_10_ns'] is None or abs(result['fall_90_10_ns']-reference['fall_90_10_ns'])>.002):failures.append('output fall time differs by >2 ps')
    elif result['valid_pulse']:failures.append('unexpected trigger')
    if result['kvl_integral_residual_fraction']>.005:failures.append('integral KVL residual exceeds 0.5%')
    if result['N'] and abs(result['deposited_relative_error'])>.001:failures.append('optical energy normalization differs by >0.1%')
    return failures

def check():
    cs=cases();refs=references()
    if len(cs)!=32 or len({c['id'] for c in cs})!=len(cs):raise ValueError('Expected 32 unique cases')
    if {c['id'] for c in cs}!=set(refs):raise ValueError('Case/reference coverage mismatch')
    manifest=json.loads((ROOT/'provenance/source_manifest.json').read_text())
    digest=hashlib.sha256((ROOT/'models/snspd_nbn_v5c.lib').read_bytes()).hexdigest()
    if digest!=manifest['model_packaged_sha256']:raise ValueError('Model differs from the audited snapshot')
    for c in cs:
        if c['Tb']<=0 or not 0<c['bias']<1 or c['N']<0 or c['stop_ns']-c['photon_ns']<30:raise ValueError('Invalid case '+c['id'])
    return {'version':'0.1.0','cases':len(cs),'reference_coverage':'complete','model_sha256':digest}
