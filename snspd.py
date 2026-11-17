#!/usr/bin/env python3
"""Command-line entry point for case preparation, simulation, and regression checks."""

import argparse
import concurrent.futures
import json
import sys
from pathlib import Path
from snspdtool.simulation import run_deck
from snspdtool.core import ROOT, build, check, check_behavior, compare, locate_ltspice, locate_opamp, references, selected
from snspdtool.inductance import configure


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['list', 'check', 'build', 'run', 'analyze', 'plot'])
    p.add_argument('--case', action='append', dest='ids', help='Case ID; repeat to select multiple cases')
    p.add_argument('--group', choices=['geiger', 'calorimetric'])
    p.add_argument('--smoke', action='store_true', help='Select the seven representative packaging checks')
    p.add_argument('--output', type=Path, default=ROOT / 'runs')
    p.add_argument('--ltspice', help='Path to the installed LTspice executable')
    p.add_argument('--opamp', help='Path to the installed LTspice opamp.sub')
    p.add_argument('--jobs', type=int, default=1)
    p.add_argument('--compare', action='store_true', help='Compare analyzed results with stored reference measurements')
    p.add_argument('--check-behavior', action='store_true', help='Check triggering, reset, and numerical validity without requiring baseline amplitudes')
    p.add_argument('--inductance-model', choices=['fixed', 'gl'], default=None, help='Build/run only; default fixed, gl explicitly enables the near-Tc candidate')
    p.add_argument('--depairing-ratio', type=float, help='GL: depairing current divided by switching current')
    p.add_argument('--lk-zero-nh', type=float, help='GL: zero-current electrical inductance, independent of geometry')
    p.add_argument('--overwrite', action='store_true', help='Explicitly replace an existing simulation in the output directory')
    a = p.parse_args()
    if a.command not in ['build', 'run'] and any(v is not None for v in [a.inductance_model, a.depairing_ratio, a.lk_zero_nh]):
        raise ValueError('Inductance options apply to build/run; analysis uses the saved case.json')
    if a.command == 'check':
        print(json.dumps(check(), indent=2))
        return 0
    cs = selected(a.ids, a.group, a.smoke)
    if not cs:
        raise ValueError('No cases selected')
    if a.command == 'list':
        for c in cs:
            print(f'{c['id']:<43} T={c['Tb']:5.2f} K  Ib/Isw={c['bias']:.4f}  N={c['N']:3}  C={c['C_pF']:3} pF  R20={c['R20_ohm']:g}')
        return 0
    if not (a.ids or a.group or a.smoke):
        raise ValueError('Select --case, --group, or --smoke explicitly')
    if a.command in ['build', 'run']:
        cs = [configure(c, a.inductance_model or 'fixed', a.depairing_ratio, a.lk_zero_nh) for c in cs]
        opamp = locate_opamp(a.opamp)
        for c in cs:
            if (a.output / c['id'] / 'case.raw').exists() and (not a.overwrite):
                raise ValueError('Existing simulation: ' + c['id'] + '. Choose a different --output or use --overwrite.')
        for c in cs:
            build(c, a.output, opamp)
        if a.command == 'build':
            print(f'Built {len(cs)} case(s) in {a.output}')
            return 0
        exe = locate_ltspice(a.ltspice)

        def run(c):
            run_deck(a.output / c["id"], exe, opamp, c["id"])
            print("Completed " + c["id"], flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
            list(pool.map(run, cs))
    if a.command in ['analyze', 'plot']:
        cs = [json.loads((a.output/c['id']/'case.json').read_text()) for c in cs]
    if a.command in ['run', 'analyze']:
        from snspdtool.analysis import analyze
        refs = references()
        results = []
        failures = {}
        for c in cs:
            d = a.output / c['id']
            r = analyze(c, d)
            results.append(r)
            (d / 'metrics.json').write_text(json.dumps(r, indent=2) + '\n')
            if a.compare or a.check_behavior:
                errs = compare(r, refs[c['id']]) if a.compare else check_behavior(r, refs[c['id']])
                if errs:
                    failures[c['id']] = errs
            print(f'{c['id']}: peak={r.get('peak_mV', float('nan')):.6f} mV, events={r.get('event_count')}, recovered={r.get('recovered')}', flush=True)
        summary = {
            'cases': len(results),
            'comparison_requested': a.compare,
            'behavior_check_requested': a.check_behavior,
            'failures': failures,
            'results': results,
        }
        (a.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        if failures:
            print(json.dumps(failures, indent=2))
            return 1
        if a.compare:
            print(f'Reference comparisons passed: {len(results)}')
        elif a.check_behavior:
            print(f'Behavior checks passed: {len(results)}')
    if a.command == 'plot':
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from snspdtool.analysis import read, time_mean
        for c in cs:
            d = a.output / c['id']
            w = read(d / 'case.raw')
            t = w['time'] * 1e9 - c['photon_ns']
            pre = (t > -2) & (t < -1)
            out = w['v(n011)']
            baseline = time_mean(t, out, pre)
            m = (t >= -0.2) & (t <= 10)
            ix = np.flatnonzero(m)[::max(1, int(m.sum() / 10000))]
            fig, axs = plt.subplots(2, 1, sharex=True, figsize=(8, 6), layout='constrained')
            axs[0].plot(t[ix], (out[ix] - baseline) * 1e3)
            axs[0].set_ylabel('Output (mV)')
            axs[1].plot(t[ix], w['v(wire:nrwire4)'][ix])
            axs[1].set(xlabel='Time after optical input (ns)', ylabel='Wire resistance (ohm)')
            for ax in axs:
                ax.grid(alpha=0.2)
            fig.suptitle(c['id'])
            fig.savefig(d / 'waveform.png', dpi=160)
            plt.close(fig)
            print(d / 'waveform.png')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print('Error: ' + str(e), file=sys.stderr)
        sys.exit(1)
