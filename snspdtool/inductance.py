"""Explicit inductance variants with fixed geometry and matching flux analysis."""
import math
import numpy as np

DEFAULT_L_H = 38e-9
CURRENT_LIMIT = .999
INDUCTOR_LINE = 'L_NBN4 drain NLSER4 {Lind} Rser=0 IC={Iinit4}'


def parameters(case):
    model = case.get('inductance_model', 'fixed')
    if model == 'fixed':
        if 'lk_zero_nH' in case or 'depairing_ratio' in case and 'inductance_model' in case:
            raise ValueError('GL parameters require inductance_model=gl')
        return model, DEFAULT_L_H, None
    if model != 'gl':
        raise ValueError('Unknown inductance model: '+str(model))
    lk = float(case['lk_zero_nH']) * 1e-9
    ratio = float(case['depairing_ratio'])
    if not math.isfinite(lk) or lk <= 0:
        raise ValueError('Zero-current inductance must be finite and positive')
    if not math.isfinite(ratio) or ratio < 1:
        raise ValueError('Depairing/switching current ratio must be finite and at least one')
    idep = ratio * case['Isw']
    if case['bias'] * case['Isw'] >= CURRENT_LIMIT * idep:
        raise ValueError('Prepared bias reaches the GL current guard')
    return model, lk, idep


def configure(case, model='fixed', depairing_ratio=None, lk_zero_nh=None):
    result = dict(case)
    if model == 'fixed':
        if depairing_ratio is not None or lk_zero_nh is not None:
            raise ValueError('Inductance parameters require --inductance-model gl')
        return result
    if depairing_ratio is None or lk_zero_nh is None:
        raise ValueError('GL requires explicit --depairing-ratio and --lk-zero-nh')
    result.update(inductance_model=model, depairing_ratio=depairing_ratio, lk_zero_nH=lk_zero_nh)
    parameters(result)
    return result


def flux_linkage(current, case):
    _, lk, idep = parameters(case)
    if idep is None:
        return lk * current
    reduced = np.clip(np.asarray(current)/idep, -CURRENT_LIMIT, CURRENT_LIMIT)
    return 3 * lk * idep * np.sin(np.arcsin(reduced)/3)


def render_variant(source, case):
    model, lk, idep = parameters(case)
    if model == 'fixed':
        return source
    if source.count(INDUCTOR_LINE) != 1:
        raise ValueError('Expected one baseline inductor declaration')
    line = (f'L_NBN4 drain NLSER4 Flux=({lk:.15g}*3*{idep:.15g}*'
            f'sin(asin(limit(x/{idep:.15g},-0.999,0.999))/3)) Rser=0 IC={{Iinit4}}')
    header = ('* Generated GL inductance variant; geometry and thermal equations are unchanged.\n'
              '* Clem and Kogan, Phys. Rev. B 86, 174521 (2012), doi:10.1103/PhysRevB.86.174521.\n'
              '* Near-Tc, quasistatic approximation; low-temperature runs are numerical stress tests.\n'
              '* x is branch current. Phi=3*L0*Id*sin(asin(I/Id)/3); V=dPhi/dt.\n'
              '* Require abs(I)/Id < 0.999 throughout the trajectory.\n')
    return header + source.replace(INDUCTOR_LINE, line)
