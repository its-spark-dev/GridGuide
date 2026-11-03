"""Replay the reviewed G4 evidence decision without observations, credentials or network.

This checks evidence bindings and fails closed; it cannot certify licensing judgments.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.risk.validation import feasibility


def evaluate():
    base=ROOT/'docs/research/phase4'
    review=json.loads((base/'evidence_review.json').read_text())
    audit=json.loads((base/'source_audit.json').read_text())
    gates=review['gates']
    # The reviewed record cannot override missing actual outcomes or permissions.
    if not audit['outage_payload_acquired'] and gates['outcome_payload']['status']=='pass':
        raise ValueError('Permission ledger contradicts absent outcome payload')
    outcome=next(d for d in review['datasets'] if d['id']=='ornl-eagle-i')
    if outcome['research_use']!='accepted_for_research' and gates['research_permission']['status']=='pass':
        raise ValueError('Unverified dataset permission')
    result=feasibility(gates)
    files=['docs/research/RISK_PROTOCOL.md','docs/research/phase4/evidence_review.json',
           'docs/research/phase4/source_audit.json','research/risk/validation.py','research/risk/audit.py',
           'scripts/evaluate_risk_feasibility.py','scripts/probe_risk_sources.py','scripts/audit_risk_sources.py']
    result.update(version='risk-feasibility-v1', evidence_class='prototype policy',
                  input_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},
                  models_fitted=0, predictive_metrics=None, real_data_split_validation=None,
                  final_outage_event_clusters=None, integration_authorized=False)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    with args.output.open('x') as f:json.dump(evaluate(),f,indent=2,sort_keys=True);f.write('\n')
