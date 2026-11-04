"""Preregistered paired metrics; no model fitting or scheduling occurs here."""
from __future__ import annotations
from collections import Counter
import numpy as np

from benchmarks.policies import POLICIES
from .artifacts import SEED

ACCEPTANCE = {
    'primary': 'mean_absolute_regret_customer_hours', 'minimum_relative_improvement': .05,
    'bootstrap_replicates': 2000, 'bootstrap_seed': SEED,
    'critical_mean_increase_limit_hours': .25, 'disparity_mean_increase_limit_hours': .25,
    'relative_regret_epsilon_customer_hours': 1/3600,
    'bootstrap_unit': 'whole_generation_configuration',
}


def cost(row: dict, policy: str) -> float:
    return row['outcomes'][policy]['cost_ticks'] / 3600


def oracle_cost(row: dict) -> float:
    return min(cost(row, p) for p in POLICIES)


def checked_pairs(rows: list[dict], predictions: list[str | None]) -> list[tuple[dict,str]]:
    if len(rows) != len(predictions):
        raise ValueError('Prediction/case count mismatch')
    for row, policy in zip(rows, predictions):
        if row['eligible'] and policy not in POLICIES:
            raise ValueError('Every eligible case requires a valid policy; selective abstention is forbidden')
        if not row['eligible'] and policy is not None:
            raise ValueError('Unsupported scope must abstain')
    return [(row, policy) for row, policy in zip(rows, predictions) if row['eligible']]


def summarize(rows: list[dict], predictions: list[str | None]) -> dict:
    finite = checked_pairs(rows, predictions)
    n = len(finite)
    regrets = [cost(r, p)-oracle_cost(r) for r, p in finite]
    relative = [v/max(oracle_cost(r), 1/3600) for (r, _), v in zip(finite, regrets)]
    confusion = [[sum(r['label'] == a and p == b for r, p in finite) for b in POLICIES] for a in POLICIES]
    def moments(values):
        return {'mean': float(np.mean(values)), 'median': float(np.median(values)),
                'p95': float(np.quantile(values, .95)), 'max': float(max(values))} if values else None
    return {'cases': len(rows), 'eligible': sum(r['eligible'] for r in rows), 'predicted': n,
            'abstained': len(rows)-n, 'coverage': n/len(rows) if rows else None,
            'absolute_regret_customer_hours': moments(regrets), 'relative_regret': moments(relative),
            'mean_completed_customer_hours': float(np.mean([cost(r,p) for r,p in finite])) if n else None,
            'mean_restricted_customer_hours_on_predicted': float(np.mean([
                r['outcomes'][p]['metrics']['restricted_horizon_customer_hours'] for r,p in finite])) if n else None,
            'exact_accuracy': sum(r['label']==p for r,p in finite)/n if n else None,
            'tie_aware_accuracy': sum(p in r['ties'] for r,p in finite)/n if n else None,
            'tied_cases': sum(len(r['ties'])>1 for r,p in finite),
            'predicted_policy_counts': dict(sorted(Counter(p for _,p in finite).items())),
            'label_counts': dict(sorted(Counter(r['label'] for r,_ in finite).items())),
            'confusion_policy_order': list(POLICIES), 'confusion_matrix': confusion}


def paired(rows: list[dict], predictions: list[str | None], fixed: str,
           *, bootstrap: bool = True) -> dict:
    finite = checked_pairs(rows, predictions)
    if fixed not in POLICIES:
        raise ValueError('Invalid fixed policy')
    improvements = [cost(r,fixed)-cost(r,p) for r,p in finite]
    fixed_regrets = [cost(r,fixed)-oracle_cost(r) for r,_ in finite]
    groups = sorted({r['group_id'] for r,_ in finite})
    interval = None
    if bootstrap and len(groups) >= 2:
        totals = np.array([sum(v for (r,_),v in zip(finite,improvements) if r['group_id']==g) for g in groups])
        counts = np.array([sum(r['group_id']==g for r,_ in finite) for g in groups])
        rng = np.random.default_rng(SEED)
        indices = rng.integers(0, len(groups), (ACCEPTANCE['bootstrap_replicates'],len(groups)))
        means = totals[indices].sum(axis=1)/counts[indices].sum(axis=1)
        interval = np.quantile(means, [.025,.975]).tolist()
    def critical(m):
        values = list(m['critical_service_latency_hours'].values())
        return max(values) if values and all(v is not None for v in values) else None
    def comparison(key):
        deltas = []
        for r,p in finite:
            a,b = r['outcomes'][p]['metrics'],r['outcomes'][fixed]['metrics']
            av,bv = (critical(a),critical(b)) if key=='critical' else (a[key],b[key])
            if av is not None and bv is not None:
                deltas.append(av-bv)
        return {'paired_cases':len(deltas), 'mean_increase_hours':float(np.mean(deltas)) if deltas else None,
                'max_increase_hours':max(deltas) if deltas else None,
                'regression_cases':sum(d>1e-12 for d in deltas)}
    critical_delta = comparison('critical')
    disparity = comparison('branch_mean_disparity_hours')
    small = comparison('small_group_mean_wait_hours')
    base = float(np.mean(fixed_regrets)) if fixed_regrets else None
    improvement = float(np.mean(improvements)) if improvements else None
    relative = improvement/base if base is not None and base>0 else None
    testable = relative is not None and interval is not None and critical_delta['paired_cases']>0 and disparity['paired_cases']>0
    passed = (relative>=.05 and interval[0]>0 and critical_delta['mean_increase_hours']<=.25
              and disparity['mean_increase_hours']<=.25) if testable else None
    return {'paired_cases':len(finite), 'configuration_groups':len(groups),
            'fixed_mean_regret_customer_hours':base, 'mean_improvement_customer_hours':improvement,
            'relative_regret_improvement':relative, 'group_bootstrap_95_interval_customer_hours':interval,
            'wins':sum(v>1e-12 for v in improvements), 'ties':sum(abs(v)<=1e-12 for v in improvements),
            'regressions':sum(v < -1e-12 for v in improvements),
            'critical_max_latency':critical_delta, 'branch_disparity':disparity, 'small_group_wait':small,
            'gate': 'PASS' if passed else 'FAIL' if passed is False else 'UNTESTABLE'}


def support(rows: list[dict]) -> dict:
    return {'cases':len(rows), 'eligible':sum(r['eligible'] for r in rows),
            'ineligible_reasons':dict(Counter(r['reason'] for r in rows if not r['eligible'])),
            'policies': {p: {'cases_with_unresolved_customers':sum(r['outcomes'][p]['metrics']['unresolved_customers']>0 for r in rows),
                'cases_with_known_later_censoring':sum(r['outcomes'][p]['metrics']['censored_customers']>0 for r in rows),
                'unresolved_customer_case_mass':sum(r['outcomes'][p]['metrics']['unresolved_customers'] for r in rows),
                'known_later_customer_case_mass':sum(r['outcomes'][p]['metrics']['censored_customers'] for r in rows),
                'mean_restricted_customer_hours_all_cases':float(np.mean([r['outcomes'][p]['metrics']['restricted_horizon_customer_hours'] for r in rows])) if rows else None}
                for p in POLICIES}}
