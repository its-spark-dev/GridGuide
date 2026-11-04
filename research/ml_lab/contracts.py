"""ML lineage wraps, and never changes, frozen benchmark compatibility contracts."""
from collections import Counter
import hashlib
from typing import Annotated, Literal

from pydantic import Field, model_validator

from backend.contracts import Contract
from benchmarks.contracts import BenchmarkProblem, canonical

GENERATOR_VERSION = 'ml-generator-v1'
Partition = Literal['train', 'dev', 'final_id', 'final_shift']
Mechanism = Literal['random_ordered', 'layered', 'bottleneck', 'modular',
                    'preferential', 'deep_sparse']
Digest = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def topology_hash(problem: BenchmarkProblem) -> str:
    """ID-invariant directed color refinement; equal hashes are rejected conservatively.

    This catches every isomorphic graph, but is not a complete graph-isomorphism
    algorithm: non-isomorphic graphs can share a refinement signature.
    """
    parents = {t.id: t.prerequisites for t in problem.tasks}
    children = {i: [] for i in parents}
    for i, ps in parents.items():
        for p in ps:
            children[p].append(i)
    colors = {i: digest([len(parents[i]), len(children[i])]) for i in parents}
    for _ in parents:
        colors = {i: digest([colors[i], sorted(colors[p] for p in parents[i]),
                            sorted(colors[c] for c in children[i])]) for i in parents}
    return digest(sorted(Counter(colors.values()).items()))


class GenerationConfig(Contract):
    mechanism: Mechanism
    task_count: Annotated[int, Field(strict=True, ge=10, le=64)]
    edge_density: Annotated[float, Field(ge=0, le=1)]
    layers: Annotated[int, Field(strict=True, ge=2, le=16)]
    modules: Annotated[int, Field(strict=True, ge=2, le=6)]
    effort_family: Literal['uniform', 'lognormal', 'mixture']
    effort_scale: Annotated[float, Field(gt=0)]
    effort_spread: Annotated[float, Field(gt=0)]
    overlap: Annotated[float, Field(ge=0, le=1)]
    group_count: Annotated[int, Field(strict=True, ge=5, le=64)]
    size_skew: Annotated[float, Field(ge=0, le=1)]
    critical_prevalence: Annotated[float, Field(ge=0, le=1)]
    report_mode: Literal['random', 'effort', 'membership']
    crew_delay_hours: Annotated[float, Field(ge=0)]
    incomplete_mode: Literal['none', 'blocked', 'missing_effort', 'unresolved_dependency']
    seed: Annotated[int, Field(strict=True, ge=0)]
    attempt: Annotated[int, Field(strict=True, ge=0)]


class MLCase(Contract):
    version: Literal['ml-case-v1'] = 'ml-case-v1'
    generator_version: Literal['ml-generator-v1'] = GENERATOR_VERSION
    partition: Partition
    group_id: Annotated[str, Field(pattern=r'^ml-[a-z0-9-]+$')]
    configuration: GenerationConfig
    graph_hash: Digest
    problem: BenchmarkProblem

    @model_validator(mode='after')
    def lineage(self):
        if self.problem.family != self.configuration.mechanism:
            raise ValueError('Family/configuration mismatch')
        if len(self.problem.tasks) != self.configuration.task_count:
            raise ValueError('Task count/configuration mismatch')
        if self.problem.seed != self.configuration.seed:
            raise ValueError('Seed/configuration mismatch')
        expected = 'evaluation' if self.partition.startswith('final') else 'development'
        if self.problem.split != expected:
            raise ValueError('ML partition/legacy compatibility split mismatch')
        if topology_hash(self.problem) != self.graph_hash:
            raise ValueError('Topology fingerprint mismatch')
        return self

    @property
    def case_id(self) -> str:
        return self.problem.id

    @property
    def fingerprint(self) -> str:
        return digest(self.model_dump(mode='json'))


def input_eligibility(problem: BenchmarkProblem) -> dict:
    """Check known complete scope without producing a schedule or future metric."""
    executable = set()
    while True:
        added = {t.id for t in problem.tasks if t.access == 'clear'
                 and t.total_person_hours is not None
                 and set(t.prerequisites) <= executable} - executable
        if not added:
            break
        executable |= added
    unresolved_groups = [g for g in problem.groups if g.unresolved_dependency
                         or not set(g.required_tasks) <= executable]
    return {'complete_customer_scope': not unresolved_groups,
            'executable_tasks': len(executable),
            'unschedulable_tasks': len(problem.tasks) - len(executable),
            'unresolved_customers': sum(len(g.customer_ids) for g in unresolved_groups)}
