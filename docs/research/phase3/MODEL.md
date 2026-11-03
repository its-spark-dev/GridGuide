# Restoration CP-SAT model v1

`backend/optimization.py` is a reusable Python adapter over the unchanged G2 offline
problem/schedule contract. It introduces no endpoint, UI or challenge-local behavior.
OR-Tools is an optional lazy import. Install `requirements-optimization.txt`; pins cover
the solver and its numerical/transitive dependencies for the recorded Python 3.12 host.
Public HTTP contracts remain centralized and unchanged; future v2 adapters need review.

## Formulation

Let E be the executable task set, determined from independently validated baseline
assignments. This is the exact reachability scope required by the unchanged G2 validator.
For each i in E, fixed duration d_i is the same upward-rounded second duration as G2.
Use integer start/end s_i,e_i and binary x_ic. Each task has exactly one x_ic=1.
Optional intervals [s_i,e_i) of length d_i participate in NoOverlap for crew c;
assignment implies s_i >= availability_c. Each explicit repair predecessor j implies
s_i >= e_j. Customer dependencies are modeled separately, never converted into implicit
repair precedence. No field constraint beyond the declared contract is invented.

Safe horizon U = max crew availability + sum executable task durations. Waiting until
all crews are available and doing every eligible task serially in topological order is
feasible within U, so the bound does not exclude a necessary optimum. Integer objective
range is rejected if max(U,168h)*customer population >= 2^50, avoiding integer overflow
and loss of exact primary comparisons through double-valued solver diagnostics.

For known group g, R_g=max(e_i for i in required_g), with R_g=0 for an empty set.
For complete customer scope: minimize P=sum(n_g*R_g), in integer customer-seconds.
For partial scope: minimize sum_known(n_g*min(R_g,604800)) + 604800*unresolved_population.
Unknown release times remain null in reported metrics; the constant is only the G2
restricted-scoring convention. All executable work remains scheduled, including tasks
whose releases cannot yet be credited. Full task/customer completion is not invented.

After CP-SAT proves primary OPTIMAL, add P=P* and minimize max_i e_i. Otherwise skip
secondary optimization. Unknown secondary status retains the primary schedule; a worse
secondary incumbent cannot replace a better primary incumbent. Full makespan remains
null for partial task scope; the secondary variable is explicitly executable makespan.

## Validated incumbent and failure boundary

Generate all four unchanged G2 baselines, check each schedule and metric independently,
then choose minimum integer primary, executable makespan, stable policy ID. Supply its
starts/ends and crew assignment as hints and add P <= incumbent P. Compare extracted
integer objectives to independently recomputed values. No floating-point improvement
test is used. Solver best bounds are diagnostics; raw CP-SAT bounds may be fractional.

Every returned candidate passes the unmodified G2 structural and metric validator.
A missing solver, wrong solver version, range error, internal error, absent incumbent,
invalid candidate, objective mismatch or worse primary/makespan falls back explicitly.
Bad baseline/input validation raises an unavailable/error outcome instead of fabricating
a schedule. Every result includes provenance, fallback reason, candidate violations and
objective, raw primary/secondary status, bounds and solver statistics. Returned primary
optimality is true only for a validated accepted candidate with a matching CP-SAT proof.
An already-optimal baseline tie is legitimate; improvement is never manufactured.

## Execution settings and evidence

The preregistered settings are fixed at one worker, seed 20261103, 0.2 deterministic
primary work and 0.05 secondary work. Offline execution has no wall cutoff. Interactive
execution accepts at most 25 tasks/four crews; primary solve gets at most 1.5 seconds,
secondary gets the remaining shared two-second solve budget. Larger inputs return the
validated baseline explicitly. Measure wrapper latency (including baseline calculation,
model build and validation) separately against the five-second reference-host budget.
These are configured solver limits and measured local engineering checks, not field
response guarantees or an operational service SLA.

The solver represents non-preemptive work by one crew per task, not splitting work by
additional crews. It retains one-effective-worker conditional durations for benchmark
comparisons; fictional effort never receives the AEP multiplier. Critical/fairness costs
are reported as tradeoffs, never hidden weights in the primary objective.

## Alternatives and boundaries

An exhaustive solver is unsuitable for 100 tasks; the independent <=8-task G2 oracle
remains correctness machinery. Weighted scalar primary/makespan objectives risk hidden
tradeoffs and large coefficients, so a proof-gated two-stage solve is used. A generic
rewrite of the original envelope planner would blur evidence and units; it is untouched.
Best-of-four is a feasible incumbent/reference, not the fixed statistical comparator.

Official API references: [CP-SAT integer constraints and statuses](https://developers.google.com/optimization/cp/cp_solver),
[interval scheduling](https://developers.google.com/optimization/scheduling/job_shop),
and [solver limits](https://developers.google.com/optimization/cp/cp_tasks).
These document implementation mechanics, not utility applicability.
