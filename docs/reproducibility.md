# Reproducibility and publication

## Reference configuration

All operating conditions are stored in `cases/`. Netlists are generated from a
single detector model and two shared external-circuit files. Absolute installation
paths appear only in generated files under `runs/`; they are not stored in source.

`provenance/source_manifest.json` records source model, schematic, and deck hashes.
The latest model's header is condensed; active SPICE lines and parameter defaults
are unchanged. `provenance/legacy_manifest.json` records the earlier subcircuits,
native BCF schematic, and symbol. Large raw waveforms are not redistributed.

`results/reference/` contains the original numerical measurements. The packaging
smoke check regenerates seven representative cases and compares their peaks,
recovery, event counts, energy normalization, and electrical residuals with those
references. Its result is recorded in `provenance/packaging_verification.json`.

Regression tolerances are 0.2% for peak amplitude, with a 2 µV absolute floor,
and 2 ps for resistance recovery and output fall time. The integral KVL residual
must remain below 0.5%; optical-energy normalization must remain within 0.1%.
These are reproducibility tolerances, not experimental uncertainties.

The recorded environment uses Python 3.12.3, LTspice 17.2.4 for macOS, and the
dependency versions in `requirements.txt`. Execution has been checked on macOS. Windows path discovery
is included but has not been validated by a Windows simulation run.

## Repeating or extending a study

1. Select a named case or copy its configuration to a new ID.
2. Preserve temperature, bias, optical normalization, and readout settings in the record.
3. Run the case and retain `case.json`, `case.cir`, `run_metadata.json`, and `metrics.json`.
4. Compare like-for-like observables. Do not identify resistance reset, current
   recovery, output fall time, and second-zero timing as the same measurement.
5. Label any updated baseline separately; do not overwrite reference results
   merely to pass a regression check.

## Regression commands

The first two commands run the fixed-inductance reference cases; the next two
run the [GL option](current_dependent_inductance.md). Keep separate output
directories for each configuration.

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

`--compare` applies the strict reference tolerances above. `--check-behavior`
checks event classification, recovery, guards, optical-energy normalization, and
the flux-integral KVL residual, allowing amplitudes and timing to change.
`verify_inductance.py` additionally checks Geiger saturation within 1% from N=1
to N=8, increasing calorimetric peaks over N=10, 20, 50, 100, and step convergence
within 0.2% in amplitude and 2 ps in falling time.

The [verification record](../provenance/inductance_verification.json) contains
results and source hashes. It supplements the original release references;
the [validation page](validation.md#current-dependent-inductance) summarizes
the findings. To plot an existing run, use `python3 snspd.py plot` with its case ID and
output directory; analysis and plotting read the saved `case.json`.

## Release verification

The release includes the latest model, earlier Geiger models, external circuit,
32 case definitions, reference metrics, circuit figures, response CSV files,
and the final Keynote/PDF presentation. Temporary builders, duplicate trace JSON,
intermediate slide decks, local run outputs, and older experimental model variants
are excluded. LTspice and its `opamp.sub` remain external dependencies.

```sh
python3 scripts/package.py --output runs/SNSPD_simulation_v0.1.2.zip
python3 scripts/package.py --verify runs/SNSPD_simulation_v0.1.2.zip
```

`MANIFEST.json` lists every packaged file, byte size, and SHA-256 digest.
`provenance/release_verification.json` records the v0.1.1 numerical checks and
the v0.1.2 attribution update. Model equations are unchanged between these versions.

## Git publication

This directory is an independent repository. The surrounding research project is
not included. Generated waveforms, local paths, and simulation output directories
are excluded by `.gitignore`.

No remote repository is assumed. After selecting a destination:

```sh
git remote add origin REMOTE_URL
git push -u origin main
git push origin v0.1.2
```

The release ZIP contains source files without Git history. After extracting it,
initialize and commit the directory with Git before configuring a remote.
