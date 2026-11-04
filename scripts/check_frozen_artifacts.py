"""Hash-only preservation check; does not rerun historical experiments."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check():
    counts = {}
    records=json.loads((ROOT/'docs/research/phase8/PRESERVED_HASHES.json').read_text())
    for name,expected in records.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
    counts['G2_G3_files']=len(records)
    for phase in (5,6,7):
        path = ROOT/f'docs/research/phase{phase}/CHECKSUMS.json'
        records = json.loads(path.read_text())
        for name, expected in records.items():
            assert hashlib.sha256((path.parent/name).read_bytes()).hexdigest() == expected, name
        counts[f'G{phase}_files'] = len(records)
    return counts


if __name__ == '__main__': print(json.dumps(check(), sort_keys=True))
