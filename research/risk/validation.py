"""Executable, fail-closed protocol primitives. No model fitting or application imports."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re

STEP = timedelta(minutes=15)
DAY = timedelta(days=1)
GATES = ('research_permission', 'outcome_payload', 'zero_missing_semantics',
         'county_time_coverage', 'labels_both_classes', 'event_reconstruction',
         'predictor_availability', 'split_integrity', 'final_event_count')
ALLOWED_FEATURES = {'month', 'weekday', 'lag_mean', 'lag_max', 'lag_latest'}


def utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError('Explicit UTC required')
    return parsed


@dataclass(frozen=True)
class Observation:
    county: str
    time: datetime
    count: int | None
    observed: bool
    reporting_scope: str | None

    def __post_init__(self):
        if not re.fullmatch(r'\d{5}', self.county):
            raise ValueError('County IDs must be five-character strings')
        if self.time.tzinfo is None or self.time.utcoffset() != timedelta(0):
            raise ValueError('Explicit UTC required')
        if self.time.minute % 15 or self.time.second or self.time.microsecond:
            raise ValueError('Off-grid observation')
        if self.count is not None and (type(self.count) is not int or self.count < 0):
            raise ValueError('Count must be a nonnegative integer or null')
        if type(self.observed) is not bool:
            raise ValueError('Observed flag must be boolean')


def label_window(county: str, issue: datetime, observations: list[Observation],
                 county_allowlist: set[str]) -> dict:
    """Missing windows stay null even when a partial positive run exists."""
    if county not in county_allowlist:
        raise ValueError('County not in verified crosswalk')
    if issue.tzinfo is None or issue.utcoffset() != timedelta(0) or any(
            (issue.hour, issue.minute, issue.second, issue.microsecond)):
        raise ValueError('Issue must be midnight UTC')
    indexed = {}
    for row in observations:
        key = (row.county, row.time)
        if key in indexed:
            raise ValueError('Duplicate county-time observation')
        indexed[key] = row
    past = [issue - DAY + STEP * i for i in range(1, 97)]
    future = [issue + STEP * i for i in range(1, 97)]
    valid = []
    for times in (past, future):
        valid.append([indexed.get((county, t)) for t in times])
    counts = [sum(r is not None and r.observed and r.count is not None and
                  bool(r.reporting_scope) for r in rows) for rows in valid]
    scopes = {r.reporting_scope for rows in valid for r in rows if r is not None}
    eligible = counts == [96, 96] and len(scopes) == 1
    result = {'county': county, 'issue': issue.isoformat(), 'label': None,
              'eligible': eligible, 'feature_observations': counts[0],
              'target_observations': counts[1], 'expected_per_window': 96,
              'reason': None if eligible else 'incomplete_or_unstable_observation_scope'}
    if eligible:
        streak = longest = 0
        for row in valid[1]:
            streak = streak + 1 if row.count > 100 else 0
            longest = max(longest, streak)
        result['label'] = int(longest >= 5)
    return result


def coverage(labels: list[dict], counties: set[str], years: tuple[int, ...]) -> dict:
    """Denominator is every daily issue in the declared county/year, including absent rows."""
    keyed = {}
    for row in labels:
        t = utc(row['issue'])
        if t.hour or t.minute or t.second or t.microsecond:
            raise ValueError('Non-daily issue')
        key = (row['county'], t.date())
        if row['county'] not in counties or t.year not in years or key in keyed:
            raise ValueError('Duplicate or out-of-scope issue')
        if type(row['eligible']) is not bool or (row['eligible'] and type(row['label']) is not int) or (
                row['eligible'] and row['label'] not in (0, 1)) or (not row['eligible'] and row['label'] is not None):
            raise ValueError('Inconsistent label availability')
        keyed[key] = row
    stats = []
    for c in sorted(counties):
        for y in years:
            expected = (datetime(y+1,1,1)-datetime(y,1,1)).days
            rows = [r for (county,day),r in keyed.items() if county == c and day.year == y]
            eligible = sum(r['eligible'] for r in rows)
            stats.append({'county': c, 'year': y, 'expected': expected,
                          'provided': len(rows), 'eligible': eligible, 'rate': eligible/expected})
    qualified = sum(all(s['rate'] >= .95 for s in stats if s['county'] == c) for c in counties)
    return {'county_years': stats, 'qualified_counties': qualified,
            'passed': bool(counties and years) and qualified/len(counties) >= .8}


def check_features(features: list[dict], issue: datetime, retrospective: bool = False) -> None:
    utc(issue.isoformat())
    for f in features:
        if f['name'] not in ALLOWED_FEATURES:
            raise ValueError('Feature outside preregistered allowlist')
        end = utc(f['observation_end'])
        if end > issue:
            raise ValueError('Future feature')
        available = f.get('available_at')
        if available is None:
            if not retrospective:
                raise ValueError('Unknown historical publication latency')
        elif utc(available) > issue or utc(available) < end:
            raise ValueError('Invalid as-of availability')


def check_splits(rows: list[dict], fit_ids: set[str], calibration_ids: set[str]) -> dict:
    """Audit already constructed event clusters; does not infer storms from IDs."""
    bounds = {'train':(2018,2021), 'validation':(2021,2022), 'test':(2022,2023)}
    seen = set(); groups = {}; identities = set(); split_ids = {k:set() for k in bounds}
    final_groups = set(); classes = {k:set() for k in bounds}
    for r in rows:
        role = r['split']
        if role not in bounds or not r['cluster'] or r['id'] in seen:
            raise ValueError('Invalid split, missing cluster or duplicate row ID')
        seen.add(r['id']); split_ids[role].add(r['id'])
        issue = utc(r['issue']); start = utc(r['feature_start']); end = utc(r['target_end'])
        if start != issue - DAY or end != issue + DAY:
            raise ValueError('Incorrect dependency window')
        a,b = bounds[role]
        if start <= datetime(a,1,1,tzinfo=timezone.utc)+DAY or end >= datetime(b,1,1,tzinfo=timezone.utc)-DAY:
            raise ValueError('Boundary embargo violation')
        identity = (r['county'],issue)
        if identity in identities:
            raise ValueError('Duplicate county-time row')
        identities.add(identity)
        if r['cluster'] in groups and groups[r['cluster']] != role:
            raise ValueError('Event cluster overlaps temporal splits')
        groups[r['cluster']] = role
        if type(r['label']) is not int or r['label'] not in (0,1):
            raise ValueError('Invalid outcome class')
        classes[role].add(r['label'])
        if role == 'test': final_groups.add(r['cluster'])
    if not fit_ids <= split_ids['train'] or not calibration_ids <= split_ids['validation']:
        raise ValueError('Fit/calibration leakage')
    return {'final_clusters':len(final_groups), 'classes':{k:sorted(v) for k,v in classes.items()},
            'sufficient':len(final_groups)>=30 and all(v=={0,1} for v in classes.values())}


def feasibility(gates: dict) -> dict:
    """Evidence ledger review, not automated certification of underlying source truth."""
    if set(gates) != set(GATES):
        raise ValueError('Missing or unknown feasibility gate')
    for gate in gates.values():
        if gate.get('status') not in ('pass', 'fail', 'unverified') or not gate.get('evidence'):
            raise ValueError('Each gate requires a status and evidence reference')
    blocked = sorted(k for k,v in gates.items() if v['status'] != 'pass')
    return {'decision':'no_go' if blocked else 'go', 'modeling_authorized':not blocked,
            'blocking_gates':blocked, 'gates':gates}
