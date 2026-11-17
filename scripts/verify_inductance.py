"""Verify fixed-model compatibility and the opt-in GL candidate across both modes.

Requires the four complete simulation groups described in
docs/current_dependent_inductance.md. Reads their metrics without rerunning SPICE.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from snspdtool.core import cases, check, check_behavior, compare, references


def verify(directory):
    package = check()
    refs = references()
    expected = {group: {c['id'] for c in cases() if c['group'] == group}
                for group in ['geiger', 'calorimetric']}
    rows, runs, checks = {}, {}, []

    def record(name, passed, **measurements):
        checks.append(dict(name=name, passed=bool(passed), **measurements))

    original_inputs = json.loads((ROOT/'experiments/falling_time/inputs.json').read_text())
    changed = [name for name, digest in original_inputs['source_sha256'].items()
               if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest]
    record('baseline_inputs_unchanged', not changed, changed_files=changed,
           baseline_commit=original_inputs['baseline_commit'])

    for folder, group, model in [('geiger_fixed', 'geiger', 'fixed'),
                                 ('cal_fixed', 'calorimetric', 'fixed'),
                                 ('geiger_gl', 'geiger', 'gl'),
                                 ('cal_gl', 'calorimetric', 'gl')]:
        summary = json.loads((directory/folder/'summary.json').read_text())
        rs = {r['id']: r for r in summary['results']}
        if set(rs) != expected[group] or len(summary['results']) != len(rs):
            raise ValueError('Incomplete or duplicate case coverage: '+folder)
        rows[folder] = rs
        failures = {}
        for name, result in rs.items():
            errors = (compare if model == 'fixed' else check_behavior)(result, refs[name])
            if result['inductance_model'] != model:
                errors.append('Wrong inductance model')
            if model == 'gl' and (result['depairing_ratio'] != 1.2 or result['lk_zero_nH'] != 38):
                errors.append('Candidate parameters differ from this verification protocol')
            if errors:
                failures[name] = errors
        record(folder+'_case_checks', not failures, count=len(rs), failures=failures)
        bias_errors = {name: abs(r['Ipre_uA']*1e-6/(r['bias']*r['Isw'])-1)
                       for name, r in rs.items()}
        bad_preparation = [name for name, r in rs.items()
                           if bias_errors[name] >= .01 or r['Rpre_max_ohm'] >= 1]
        record(folder+'_prepared_state', not bad_preparation,
               failed_cases=bad_preparation, max_relative_bias_error=max(bias_errors.values()))
        fields = ['id', 'Tb', 'bias', 'N', 'C_pF', 'R20_ohm', 'dt', 'stop_ns',
                  'finite', 'inductance_model', 'depairing_ratio', 'lk_zero_nH', 'peak_mV',
                  'fall_90_10_ns', 'event_count', 'valid_pulse', 'recovered',
                  'reset_below_1ohm_ns', 'thermal_cap_hit', 'inductance_guard_hit',
                  'max_current_over_depairing', 'kvl_integral_residual_fraction',
                  'deposited_relative_error', 'Rtail_max_ohm', 'Itail_uA',
                  'Ipre_uA', 'Rpre_max_ohm']
        runs[folder] = [{key: r[key] for key in fields if key in r} for r in rs.values()]

    for model in ['fixed', 'gl']:
        geiger, cal = rows['geiger_'+model], rows['cal_'+model]
        a, b = (geiger['geiger_c30_high_'+s] for s in ['dt005', 'N8'])
        saturation = abs(b['peak_mV']/a['peak_mV']-1)
        record(model+'_geiger_saturation', saturation < .01,
               relative_peak_change_N1_to_N8=saturation, tolerance=.01)
        energies = [10, 20, 50, 100]
        peaks = [cal[f'calorimetric_c30_b90_n{n}']['peak_mV'] for n in energies]
        record(model+'_calorimetric_energy_dependence',
               all(b > a for a, b in zip(peaks, peaks[1:])) and peaks[-1]/peaks[0] > 1.1,
               N=energies, peak_mV=peaks)
        low = [cal[f'calorimetric_c30_b90_n{n}']['peak_mV'] for n in [1, 4]]
        # An observation, not an acceptance condition: this known limitation must
        # remain visible even when all numerical regression checks pass.
        runs[model+'_low_energy'] = {'N': [1, 4], 'peak_mV': low,
                                     'nonmonotonic_peak': low[1] < low[0]}
        pairs = [(geiger, 'geiger_c30_high_dt005', 'geiger_c30_high_dt0025')]
        for suffix in ['b90_n1', 'b90_n4', 'b96_n10']:
            name = 'calorimetric_c30_'+suffix
            pairs.append((cal, name, name+'_refined'))
        for group_rows, coarse, refined in pairs:
            a, b = group_rows[coarse], group_rows[refined]
            amp = abs(a['peak_mV']/b['peak_mV']-1)
            fall = abs(a['fall_90_10_ns']-b['fall_90_10_ns'])
            record(model+'_step_convergence_'+coarse, amp < .002 and fall < .002,
                   relative_peak_difference=amp, fall_difference_ps=fall*1000)

    biases = [60, 70, 80, 90, 96]
    falls = [rows['cal_gl'][f'calorimetric_c30_b{b}_n10']['fall_90_10_ns'] for b in biases]
    record('gl_bias_dependent_fall', all(b > a for a, b in zip(falls, falls[1:])),
           bias_fraction=[b/100 for b in biases], fall_90_10_ns=falls)

    historical = json.loads((ROOT/'experiments/falling_time/results.json').read_text())
    if isinstance(historical, dict):
        historical = historical['results']
    for old in historical:
        if old['variant'] not in ['gl_ratio12', 'gl_ratio12_long']:
            continue
        name = f'calorimetric_c30_b{round(old["bias"]*100)}_n{old["N"]}'
        if old['dt'] == '0.025p':
            name += '_refined'
        elif old['stop_ns'] > 800:
            name += '_long'
        new = rows['cal_gl'][name]
        delta_peak = abs(new['peak_mV']-old['peak_mV'])
        delta_fall = (abs(new['fall_90_10_ns']-old['fall_90_10_ns'])
                      if old['fall_90_10_ns'] is not None else 0.)
        record('historical_probe_'+name,
               delta_peak < max(.002, abs(old['peak_mV'])*.002) and delta_fall < .002,
               peak_difference_mV=delta_peak, fall_difference_ps=delta_fall*1000)

    inputs = ['snspd.py', 'snspdtool/core.py', 'snspdtool/analysis.py',
              'snspdtool/inductance.py', 'snspdtool/simulation.py',
              'scripts/verify_inductance.py', 'models/snspd_nbn_v5c.lib',
              'legacy/snspd_geiger.lib', 'cases/geiger.json', 'cases/calorimetric.json',
              'circuits/amplifier_chain.inc', 'circuits/bias_tee_and_load.inc',
              'results/reference/geiger_metrics.json', 'results/reference/calorimetric_metrics.json',
              'experiments/falling_time/results.json']
    environment = json.loads((directory/'cal_gl/calorimetric_c30_b90_n10/run_metadata.json').read_text())
    environment.pop('case_id')
    environment.pop('deck_sha256')
    record('opamp_dependency_unchanged',
           environment['opamp_sha256'] == original_inputs['opamp_sha256'])
    return dict(created_utc=datetime.now(timezone.utc).isoformat(), package=package,
                scope='Fixed baseline regression and opt-in GL behavior; not experimental calibration',
                candidate={'lk_zero_nH': 38, 'depairing_ratio': 1.2},
                environment=environment,
                source_sha256={s: hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in inputs},
                passed=all(c['passed'] for c in checks), checks=checks, runs=runs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=Path, default=ROOT/'runs/lk_integration')
    parser.add_argument('--report', type=Path, default=ROOT/'provenance/inductance_verification.json')
    args = parser.parse_args()
    report = verify(args.runs)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    failed = [c['name'] for c in report['checks'] if not c['passed']]
    print(f'{len(report["checks"])-len(failed)}/{len(report["checks"])} checks passed; 64 simulations')
    for name in failed:
        print('FAILED: '+name)
    return bool(failed)


if __name__ == '__main__':
    sys.exit(main())
