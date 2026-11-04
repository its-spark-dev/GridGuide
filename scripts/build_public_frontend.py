"""Build only the two fictional entries; do not copy frontend/public wholesale."""
from pathlib import Path
import os
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
front=ROOT/'frontend'
subprocess.run(['npm','exec','--','tsc','--noEmit'],cwd=front,check=True)
subprocess.run(['npm','exec','--','vite','build','--config','vite.public.config.ts'],cwd=front,check=True)
for name in ['frames.json','kit.txt']:
    target=front/'dist-public/preparedness'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(front/'public/preparedness'/name,target)
subprocess.run(['node','scripts/build-preparedness.mjs'],cwd=front,
               env=dict(os.environ,GRIDGUIDE_BUILD_DIR='dist-public'),check=True)
