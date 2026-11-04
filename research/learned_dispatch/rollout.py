"""Complete event rollouts; agreement queries are outside measured policy callbacks."""
from functools import partial
import time

from research.adaptive_dispatch.environment import Environment, checked_result, sample_durations
from research.adaptive_dispatch.policies import fixed_episode, heuristic, lookahead
from research.adaptive_dispatch.validation import validate_trajectory
from research.ml_lab.artifacts import digest
from .models import LearnedPolicy
from .public import static_context, validate_state
from .teacher import label

FIXED = "fixed-order:legacy-release-per-person-hour-adapter-v1"
REACTIVE = "reactive:downstream"
MEDIAN = "search:support-median"
EIGHT = "search:stochastic-8"
BASELINES = (FIXED, REACTIVE, MEDIAN, EIGHT)


def execute(problem, profile, seed, name, model=None):
    begin = time.perf_counter_ns()
    begin_cpu = time.process_time_ns()
    static_context.cache_clear()  # count cold static validation once in each policy episode
    if name == FIXED:
        result = fixed_episode(problem, profile, seed, FIXED.split(":", 1)[1], planned_floors=False)
        timing = dict(planning_nanoseconds=result.pop("planning_nanoseconds"),
                      episode_wall_nanoseconds=time.perf_counter_ns()-begin,
                      episode_cpu_nanoseconds=time.process_time_ns()-begin_cpu)
        result.update(agreements=[], fallbacks=[], invalid_actions=0)
        return result, timing
    if name in BASELINES:
        raw = partial(heuristic, name="downstream") if name == REACTIVE else partial(lookahead, median=name == MEDIAN)
        def policy(state):
            validate_state(state)
            return raw(state)
        learned = False
    elif model is not None and model.candidate == name:
        policy = LearnedPolicy(model)
        learned = True
    else:
        raise ValueError("Unknown/unloaded rollout policy")
    durations = sample_durations(problem, profile, seed)
    env = Environment(problem, profile, durations)
    records, walls, cpus, choices, agreements = [], [], [], [], []
    while not (state := env.observe()).terminal:
        wall, cpu = time.perf_counter_ns(), time.process_time_ns()
        action = policy(state)
        cpus.append(time.process_time_ns()-cpu)
        walls.append(time.perf_counter_ns()-wall)
        choices.append(len(state.actions(canonical_crew=True)))
        if action not in state.actions():
            raise ValueError("Policy proposed invalid action")
        if learned and choices[-1] > 1:
            teaching = label(state)
            agreements.append(dict(decision=len(records), exact=vars(action) == teaching["teacher"],
                tie_aware=vars(action) in teaching["ties"], teacher=teaching["teacher"],
                predicted=vars(action), teacher_ties=teaching["ties"],
                teacher_regret=teaching["targets"][teaching["actions"].index(vars(action))]))
        records.append(dict(now=state.now, completed=[a.model_dump(mode="json") for a in state.completed],
                            active=[vars(a) for a in state.active], action=vars(action)))
        env.step(action)
    result = checked_result(problem, durations, tuple(env.completed), name)
    errors = validate_trajectory(problem, profile, durations, records, result["schedule"])
    if errors:
        raise RuntimeError(f"Independent trajectory verification failed: {errors}")
    result.update(profile=profile, episode_seed=seed, durations=durations, trajectory_validated=True,
        trace=records, agreements=agreements, invalid_actions=0, fallbacks=policy.fallbacks if learned else [])
    timing = dict(decision_nanoseconds=walls, decision_cpu_nanoseconds=cpus, decision_choice_counts=choices,
                  episode_wall_nanoseconds=time.perf_counter_ns()-begin,
                  episode_cpu_nanoseconds=time.process_time_ns()-begin_cpu)
    return result, timing
