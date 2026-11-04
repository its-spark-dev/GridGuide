"""Read-only sources with content hashes and strictly new output destinations."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


class Sources:
    def __init__(self):
        self.hashes = {}

    def path(self, relative):
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or not str(path.relative_to(ROOT)).startswith(("docs/", "research/", "benchmarks/", "backend/")):
            raise ValueError("Source outside research allowlist")
        self.hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path

    def json(self, relative):
        return json.loads(self.path(relative).read_text())

    def rows(self, relative):
        with gzip.open(self.path(relative), "rt") as stream:
            for line in stream:
                yield json.loads(line)


def save_new(directory, files):
    path = Path(directory).resolve()
    # Never overwrite historical, source, or untracked user content.
    if path.exists():
        raise ValueError("Output directory must not exist")
    if path.is_relative_to(ROOT) and not path.is_relative_to(ROOT/"artifacts"):
        raise ValueError("Generate outside source/evidence directories, then explicitly review/copy")
    path.mkdir(parents=True)
    for name, value in files.items():
        (path/name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n")
