"""Build/inspect a minimal Phase 1 catalog archive; not the future hosted release.

Exact file allowlist, content hashes, symlink rejection and schema validation are
publication checks. The original repository and its history remain unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.scenarios import CATALOG_SHA256, prepare_synthetic

ALLOWLIST = (
    "backend/__init__.py", "backend/contracts.py", "backend/risk_rules.py",
    "backend/runtime.py", "backend/scenarios.py", "backend/synthetic_api.py",
    "data/synthetic/catalog.json", "data/synthetic/README.md",
    "requirements-synthetic.txt", "docs/research/phase1/ARTIFACT_README.md",
    "THIRD_PARTY_NOTICES.md",
)
MANIFEST = "ARTIFACT_MANIFEST.json"
MAX_BYTES = 2_000_000


def approved_files(root: Path) -> dict[str, bytes]:
    root = root.resolve()
    result = {}
    for name in ALLOWLIST:
        path = root / name
        if any(p.is_symlink() for p in (path, *path.parents) if p != root and root in p.parents):
            raise ValueError("Publication input must not be a symlink")
        if not path.is_file() or not path.resolve().is_relative_to(root) or path.stat().st_size > MAX_BYTES:
            raise ValueError("Invalid publication input")
        result[name] = path.read_bytes()
    if hashlib.sha256(result["data/synthetic/catalog.json"]).hexdigest() != CATALOG_SHA256:
        raise ValueError("Publication catalog does not match the approved pin")
    prepare_synthetic(root / "data/synthetic/catalog.json")
    return result


def inspect_artifact(path: Path, root: Path = ROOT) -> dict:
    expected = approved_files(root)
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        if len(names) != len(set(names)) or set(names) != set(ALLOWLIST) | {MANIFEST}:
            raise ValueError("Unexpected, duplicate or missing artifact entry")
        if sum(i.file_size for i in infos) > MAX_BYTES:
            raise ValueError("Artifact exceeds its bounded scope")
        for info in infos:
            name = PurePosixPath(info.filename)
            if name.is_absolute() or ".." in name.parts or stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError("Unsafe artifact entry")
        expected_hashes = {name: hashlib.sha256(content).hexdigest() for name, content in expected.items()}
        manifest = json.loads(archive.read(MANIFEST))
        if manifest != {"version": "phase1-catalog-artifact-v1", "files": expected_hashes}:
            raise ValueError("Artifact manifest mismatch")
        for name, content in expected.items():
            if archive.read(name) != content:
                raise ValueError("Artifact content differs from reviewed inputs")
    return {"version": "phase1-artifact-check-v1", "passed": True, "files": len(names),
            "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "catalog_sha256": CATALOG_SHA256,
            "scope": "Catalog API only; no frontend, source datasets, Git history, research observations or provider code. Not a repository-history remediation or a license grant."}


def build_artifact(path: Path, root: Path = ROOT) -> dict:
    root = root.resolve()
    # Avoid overwriting source, prior artifacts or following destination symlinks.
    if path.resolve().is_relative_to(root) and not path.resolve().is_relative_to(root / "artifacts"):
        raise ValueError("Artifact output must be outside source or under ignored artifacts/")
    files = approved_files(root)
    files[MANIFEST] = (json.dumps({"version": "phase1-catalog-artifact-v1", "files": {
        name: hashlib.sha256(content).hexdigest() for name, content in files.items()}}, sort_keys=True, indent=2) + "\n").encode()
    with path.open("xb") as output:
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in sorted(files.items()):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, content)
    return inspect_artifact(path, root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--build", type=Path, help="Create a new catalog-only archive")
    group.add_argument("--inspect", type=Path, help="Check against the current reviewed allowlist and bytes")
    args = parser.parse_args()
    report = build_artifact(args.build) if args.build else inspect_artifact(args.inspect)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
