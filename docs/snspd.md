# SNSPD structure and functions

The latest model represents the nanowire as a kinetic inductance in series with
a time-dependent resistance. Thermal states determine the resistance, while
current redistribution changes the Joule heating.

![SNSPD electrical and thermal feedback](figures/concept_snspd.png)

[Vector SVG](figures/concept_snspd.svg) · [Concept PDF](figures/model_concepts.pdf)

| Component or state | Function |
|---|---|
| Kinetic inductance, $L_k$ | Limits how quickly detector current can change; fixed in this model |
| Seed electrons, $T_e$ | Receive optical power and seed Joule heating; lose heat to phonons and the surrounding wire |
| Seed phonons, $T_{ph}$ | Exchange heat with electrons and transfer heat to the substrate |
| Seed resistance, $R_{seed}$ | Changes continuously with temperature and current |
| Normal-domain resistance, $R_d$ | Tracks domain formation, growth, and retraction beyond the seed |
| External circuit | Diverts current during the resistive event and shapes the measured pulse |

The four dynamic states are current, two seed temperatures, and domain resistance.
The domain has no independent thermal-energy state; its Joule diagnostic is not
added to the seed heat balance. Geiger and near-transition cases use the same
equations with different bath temperatures, bias currents, and optical inputs.

The [model reference](model.md) is the equation and parameter reference.
The [implementation guide](snspd_implementation.md) maps those quantities to
SPICE elements. The [earlier Geiger models](../legacy/README.md) use separate,
simpler switching and boundary-growth representations.
