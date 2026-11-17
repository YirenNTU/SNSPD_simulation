# SNSPD electrothermal simulation

**Version 0.1.0 · Research snapshot · 17 November 2026**

This package combines an NbN electrothermal detector model, a complete bias-tee
and amplifier circuit, and reproducible Geiger and near-transition calorimetric
tests. Both regimes use the same detector equations; operating temperature,
bias, and optical input are specified per case.

The package preserves the audited model without changing its physical parameters.
It is a documented simulation baseline, not a fully validated detector model.

## Scope and status

| Component | Included behavior | Validation status |
|---|---|---|
| Geiger regime, 4.68 K | Triggering, amplitude saturation, and recovery | The tested 30 pF circuit recovers; an 800 ns observation contains one event. |
| Near-transition regime, 11.47 K | Energy-dependent response and bias-dependent resistance recovery | Energy dependence remains. Output peak is non-monotonic at low input energy. |
| External circuit | Bias resistor, bias-tee inductance and capacitance, RF shunts, series return resistor, and amplifier chain | Explicit circuit variants are retained and identified. |
| Output timing | Baseline-subtracted 90–10% fall time | A substantial increase with bias is not reproduced in the tested full circuits. |

The complete reference set contains **7 Geiger and 25 calorimetric cases**.
See [validation](docs/validation.md) for measured quantities, convergence, and limitations.

## Circuit schematics

![Detector, bias tee, and RF readout](docs/figures/circuit_overview.png)

The [circuit documentation](docs/circuit.md) includes the connections within all
four amplifier stages. Component names, values, and node labels match the netlists.
The [two-page PDF](docs/figures/circuit_schematics.pdf) contains both schematics;
SVG and PNG versions and the rendering script are included.

## Quick start

Requirements: Python 3.12, LTspice, and the standard `opamp.sub` supplied with LTspice.
The recorded Python dependency versions are in `requirements.txt`.

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 snspd.py check
python3 snspd.py list
python3 snspd.py run --smoke --jobs 2 --compare
```

On Windows, activate the environment using `.venv\Scripts\activate` and use `python`
in place of `python3`. The runner locates common LTspice installations. Explicit paths
can be supplied with `--ltspice` and `--opamp`, or through `LTSPICE_EXECUTABLE` and
`LTSPICE_OPAMP_SUB`.

The seven-case smoke set checks both operating regimes and a second readout
configuration. It compares regenerated waveforms with stored reference measurements.
Full sweeps are explicit:

```sh
python3 snspd.py run --group geiger --compare
python3 snspd.py run --group calorimetric --compare
```

Each case produces its netlist, LTspice output, dependency metadata, and measured
results under `runs/<case-id>/`. Existing simulations are preserved unless
`--overwrite` is supplied. Use a different `--output` directory for a separate run.

```sh
python3 snspd.py build --case geiger_c30_high_dt005
python3 snspd.py analyze --case geiger_c30_high_dt005 --compare
python3 snspd.py plot --case geiger_c30_high_dt005
python3 -m unittest discover -s tests -v
```

## Package contents

| Path | Purpose |
|---|---|
| `models/` | Shared continuous electrothermal detector model |
| `circuits/` | Bias-tee/load network and amplifier chain |
| `cases/` | Explicit operating conditions and circuit variants |
| `snspdtool/`, `snspd.py` | Netlist generation, execution, analysis, and regression comparison |
| `results/reference/` | Audited numerical measurements |
| `results/figures/` | Reference behavior plots |
| `provenance/` | Source hashes, circuit-value checks, and packaging verification |
| `docs/` | Model equations, parameter definitions, circuit topology, and validation scope |
| `docs/figures/`, `scripts/draw_circuit.py` | Circuit schematics and their reproducible renderer |

## Documentation

- [Model and parameter definitions](docs/model.md)
- [External circuit](docs/circuit.md)
- [Validation and known limitations](docs/validation.md)
- [Reproducibility and publication](docs/reproducibility.md)
- [Dependency and attribution notes](NOTICE.md)

Generated `.raw` files are excluded from version control. No experimental waveform
data are included. Reference plots show simulation results only.
