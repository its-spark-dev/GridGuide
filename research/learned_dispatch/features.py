"""Versioned GridGuide state/action features; no teacher labels, identities or private futures."""
from __future__ import annotations

import math
import numpy as np

from research.adaptive_dispatch.environment import Action, Observation, PROFILES, WAIT
from . import FEATURE_VERSION
from .public import ValidatedState, validate_state

# Each feature has explicit meaning/units; ordering is part of the model contract.
DEFINITIONS = (
    ("task_count", "count", "Known repair tasks"),
    ("crew_count", "count", "Known identical-composition crews"),
    ("elapsed_scaled", "ratio", "Current ticks / mean nominal task ticks"),
    ("completed_fraction", "ratio", "Completed tasks / task count"),
    ("active_fraction", "ratio", "Active tasks / task count"),
    ("ready_fraction", "ratio", "Ready unstarted tasks / task count"),
    ("idle_crew_fraction", "ratio", "Idle available crews / all crews"),
    ("remaining_work_fraction", "ratio", "Expected uncompleted work / initial nominal work"),
    ("unreleased_customer_fraction", "ratio", "Customers with uncompleted dependencies / all customers"),
    ("unreleased_critical_fraction", "ratio", "Unreleased declared-critical customers / all customers"),
    ("ready_work_fraction", "ratio", "Nominal ready work / initial nominal work"),
    ("active_elapsed_scaled", "ratio", "Mean observed active elapsed / mean nominal task ticks; zero if none"),
    ("active_remaining_mean_scaled", "ratio", "Mean conditional expected active residual / mean nominal; zero if none"),
    ("active_remaining_min_scaled", "ratio", "Minimum conditional expected active residual / mean nominal; zero if none"),
    ("next_crew_delay_scaled", "ratio", "Delay to next known future crew arrival / mean nominal; zero if none"),
    ("remaining_dependency_fraction", "ratio", "Customer-weighted unfinished direct requirements / tasks, over unreleased customers"),
    ("uncertainty_cv", "ratio", "Coefficient of variation of declared duration multiplier support"),
    ("active_only_release_fraction", "ratio", "Customers whose remaining requirements are all active / all customers"),
    ("action_wait", "indicator", "Candidate is WAIT"),
    ("action_nominal_scaled", "ratio", "Candidate nominal ticks / mean nominal; zero for WAIT"),
    ("action_expected_scaled", "ratio", "Candidate support-mean ticks / mean nominal; zero for WAIT"),
    ("action_work_fraction", "ratio", "Candidate nominal ticks / expected remaining work; zero for WAIT"),
    ("direct_customer_fraction", "ratio", "Customers directly requiring candidate task / all customers"),
    ("downstream_customer_fraction", "ratio", "Unreleased customers with candidate in remaining prerequisite ancestry / all customers"),
    ("marginal_release_fraction", "ratio", "Customers requiring only candidate among unfinished direct requirements / all customers"),
    ("critical_downstream_fraction", "ratio", "Declared-critical subset of downstream impact / all customers"),
    ("critical_marginal_fraction", "ratio", "Declared-critical subset of marginal release / all customers"),
    ("dependent_group_fraction", "ratio", "Unreleased groups in candidate downstream impact / all groups"),
    ("impacted_remaining_dependency_fraction", "ratio", "Weighted remaining requirements among impacted customers / task count"),
    ("depth_fraction", "ratio", "Candidate prerequisite depth / maximum graph depth; roots depth one"),
    ("ancestor_fraction", "ratio", "Strict candidate ancestors / task count"),
    ("descendant_fraction", "ratio", "Strict candidate descendants / task count"),
    ("unfinished_descendant_fraction", "ratio", "Candidate descendants not completed / task count"),
    ("parent_fraction", "ratio", "Candidate direct prerequisites / task count"),
    ("child_fraction", "ratio", "Candidate direct children / task count"),
    ("unlock_fraction", "ratio", "Unstarted children whose last incomplete prerequisite is candidate / task count"),
    ("unlock_customer_fraction", "ratio", "Customers directly requiring any newly unlockable child / all customers"),
    ("report_rank_fraction", "ratio", "Candidate report_order / (maximum report_order+1)"),
    ("downstream_per_duration", "ratio", "Downstream customer fraction / scaled expected candidate duration"),
    ("marginal_per_duration", "ratio", "Marginal release fraction / scaled expected candidate duration"),
    ("critical_per_duration", "ratio", "Critical downstream fraction / scaled expected candidate duration"),
    ("active_overlap_fraction", "ratio", "Impacted customers also having an active task in remaining ancestry / all customers"),
    ("wait_active_release_fraction", "ratio", "WAIT indicator times active-only release fraction"),
    ("ready_competitor_fraction", "ratio", "Other ready tasks / task count; all ready tasks for WAIT"),
    ("progress_downstream", "ratio", "Completed fraction times downstream customer fraction"),
    ("active_remaining_to_duration", "ratio", "Minimum expected active residual / candidate nominal; zero if no active or WAIT"),
)
FEATURE_NAMES = tuple(row[0] for row in DEFINITIONS)


def schema() -> dict:
    return dict(version=FEATURE_VERSION, features=[dict(name=n, unit=u, definition=d) for n, u, d in DEFINITIONS],
                missingness="No target/input imputation; unsupported scope uses explicit deterministic fallback",
                forbidden=["case_id", "task_id", "crew_id", "seed", "partition", "family", "teacher_action",
                           "teacher_cost", "actual_remaining_duration", "future_event_queue", "episode_outcome"])


