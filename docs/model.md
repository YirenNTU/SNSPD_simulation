# Detector model

The subcircuit `nanowireElectrothermal_NbN_v5c` combines kinetic inductance,
a two-temperature seed, and continuous normal-domain evolution. Its ports
are `gate`, `gatereturn`, `drain`, and `source`. The gate is a numerical optical-power
control input; it is not a physical detector terminal.
The [implementation reference](snspd_implementation.md) maps these quantities to
SPICE elements; [model lineage](model_lineage.md) documents the Berggren et al.
framework and subsequent extensions.

## State equations

With the default fixed inductance, the electrical state follows

\[
L_k\frac{dI}{dt}=V_{\mathrm{drain}}-V_{\mathrm{source}}
-I(R_{\mathrm{wire}}+R_s),
\]

where \(R_{\mathrm{wire}}=\min[R_n,\max(R_{\mathrm{seed}}+R_{\mathrm{domain}},0)]\)
and the numerical series resistance is \(R_s=10\,\mu\Omega\). Ideal 0 V sources
measure detector and gate currents used by behavioral sources.

For the fixed seed volume, the implemented lumped heat capacities are
\(C_e^{\mathrm{seed}}=c_eV_{\mathrm{seed}}\) and
\(C_{ph}^{\mathrm{seed}}=c_{ph}V_{\mathrm{seed}}\):

\[
C_e^{\mathrm{seed}}\dot T_e=P_{\mathrm{opt}}+I^2R_{\mathrm{seed}}
-P_{e-ph}-P_{\mathrm{diff}},\qquad
C_{ph}^{\mathrm{seed}}\dot T_{ph}=P_{e-ph}-P_{\mathrm{sub}}.
\]

\[
P_{e-ph}=\Sigma V_{\mathrm{seed}}(T_e^5-T_{ph}^5),\qquad
P_{\mathrm{sub}}=\beta A_{\mathrm{seed}}(T_{ph}^4-T_b^4).
\]

The electron heat capacity uses a smooth superconducting interpolation. Diffusion
uses a Wiedemann–Franz expression with superconducting suppression. Numerical state
reference conductances add negligible relaxation on the simulated time scales.

The normal-domain state uses continuous formation, growth, and retraction terms.
Its finite-size retraction contribution includes

\[
F_{\mathrm{penalty}}=F_0(1-T_b/T_c)^p
\frac{R_c}{R_{\mathrm{domain}}+R_c}.
\]

The critical scale \(R_c\) is evaluated at the prepared bias. This closure can make
larger high-bias domains retract more slowly. The developed domain has no
independent thermal-energy state. The consequences of this phenomenological
closure are described in [validation](validation.md#physical-consistency-and-validation-scope).

There is no operating-mode selector, event timer, or reset switch. The optional
[GL inductance law](current_dependent_inductance.md) replaces the fixed electrical
inductance while retaining these thermal equations and the inferred geometry.

## Principal parameters

| Parameter | Value | Interpretation |
|---|---:|---|
| `Lind` | 38 nH | Fixed device inductance used in this model |
| `width`, `thickness` | 200 nm, 15 nm | Wire geometry |
| `sheetRes`, `Tc` | 165 Ω/square, 12 K | Device inputs |
| Inferred wire length | approximately 400.53 µm | Derived using the existing inductance-per-square approximation |
| `IswBath` | 127.6286 µA at 4.68 K; 13 µA at 11.47 K | Operating-point inputs, not universal NbN constants |
| `alphaIc` | 0.87 | Empirical switching-current temperature dependence |
| `tauEphRef`, `TEphRef` | 2.1 ps, 10 K | Normal-state electron–phonon energy-relaxation reference |
| `ephExponent` | 5 | Retained heat-flow approximation |
| `betaTBC` | 86.8 W m⁻² K⁻⁴ | Substrate heat-flow coefficient |
| `gammaCe`, `gammaCph` | 160 J m⁻³ K⁻²; 2.38 J m⁻³ K⁻⁴ | Heat-capacity coefficients |
| `kappa` | 0.108 W m⁻¹ K⁻¹ | Boundary-model thermal conductivity |
| `Lseed` | 15 nm | Fixed seed length |
| `finiteSizePenalty0`, `penaltyExponent` | 10, 1 | Phenomenological boundary-closure parameters |

The 2.1 ps reference replaces a previous 12 ps assignment that did not distinguish
scattering time from energy-relaxation time. The conversion follows Eq. (1) and
Table III of Sidorova et al., *Physical Review B* **102**, 054501 (2020),
[doi:10.1103/PhysRevB.102.054501](https://doi.org/10.1103/PhysRevB.102.054501).
The cited films differ from this device in thickness and substrate. The adopted
value is a literature-informed estimate, not a measurement of this detector.

The coefficient is computed as

\[
\Sigma=\frac{\gamma_e}{m\tau_{EP,\mathrm{ref}}T_{\mathrm{ref}}^{m-2}},\quad m=5.
\]

The reference time is not the simulated pulse decay time. Superconducting heat
capacity, phonon dynamics, substrate cooling, diffusion, and readout all contribute.

## Optical input

Cases use a 532 nm optical input, `etaAbs=0.1`, and a normalized 5 ps control-pulse
area. The deposited energy is

\[
E_{\mathrm{dep}}=N\eta_{\mathrm{Abs}}hc/\lambda
\simeq 0.233212N\ \mathrm{eV}.
\]

Here \(N\) is an input multiplier. It is not a calibrated absorbed-photon count.
The subcircuit default normalization is overridden explicitly in every case.

The implemented equations and numerical regularizations are authoritative in
[`models/snspd_nbn_v5c.lib`](../models/snspd_nbn_v5c.lib).
