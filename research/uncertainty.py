"""Numerical summaries only: no empirical restoration calibration."""
import math
import numpy as np


def nearest(values, q):
    return float(np.sort(values)[max(0,math.ceil(q*len(values))-1)])


def summarize(values):
    values=np.asarray(values);missing=int(np.isnan(values).sum());n=len(values)
    if missing:
        return {'trials':n,'unresolved_trials':missing,'mean':None,'p10':None,'p50':None,'p90':None,
                'width_p90_p10':None,'batch_quantile_se':None}
    qs=[nearest(values,q) for q in (.1,.5,.9)]
    batches=np.array_split(values,10) if n>=10 else []
    se=[float(np.std([nearest(b,q) for b in batches],ddof=1)/np.sqrt(10)) for q in (.1,.5,.9)] if batches else None
    return {'trials':n,'unresolved_trials':0,'mean':float(np.mean(values)),
            **dict(zip(('p10','p50','p90'),qs)),'width_p90_p10':qs[2]-qs[0],
            'batch_quantile_se':se}


def paired(candidate,reference):
    delta=candidate-reference;valid=np.isfinite(delta)
    return {**summarize(delta),'better':int(np.sum(delta<0)),'ties':int(np.sum(delta==0)),
            'worse':int(np.sum(delta>0)),'unavailable':int(np.sum(~valid)),
            'direction':'candidate minus reference; lower is better'}


def convergence(values):
    if len(values)!=10000:raise ValueError('Convergence requires 10000 trials')
    if not np.all(np.isfinite(values)):return {'status':'unavailable','checks':[]}
    checks=[]
    for q in (.1,.5,.9):
        small=nearest(values[:2000],q);large=nearest(values,q);difference=abs(small-large)
        limit=max(.25,.02*abs(large))
        checks.append({'q':q,'q2000':small,'q10000':large,'difference_hours':difference,
                       'tolerance_hours':limit,'passed':difference<=limit})
    return {'status':'stable' if all(c['passed'] for c in checks) else 'unstable_at_cap','checks':checks}
