"""Pulse measurements and electrical and thermal balance checks."""

from pathlib import Path
import re
import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.signal import find_peaks
from PyLTSpice import RawRead
from snspdtool.inductance import CURRENT_LIMIT, flux_linkage, parameters as inductance_parameters


def read(path):
    p = Path(path)
    r = RawRead(str(p), [], dialect='ltspice')
    w = {n.lower(): np.asarray(r.get_wave(n), dtype=float) for n in r.get_trace_names()}
    with p.open('rb') as stream:
        h = stream.read(4096).decode('utf-16-le', errors='ignore')
    m = re.search('^Offset:\\s*(\\S+)', h, re.M)
    if m:
        w['time'] += float(m.group(1))
    return w


def time_mean(t, y, mask):
    """Time-weighted mean for an adaptively sampled waveform."""
    return float(np.trapezoid(y[mask], t[mask]) / (t[mask][-1] - t[mask][0]))


def crossing(t, y, level, start, direction):
    j = np.arange(start + 1, len(y))
    yes = (y[j] <= level) & (y[j - 1] > level) if direction == 'down' else (y[j] >= level) & (y[j - 1] < level)
    hits = j[yes]
    if not len(hits):
        return None
    j = hits[0]
    return float(t[j - 1] + (level - y[j - 1]) * (t[j] - t[j - 1]) / (y[j] - y[j - 1]))


def decay(t, y, post):
    peak = np.flatnonzero(post)[np.argmax(y[post])]
    if y[peak] <= 1e-12:
        return None
    a = crossing(t, y, 0.9 * y[peak], peak, 'down')
    b = crossing(t, y, 0.1 * y[peak], peak, 'down')
    return float((b - a) * 1e9) if a is not None and b is not None else None