def feature_rows(state: Observation, validated: ValidatedState | None = None) -> tuple[tuple[Action, ...], np.ndarray]:
    view = validate_state(state) if validated is None else validated
    if view.observation is not state:
        raise ValueError("Validation belongs to a different observation")
    if not view.supported or not view.actions:
        raise ValueError("Unsupported state or no decision")
    ctx, s = view.context, state.static
    n, c, total = len(ctx.tasks), len(ctx.crews), ctx.customers
    nominal = ctx.nominal
    mean = ctx.mean_nominal
    expected = {i: sum(s.support(i))/len(s.support(i)) for i in ctx.tasks}
    elapsed = [state.now-a.start_tick for a in view.active.values()]
    residual = {i: sum(s.support(i, state.now-a.start_tick))/len(s.support(i, state.now-a.start_tick))
                - (state.now-a.start_tick) for i, a in view.active.items()}
    remaining_work = sum(residual[i] if i in residual else expected[i] for i in ctx.tasks if i not in view.done)
    remaining = {g.id: frozenset(g.required_tasks) - view.done for g in s.groups}
    unreleased = [g for g in s.groups if remaining[g.id]]
    unreleased_count = sum(len(g.customer_ids) for g in unreleased)
    critical_count = sum(len(g.customer_ids) for g in unreleased if g.critical_service)
    active_only = sum(len(g.customer_ids) for g in unreleased if remaining[g.id] <= view.active.keys()) / total
    future_crews = [crew.available_tick-state.now for crew in s.crews if crew.available_tick > state.now]
    factors = [float(f) for f in PROFILES[s.profile]]
    factor_mean = sum(factors)/len(factors)
    cv = math.sqrt(sum((f-factor_mean)**2 for f in factors)/len(factors)) / factor_mean
    shared = [n, c, state.now/mean, len(view.done)/n, len(view.active)/n, len(view.ready)/n,
        len(view.available)/c, remaining_work/(mean*n), unreleased_count/total, critical_count/total,
        sum(nominal[i] for i in view.ready)/(mean*n), sum(elapsed)/len(elapsed)/mean if elapsed else 0.,
        sum(residual.values())/len(residual)/mean if residual else 0., min(residual.values())/mean if residual else 0.,
        min(future_crews)/mean if future_crews else 0.,
        sum(len(g.customer_ids)*len(remaining[g.id]) for g in unreleased)/unreleased_count/n if unreleased_count else 0., cv, active_only]
    group_ancestry = {g.id: frozenset(a for t in remaining[g.id] for a in ctx.ancestors[t]) for g in unreleased}
    action_features = {}
    for i in view.ready:
        task = ctx.tasks[i]
        impacted = [g for g in unreleased if i in group_ancestry[g.id]]
        downstream = sum(len(g.customer_ids) for g in impacted)
        marginal = sum(len(g.customer_ids) for g in unreleased if remaining[g.id] == {i})
        critical = sum(len(g.customer_ids) for g in impacted if g.critical_service)
        critical_marginal = sum(len(g.customer_ids) for g in unreleased if g.critical_service and remaining[g.id] == {i})
        unlock = {j for j in ctx.children[i] if j not in view.done and j not in view.active
                  and set(ctx.tasks[j].prerequisites) <= view.done | {i}}
        overlap = sum(len(g.customer_ids) for g in impacted if group_ancestry[g.id] & view.active.keys())
        dur = expected[i]/mean
        action_features[i] = [0., nominal[i]/mean, dur, nominal[i]/remaining_work,
            sum(len(g.customer_ids) for g in unreleased if i in remaining[g.id])/total,
            downstream/total, marginal/total, critical/total, critical_marginal/total, len(impacted)/len(s.groups),
            sum(len(g.customer_ids)*len(remaining[g.id]) for g in impacted)/downstream/n if downstream else 0.,
            ctx.depth[i]/max(ctx.depth.values()), (len(ctx.ancestors[i])-1)/n, len(ctx.descendants[i])/n,
            len(ctx.descendants[i] - view.done)/n, len(task.prerequisites)/n, len(ctx.children[i])/n,
            len(unlock)/n, sum(len(g.customer_ids) for g in unreleased if remaining[g.id] & unlock)/total,
            task.report_order/(max(t.report_order for t in s.tasks)+1),
            downstream/total/dur, marginal/total/dur, critical/total/dur, overlap/total, 0.,
            (len(view.ready)-1)/n, len(view.done)/n*downstream/total,
            min(residual.values())/nominal[i] if residual else 0.]
    wait_features = [0.] * (len(FEATURE_NAMES)-len(shared))
    wait_features[0] = 1.
    wait_features[24] = active_only
    wait_features[25] = len(view.ready)/n
    rows = [shared + (wait_features if a == WAIT else action_features[a.task_id]) for a in view.actions]
    matrix = np.asarray(rows, dtype=np.float64)
    if matrix.shape != (len(view.actions), len(FEATURE_NAMES)) or not np.isfinite(matrix).all():
        raise ValueError("Invalid feature matrix")
    return view.actions, matrix


def extract(state: Observation, candidate: Action) -> dict[str, float]:
    actions, values = feature_rows(state)
    if type(candidate) is not Action or candidate not in actions:
        raise ValueError("Candidate is not a legal action")
    return dict(zip(FEATURE_NAMES, values[actions.index(candidate)].tolist()))
