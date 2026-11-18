# Original models and project extensions

The starting point is Berggren et al., *Superconductor Science and Technology*
**31**, 055010 (2018), [doi:10.1088/1361-6668/aab149](https://doi.org/10.1088/1361-6668/aab149),
and its [SPICE library](https://github.com/qnngroup/snspd-spice).
The paper describes the curve-fit and dynamic models in Sections 3 and 4,
and a thermal extension in Supplementary Appendix A.

Section 7 of the paper identifies temperature-dependent thermal parameters and
separate electron/phonon temperatures as missing extensions. The v5c seed
implements these effects within a lumped approximation.

| Aspect | BCF / Dynamic baseline | Latest v5c implementation |
|---|---|---|
| Electrical representation | Kinetic inductance and a resistive hotspot; nonlinear flux relation in the supplied code | Same lumped circuit concept; fixed 38 nH by default, with an optional GL flux law |
| Thermal states | No separate electron and phonon temperature states in BCF / Dynamic | Explicit seed electron and phonon temperatures, with their own heat balances |
| Optical input | Gate-current pulse drives a switching criterion | Gate pulse is normalized to deposited optical power; its time integral is the model input energy |
| Resistive dynamics | Plateau-current switches in BCF; hotspot-boundary integration and restoration logic in Dynamic | Continuous seed resistance plus a propagated domain; formation, growth, retraction, and finite-size survival terms |
| Operating regimes | Switching/hotspot pulse models | Shared state equations used at low temperature and near the transition, without a mode-selection flag |

## Relation to later work

[Nguyen et al. (2025), *Modeling electrothermal feedback of superconducting
nanowire single photon detectors in SPICE*](https://arxiv.org/abs/2508.02791)
provide a later electrothermal SPICE comparison:

| Aspect | Nguyen et al. (2025) | Present v5c model |
|---|---|---|
| Dynamic thermal states | One wire temperature shared by electronic and phononic heat capacities | Separate electron and phonon temperatures in a fixed seed |
| Resistive evolution | Hotspot-boundary velocity with thermal feedback | Seed resistance plus a propagated domain with a finite-size survival approximation |
| Optical input | Energy-normalized thermal pulse | Energy-normalized thermal pulse deposited in the seed electrons |
| Demonstrated scope | Reset, afterpulsing, and latching | Reference cases with Geiger-like saturation and near-transition energy dependence; quantitative limitations remain |

Separate electron and phonon temperatures are established in SNSPD physics;
[Vodolazov (2019)](https://doi.org/10.1103/PhysRevApplied.11.014016) couples a
two-temperature model to a modified time-dependent Ginzburg–Landau equation.

## Extent of the changes

The packaged legacy BCF remains close to the original circuit structure, with
device parameters and numerical bounds changed. The local legacy Dynamic also
changes its restoration logic and adds an optional geometric-seed path, while
retaining the hotspot-boundary approach.

The v5c extension adds coupled seed heat balances and a phenomenological
finite-size domain-survival closure to the original lumped circuit and
hotspot-boundary approach. The optional current-dependent inductance follows
[Clem and Kogan (2012)](https://doi.org/10.1103/PhysRevB.86.174521), as detailed
in the [GL reference](current_dependent_inductance.md).

## Supported claims

The contribution under investigation is the integration of two-temperature seed
dynamics, continuous domain evolution, and the readout circuit for both response
regimes. These physical ingredients have prior literature; publication priority
has not been established, and no first-implementation claim is made.

Predictive assessment requires comparisons with the 2018 and 2025 baselines under
the same readout conditions and controlled removal of the added domain terms.
See [validation](validation.md#physical-consistency-and-validation-scope) for
current evidence and calibration limits, and [references.bib](references.bib)
for bibliographic records.