def analyze(c, run_directory):
    root = Path(run_directory)
    name = 'case'
    log = (root / (name + '.log')).read_bytes().decode('utf-16-le', errors='replace')
    if 'Total elapsed time:' not in log:
        raise RuntimeError(name + ' incomplete')
    w = read(root / 'case.raw')
    g = lambda n: w[n.lower()]
    row = dict(c, finite=all((np.isfinite(x).all() for x in w.values())))
    if not row['finite']:
        return row
    t = g('time')
    tp = c['photon_ns'] * 1e-09
    pre = (t > tp - 2e-09) & (t < tp - 1e-09)
    post = t >= tp
    tail = t > tp + 3e-08
    prepared = t >= tp - 3e-09

    def avg(y, mask):
        return time_mean(t, y, mask)
    I = g('I(wire:L_NBN4)')
    R = g('V(wire:NRwire4)')
    Rd = g('V(wire:NRdom4)')
    Te = g('V(wire:NTeUse4)')
    Tph = g('V(wire:NTphUse4)')
    out = g('V(N011)') - avg(g('V(N011)'), pre)
    rf = g('V(N013)') - avg(g('V(N013)'), pre)
    idx = np.flatnonzero(post)[np.argmax(out[post])]
    peak = float(out[idx])
    ir = np.flatnonzero(post)[np.argmax(R[post])]
    suffix = np.maximum.accumulate(R[::-1])[::-1]
    resets = np.flatnonzero((np.arange(len(t)) >= ir) & (suffix < 1))
    ib = avg(I, pre)
    expected = c['bias'] * c['Isw']
    eps = 1.602176634e-19
    deposited = float(np.trapezoid(g('V(wire:NPph4)'), t) / eps)
    intended = 0.1 * c['N'] * 1.9878e-25 / 5.32e-07 / eps
    z = crossing(t, out, 0, idx, 'down') if c['N'] else None
    pm = post & (t <= z) if z is not None else post
    peaks, _ = find_peaks(R, height=max(1, 0.2 * float(max(R[post]))), prominence=max(0.5, 0.1 * float(max(R[post]))))
    peaks = peaks[t[peaks] >= tp]
    event_times = []
    for j in peaks:
        if not event_times or t[j] - event_times[-1] > 5e-10:
            event_times.append(float(t[j]))
    ti = t[prepared]
    drive = g('V(N012)') - g('V(N024)') - (R + 1e-05) * I
    inductance_model, _, idep = inductance_parameters(c)
    phi = flux_linkage(I[prepared], c)
    kvl = phi - phi[0] - cumulative_trapezoid(drive[prepared], ti, initial=0)
    phi_bias = float(flux_linkage(expected, c))
    vwire = g('V(wire:NET4)') - g('V(N024)')
    valid_pulse = bool(c['N'] and peak > 1e-06 and (max(R[post]) > 0.01))
    row.update(
        Ipre_uA=ib * 1e6,
        Itail_uA=avg(I, tail) * 1e6,
        Imin_uA=float(min(I[post]) * 1e6),
        peak_mV=peak * 1e3,
        rf_peak_uV=float(max(rf[post]) * 1e6),
        peak_time_ns=float((t[idx] - tp) * 1e9),
        fall_90_10_ns=decay(t, out, post) if valid_pulse else None,
        positive_lobe_area_mV_ns=float(np.trapezoid(np.maximum(out[pm], 0), t[pm]) * 1e12) if valid_pulse else None,
        Rpeak_ohm=float(max(R[post])),
        Rdomain_peak_ohm=float(max(Rd[post])),
        Rpre_max_ohm=float(max(R[pre])),
        Rtail_max_ohm=float(max(R[tail])),
        R_decay_90_10_ns=decay(t, R, post) if valid_pulse else None,
        reset_below_1ohm_ns=float((t[resets[0]] - tp) * 1e9) if valid_pulse and len(resets) else None,
        Te_peak_K=float(max(Te[post])),
        Tph_peak_K=float(max(Tph[post])),
        Te_tail_K=avg(Te, tail),
        Te_decay_90_10_ns=decay(t, Te - c['Tb'], post) if valid_pulse else None,
        deposited_eV=deposited,
        deposited_relative_error=deposited / intended - 1 if intended else None,
        recovered=bool(max(R[tail]) < 1 and abs(avg(I, tail) / expected - 1) < 0.01 and (abs(avg(Te, tail) - c['Tb']) < 0.01)),
        valid_pulse=valid_pulse,
        event_count=len(event_times),
        event_peak_times_ns=[(x - tp) * 1e9 for x in event_times],
        kvl_integral_residual_fraction=float(max(abs(kvl)) / phi_bias),
        inductance_model=inductance_model,
        inductance_guard_hit=bool(idep is not None and max(abs(I[prepared]))/idep >= CURRENT_LIMIT),
        max_current_over_depairing=float(max(abs(I[prepared]))/idep) if idep else None,
        resistor_voltage_error_V=float(max(abs(vwire - R * I)[prepared])),
        thermal_cap_hit=bool(max(Te[prepared]) >= 49.99 or max(Tph[prepared]) >= 49.99),
        domain_joule_eV=float(np.trapezoid(g('V(wire:NPjDomain4)'), t) / eps),
        wire_resistive_peak_uV=float(max((R * I)[post]) * 1e6),
    )
    Ce = g('V(wire:NCe4)')
    Cp = g('V(wire:NCp4)')
    Pin = g('V(wire:NPph4)') + g('V(wire:NPjSeed4)')
    Pe = g('V(wire:NPeph4)')
    Pc = g('V(wire:NPcool4)')
    Pd = g('V(wire:NPdiff4)')
    norm = max(cumulative_trapezoid(Pin[prepared], ti, initial=0))
    for label, heat, temp, flux in [('electron', Ce, Te, Pin - Pe - Pd - Ce * (Te - c['Tb']) * 1e-09), ('phonon', Cp, Tph, Pe - Pc - Cp * (Tph - c['Tb']) * 1e-09)]:
        u = cumulative_trapezoid(heat[prepared], temp[prepared], initial=0)
        f = cumulative_trapezoid(flux[prepared], ti, initial=0)
        row[label + '_seed_balance_residual_fraction'] = float(max(abs(u - f)) / norm) if norm > 1e-30 else None
    return row
