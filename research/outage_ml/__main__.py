from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import run, save
from .sources import acquire, digest


def main() -> None:
    parser = argparse.ArgumentParser(description="ML Lab II source audit; no training command")
    parser.add_argument("command", choices=["acquire", "audit", "report", "verify"])
    parser.add_argument("--cache", type=Path, default=Path("data/external/outage-ml/audit-v1"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, default=Path("docs/outage-ml/evidence/source-audit.json"))
    args = parser.parse_args()
    if args.command == "acquire":
        save(acquire(args.cache), args.output)
    elif args.command == "audit":
        save(run(args.cache), args.output)
    elif args.command == "report":
        from .report import render, table_report
        args.output.mkdir(parents=True, exist_ok=True)
        render(args.evidence, args.output / "figures")
        (args.output / "MEASURED.md").write_text(table_report(json.loads(args.evidence.read_text())))
    else:
        manifest = json.loads((args.output / "figures/manifest.json").read_text())
        if digest(args.evidence.read_bytes()) != manifest["source_sha256"]:
            raise ValueError("Figure evidence changed")
        for name, sha in manifest["files"].items():
            if digest((args.output / "figures" / name).read_bytes()) != sha:
                raise ValueError("Figure changed")
        from .report import table_report
        if (args.output / "MEASURED.md").read_text() != table_report(json.loads(args.evidence.read_text())):
            raise ValueError("Measured report changed")
        print("Committed presentation hashes and measured table verified")


if __name__ == "__main__":
    main()
