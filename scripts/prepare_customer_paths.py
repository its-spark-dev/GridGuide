"""Prepare bounded fictional customer frames, never challenge sources or Monte Carlo.

The source catalog is unchanged. Existing G2 arithmetic/validation owns all results.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.contracts import CustomerPathFrame
from backend.scenarios import prepare_synthetic, CATALOG_SHA256
from benchmarks.contracts import BenchmarkProblem
from benchmarks.policies import schedule, POLICIES
from benchmarks.metrics import calculate
from benchmarks.validation import validate


def canonical(value):
    # The bounded fixture numbers are whole or half hours. Normalize whole floats
    # to match JSON.stringify's canonical number spelling for browser integrity checks.
    if isinstance(value, dict): return {k: canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [canonical(v) for v in value]
    if isinstance(value, float) and value.is_integer(): return int(value)
    return value


def fingerprint(value):
    return hashlib.sha256(json.dumps(canonical(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def prepare():
    context = prepare_synthetic()
    frames = []
    for scenario in context.scenarios.values():
        repairs = {r.asset_id: r for r in scenario.repairs}
        unknown = {a.id for a in scenario.assets if a.kind == 'unresolved'}
        problem = BenchmarkProblem.model_validate(dict(
            id=scenario.id, family='customer-fictional-catalog', seed=0, split='micro',
            tasks=[dict(id=r.id, total_person_hours=None if r.repair_person_hours is None else str(r.repair_person_hours),
                        prerequisites=r.prerequisite_ids, report_order=i, access=r.access)
                   for i, r in enumerate(scenario.repairs)],
            groups=[dict(id=f'{p.customer_id}-group', customer_ids=[p.customer_id],
                         required_tasks=[repairs[a].id for a in p.asset_ids if a in repairs],
                         unresolved_dependency=bool(set(p.asset_ids) & unknown), branch=p.asset_ids[0])
                    for p in scenario.customer_paths],
            crews=[dict(id=f'{scenario.id}-crew-{i}', people=scenario.crews.people_per_crew,
                        available_tick=int(hours * 3600))
                   for i, hours in enumerate(scenario.crews.available_at_hours)]))
        plan = schedule(problem, POLICIES[2])
        metrics = calculate(problem, plan)
        if validate(problem, plan, metrics): raise ValueError('Invalid prepared plan')
        ends = {a.task_id: a.end_tick for a in plan.assignments}
        for step, tick in enumerate(sorted({0, *ends.values()})):
            nodes = []
            for i, a in enumerate(scenario.assets):
                repair = repairs.get(a.id)
                state = ('unresolved' if a.id in unknown or repair and repair.repair_person_hours is None
                         else 'intact_assumption' if repair is None else 'blocked' if repair.access == 'blocked'
                         else 'dependency_blocked' if repair.id not in ends
                         else 'completed_simulated' if ends[repair.id] <= tick else 'declared_damage')
                reasons = {
                    'unresolved': 'Evidence is missing; this component cannot be treated as intact or completed.',
                    'intact_assumption': 'Supply or equipment is assumed intact in this fictional definition, not observed.',
                    'blocked': 'Declared access is blocked. Clearance time is unknown.',
                    'dependency_blocked': 'A repair prerequisite is unavailable. This work cannot yet be scheduled.',
                    'completed_simulated': 'This repair is complete only in the selected precomputed fictional milestone.',
                    'declared_damage': 'Damage and repair scope are assumptions. This repair is not yet complete in this milestone.'}
                nodes.append(dict(id=a.id, kind=a.kind, label='Abstract supply terminal' if a.kind == 'supply_terminal'
                                  else f'{a.kind.title()} {i}', state=state, repair_id=repair.id if repair else None,
                                  prerequisite_ids=repair.prerequisite_ids if repair else (), reason=reasons[state]))
            customers = []
            for i, (p, group) in enumerate(zip(scenario.customer_paths, problem.groups), 1):
                release = metrics['release_ticks'][group.id]
                state = 'unresolved' if release is None else 'released_simulated' if release <= tick else 'waiting'
                customers.append(dict(id=p.customer_id, label=f'Fictional customer {i}', asset_ids=p.asset_ids,
                    unresolved_link_from_ids=[e.downstream_id for e in scenario.links if e.status == 'unresolved' and e.downstream_id in p.asset_ids],
                    required_repair_ids=group.required_tasks, release_state=state,
                    reason={'unresolved': 'Release cannot be determined: a connection, required repair effort or clearance is unresolved.',
                            'waiting': 'Every listed damaged dependency must be repaired before this fictional path can be released.',
                            'released_simulated': 'All declared damaged dependencies are complete in this milestone. This is not confirmed utility restoration.'}[state]))
            frame = CustomerPathFrame(scenario_id=scenario.id, scenario_revision=scenario.revision,
                label=scenario.label, input_fingerprint=context.metadata[scenario.id].input_fingerprint,
                step=step, step_label='Before repairs' if tick == 0 else f'Modeled milestone {step}', elapsed_hours=tick/3600,
                nodes=tuple(nodes), customers=tuple(customers),
                released_customers=sum(c['release_state']=='released_simulated' for c in customers),
                unresolved_customers=metrics['unresolved_customers'], completion_hours=metrics['full_customer_release_hours'],
                result_fingerprint='pending').model_dump(mode='json')
            frame.pop('result_fingerprint')
            frame['result_fingerprint'] = fingerprint(frame)
            frames.append(canonical(frame))
    return dict(version='customer-path-catalog-v1', catalog_sha256=CATALOG_SHA256, frames=frames)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    data = prepare()
    (args.output/'frames.json').write_text(json.dumps(data, sort_keys=True, indent=2)+'\n')
    trust = dict(catalog_sha256=CATALOG_SHA256, frames_sha256=fingerprint(data),
                 approved_frames=[f['result_fingerprint'] for f in data['frames']])
    (args.output/'pathTrust.generated.ts').write_text('// Generated by scripts/prepare_customer_paths.py; do not hand edit.\nexport const pathTrust = '+json.dumps(trust, sort_keys=True)+' as const;\n')
    print(len(data['frames']), 'validated fictional frames')
