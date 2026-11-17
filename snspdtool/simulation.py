"""LTspice batch execution and dependency records."""
import hashlib
import json
import platform
import subprocess
from pathlib import Path


def run_deck(directory, executable, opamp, case_id):
    directory = Path(directory).resolve()
    for name in ("case.log", "case.raw", "case.op.raw"):
        (directory / name).unlink(missing_ok=True)
    process = subprocess.run(
        [str(executable), "-b", str(directory / "case.cir")],
        cwd=directory, capture_output=True,
    )
    log_path = directory / "case.log"
    log = log_path.read_bytes().decode("utf-16-le", errors="replace") if log_path.exists() else ""
    if process.returncode or "Total elapsed time:" not in log or not (directory / "case.raw").exists():
        raise RuntimeError(f"{case_id} failed: {log[-1500:]}")
    metadata = {
        "case_id": case_id,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ltspice_executable": Path(executable).name,
        "opamp_sha256": hashlib.sha256(Path(opamp).read_bytes()).hexdigest(),
        "deck_sha256": hashlib.sha256((directory / "case.cir").read_bytes()).hexdigest(),
    }
    (directory / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
