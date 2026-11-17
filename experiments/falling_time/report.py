#!/usr/bin/env python3
"""Summarize every completed recovery experiment and export comparison figures."""
import csv
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from experiments.falling_time.run import definitions, fit_tail
from snspdtool.analysis import decay

HERE = Path(__file__).resolve().parent
RUNS = ROOT/'runs/falling_time'


def main():
    rows = []
    missing = []
    for c in definitions():
        p = RUNS/c['id']/'metrics.json'
        if not p.exists():
            missing.append(c['id'])
            continue
        rows.append(json.loads(p.read_text()))
    by_id = {r['id']: r for r in rows}
    experiment_path = ROOT/'data/response/experiment.csv'
    exp = np.genfromtxt(experiment_path, delimiter=',', names=True)
    exp_metrics = {'fall_90_10_ns': decay(exp['time_from_peak_ns']*1e-9,
                      exp['output_mV'], exp['time_from_peak_ns'] >= 0),
                   'peak_mV': float(max(exp['output_mV'])),
                   'fit_85_15': fit_tail(exp['time_from_peak_ns'], exp['output_mV'], uniform=False),
                   'sha256': hashlib.sha256(experiment_path.read_bytes()).hexdigest(),
                   'scope': 'Packaged Geiger average; no calorimetric bias-sweep traces supplied.'}
    inputs = json.loads((HERE/'inputs.json').read_text())
    result = {'source_commit': inputs['baseline_commit'],
              'missing_cases': missing, 'experimental_geiger': exp_metrics, 'results': rows}
    (HERE/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    fields = ['id', 'variant', 'bias', 'N', 'probe_L_nH', 'depairing_ratio',
              'peak_mV', 'output_fall_90_10_ns', 'R_decay_90_10_ns',
              'R_at_output_peak_ohm', 'recovered', 'event_count',
              'accepted_numerics', 'flux_kvl_residual_fraction']
    with (HERE/'results.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)

    def wave(case_id):
        return np.genfromtxt(RUNS/case_id/'waveform.csv', names=True, delimiter=',')

    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'savefig.dpi': 180})
    fig, ax = plt.subplots(2, 2, figsize=(11.2, 8), layout='constrained')
    colors = {'baseline':'#303b46', 'gl_ratio12':'#c95b36', 'gl_ratio15':'#1c7a88'}
    labels = {'baseline':'Fixed L = 38 nH', 'gl_ratio12':'GL: Id / Isw = 1.2', 'gl_ratio15':'GL: Id / Isw = 1.5'}
    for variant in colors:
        rs = sorted([r for r in rows if r['variant']==variant and r['stage']=='screen'], key=lambda r:r['bias'])
        ax[0,0].plot([r['bias'] for r in rs], [r['output_fall_90_10_ns'] for r in rs],
                     'o-', color=colors[variant], label=labels[variant])
    ax[0,0].set(xlabel='Bias / switching current', ylabel='Output fall, 90–10% (ns)',
                title='A  Current-dependent inductance changes the bias trend')
    ax[0,0].legend(frameon=False, fontsize=9)
    for name, style, color in [('baseline_b60_n10','--','#303b46'), ('baseline_b96_n10',':','#303b46'),
                               ('gl_ratio12_b60_n10','-','#1c7a88'), ('gl_ratio12_b96_n10','-','#c95b36')]:
        if name not in by_id:
            continue
        w = wave(name); y=w['output_V']; t=w['time_ns']
        t=t-t[np.argmax(y)]
        ax[0,1].plot(t,y/y.max(),style,color=color,
                     label=('Fixed L' if 'baseline' in name else 'GL')+f', bias {by_id[name]["bias"]:.2f}')
    ax[0,1].set(xlim=(-.5,5), ylim=(-.15,1.08), xlabel='Time from output peak (ns)',
                ylabel='Output / peak', title='B  Normalized near-transition waveforms')
    ax[0,1].legend(frameon=False, fontsize=9)

    controls = [('baseline','Baseline'), ('cap_zero','C = 0'), ('linear_L76','L = 76 nH'),
                ('no_size_penalty','No size penalty'), ('domain_energy','Energy closure')]
    for j,bias in enumerate([.6,.96]):
        heights=[]
        for variant,_ in controls:
            r=by_id.get(f'{variant}_b{round(100*bias)}_n10')
            heights.append(r['output_fall_90_10_ns'] if r and r['output_fall_90_10_ns'] else np.nan)
        bars = ax[1,0].bar(np.arange(len(controls))+(j-.5)*.34,heights,.34,
                           color=['#1c7a88','#c95b36'][j],label=f'Bias {bias:.2f}')
        for bar,(variant,_) in zip(bars,controls):
            r=by_id.get(f'{variant}_b{round(100*bias)}_n10')
            if r and not r['recovered']:
                bar.set_hatch('///')
                bar.set_edgecolor('#303b46')
    ax[1,0].set(xticks=np.arange(len(controls)),xticklabels=[s for _,s in controls],
                ylabel='Output fall, 90–10% (ns)',title='C  Controlled circuit and domain changes')
    ax[1,0].tick_params(axis='x',labelrotation=18)
    ax[1,0].legend(frameon=False, fontsize=9)
    ax[1,0].text(.02,.95,'Hatched: incomplete reset',transform=ax[1,0].transAxes,
                 va='top',fontsize=8)

    ax[1,1].plot(exp['time_from_peak_ns'], exp['output_mV'],'o',ms=3.2,color='#171717',label='Measured Geiger average')
    for lk,color in [(38,'#303b46'),(60,'#1c7a88'),(76,'#c95b36')]:
        name=f'geiger_L{lk}'
        if name in by_id:
            w=wave(name); t=w['time_ns']; y=w['output_V']*1e3
            ax[1,1].plot(t-t[np.argmax(y)],y,color=color,label=f'Simulation, L = {lk} nH')
    ax[1,1].set(xlim=(-2,9),xlabel='Time from output peak (ns)',ylabel='Output (mV)',
                title='D  Geiger comparison: amplitude is not rescaled')
    ax[1,1].legend(frameon=False,fontsize=9)
    for a in ax.flat:
        a.grid(alpha=.16)
    fig.savefig(HERE/'recovery_experiments.png')
    fig.savefig(HERE/'recovery_experiments.pdf')
    plt.close(fig)

    fig,axs=plt.subplots(1,3,figsize=(12,3.7),layout='constrained')
    for variant in colors:
        rs=sorted([r for r in rows if r['variant']==variant and r['stage']=='screen'],key=lambda r:r['bias'])
        for axis,key in [(axs[0],'tau_ns'),(axs[1],'tau_fixed_baseline_ns'),(axs[2],'offset_fraction')]:
            axis.plot([r['bias'] for r in rs],[r['output_fit_85_15'].get(key,np.nan) for r in rs],
                      'o-',color=colors[variant],label=labels[variant])
    axs[0].set(ylabel='Fitted tau (ns)',title='Free fitted offset')
    axs[1].set(ylabel='Fitted tau (ns)',title='Offset fixed at pre-pulse baseline')
    axs[2].set(ylabel='Fitted offset / peak',title='Free offset is not the measured baseline')
    axs[0].legend(frameon=False,fontsize=8)
    for a in axs:
        a.set_xlabel('Bias / switching current'); a.grid(alpha=.16)
    fig.savefig(HERE/'fit_definition.png')
    plt.close(fig)
    print(json.dumps({'completed':len(rows),'missing':missing,'experimental_geiger':exp_metrics},indent=2))


if __name__=='__main__':
    main()
