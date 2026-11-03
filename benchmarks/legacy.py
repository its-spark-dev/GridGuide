"""Source-dependent regression lane. No synthetic benchmark adapters are used.

Only public labels and aggregate numerical values are retained, never private
customer membership or real geometry. Date-only reports are not ordered as FIFO.
"""
import hashlib
import json
from pathlib import Path

FROZEN = Path(__file__).parent/'frozen'/'legacy-v1.json'


def capture():
    from backend.config import SOURCE_SHA256
    from backend.contracts import CandidateAccess, PlanRequest
    from backend.data import verify_sources
    from backend.planning import make_plan, prepare_planning
    verify_sources()
    context=prepare_planning()
    default=make_plan(context,PlanRequest())
    upstream=next(c.id for c in default.candidates if c.label=='Golden upstream fuse')
    rows=[]
    for crews in (1,2):
        for people in (2,4,8):
            for critical in (False,True):
                for blocked in (False,True):
                    p=make_plan(context,PlanRequest(crew_count=crews,crew_size=people,use_critical_proxy=critical,
                        access=(CandidateAccess(candidate_id=upstream,access='blocked'),) if blocked else ()))
                    labels={c.id:c.label for c in p.candidates}
                    rows.append({'crews':crews,'people':people,'critical_proxy':critical,'blocked_upstream':blocked,
                        'repair_person_hours':p.repair_person_hours,'total_person_hours':p.total_person_hours,
                        'distinct_dependency_customers':p.unique_dependent_premises,
                        'completion_hours':None if p.completion_hours is None else p.completion_hours.model_dump(),
                        'tasks':[{'label':labels[t.candidate_id],'crew':t.crew,'start':t.start_hours.model_dump(),
                                  'finish':t.finish_hours.model_dump()} for t in p.tasks],
                        'milestones':[{'elapsed_hours':m.elapsed_hours.model_dump(),'additional':m.additional_premises,
                                       'cumulative':m.cumulative_premises} for m in p.milestones]})
    root=Path(__file__).resolve().parents[1]
    return {'version':'legacy-regression-v1','baseline_commit':'9b04fcf',
            'evidence':'Challenge-backed modeled envelopes, historical spatial hypotheses and declared damage; not observations of restoration.',
            'source_sha256':SOURCE_SHA256,'implementation_sha256':hashlib.sha256((root/'backend/planning.py').read_bytes()).hexdigest(),
            'normalized_adapter_equivalence_claim':False,'cases':rows}


def verify():
    actual=capture()
    if actual!=json.loads(FROZEN.read_text()):
        raise ValueError('Legacy regression changed')
    return {'status':'passed','cases':len(actual['cases']),'version':'legacy-regression-check-v1',
            'frozen_sha256':hashlib.sha256(FROZEN.read_bytes()).hexdigest()}
