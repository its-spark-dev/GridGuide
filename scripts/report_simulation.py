"""Render verified simulation artifacts; no solver or random draws."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmarks.simulation_reporting import report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    r=report(p.parse_args().directory);print(r['runs'],'runs;',len(r['failures']),'failed')
