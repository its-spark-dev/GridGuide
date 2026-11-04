"""Check baseline files without opening any source data; historical checks stay intact."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    record = json.loads((ROOT/"docs/research/ml-opportunity/PRESERVATION.json").read_text())
    failures = [p for p, digest in record["files"].items()
                if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest() != digest]
    tree = subprocess.check_output(["git", "ls-tree", "-r", "HEAD", "data"], cwd=ROOT, text=True)
    blobs = {line.split("\t", 1)[1]:line.split("\t", 1)[0].split()[2] for line in tree.splitlines()}
    if blobs != record["data_git_blobs_only"]:
        failures.append("Tracked data Git object identities")
    if failures:
        raise SystemExit("Preservation mismatch: "+", ".join(failures))
    print(json.dumps(dict(preserved_files=len(record["files"]), data_git_objects=len(blobs),
                          raw_data_opened=False, baseline=record["baseline"])))


if __name__ == "__main__":
    main()
