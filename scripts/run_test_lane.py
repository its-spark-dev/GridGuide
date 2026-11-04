"""Enumerated execution lanes; absent authorized sources are NOT EXECUTED.

Inventory uses AST, so unavailable suites are counted without importing source loaders.
Every discovered unittest method belongs to exactly one lane. Subtests are diagnostics,
not additional independently executed test cases.
"""
import argparse
import ast
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PUBLIC = {'test_phase1','test_customer_paths','test_review','test_risk_research',
          'test_claim_safety','test_distribution','test_public_properties'}
SMALL_SIM = {'test_deterministic_all_frozen_micro_schedules',
             'test_deliberate_idle_time_is_preserved', 'test_blocked_mass_never_acquires_finite_completion'}


def inventory():
    result = {k: [] for k in ('public', 'challenge', 'research')}
    for path in sorted((ROOT/'tests').glob('test_*.py')):
        for cls in ast.parse(path.read_text()).body:
            if not isinstance(cls, ast.ClassDef): continue
            for method in cls.body:
                if not isinstance(method, ast.FunctionDef) or not method.name.startswith('test_'): continue
                lane = 'challenge'
                if path.stem in PUBLIC: lane = 'public'
                elif path.stem == 'test_benchmarks':
                    lane = 'research' if cls.name in ('OracleTests','RunnerTests') or method.name == 'test_standard_matrix_all_policies_independently_feasible' else 'public'
                elif path.stem in ('test_optimization','test_simulation'): lane = 'research'
                if path.stem == 'test_simulation' and method.name in SMALL_SIM: lane = 'public'
                result[lane].append(f'tests.{path.stem}.{cls.name}.{method.name}')
    return result


def deny_sources(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).resolve()
        if any(path.is_relative_to(ROOT/'data'/name) for name in ('raw','processed','external','prepared')):
            raise PermissionError('Source access forbidden in public lane')
    if event == 'socket.connect': raise PermissionError('Network forbidden in public Python tests')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lane', choices=('public','challenge','research'), required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--inventory-only', action='store_true')
    args = parser.parse_args()
    names = inventory()[args.lane]
    absent = args.lane == 'challenge' and not (ROOT/'data/raw').is_dir()
    report = dict(lane=args.lane, collected=len(names), case_ids=names, executed=0,
                  passed=0, failed=0, errors=0, skipped=0, unavailable=0, not_executed=0)
    if args.inventory_only or absent:
        report.update(status='NOT EXECUTED', not_executed=len(names), unavailable=len(names) if absent else 0,
                      reason='Authorized source dataset unavailable' if absent else 'Explicit inventory only')
    else:
        if args.lane == 'public': sys.addaudithook(deny_sources)
        suite = unittest.defaultTestLoader.loadTestsFromNames(names)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        failures = {test.id() for test, _ in result.failures}
        errors = {test.id() for test, _ in result.errors}
        # A subtest failure counts its parent once, while full diagnostics remain below.
        bad = {name.split(' (')[0] for name in failures | errors}
        skipped = {test.id() for test, _ in result.skipped}
        report.update(status='PASS' if result.wasSuccessful() else 'FAIL', executed=result.testsRun,
                      failed=len({n.split(' (')[0] for n in failures}), errors=len({n.split(' (')[0] for n in errors}),
                      skipped=len(skipped), passed=result.testsRun-len(bad|skipped),
                      failure_ids=sorted(failures), error_ids=sorted(errors), skipped_ids=sorted(skipped))
        if result.testsRun != len(names): report.update(status='FAIL', reason='Collection/execution count mismatch')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in report.items() if not k.endswith('_ids')}))
    return int(report['status'] == 'FAIL')


if __name__ == '__main__': raise SystemExit(main())
