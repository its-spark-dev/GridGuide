"""Preserve full reports, paired descriptive tables and bounded fictional demo trials.

Consumes completed reports; does not sample, optimize, change inputs or select winners.
Large standard trial caches remain locally retained and independently regenerable.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmarks.contracts import canonical


def load_suite(folder):
    manifest = json.loads((folder / 'manifest.json').read_text())
    report = json.loads((folder / 'report.json').read_text())
    expected = {(case, profile, policy) for case in manifest['inputs']
                for profile in manifest['profiles'] for policy in manifest['policies']}
    actual = {(r['case'], r['profile'], r['policy']) for r in report['summaries']}
    if (report['failures'] or len(report['summaries']) != len(expected) or actual != expected
            or report['numerical_sha256'] != manifest['numerical_sha256']
            or hashlib.sha256(canonical(manifest['records'])).hexdigest() != manifest['numerical_sha256']):
        raise ValueError('Incomplete or mismatched simulation report')
    return manifest, report


def package(standard, convergence, output):
    output.mkdir(parents=True, exist_ok=False)
    sm, sr = load_suite(standard)
    cm, cr = load_suite(convergence)
    if sm['suite'] != 'standard' or cm['suite'] != 'convergence':
        raise ValueError('Expected standard and convergence suites')
    for name, source in [('standard', standard), ('convergence', convergence)]:
        target = output / name
        target.mkdir()
        for file in ('manifest.json', 'report.json', 'timing.json'):
            (target / (file + '.gz')).write_bytes(gzip.compress((source / file).read_bytes(), mtime=0))
        shutil.copyfile(source / 'REPORT.md', target / 'REPORT.md')

    comparisons = []
    for profile in sm['profiles']:
        for policy, reference in [('cpsat', 'fixed'), ('fifo', 'fixed'),
                                  ('customer-count', 'fixed'), ('best-of-four', 'fixed'),
                                  ('cpsat', 'best-of-four')]:
            rows = [r for r in sr['paired_comparisons'] if r['profile'] == profile
                    and r['policy'] == policy and r['reference'] == reference and r['family'] != 'micro']
            for metric in ('modeled_customer_outage_hours', 'restricted_horizon_customer_hours',
                           'full_customer_release_hours', 'branch_mean_disparity_hours'):
                values = [r['metrics'][metric] for r in rows]
                finite = [r['mean'] for r in values if r['mean'] is not None]
                comparisons.append({'profile': profile, 'policy': policy, 'reference': reference,
                    'metric': metric, 'finite_cases': len(finite), 'unavailable_cases': len(rows)-len(finite),
                    'mean_paired_case_difference': statistics.mean(finite) if finite else None,
                    'case_means_better': sum(v < 0 for v in finite), 'case_means_tied': sum(v == 0 for v in finite),
                    'case_means_worse': sum(v > 0 for v in finite),
                    'paired_trial_counts': {key: sum(r[key] for r in values)
                                           for key in ('better', 'ties', 'worse', 'unavailable')}})
    sensitivity = []
    for profile in sm['profiles']:
        rows = [r for r in sr['summaries'] if r['profile'] == profile and r['policy'] == 'fixed' and r['family'] != 'micro']
        for metric in ('modeled_customer_outage_hours', 'restricted_horizon_customer_hours',
                       'full_customer_release_hours', 'unresolved_customers', 'censored_customers'):
            values = [r['metrics'][metric] for r in rows]
            finite = [r for r in values if r['mean'] is not None]
            sensitivity.append({'profile': profile, 'metric': metric, 'finite_cases': len(finite),
                'unavailable_cases': len(rows)-len(finite),
                **{f'mean_of_case_{field}': statistics.mean(r[field] for r in finite) if finite else None
                   for field in ('mean', 'p10', 'p50', 'p90', 'width_p90_p10')}})
    summary = {'version': 'simulation-review-summary-v1', 'standard_sha256': sm['numerical_sha256'],
        'convergence_sha256': cm['numerical_sha256'], 'paired_comparisons': comparisons, 'sensitivity': sensitivity,
        'convergence_counts': {status: sum(r['status'] == status for r in cr['convergence'])
                               for status in ('stable', 'unstable_at_cap', 'unavailable')},
        'failed_quantile_checks': sum(not c['passed'] for r in cr['convergence'] for c in r['checks']),
        'interpretation': 'Descriptive paired trial and case summaries only. Correlated variants are not independent population samples; no confidence interval or default promotion.'}
    (output / 'summary.json').write_bytes(canonical(summary) + b'\n')

    # Retain every fixed-baseline microcase, including unresolved and unstable results.
    # Future product integration must bind these immutable inputs and check the flags.
    checks = {(r['case'], r['profile'], r['policy']): r for r in cr['convergence']}
    records = {(r['case'], r['profile'], r['policy']): r for r in sm['records']}
    demo = output / 'demo'
    demo.mkdir()
    presets = []
    for row in sr['summaries']:
        if row['family'] != 'micro' or row['policy'] != 'fixed':
            continue
        key = row['case'], row['profile'], row['policy']
        record = records[key]
        shutil.copyfile(standard / record['file'], demo / record['file'])
        presets.append({**row, 'record': record,
                        'completion_convergence': checks.get(key, {'status': 'unavailable', 'checks': []})})
    demo_inputs = {case: {'problem': data['problem'], 'schedule': data['schedules']['fixed']}
                   for case, data in sm['inputs'].items() if data['problem']['family'] == 'micro'}
    (demo / 'presets.json').write_bytes(canonical({'version': 'simulation-demo-presets-v1',
        'approval': 'pending independent G5 review; future integration separately gated',
        'policy': 'legacy-release-per-person-hour-adapter-v1', 'calibrated': False,
        'source_suite_sha256': sm['numerical_sha256'], 'profiles_sha256': sm['profile_sha256'],
        'inputs': demo_inputs, 'presets': presets}) + b'\n')
    manifest = {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(output.rglob('*')) if p.is_file()}
    (output / 'CHECKSUMS.json').write_bytes(canonical(manifest) + b'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--standard', type=Path, required=True)
    parser.add_argument('--convergence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package(args.standard, args.convergence, args.output)
    print('Complete review reports and fixed-baseline demo trials preserved')
