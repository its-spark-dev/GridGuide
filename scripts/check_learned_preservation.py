"""Read-only preservation check for the new, isolated learned-dispatch study."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def check():
    record = json.loads((ROOT/"docs/learned-dispatch/PRESERVATION.json").read_text())
    for relative, expected in record["files"].items():
        if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Prior artifact changed: {relative}")
    readme = (ROOT/"README.md").read_text()
    original = re.sub(r"<!-- learned-dispatch:start -->\n.*?<!-- learned-dispatch:end -->\n\n", "", readme, flags=re.S)
    if hashlib.sha256(original.encode()).hexdigest() != record["readme_sha256"]:
        raise ValueError("README changed beyond the explicitly added learned-dispatch section")
    return dict(status="PASS", files=len(record["files"]), baseline=record["base_commit"],
                scope=record["scope"])


if __name__ == "__main__":
    print(json.dumps(check(), sort_keys=True))
