"""Generate runtime notices in the locked public Python environment after npm ci."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.package_demo import dependency_notices, ROOT, sha, read

if __name__=='__main__':
    header='Runtime lock SHA256: '+sha(read(ROOT,'deploy/requirements.lock'))+'\n'
    sys.stdout.buffer.write(header.encode()+dependency_notices(ROOT))
