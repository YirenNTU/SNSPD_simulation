# Current-dependent inductance candidate

This option replaces the fixed 38 nH electrical inductor with a nonlinear
flux-current relation. Geometry, thermal equations, and external circuitry retain
their baseline definitions.

## Constitutive law and scope

The candidate uses the near-transition, quasistatic Ginzburg–Landau relation
discussed by [Clem and Kogan, *Physical Review B* **86**, 174521 (2012)](
https://doi.org/10.1103/PhysRevB.86.174521). Writing the dimensionless phase
gradient as $q$ on the stable branch,

$$
I=\frac{3\sqrt{3}}{2}I_dq(1-q^2),\qquad |q|<\frac{1}{\sqrt{3}},
$$

$$
q=\frac{2}{\sqrt{3}}\sin\!\left[\frac{1}{3}\arcsin\!\left(\frac{I}{I_d}\right)\right],
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

The example uses trial values, not measured detector parameters. `Lind` remains
38 nH for the inferred thermal geometry; `--lk-zero-nh` sets the electrical $L_0$.

Each run directory contains `detector_gl.lib`, `model_variant.json`, and
`case.json`. The generated model changes only the inductor declaration and
records the source hashes. Subsequent `analyze` and `plot` commands read the
saved case configuration; inductance flags are accepted only by `build` and
`run`.

Use `--check-behavior` for this option; `--compare` requires agreement with the
fixed-model amplitudes and timing. Full commands and acceptance criteria are in
the [regression protocol](reproducibility.md#regression-commands).

The implementation clips $I/I_d$ at $\pm0.999$ only to protect the inverse sine
from invalid trial values. A reported trajectory reaching this guard is rejected.
Guard and KVL checks cover the prepared interval from 3 ns before the optical
input through the end of the simulation.

## Evidence

[Validation](validation.md#current-dependent-inductance) records the 64-run
comparison, preserved response characteristics, convergence, and remaining
calibration limits. The [controlled recovery experiment](../experiments/falling_time/README.md)
compares this mechanism with circuit and domain changes and explains why an
exponential fit can differ from the 90–10% falling-time observable.
