"""Manifest integrity and recursive artifact boundaries, independent of the checkout."""
import hashlib
import json
from pathlib import Path, PurePosixPath

FORBIDDEN = {'.git', '.env', 'raw', 'processed', 'external', 'node_modules', '.venv', '__pycache__'}


def verify_tree(root: Path):
    manifest = json.loads((root/'PUBLIC_MANIFEST.json').read_text())
    if set(manifest) != {'version','files'} or manifest['version'] != 'public-package-v1':
        raise ValueError('Unsupported public manifest')
    expected = manifest['files']
    found = set()
    for p in root.rglob('*'):
        if p.is_symlink(): raise ValueError('Symlink in public distribution')
        if p.is_file(): found.add(p.relative_to(root).as_posix())
    if found != set(expected) | {'PUBLIC_MANIFEST.json'}:
        raise ValueError('Unexpected or missing public file')
    for name, digest in expected.items():
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or FORBIDDEN.intersection(path.parts):
            raise ValueError('Forbidden public path')
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Public file integrity mismatch')
    return {'version': manifest['version'], 'verified_files': len(expected)}
