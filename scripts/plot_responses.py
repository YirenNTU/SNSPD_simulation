"""Reproduce the presentation response plots from the packaged CSV traces."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data/response")
    parser.add_argument("--output", type=Path, default=ROOT / "results/figures")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((args.data / "metadata.json").read_text())
    energies = {row["name"]: row["energy_eV"] for row in metadata["simulations"]}
    groups = {
        "geiger_experiment": ["geiger_comparison", "experiment"],
        "geiger_energy": ["geiger_energy_low", "geiger_energy_high"],
        "calorimetric_energy": [f"calorimetric_energy_n{n}" for n in (1, 4, 10, 100)],
    }
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 15,
                         "axes.labelsize": 17, "legend.fontsize": 13,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42})
    colors = ["#245C85", "#C47829", "#5B8B76", "#915B9F"]
    for name, traces in groups.items():
        comparison = name == "geiger_experiment"
        fig, ax = plt.subplots(figsize=(10, 5.25))
        ax.axhline(0, color="#CCD3D9", lw=0.8)
        for i, trace in enumerate(traces):
            data = np.loadtxt(args.data / f"{trace}.csv", delimiter=",", skiprows=1)
            label = ("Simulation" if i == 0 else "Experiment (average)") if comparison else f"{energies[trace]:.3g} eV"
            ax.plot(data[:, 0], data[:, 1], color=colors[i], lw=2.8,
                    ls="--" if name == "geiger_energy" and i == 1 else "-",
                    marker="o" if trace == "experiment" else None, ms=3.5, label=label)
        ax.set_xlim((-3, 12) if comparison else (-1, 10))
        ax.set_xlabel("Time from output peak (ns)" if comparison else "Time from optical input (ns)")
        ax.set_ylabel("Output voltage (mV)")
        ax.legend(frameon=False, title=None if comparison else "Deposited energy")
        ax.grid(axis="y", alpha=0.16)
        fig.tight_layout()
        for extension in ("png", "pdf"):
            fig.savefig(args.output / f"{name}.{extension}", dpi=180)
        plt.close(fig)


if __name__ == "__main__":
    main()
