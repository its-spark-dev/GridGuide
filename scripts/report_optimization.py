"""Render and audit an existing optimization result artifact."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks.optimization_reporting import render
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    r=render(p.parse_args().directory)
    print('Promotion target met:',r['promotion_target_met_on_published_suite'])
