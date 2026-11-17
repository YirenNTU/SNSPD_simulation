# Current-dependent inductance candidate

This experimental option replaces the electrical inductor with a nonlinear
flux-current relation. The default model remains the fixed 38 nH implementation.
The original model files, thermal equations, geometry, external circuit, case
definitions, and stored reference measurements are unchanged.

## Constitutive law and scope

The candidate uses the near-transition, quasistatic Ginzburg–Landau relation
discussed by [Clem and Kogan, *Physical Review B* **86**, 174521 (2012)](
https://doi.org/10.1103/PhysRevB.86.174521). Writing the dimensionless phase
gradient as $q$ on the stable branch,

$$
I=\frac{3\sqrt{3}}{2}I_dq(1-q^2),\qquad |q|<\frac{1}{\sqrt{3}},
$$

gives the flux linkage used in LTspice:

$$
\Phi(I)=3L_0I_d\sin\!\left[\frac{1}{3}\arcsin\!\left(\frac{I}{I_d}\right)\right],
\qquad
V_L=\frac{d\Phi}{dt}=L_{\mathrm{diff}}(I)\frac{dI}{dt},
$$

$$
L_{\mathrm{diff}}(I)=\frac{d\Phi}{dI}
=\frac{L_0}{1-3q^2}.
$$

$L_0$ is the zero-current differential inductance and $I_d$ is the depairing
current. The code takes $I_d/I_{\mathrm{sw}}$ as an explicit input; it does not
identify switching current with depairing current. `Flux=` implements the
integrated constitutive relation, not the product $L_{\mathrm{diff}}(I)I$.

As the wire current recovers toward a larger bias, its differential inductance
increases. This can extend the electrical falling edge without changing the
thermal recovery law. The output also includes the bias-tee and amplifier
response, so its full decay is not generally a single $L/R$ exponential.

The GL approximation is intended for temperatures near $T_c$ with sufficiently
fast order-parameter relaxation. The implementation holds $L_0$ and $I_d$ fixed
at the chosen operating temperature; it does not evolve their local temperature
dependence or the order parameter. Applying it throughout a large pulse is a
modeling approximation. Geiger runs at 4.68 K are numerical stress tests of this
option, not a physical validation of the near-$T_c$ law at low temperature.

## Usage

The candidate requires both parameters explicitly:

```sh
python3 snspd.py run --group calorimetric \
  --inductance-model gl --depairing-ratio 1.2 --lk-zero-nh 38 \
  --output runs/lk_integration/cal_gl --check-behavior --jobs 2
```

The values 1.2 and 38 nH specify the controlled candidate studied here. They are
not independently measured detector parameters. The electrical inductance is
changed separately from `Lind`, which still sets the baseline geometry in the
thermal model.

Each run directory contains `detector_gl.lib`, `model_variant.json`, and
`case.json`. The generated model changes only the inductor declaration and
records the source hashes. Subsequent `analyze` and `plot` commands read the
saved case configuration; inductance flags are accepted only by `build` and
`run`.

`--compare` retains the strict fixed-model reference comparison, including
amplitude and timing. `--check-behavior` checks event classification, recovery,
numerical guards, optical energy normalization, and the flux-integral KVL
residual. It does not require the candidate to reproduce fixed-model amplitudes
or falling times. Cross-case saturation, energy dependence, and step convergence
are checked separately by `scripts/verify_inductance.py`.

The implementation clips $I/I_d$ at $\pm0.999$ only to protect the inverse sine
from invalid trial values. A reported trajectory reaching this guard is rejected.
Guard and KVL checks cover the prepared interval from 3 ns before the optical
input through the end of the simulation.

## Reproduce the regression

Use separate output directories for the four groups:

```sh
python3 snspd.py run --group geiger --compare --jobs 2 \
  --output runs/lk_integration/geiger_fixed
python3 snspd.py run --group calorimetric --compare --jobs 2 \
  --output runs/lk_integration/cal_fixed
python3 snspd.py run --group geiger --check-behavior --jobs 2 \
  --inductance-model gl --depairing-ratio 1.2 --lk-zero-nh 38 \
  --output runs/lk_integration/geiger_gl
python3 snspd.py run --group calorimetric --check-behavior --jobs 2 \
  --inductance-model gl --depairing-ratio 1.2 --lk-zero-nh 38 \
  --output runs/lk_integration/cal_gl
python3 scripts/verify_inductance.py
python3 -m unittest discover -s tests -v
```

The verification preserves the original amplitude tolerance of 0.2% (or 2 µV)
and timing tolerance of 2 ps for the default model. For both options it also
checks high-bias Geiger saturation within 1% between N=1 and N=8, increasing
calorimetric peak amplitude over N=10, 20, 50, 100, and convergence under halving
the maximum time step. N is the optical-input multiplier defined by the model,
not a calibrated count of absorbed photons.

## Verification results — 18 November 2026

The [machine-readable verification record](../provenance/inductance_verification.json)
contains 64 newly executed simulations, source hashes, and all 32 verification
checks. All checks passed. The default netlists were also compared with commit
`d40f46f4b8886eb2996866fb5c73768004f4a0f4`; all 32 were identical. The 18 Python
unit tests passed.

| Configuration | Geiger cases | Calorimetric cases | Acceptance criterion |
|---|---:|---:|---|
| Default fixed inductance | 7/7 | 25/25 | Original strict amplitude, timing, event, and recovery comparisons |
| GL, $L_0=38$ nH, $I_d/I_{\mathrm{sw}}=1.2$ | 7/7 | 25/25 | Same trigger classification and recovery; numerical validity |

The GL option retained high-bias Geiger saturation: increasing N from 1 to 8
changed peak amplitude by 0.00507%. The 1 V, N=1 no-trigger case remained below
threshold; the N=8 case still triggered. Dark-input cases produced no events.
Both modes recovered in the tests extending 800 ns after excitation, without
additional detected events. These deterministic tests do not model stochastic
dark counts.

For the 30 pF calorimetric circuit at $I_b/I_{\mathrm{sw}}=0.9$:

| Optical multiplier N | GL peak amplitude (mV) |
|---:|---:|
| 10 | 24.001 |
| 20 | 33.564 |
| 50 | 41.863 |
| 100 | 45.649 |

Thus the tested calorimetric response remains energy-sensitive. At N=10, its
90–10% output falling time increases with bias:

| $I_b/I_{\mathrm{sw}}$ | Fixed 38 nH (ns) | GL candidate (ns) |
|---:|---:|---:|
| 0.60 | 1.533 | 1.657 |
| 0.70 | 1.533 | 1.716 |
| 0.80 | 1.533 | 1.795 |
| 0.90 | 1.533 | 1.899 |
| 0.96 | 1.533 | 1.977 |

For the four GL step-refinement pairs, the largest amplitude change was 0.00469%
and the largest falling-time change was 0.00338 ps. All numerical guards remained
inactive; the largest sampled $|I|/I_d$ was 0.827. The GL integral KVL residual
was below 0.000733%. All nine overlapping GL cases reproduced the earlier
controlled experiment's peak amplitudes and falling times exactly as recorded.
This establishes implementation consistency for the tested parameters, not a
fit to experimental calorimetric waveforms.

## Remaining physical checks

The existing low-energy calorimetric amplitude inversion between N=1 and N=4
is recorded explicitly and is not treated as a passing physical calibration.
With the GL option, the corresponding peaks are 17.763 and 17.303 mV.
Preserving energy sensitivity does not establish calibrated energy resolution.

The falling-edge observable is the baseline-subtracted 90–10% duration. A
free-offset exponential fit can give a different bias trend; see the
[controlled experiment](../experiments/falling_time/README.md). Experimental
bias-sweep traces and independent constraints on $L_0$ and $I_d$ are still needed
to test the proposed mechanism. No default parameters or reference data are
retuned to obtain the candidate's trend.
