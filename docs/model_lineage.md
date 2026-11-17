# Original models and project extensions

The starting point is Berggren et al., *Superconductor Science and Technology*
**31**, 055010 (2018), [doi:10.1088/1361-6668/aab149](https://doi.org/10.1088/1361-6668/aab149),
and its [SPICE library](https://github.com/qnngroup/snspd-spice).
The paper describes the curve-fit and dynamic models in Sections 3 and 4,
and a thermal extension in Supplementary Appendix A.

The comparison below concerns the BCF and Dynamic implementations from which
this project developed. It is not a claim that all thermal modeling originated
in this project.

Section 7 of the paper identifies temperature-dependent thermal parameters and
separate electron/phonon temperatures as missing extensions. The v5c seed
implements these effects within a lumped approximation; it does not resolve
the temperature field throughout the developed domain.

| Aspect | BCF / Dynamic baseline | Latest v5c implementation |
|---|---|---|
| Electrical representation | Kinetic inductance and a resistive hotspot; nonlinear flux relation in the supplied code | Same lumped circuit concept, with fixed 38 nH inductance and sensed branch current |
| Thermal states | No separate electron and phonon temperature states in BCF / Dynamic | Explicit seed electron and phonon temperatures, with their own heat balances |
| Optical input | Gate-current pulse drives a switching criterion | Gate pulse is normalized to deposited optical power; its time integral is the model input energy |
| Resistive dynamics | Plateau-current switches in BCF; hotspot-boundary integration and restoration logic in Dynamic | Continuous seed resistance plus a propagated domain; formation, growth, retraction, and finite-size survival terms |
| Operating regimes | Switching/hotspot pulse models | Shared state equations used at low temperature and near the transition, without a mode-selection flag |

## Relation to later work

Differences from the 2018 baseline alone do not establish novelty relative to
subsequent literature.

[Nguyen et al. (2025), *Modeling electrothermal feedback of superconducting
nanowire single photon detectors in SPICE*](https://arxiv.org/abs/2508.02791),
combine hotspot-boundary dynamics with one uniform wire-temperature state.
Their model includes temperature-dependent heat capacity and an optical-power
pulse normalized by its energy, and demonstrates reset, afterpulsing, and latching.
Although electronic and phononic heat capacities are included, they contribute
to a common temperature rather than separate electron and phonon states.

Separate electron and phonon temperatures are established in SNSPD physics; for
example, [Vodolazov (2019)](https://doi.org/10.1103/PhysRevApplied.11.014016)
couples a two-temperature model to a modified time-dependent Ginzburg–Landau
equation. That work establishes prior use of the physics, not the specific
compact SPICE implementation developed here.

| Aspect | Nguyen et al. (2025) | Present v5c model |
|---|---|---|
| Dynamic thermal states | One uniform wire temperature | Separate electron and phonon temperatures in a fixed seed |
| Resistive evolution | Hotspot-boundary velocity with thermal feedback | Seed resistance plus a propagated domain with a finite-size survival approximation |
| Optical input | Energy-normalized thermal pulse | Energy-normalized thermal pulse deposited in the seed electrons |
| Demonstrated scope | Reset, afterpulsing, and latching | Reference cases with Geiger-like saturation and near-transition energy dependence; quantitative limitations remain |

The candidate methodological contribution is a compact SPICE representation that
couples two-temperature seed dynamics and continuous domain evolution to examine
both response regimes with a common set of equations. Its value must be assessed
by the behavior it predicts and its suitability for circuit simulation.
Publication priority has not been established; this repository makes no claim
to the first such implementation. Bibliographic records are in
[`references.bib`](references.bib).

## Extent of the changes

The packaged legacy BCF remains close to the original circuit structure, with
device parameters and numerical bounds changed. The local legacy Dynamic also
changes its restoration logic and adds an optional geometric-seed path, while
retaining the hotspot-boundary approach.

The latest v5c is a substantial structural extension. Its four continuous states
are detector current, two seed temperatures, and propagated-domain resistance.
The coupled heat balances, energy-normalized excitation, and domain closure change
how a pulse is generated and recovers. The original lumped electrical circuit,
hotspot picture, boundary-growth approach, and SPICE implementation strategy
remain its foundation.

The finite-size survival term uses a critical scale evaluated at the prepared
bias. It is a project closure with approximations and fitted coefficients.
It is not established as a universal material law. Standard two-temperature heat
balances, Joule heating, and thermal transport laws are not new physical principles.

## Supported claims

The current tests show Geiger-like amplitude saturation and an energy-dependent
near-transition response using the same equations. Low-energy output peaks are
not monotonic.
The developed domain has no independent thermal-energy state.

These results support describing the implementation as an electrothermal extension
of the Berggren et al. framework. The model has a physically motivated structure
with semi-empirical domain dynamics; it is not yet a quantitatively validated
description of the full Geiger-to-calorimetric transition.

To establish a predictive contribution, compare the 2018 and 2025 baselines under
the same readout conditions, remove the added domain terms in controlled tests,
and predict held-out bias, temperature, and deposited-energy scans. Material and
closure parameters should remain fixed across those scans, with independently
measured operating-point inputs supplied explicitly. See
[validation](validation.md#physical-consistency-and-validation-scope).
