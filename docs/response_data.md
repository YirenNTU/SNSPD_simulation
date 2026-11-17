# Response curves and presentation

The editable 12-slide Keynote and its PDF are in `presentations/`. The deck covers
the external circuit, SNSPD structure and equations, Geiger and near-transition
operation, the experimental overlay, and deposited-energy sweeps.
`SNSPD_equations.tex` contains the equation source.

`data/response/` stores eight CSV traces and `metadata.json`. The metadata records
source hashes, simulation case IDs, deposited energies, and waveform processing.
Each simulation trace maps to a case in `cases/`.

| Plot | Conditions | Interpretation |
|---|---|---|
| `geiger_experiment` | 4.68 K, 1 V supply; simulation uses N = 8 | Peak-aligned overlay; voltage amplitudes are not rescaled |
| `geiger_energy` | 4.68 K, 0.96 Isw, N = 1 and 8 | Nearly saturated output amplitude |
| `calorimetric_energy` | 11.47 K, 0.90 Isw, N = 1, 4, 10, 100 | Nonlinear energy dependence; the low-energy decrease is retained |

Energy labels refer to deposited model energy, $N\eta hc/\lambda$, with fixed
532 nm wavelength and absorption factor 0.1. They do not describe a sweep of
single-photon wavelength. Experimental deposited energy and complete readout
calibration are unavailable, so the overlay is not a matched-energy validation.
The experimental falling edge is broader than the simulated curve.

Simulation traces are baseline-subtracted and interpolated to 0.025 ns spacing.
The experimental average retains its 0.4 ns spacing. The comparison is aligned
at each waveform's peak; energy sweeps are aligned to the optical input.
Full-resolution simulation metrics are retained in `results/reference/`.

Regenerate the three response plots without LTspice:

```sh
python3 scripts/plot_responses.py
```

PNG and PDF exports are written to `results/figures/`. The CSV files are the
canonical plotted traces; duplicate JSON trace arrays and temporary slide-import
presentations are omitted.
