"""Explicit-allowlist synthetic distribution. No broad repository copy or deletion pass."""
import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.public_integrity import verify_tree

FILES = (
 'backend/__init__.py','backend/contracts.py','backend/risk_rules.py','backend/scenarios.py',
 'backend/synthetic_api.py','backend/operator_api.py','backend/review.py','backend/review_contracts.py',
 'backend/optimization.py','backend/public_app.py','backend/public_integrity.py',
 'benchmarks/__init__.py','benchmarks/contracts.py','benchmarks/policies.py','benchmarks/metrics.py','benchmarks/validation.py',
 'data/synthetic/catalog.json','data/operator/catalog.json','scripts/replay_review.py',
 'deploy/serve.py','deploy/Dockerfile','deploy/requirements.in','deploy/requirements.lock','deploy/README.md',
 'THIRD_PARTY_NOTICES.md')
FIXED_STATIC = ('preparedness/index.html','operator/index.html','preparedness/frames.json',
                'preparedness/kit.txt','preparedness/service-worker.js','preparedness/cache-manifest.json')
MANIFEST='PUBLIC_MANIFEST.json'
LIMIT=8_000_000


def sha(raw):return hashlib.sha256(raw).hexdigest()


def read(root,name):
    p=root/name
    if p.is_symlink() or any(x.is_symlink() for x in p.parents if x!=root and root in x.parents):
        raise ValueError('Symlink in approved inputs')
    if not p.resolve().is_relative_to(root.resolve()) or not p.is_file() or p.stat().st_size>LIMIT:
        raise ValueError('Invalid approved input')
    return p.read_bytes()


def dependency_notices(root):
    blocks=['GridGuide public runtime dependency notices. No new project/data license is granted.\n']
    requirements=read(root,'deploy/requirements.lock').decode()
    for name,version in re.findall(r'^([\w-]+)==([^\s\\]+)',requirements,re.M):
        dist=metadata.distribution(name)
        if dist.version!=version:raise ValueError('Build with the locked public runtime environment')
        licenses=sorted(f for f in dist.files or [] if re.search(r'(^|/)(LICENSE|COPYING|NOTICE)',str(f),re.I))
        if not licenses:raise ValueError('Missing Python license notice: '+name)
        blocks.append('\n'+name+' '+version+'\n')
        for f in licenses:blocks.append(Path(dist.locate_file(f)).read_text())
    for name in ['react','react-dom','scheduler']:
        package=json.loads(read(root,'frontend/node_modules/'+name+'/package.json'))
        blocks.extend(['\n'+name+' '+package['version']+'\n',read(root,'frontend/node_modules/'+name+'/LICENSE').decode()])
    return '\n'.join(blocks).encode()


def approved(root=ROOT):
    out={name:read(root,name) for name in FILES}
    # Both numerical catalogs must still be the accepted independently authored inputs.
    from backend.scenarios import CATALOG_SHA256
    from backend.review import CATALOG_SHA
    if sha(out['data/synthetic/catalog.json'])!=CATALOG_SHA256 or sha(out['data/operator/catalog.json'])!=CATALOG_SHA:
        raise ValueError('Unapproved fictional input')
    dist=root/'frontend/dist-public'
    manifest=json.loads(read(dist,'.vite/manifest.json'))
    selected=set(FIXED_STATIC)
    visited=set()
    def visit(key):
        if key in visited:return
        visited.add(key)
        if key not in manifest:raise ValueError('Missing public entry')
        item=manifest[key]
        for name in [item['file'],*item.get('css',[])]:
            if not re.fullmatch(r'assets/[A-Za-z0-9_-]+\.(js|css)',name):raise ValueError('Unapproved compiled asset')
            selected.add(name)
        if item.get('dynamicImports') or item.get('assets'):raise ValueError('Unexpected build dependency')
        for dependency in item.get('imports',[]):visit(dependency)
    for key in ('preparedness/index.html','operator/index.html'):visit(key)
    actual={p.relative_to(dist).as_posix() for p in dist.rglob('*') if p.is_file()}
    if actual!=selected|{'.vite/manifest.json'}:raise ValueError('Unexpected file in public build')
    for name in selected:out['static/'+name]=read(dist,name)
    # The prepared frames must be the same reviewed bytes consumed by G6 trust bindings.
    if out['static/preparedness/frames.json']!=read(root,'frontend/public/preparedness/frames.json'):
        raise ValueError('Prepared artifact drift')
    cache=json.loads(out['static/preparedness/cache-manifest.json'])
    for url,pin in cache['allowlist'].items():
        name=url.lstrip('/')+('index.html' if url.endswith('/') else '')
        if 'static/'+name not in out or sha(out['static/'+name])!=pin:raise ValueError('Offline shell mismatch')
    notices=read(root,'deploy/DEPENDENCY_NOTICES.txt')
    if not notices.startswith(('Runtime lock SHA256: '+sha(out['deploy/requirements.lock'])+'\n').encode()):
        raise ValueError('Dependency notices need regeneration for this lock')
    out['DEPENDENCY_NOTICES.txt']=notices
    # Credential signatures; schema words such as "email" are not themselves secrets.
    secret=re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AIza[0-9A-Za-z_-]{35}|gh[pousr]_[0-9A-Za-z]{30,}|sk-[A-Za-z0-9]{32,}')
    for name,raw in out.items():
        if secret.search(raw):raise ValueError('Potential credential in approved file')
        if name.startswith(('data/','static/preparedness/frames')):
            if any(token in raw for token in (b'road_name',b'anno_strin',b'critical_c',b'latitude',b'longitude',b'"contact"',b'"declarations"')):
                raise ValueError('Protected field in fictional artifact')
    if sum(map(len,out.values()))>LIMIT:raise ValueError('Package outside bounded scope')
    return out


def manifest_bytes(files):
    return (json.dumps({'version':'public-package-v1','files':{k:sha(v) for k,v in sorted(files.items())}},sort_keys=True,indent=2)+'\n').encode()


def inspect(path, root=ROOT):
    expected=approved(root)
    expected[MANIFEST]=manifest_bytes(expected)
    with zipfile.ZipFile(path) as z:
        infos=z.infolist()
        if len(infos)!=len(expected) or {i.filename for i in infos}!=set(expected):raise ValueError('Unexpected archive entries')
        if sum(i.file_size for i in infos)>LIMIT:raise ValueError('Archive too large')
        for i in infos:
            p=PurePosixPath(i.filename)
            if p.is_absolute() or '..' in p.parts or stat.S_ISLNK(i.external_attr>>16):raise ValueError('Unsafe archive path')
            if z.read(i)!=expected[i.filename]:raise ValueError('Archive bytes differ from approved inputs')
    return {'version':'public-package-check-v1','files':len(expected),'archive_sha256':sha(path.read_bytes()),
            'manifest':json.loads(expected[MANIFEST]),'bytes':sum(map(len,expected.values()))}


def build(path, root=ROOT):
    if path.resolve().is_relative_to(root) and not path.resolve().is_relative_to(root/'artifacts'):
        raise ValueError('Write outside source or under ignored artifacts/')
    files=approved(root);files[MANIFEST]=manifest_bytes(files)
    with path.open('xb') as stream,zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,raw in sorted(files.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.create_system=3
            info.external_attr=(stat.S_IFREG|0o644)<<16;info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,raw)
    return inspect(path,root)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--build',type=Path);g.add_argument('--inspect',type=Path)
    a=p.parse_args();print(json.dumps(build(a.build) if a.build else inspect(a.inspect),indent=2,sort_keys=True))
