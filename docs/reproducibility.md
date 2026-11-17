# Reproducibility and publication

## Reference configuration

All operating conditions are stored in `cases/`. Netlists are generated from a
single detector model and two shared external-circuit files. Absolute installation
paths appear only in generated files under `runs/`; they are not stored in source.

`provenance/source_manifest.json` records the source model, schematic, and audited
deck hashes. The packaged model adds a descriptive header; its equations and
parameter defaults are unchanged. Original schematics and large raw waveforms are
not redistributed.

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

## Git publication

This directory is an independent repository. The surrounding research project is
not included. Generated waveforms, local paths, and simulation output directories
are excluded by `.gitignore`.

No remote repository is assumed. After selecting a destination:

```sh
git remote add origin REMOTE_URL
git push -u origin main
git push origin v0.1.0
```

If the repository is restored from the supplied Git bundle, its initial `origin`
points to that bundle. Replace it with `git remote set-url origin REMOTE_URL` before
pushing. No public deployment or repository visibility change is performed by the
simulation tools.
