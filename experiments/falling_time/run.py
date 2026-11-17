#!/usr/bin/env python3
"""Controlled recovery experiments; production model and references remain inputs."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.optimize import curve_fit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from snspdtool.core import deck, locate_ltspice, locate_opamp, selected
from snspdtool.simulation import run_deck
from snspdtool.analysis import analyze, crossing, decay, read, time_mean

SOURCE = ROOT / 'models/snspd_nbn_v5c.lib'
ORIGINAL_L = 'L_NBN4 drain NLSER4 {Lind} Rser=0 IC={Iinit4}'


def flux(current, inductance, depairing=None):
    """GL equilibrium flux; inductance is its zero-current differential value."""
    if depairing is None:
        return inductance * current
    q = 2 / np.sqrt(3) * np.sin(np.arcsin(np.clip(current / depairing, -.999, .999)) / 3)
    return inductance * 3 * np.sqrt(3) / 2 * depairing * q


def fit_tail(time_ns, values, high=.85, low=.15, uniform=True):
    """Fit A exp[-(t-t_start)/tau] + C between first descending crossings.

    Simulation fits use an equally spaced time grid, avoiding adaptive-step
    weighting. Experimental points are fitted at their original sample times.
    A window-limited exponential fit is descriptive, not an extracted L/R.
    """
    t, y = np.asarray(time_ns), np.asarray(values)
    peak = int(np.argmax(y))
    if y[peak] <= 1e-12:
        return None
    a = crossing(t, y, high * y[peak], peak, 'down')
    b = crossing(t, y, low * y[peak], peak, 'down')
    if a is None or b is None or b <= a:
        return None
    mask = (t >= a) & (t <= b)
    if mask.sum() < 4:
        return {'valid': False, 'reason': 'fewer than four original fit samples'}
    tx = np.linspace(a, b, 301) if uniform else t[mask]
    yy = np.interp(tx, t, y) / y[peak] if uniform else y[mask] / y[peak]
    x = tx - tx[0]
    fn = lambda x, amp, tau, offset: amp * np.exp(-x / tau) + offset
    guess = max((b - a) / np.log(high / low), .01)
    try:
        p, _ = curve_fit(fn, x, yy, p0=[high, guess, 0],
                         bounds=([0, .001, -2], [5, 1000, 1]), maxfev=10000)
    except (RuntimeError, ValueError) as e:
        return {'valid': False, 'reason': str(e)}
    residual = yy - fn(x, *p)
    fixed_fn = lambda x, amp, tau: amp * np.exp(-x / tau)
    pf, _ = curve_fit(fixed_fn, x, yy, p0=[high, guess],
                      bounds=([0, .001], [5, 1000]), maxfev=10000)
    return {'valid': bool(.00101 < p[1] < 999 and p[2] > -1.999),
            'tau_ns': float(p[1]), 'offset_fraction': float(p[2]),
            'r2': float(1 - np.sum(residual**2) / np.sum((yy-yy.mean())**2)),
            'rmse_fraction': float(np.sqrt(np.mean(residual**2))),
            'tau_fixed_baseline_ns': float(pf[1]),
            'r2_fixed_baseline': float(1 - np.sum((yy-fixed_fn(x, *pf))**2) / np.sum((yy-yy.mean())**2)),
            'start_ns': float(a), 'end_ns': float(b), 'samples': int(len(tx))}


def definitions():
    configs = []
    def add(variant, bias, n=10, **changes):
        c = dict(selected(['calorimetric_c30_b90_n10'])[0])
        c.update(bias=bias, N=n, variant=variant, probe_L_nH=38., depairing_ratio=None,
                 domain_energy=0, finite_penalty=10, stage='screen')
        c.update(changes)
        suffix = '_refined' if c['dt'] == '0.025p' else ''
        c['id'] = f'{variant}_b{round(100*bias):02d}_n{n}{suffix}'
        configs.append(c)
    for bias in [.6, .9, .96]:
        add('baseline', bias)
        add('gl_ratio12', bias, depairing_ratio=1.2)
        add('gl_ratio15', bias, depairing_ratio=1.5)
    for bias in [.6, .96]:
        add('cap_zero', bias, C_pF=0)
        add('linear_L76', bias, probe_L_nH=76.)
        add('no_size_penalty', bias, finite_penalty=0)
        add('domain_energy', bias, domain_energy=1)
    for n in [0, 1, 4, 100]:
        add('gl_ratio12', .9, n, stage='validation')
    add('gl_ratio12', .96, dt='0.025p', stage='validation')
    add('gl_ratio12_long', .96, dt='0.5p', stop_ns=805, stage='validation', depairing_ratio=1.2)
    # Supply the nonlinear law explicitly to every validation case.
    for c in configs:
        if c['variant'] == 'gl_ratio12':
            c['depairing_ratio'] = 1.2
    for lk in [38., 60., 76.]:
        c = dict(selected(['geiger_c30_schematic_1V_N8'])[0])
        c.update(id=f'geiger_L{lk:g}', variant='geiger_L', probe_L_nH=lk,
                 depairing_ratio=None, domain_energy=0, finite_penalty=10,
                 stage='geiger')
        configs.append(c)
    return configs


def prepare(c, directory, opamp):
    directory.mkdir(parents=True, exist_ok=True)
    model = SOURCE.read_text()
    if model.count(ORIGINAL_L) != 1:
        raise ValueError('Expected one production inductor declaration')
    lk = c['probe_L_nH'] * 1e-9
    if c['depairing_ratio'] is None:
        line = f'L_NBN4 drain NLSER4 {lk:.15g} Rser=0 IC={{Iinit4}}'
    else:
        idep = c['depairing_ratio'] * c['Isw']
        # x is branch current. Flux is integrated differential inductance,
        # not L_differential(x)*x. Guard must stay inactive in accepted runs.
        line = (f'L_NBN4 drain NLSER4 Flux=({lk:.15g}*3*{idep:.15g}*'
                f'sin(asin(limit(x/{idep:.15g},-0.999,0.999))/3)) Rser=0 IC={{Iinit4}}')
    model = model.replace(ORIGINAL_L, line)
    model_path = directory / 'detector_probe.lib'
    model_path.write_text(model)
    text = deck(c, opamp).replace(str(SOURCE), str(model_path.resolve()))
    text = text.replace('finiteSizePenalty0=10 penaltyExponent=1',
                        f'finiteSizePenalty0={c["finite_penalty"]} penaltyExponent=1'
                        f' domainEnergyClosure={c["domain_energy"]}')
    # Geometry continues to use Lind=38 nH in every experiment.
    (directory / 'case.cir').write_text(text)
    (directory / 'case.json').write_text(json.dumps(c, indent=2) + '\n')


def measurements(c, directory):
    row = analyze(c, directory)
    # Generic analyzer assumes a fixed 38 nH; replace its KVL result below.
    row.pop('kvl_integral_residual_fraction', None)
    w = read(directory / 'case.raw')
    t = w['time']; tp = c['photon_ns'] * 1e-9
    pre = (t > tp-2e-9) & (t < tp-1e-9)
    post = t >= tp
    current = w['i(wire:l_nbn4)']
    resistance = w['v(wire:nrwire4)']
    prepared = t >= tp-3e-9
    idep = None if c['depairing_ratio'] is None else c['depairing_ratio'] * c['Isw']
    phi = flux(current, c['probe_L_nH']*1e-9, idep)
    drive = w['v(n012)'] - w['v(n024)'] - current*(resistance+1e-5)
    residual = phi[prepared] - phi[prepared][0] - cumulative_trapezoid(drive[prepared], t[prepared], initial=0)
    phi_bias = float(flux(c['bias']*c['Isw'], c['probe_L_nH']*1e-9, idep))
    row['flux_kvl_residual_fraction'] = float(np.max(np.abs(residual))/phi_bias)
    row['max_current_over_depairing'] = float(np.max(np.abs(current[prepared]))/idep) if idep else None
    row['flux_guard_hit'] = bool(idep and row['max_current_over_depairing'] >= .999)
    for label, key in [('output', 'v(n011)'), ('rf', 'v(n013)')]:
        y = w[key] - time_mean(t, w[key], pre)
        row[label+'_fall_90_10_ns'] = decay(t, y, post) if row['valid_pulse'] else None
        row[label+'_fit_85_15'] = fit_tail((t[post]-tp)*1e9, y[post]) if row['valid_pulse'] else None
        row[label+'_fit_70_30'] = fit_tail((t[post]-tp)*1e9, y[post], .7, .3) if row['valid_pulse'] else None
    idx_peak = np.flatnonzero(post)[np.argmax(w['v(n011)'][post])]
    row['R_at_output_peak_ohm'] = float(resistance[idx_peak])
    ib = time_mean(t, current, pre)
    row['current_deficit_fall_90_10_ns'] = decay(t, ib-current, post) if row['valid_pulse'] else None
    row['accepted_numerics'] = bool(row['finite'] and not row['thermal_cap_hit']
        and not row['flux_guard_hit'] and row['flux_kvl_residual_fraction'] < .005
        and (not c['N'] or abs(row['deposited_relative_error']) < .001))
    # Export dense points around thermal dynamics, coarser points over the tail.
    grid = np.unique(np.r_[np.arange(-1, .5, .001), np.arange(.5, 20.001, .01)])
    channels = ['v(n011)', 'v(n013)', 'i(wire:l_nbn4)', 'v(wire:nrwire4)',
                'v(wire:nteuse4)', 'v(wire:ntphuse4)']
    data = [grid] + [np.interp(tp+grid*1e-9, t, w[key]) for key in channels]
    np.savetxt(directory / 'waveform.csv', np.column_stack(data), delimiter=',',
               header='time_ns,output_V,rf_V,current_A,resistance_ohm,Te_K,Tph_K', comments='')
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'runs/falling_time')
    parser.add_argument('--stage', choices=['screen', 'validation', 'geiger', 'all'], default='screen')
    parser.add_argument('--variant', action='append')
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--analyze-only', action='store_true')
    args = parser.parse_args()
    configs = [c for c in definitions() if (args.stage == 'all' or c['stage'] == args.stage)
               and (not args.variant or c['variant'] in args.variant)]
    opamp, executable = locate_opamp(), locate_ltspice()
    inputs = json.loads((Path(__file__).with_name('inputs.json')).read_text())
    for name, expected in inputs['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Baseline input changed; define a new experiment: '+name)
    if hashlib.sha256(opamp.read_bytes()).hexdigest() != inputs['opamp_sha256']:
        raise ValueError('Installed opamp model differs from the recorded experiment')
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    args.output.mkdir(parents=True, exist_ok=True)

    def run(c):
        directory = args.output / c['id']
        if (directory / 'case.raw').exists():
            if json.loads((directory/'case.json').read_text()) != c:
                raise ValueError('Existing configuration differs: '+c['id'])
            saved = json.loads((directory/'run_metadata.json').read_text())
            if hashlib.sha256((directory/'case.cir').read_bytes()).hexdigest() != saved['deck_sha256']:
                raise ValueError('Existing netlist differs from the simulated deck: '+c['id'])
        elif args.analyze_only:
            raise FileNotFoundError(directory/'case.raw')
        else:
            prepare(c, directory, opamp)
            run_deck(directory, executable, opamp, c['id'])
        row = measurements(c, directory)
        row['production_model_sha256'] = source_hash
        (directory/'metrics.json').write_text(json.dumps(row, indent=2)+'\n')
        fit = row['output_fit_85_15'] or {}
        print(f'{c["id"]}: fall={row["output_fall_90_10_ns"]}, '
              f'tau={fit.get("tau_ns")}, recovery={row["recovered"]}, '
              f'numerics={row["accepted_numerics"]}', flush=True)
        return row
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        rows = list(pool.map(run, configs))
    scope = args.stage + ('_' + '_'.join(args.variant) if args.variant else '')
    (args.output/f'{scope}_summary.json').write_text(json.dumps(rows, indent=2)+'\n')
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError('Production model changed during experiment')


if __name__ == '__main__':
    main()
