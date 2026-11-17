"""Build or run an earlier Geiger model with the shared external circuit."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from snspdtool.core import locate_ltspice, locate_opamp
from snspdtool.simulation import run_deck


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("bcf", "dynamic"), default="bcf")
    parser.add_argument("--run", action="store_true", help="Execute LTspice after building")
    parser.add_argument("--output", type=Path, default=ROOT / "runs" / "legacy")
    parser.add_argument("--opamp")
    parser.add_argument("--ltspice")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    directory = args.output / args.model
    if (directory / "case.raw").exists() and not args.overwrite:
        raise ValueError("Existing simulation. Use a different --output or --overwrite.")
    opamp = locate_opamp(args.opamp)
    model = {"bcf": "nanowireBCF", "dynamic": "nanowireDynamic"}[args.model]
    directory.mkdir(parents=True, exist_ok=True)
    netlist = f'''* Earlier Geiger model: {model}; explicit low-temperature example.
.include "{(ROOT / 'legacy/snspd_geiger.lib').as_posix()}"
.include "{opamp.as_posix()}"
.param Cshunt=30p Rextra=50 AmpGainCal=1
Xwire N020 0 N012 N024 {model} Tsub=4.68 Jc=42.3G Lind=65n
I1 0 N020 PULSE(0 30u 5n 1p 200p 1p 50n 1)
V1 N001 0 1
.include "{(ROOT / 'circuits/amplifier_chain.inc').as_posix()}"
.include "{(ROOT / 'circuits/bias_tee_and_load.inc').as_posix()}"
.tran 0 30n 0 0.5p
.options plotwinsize=0 numdgt=15 method=gear
.save V(N011) V(N012) V(N024) I(wire:L1)
.end
'''
    (directory / "case.cir").write_text(netlist)
    if args.run:
        run_deck(directory, locate_ltspice(args.ltspice), opamp, f"legacy_{args.model}")
    print(directory / "case.cir")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError, RuntimeError) as error:
        sys.exit(str(error))
