"""Canonical immutable evidence I/O; timings intentionally live outside numeric hashes."""
from __future__ import annotations

import gzip
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261104


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = b''.join(canonical(row) + b'\n' for row in rows)
    with path.open('xb') as stream:
        stream.write(gzip.compress(payload, mtime=0))


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]


def source_hashes() -> dict[str, str]:
    paths = list((ROOT/'research/ml_lab').glob('*.py'))
    paths += [ROOT/'benchmarks'/f'{name}.py' for name in ('contracts','policies','metrics','validation')]
    paths += [ROOT/'backend/contracts.py', ROOT/'backend/risk_rules.py', ROOT/'requirements-ml.lock',
              ROOT/'docs/planning/V1_2_0_IMPLEMENTATION.md']
    # Presentation and CLI dispatch do not affect frozen numerical evaluation.
    return {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(paths)
            if p.name not in ('report.py', '__main__.py')}


def revision() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def require_committed(paths: list[Path]) -> str:
    for path in paths:
        relative = str(path.resolve().relative_to(ROOT))
        actual = subprocess.check_output(['git', 'show', f'HEAD:{relative}'], cwd=ROOT)
        if actual != path.read_bytes():
            raise ValueError(f'Not committed at current HEAD: {relative}')
    return revision()


def environment() -> dict:
    names = ('numpy','scipy','scikit-learn','joblib','threadpoolctl','pydantic','matplotlib')
    return {'python': platform.python_version(), 'system': platform.system(),
            'machine': platform.machine(), 'processor': platform.processor(),
            'cpu_count': os.cpu_count(),
            'packages': {n: importlib.metadata.version(n) for n in names},
            'thread_limit': 1}


def validate_hashes(base: Path, hashes: dict[str, str]) -> None:
    for relative, expected in hashes.items():
        path = (base/relative).resolve()
        if not path.is_relative_to(base.resolve()) or file_hash(path) != expected:
            raise ValueError(f'Artifact hash mismatch: {relative}')
