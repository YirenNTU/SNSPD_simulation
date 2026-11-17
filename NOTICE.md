# Dependency and attribution notes

The detector implementation is the project's existing v5c compact-model candidate
with the documented electron–phonon reference correction and current-sensing
revision. Existing source comments and scientific attribution are retained.
The runner, analysis utilities, and package documentation accompany that snapshot.

The circuit figure's SNSPD geometry is derived from `snspdWithPhotonPort.asy`
in the installed `snspd-spice` library. Its LINE coordinates match that library's
upstream copy. The geometry and original pin metadata are retained in
`symbols/snspd_geometry.json`; current-model labels follow subcircuit pin order.
The upstream MIT license is reproduced in `symbols/LICENSE.snspd-spice` and
applies to the reused symbol geometry.

LTspice is an external dependency. Its standard `opamp.sub` is loaded from the
user's installation and is not redistributed in this repository. Its hash is
recorded for each simulation. Python dependencies retain their respective licenses.

This snapshot does not assign a new project-wide open-source license or replace
any upstream terms. The scientific reference and validation status are described
in `docs/model.md` and `docs/validation.md`.
