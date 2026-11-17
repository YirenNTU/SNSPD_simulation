"""Build or verify a source release with a complete SHA-256 file manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from snspdtool import __version__

EXCLUDED_DIRS = {".git", ".venv", "__pycache__", "runs"}
EXCLUDED_SUFFIXES = {".pyc", ".raw", ".log", ".zip", ".bundle"}


def source_files():
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if any(part.startswith(".") and part != ".gitignore" for part in relative.parts):
            continue
        if relative.as_posix() == "MANIFEST.json":
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES or not path.is_file():
            continue
        if path.is_symlink():
            raise ValueError(f"Release source must not be a symlink: {relative}")
        yield path


def verify(archive):
    with ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive entries")
        manifests = [name for name in names if name.endswith("/MANIFEST.json")]
        if len(manifests) != 1:
            raise ValueError("Expected one file manifest")
        manifest_name = manifests[0]
        prefix = manifest_name.removesuffix("MANIFEST.json")
        manifest = json.loads(bundle.read(manifest_name))
        expected = {prefix + path for path in manifest["files"]} | {manifest_name}
        if set(names) != expected:
            raise ValueError("Archive membership differs from manifest")
        for name, record in manifest["files"].items():
            payload = bundle.read(prefix + name)
            if len(payload) != record["bytes"] or hashlib.sha256(payload).hexdigest() != record["sha256"]:
                raise ValueError(f"File integrity check failed: {name}")
        return len(manifest["files"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "runs" / f"SNSPD_simulation_v{__version__}.zip")
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        print(f"Verified {verify(args.verify)} files in {args.verify}")
        return
    files = list(source_files())
    prefix = f"SNSPD_simulation-v{__version__}/"
    manifest = {"version": __version__, "files": {}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", ZIP_DEFLATED) as bundle:
        for path in files:
            name = path.relative_to(ROOT).as_posix()
            payload = path.read_bytes()
            manifest["files"][name] = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
            bundle.writestr(prefix + name, payload)
        bundle.writestr(prefix + "MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    print(f"Packaged and verified {verify(args.output)} files: {args.output}")


if __name__ == "__main__":
    main()
