"""Independent event/action audit. Deliberately imports neither simulator nor policies."""
from fractions import Fraction
import math

from benchmarks.contracts import BenchmarkProblem, Schedule


def validate_trajectory(problem, profile, durations, records, schedule) -> list[str]:
    try:
        p = BenchmarkProblem.model_validate(problem.model_dump())
        s = Schedule.model_validate(schedule)
        # Independent definition of the protocol's discrete assumptions.
        factors = {"deterministic": (Fraction(1),), "low": (Fraction(1, 2), Fraction(3, 2)),
                   "high": (Fraction(1, 4), Fraction(1, 2), Fraction(9, 4))}[profile]
        tasks = {t.id: t for t in p.tasks}
        crews = {c.id: c for c in p.crews}
        executable = set()
        while True:
            enlarged = executable | {t.id for t in p.tasks if t.access == "clear"
                and t.total_person_hours is not None and set(t.prerequisites) <= executable}
            if enlarged == executable:
                break
            executable = enlarged
        if set(durations) != executable:
            return ["duration_scope"]
        for i, value in durations.items():
            divisor = p.crews[0].people if p.duration_assumption == "ideal_all_people" else 1
            nominal = math.ceil(Fraction(tasks[i].total_person_hours) * 3600 / divisor)
            if type(value) is not int or value not in [math.ceil(nominal * f) for f in factors]:
                return ["duration_support"]
        now, done, active = 0, {}, {}
        for row in records:
            if set(row) != {"now", "completed", "active", "action"} or type(row["now"]) is not int:
                return ["public_state_schema"]
            if row["now"] != now or row["completed"] != sorted(done.values(), key=lambda a: (a["end_tick"], a["task_id"])):
                return ["observed_history"]
            if row["active"] != sorted(active.values(), key=lambda a: a["task_id"]):
                return ["active_public_state"]
            action = row["action"]
            if set(action) != {"task_id", "crew_id"}:
                return ["action_schema"]
            task, crew = action["task_id"], action["crew_id"]
            if task is None and crew is None:
                events = [a["start_tick"] + durations[i] for i, a in active.items()]
                events += [c.available_tick for c in p.crews if c.available_tick > now]
                if not events or (not active and set(done) == executable):
                    return ["invalid_wait"]
                now = min(events)
                finished = [i for i, a in active.items() if a["start_tick"] + durations[i] == now]
                for i in finished:
                    done[i] = dict(active.pop(i), end_tick=now)
            else:
                if type(task) is not str or type(crew) is not str:
                    return ["action_id_type"]
                if task not in executable or task in done or task in active or crew not in crews:
                    return ["invalid_assignment"]
                if crews[crew].available_tick > now or any(a["crew_id"] == crew for a in active.values()):
                    return ["crew_capacity"]
                if not set(tasks[task].prerequisites) <= done.keys():
                    return ["uncompleted_prerequisite"]
                active[task] = dict(task_id=task, crew_id=crew, start_tick=now)
        if active or done.keys() != executable:
            return ["incomplete_trajectory"]
        if sorted((a.model_dump() for a in s.assignments), key=lambda a: a["task_id"]) != sorted(done.values(), key=lambda a: a["task_id"]):
            return ["trajectory_schedule_mismatch"]
        if set(s.unscheduled_tasks) != tasks.keys() - executable:
            return ["unscheduled_scope"]
        return []
    except (ValueError, TypeError, KeyError, AttributeError):
        return ["invalid_trajectory_schema"]
