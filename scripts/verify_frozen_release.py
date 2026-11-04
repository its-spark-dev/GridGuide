"""Verify the immutable published ZIP against its historical manifest, not current inputs."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile


def verify(path):
    record = json.loads((Path(__file__).resolve().parents[1] / 'docs/releases/v1.1.0/package.json').read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest() != record['archive_sha256']:
        raise ValueError('Frozen release archive checksum mismatch')
    expected = dict(record['manifest']['files'])
    manifest = (json.dumps(record['manifest'], sort_keys=True, indent=2) + '\n').encode()
    expected['PUBLIC_MANIFEST.json'] = hashlib.sha256(manifest).hexdigest()
    with zipfile.ZipFile(path) as archive:
        if len(archive.infolist()) != len(expected) or set(archive.namelist()) != set(expected):
            raise ValueError('Frozen release entry mismatch')
        for name, digest in expected.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError('Frozen release member checksum mismatch')
    print('Frozen v1.1.0 archive and all 47 members verified')


if __name__ == '__main__':
    verify(Path(sys.argv[1]))
