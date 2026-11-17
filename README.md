# SNSPD simulation

Version 0.1.2 · 17 November 2026

NbN detector models with a shared bias-tee and amplifier circuit, numerical
reference cases, experimental response data, and an editable presentation.

The original SNSPD SPICE models are from **Berggren et al. (2018)**,
[“A superconducting nanowire can be modeled by using SPICE,”
*Superconductor Science and Technology* **31**, 055010](https://doi.org/10.1088/1361-6668/aab149),
and the accompanying [MIT QNN `snspd-spice` code](https://github.com/qnngroup/snspd-spice).
This package contains locally modified versions and a subsequent electrothermal
extension. Please cite the original paper when using these models; the
[attribution notes](NOTICE.md) identify the source and project modifications.
[BibTeX](docs/references.bib) and [citation metadata](CITATION.cff) are included.

## Models

| Model | Location | Scope |
|---|---|---|
| Simplified Geiger model (`nanowireBCF`) | `legacy/snspd_geiger.lib` | Inductive flux, hotspot-current plateau, and switching thresholds |
| Earlier dynamic Geiger model (`nanowireDynamic`) | `legacy/snspd_geiger.lib` | Hotspot-boundary evolution and a restoration switch |
| Latest electrothermal model (`nanowireElectrothermal_NbN_v5c`) | `models/snspd_nbn_v5c.lib` | Shared equations for Geiger and near-transition calorimetric responses |

The latest model couples current, seed electron and phonon temperatures, and
normal-domain resistance. Operating conditions determine the response; there is
no Geiger/calorimetric selector. Its reference set contains 7 Geiger and
25 calorimetric cases. The earlier model bodies and latest model equations are
preserved in this release.

## Quick start

Requirements: Python 3.12, LTspice, and its standard `opamp.sub`.

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 snspd.py check
python3 snspd.py list
python3 snspd.py run --smoke --jobs 2 --compare
```

On Windows, activate with `.venv\Scripts\activate` and use `python`.
Installation paths can be set with `--ltspice` and `--opamp`, or the environment
variables `LTSPICE_EXECUTABLE` and `LTSPICE_OPAMP_SUB`.

```sh
python3 scripts/run_legacy.py --model bcf --run
python3 scripts/run_legacy.py --model dynamic --run
python3 snspd.py run --group geiger --compare
python3 snspd.py run --group calorimetric --compare
python3 snspd.py plot --case geiger_c30_high_dt005
python3 scripts/plot_responses.py
python3 -m unittest discover -s tests -v
```

Results go to `runs/`. Existing simulations require `--overwrite` or a different
`--output` directory. Use `build` instead of `run` to prepare the latest model's
netlists without executing LTspice. See the [legacy guide](legacy/README.md)
for earlier-model defaults and examples.

## Contents

| Path | Contents |
|---|---|
| `models/`, `legacy/` | Latest model; earlier Geiger models, native schematic, and symbol |
| `circuits/`, `cases/` | Shared external circuit and 32 latest-model configurations |
| `snspd.py`, `snspdtool/`, `scripts/`, `tests/` | Execution, analysis, plotting, packaging, and checks |
| `results/reference/` | Numerical measurements and convergence records |
| `data/response/`, `results/figures/` | Experimental/simulated CSV curves, provenance, and plots |
| `presentations/` | Final 12-slide Keynote, PDF, and LaTeX equation source |
| `docs/`, `docs/figures/` | Circuit topology, equations, structure diagrams, and validation |
| `symbols/`, `provenance/` | Symbol geometry, upstream license, source hashes, and verification |

![External circuit](docs/figures/concept_external_circuit.png)

## Status

The tested 30 pF Geiger cases show triggering, amplitude saturation, and recovery.
Near-transition responses remain energy-dependent, with slower internal resistance
recovery at higher bias. The tested amplifier-output fall time does not reproduce
a substantial bias dependence, and low-energy peak amplitude is non-monotonic.

The experimental overlay is peak-aligned without amplitude rescaling. Experimental
deposited energy is unavailable; it is a waveform comparison, not a matched-energy
validation. Numerical regression checks establish reproducibility, not full
physical validation.

- [Model equations and parameters](docs/model.md)
- [Original models and project extensions](docs/model_lineage.md)
- [SNSPD structure and functions](docs/snspd.md)
- [External circuit](docs/circuit.md) and [concept figures](docs/concepts.md)
- [Implementation reference](docs/snspd_implementation.md)
- [Validation and limitations](docs/validation.md)
- [Response curves and presentation](docs/response_data.md)
- [Reproducibility and release verification](docs/reproducibility.md)
- [Dependencies and attribution](NOTICE.md)

The ZIP includes a file-by-file SHA-256 manifest. Raw LTspice waveforms, temporary
builders, duplicate slide imports, and unrelated historical variants are excluded.
`opamp.sub` is loaded from the user's LTspice installation.
