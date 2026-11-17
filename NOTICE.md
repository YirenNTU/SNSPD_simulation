# Dependency and attribution notes

## Original model and paper

The original curve-fitting and dynamic SNSPD SPICE models were developed by
Karl K. Berggren, Qing-Yuan Zhao, Nathnael Abebe, Minjie Chen,
Prasana Ravindran, Adam McCaughan, and Joseph C. Bardin:

**“A superconducting nanowire can be modeled by using SPICE.”**
*Superconductor Science and Technology* **31**(5), 055010 (2018).
[DOI: 10.1088/1361-6668/aab149](https://doi.org/10.1088/1361-6668/aab149).

The authors were affiliated with MIT and the University of Massachusetts Amherst.
The accompanying source is [qnngroup/snspd-spice](https://github.com/qnngroup/snspd-spice).
The [MIT-hosted manuscript](https://qnn-rle.mit.edu/wp-content/uploads/2020/02/A_Superconducting_Nanowire_can_be_Modeled_by_Using_SPICE.pdf)
includes the model code in Supplementary Appendix F. Cite the paper when using
the original modeling framework, and identify this repository and commit when
using its modifications or numerical results. A [BibTeX entry](docs/references.bib)
is provided.

## Project modifications

The `nanowireBCF` and `nanowireDynamic` implementations in `legacy/` are locally
modified derivatives of the original library. They retain device-parameter
changes and, in the dynamic model, an optional geometric seed. The packaged
bodies preserve the local source; they are not unmodified upstream releases.

The latest `nanowireElectrothermal_NbN_v5c` implementation extends that modeling
framework with a coupled electron/phonon seed, a continuous domain-resistance
closure, and a common set of equations for the two operating regimes. Its fixed
inductance, parameters, external readout circuit, analysis, and calibration choices
are documented in this project. These additions should not be attributed to the
2018 paper as published equations or validated results. The electron–phonon
reference has its separate citation in [the model documentation](docs/model.md).

## Code, symbol, and dependency licenses

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
