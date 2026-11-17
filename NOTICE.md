# Dependency and attribution notes

The main detector implementation is the project's v5c compact model, including
the electron–phonon reference correction and current-sensing revision.
The earlier `nanowireBCF` and `nanowireDynamic` implementations in `legacy/`
derive from the `snspd-spice` library and retain the project's local modifications.
Their upstream MIT license is reproduced in `symbols/LICENSE.snspd-spice`.

The circuit figure's SNSPD geometry is derived from `snspdWithPhotonPort.asy`
in the installed `snspd-spice` library. Its LINE coordinates match that library's
upstream copy. The geometry and original pin metadata are retained in
`symbols/snspd_geometry.json`; current-model labels follow subcircuit pin order.
The upstream MIT license is reproduced in `symbols/LICENSE.snspd-spice` and
applies to the reused symbol geometry and upstream library code.

LTspice is an external dependency. Its standard `opamp.sub` is loaded from the
user's installation and is not redistributed in this repository. Its hash is
recorded for each simulation. Python dependencies retain their respective licenses.

This package does not assign a new project-wide open-source license or replace
any upstream terms. The scientific reference and validation status are described
in `docs/model.md` and `docs/validation.md`.
