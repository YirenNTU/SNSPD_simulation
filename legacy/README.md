# Earlier Geiger models

`snspd_geiger.lib` contains the project's earlier `nanowireBCF` and
`nanowireDynamic` subcircuits, extracted from `LTspice_model/snspd.lib`.
Their subcircuit bodies, equations, and parameter defaults are unchanged.

| Model | Representation | Intended use |
|---|---|---|
| `nanowireBCF` | Nonlinear inductive flux, hotspot-current plateau, current and voltage switches | Simplified Geiger pulse model |
| `nanowireDynamic` | Nonlinear inductive flux, hotspot-resistance integrator, superconducting restoration switch | Earlier Geiger boundary-growth model |
| `nanowireElectrothermal_NbN_v5c` in `../models/` | Fixed kinetic inductance, electron and phonon temperatures, continuous domain growth and retraction | Shared Geiger and near-transition model |

The earlier models do not implement the latest model's two-temperature optical
energy balance. Their gate pulses are trigger controls, not calibrated deposited
energies. Their parameters should not be transferred to the latest model by name alone.

## Run an example

From the package root:

```sh
python3 scripts/run_legacy.py --model bcf --run
python3 scripts/run_legacy.py --model dynamic --run
```

Omit `--run` to generate a netlist only. Installation paths can be supplied with
`--ltspice` and `--opamp`. Results are written under `runs/legacy/<model>/`.

These examples use the shared 30 pF external circuit, 1 V bias supply,
65 nH inductance parameter, 4.68 K bath, and `Jc=42.3G` (126.9 µA switching current).
The 30 µA gate pulse starts at 5 ns. The examples demonstrate executable legacy
models; they are separate from the latest model's 32-case regression set.
The local BCF source defaults to 11.37 K and `Jc=4.2G`; the example explicitly
overrides both for low-temperature operation.

## Original schematic

`snspd-bcf.asc` retains the original circuit and settings. Only its library
include filename and the symbol's `ModelFile` were changed to local paths.
Its historical operating point and initialization are not the example above.
Open it with LTspice and keep the supplied `.asy` beside it.
The archived 1 V supply implies about 100 µA, above the current BCF source
default of 12.6 µA. That historical combination is not a valid low-temperature
benchmark; use the explicit example overrides for the packaged Geiger check.

The original `SNSPD_dynamic.asc` differed from `snspd-bcf.asc` only in its title.
Both inherited `nanowireBCF` from the same symbol. The duplicate is omitted;
use `--model dynamic` to select `nanowireDynamic` explicitly.

Source and extracted-body hashes are in `../provenance/legacy_manifest.json`.
The upstream license is retained in `../symbols/LICENSE.snspd-spice`.
