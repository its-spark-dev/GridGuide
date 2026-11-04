"""Local-only, bounded Docker rehearsal. Does not push an image or deploy a host.

HTTP measurements are local observations, not an SLA. The second container has
network=none and verifies readiness/comparison from inside its own namespace.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import time
import urllib.request
import uuid


def docker(*args):
    return subprocess.check_output(['docker',*args], text=True).strip()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image',required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    image=json.loads(docker('image','inspect',args.image))[0]
    assert image['Config']['User']=='10001:10001'
    assert set(image['Config']['Env']) >= {'GRIDGUIDE_MODE=synthetic-demo','GRIDGUIDE_AI_PROVIDER=none'}
    name='gridguide-g8-'+uuid.uuid4().hex[:10]
    report={'image_id':image['Id'],'architecture':image['Architecture'],
            'user':image['Config']['User'],'cold_start_ms':[], 'restart_ms':None}
    options=['--read-only','--cap-drop=ALL','--security-opt=no-new-privileges',
             '--tmpfs','/tmp:rw,noexec,nosuid,size=16m']
    try:
        started=time.perf_counter()
        docker('run','-d','--name',name,*options,'-p','127.0.0.1:18189:8000',args.image)
        def ready():
            until=time.monotonic()+20
            while time.monotonic()<until:
                try:
                    with urllib.request.urlopen('http://127.0.0.1:18189/ready',timeout=1) as r:
                        value=json.load(r)
                    assert value['ready'] and not value['interactive_solver'];return
                except OSError:time.sleep(.1)
            raise RuntimeError('Readiness timeout')
        ready();report['cold_start_ms'].append(1000*(time.perf_counter()-started))
        raw=docker('exec',name,'cat','/app/PUBLIC_MANIFEST.json');manifest=json.loads(raw)
        assert docker('exec',name,'/opt/runtime/bin/python','-c',
            "from pathlib import Path;from backend.public_integrity import verify_tree;verify_tree(Path('/app'));print('verified')")=='verified'
        report['runtime_manifest_verified']=True;report['application_files']=len(manifest['files'])+1
        docker('stop','--time','10',name)
        try:urllib.request.urlopen('http://127.0.0.1:18189/ready',timeout=1)
        except OSError:report['actual_outage_unavailable']=True
        else:raise AssertionError('Stopped service still reachable')
        started=time.perf_counter();docker('start',name);ready()
        report['restart_ms']=1000*(time.perf_counter()-started)
        report['body_logging']=docker('logs',name)
        assert not report['body_logging']
        report['container_config']=json.loads(docker('inspect',name))[0]['HostConfig']
        # Scan *all* image layers, including files a subsequent layer might hide.
        with tempfile.TemporaryDirectory() as tmp:
            archive=Path(tmp)/'image.tar';docker('image','save','-o',str(archive),args.image)
            inspected=0
            with tarfile.open(archive) as outer:
                for entry in outer:
                    if not entry.isfile():continue
                    stream=outer.extractfile(entry)
                    try:layer=tarfile.open(fileobj=stream,mode='r|*')
                    except tarfile.ReadError:continue
                    try:
                        for member in layer:
                            name_in_layer=member.name.removeprefix('./')
                            if name_in_layer.startswith('app/') and not member.isdir():
                                relative=name_in_layer[4:]
                                assert member.isfile() and not member.issym() and not member.islnk(),relative
                                data=layer.extractfile(member).read()
                                if relative=='PUBLIC_MANIFEST.json':assert data.decode().strip()==raw.strip()
                                else:assert hashlib.sha256(data).hexdigest()==manifest['files'][relative],relative
                                inspected+=1
                    finally:layer.close()
            assert inspected==report['application_files']
            report['all_application_layer_files_verified']=inspected
    finally:
        subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    isolated=name+'-offline'
    try:
        docker('run','-d','--name',isolated,*options,'--network','none',args.image)
        code="""import json,time,urllib.request
for i in range(100):
 try:
  ready=json.load(urllib.request.urlopen('http://127.0.0.1:8000/ready'));break
 except OSError:time.sleep(.1)
else:raise RuntimeError('No readiness')
catalog=json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/v2/operator/scenarios'))
s=catalog['scenarios'][0]
body=json.dumps({'scenario_id':s['scenario_id'],'scenario_fingerprint':s['scenario_fingerprint']}).encode()
r=json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/api/v2/operator/compare',data=body,headers={'Content-Type':'application/json'})))
assert r['recommended_policy']=='legacy-release-per-person-hour-adapter-v1'
print('ready and comparison verified with no external interface')
"""
        report['network_none']=docker('exec',isolated,'/opt/runtime/bin/python','-c',code)
    finally:subprocess.run(['docker','rm','-f',isolated],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    # Avoid retaining verbose Docker host configuration; record the tested boundaries only.
    c=report.pop('container_config')
    report['runtime_bounds']={k:c[k] for k in ('ReadonlyRootfs','CapDrop','SecurityOpt','Tmpfs')}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
