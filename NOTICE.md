# Dependency and attribution notes

The detector implementation is the project's existing v5c compact-model candidate
with the documented electron–phonon reference correction and current-sensing
revision. Existing source comments and scientific attribution are retained.
The runner, analysis utilities, and package documentation accompany that snapshot.

LTspice is an external dependency. Its standard `opamp.sub` is loaded from the
user's installation and is not redistributed in this repository. Its hash is
recorded for each simulation. Python dependencies retain their respective licenses.

This snapshot does not assign a new project-wide open-source license or replace
any upstream terms. The scientific reference and validation status are described
in `docs/model.md` and `docs/validation.md`.
