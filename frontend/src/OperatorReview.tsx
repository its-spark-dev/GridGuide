import { useEffect, useRef, useState } from 'react';
import type { components } from './api.generated';
type Catalog=components['schemas']['ReviewCatalog'];
type Scenario=components['schemas']['ReviewScenario-Output'];
type Request=components['schemas']['CompareRequest'];
type Comparison=components['schemas']['OperatorComparison-Output'];
type Export=components['schemas']['ReviewExport'];
type Policy=components['schemas']['PolicyResult-Output']['policy'];
type Reason=components['schemas']['ReviewRequest']['reason'];
type Edge=components['schemas']['Precedence'];
const FIXED:Policy='legacy-release-per-person-hour-adapter-v1';
const names:Record<Policy,string>={'fifo-v1':'FIFO','customer-count-v1':'Customer count',
  'legacy-release-per-person-hour-adapter-v1':'Fixed release/person-hour baseline',
  'legacy-critical-proxy-first-adapter-v1':'Legacy critical-proxy-first','restoration-cpsat-v1':'Protected CP-SAT (experimental)'};
const acknowledgements={fictional:'This scenario is independently authored fiction.',
 modeled_not_field_confirmed:'Recommendations are modeled, not field-confirmed.',
 gaps_and_unresolved:'I reviewed the evidence gaps and unresolved work.',
 objective_and_tradeoffs:'I reviewed the objective and secondary tradeoffs.',
 experimental_and_simulation_limits:'CP-SAT is experimental; no calibrated simulation intervals are supplied.'} as const;
type Ack=keyof typeof acknowledgements;
const ackKeys=Object.keys(acknowledgements) as Ack[];
const emptyAck=()=>Object.fromEntries(ackKeys.map(k=>[k,false])) as Record<Ack,boolean>;
const number=(n:number|null|undefined)=>n==null?'Unavailable':new Intl.NumberFormat('en-US',{maximumFractionDigits:3}).format(n);
const metricLabels:Record<string,string>={modeled_customer_outage_hours:'Completed customer-hours',
 restricted_horizon_customer_hours:'Restricted-horizon customer-hours',makespan_hours:'Makespan',
 weighted_p95_hours:'Customer-weighted p95 wait',branch_mean_disparity_hours:'Branch mean disparity',
 small_group_mean_wait_hours:'Small-group mean wait'};
const tradeoffLabel=(text:string)=>{const [key,...rest]=text.split(':');return `${metricLabels[key]??key}:${rest.join(':')}`;};
async function json<T>(url:string,signal:AbortSignal,body?:unknown):Promise<T>{
 const response=await fetch(url,{method:body?'POST':'GET',signal,cache:'no-store',credentials:'omit',
  headers:body?{'Content-Type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined});
 if(!response.ok)throw new Error('Validation failed or service unavailable. Check the scenario and precedence constraints, then retry.');
 return response.json() as Promise<T>;
}
function download(value:string,type:string,name:string){const url=URL.createObjectURL(new Blob([value],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}

export function OperatorReview(){
 const [catalog,setCatalog]=useState<Catalog|null>(null);
 const [scenario,setScenario]=useState<Scenario|null>(null);
 const [policy,setPolicy]=useState<Policy>(FIXED);
 const [experimental,setExperimental]=useState(false);
 const [edges,setEdges]=useState<Edge[]>([]);
 const [before,setBefore]=useState('');const [after,setAfter]=useState('');const [dirty,setDirty]=useState(false);
 const [comparison,setComparison]=useState<Comparison|null>(null);
 const [ack,setAck]=useState(emptyAck);const [reason,setReason]=useState<Reason>('conservative-baseline-preference');
 const [reviewed,setReviewed]=useState<Export|null>(null);
 const [busy,setBusy]=useState(false);const [reviewBusy,setReviewBusy]=useState(false);
 const [message,setMessage]=useState('Loading fictional operator scenarios…');
 const revision=useRef(0);const current=useRef<AbortController|null>(null);const exporting=useRef<AbortController|null>(null);
 function invalidate(){exporting.current?.abort();setReviewBusy(false);setReviewed(null);setAck(emptyAck());}
 async function compare(s:Scenario,p:Policy,x:boolean,overrides:Edge[]){
  current.current?.abort();invalidate();const controller=new AbortController();current.current=controller;
  const rev=++revision.current;setBusy(true);setComparison(null);setMessage('Recomputing and independently validating. Prior review is invalid.');
  setScenario(s);setPolicy(p);setExperimental(x);setEdges(overrides);setDirty(false);
  const request:Request={version:'operator-request-v1',scenario_id:s.scenario_id,scenario_revision:s.scenario_revision,
   scenario_fingerprint:s.scenario_fingerprint,revision:rev,selected_policy:p,include_experimental:x,precedence:overrides};
  try{
   const c=await json<Comparison>('/api/v2/operator/compare',AbortSignal.any([controller.signal,AbortSignal.timeout(10000)]),request);
   if(controller.signal.aborted||revision.current!==rev)return;
   if(c.request.scenario_id!==s.scenario_id||c.request.scenario_revision!==s.scenario_revision||
    c.request.scenario_fingerprint!==s.scenario_fingerprint||c.request.revision!==rev||
    c.request.selected_policy!==p||c.request.include_experimental!==x||JSON.stringify(c.request.precedence)!==JSON.stringify(overrides)||
    c.problem.id!==s.scenario_id)throw new Error('Mismatched scenario response rejected. Refresh before reviewing.');
   setComparison(c);setMessage('Validated fictional comparison. Human review required.');
  }catch(error){if(!controller.signal.aborted)setMessage(error instanceof Error?error.message:'Comparison unavailable.');}
  finally{if(current.current===controller)setBusy(false);}
 }
 useEffect(()=>{const controller=new AbortController();
  void json<Catalog>('/api/v2/operator/scenarios',AbortSignal.any([controller.signal,AbortSignal.timeout(10000)])).then(c=>{if(controller.signal.aborted)return;setCatalog(c);
   const s=c.scenarios[0];if(!s)throw new Error('No approved scenario available.');setBefore(s.problem.tasks[0].id);setAfter(s.problem.tasks[1]?.id??s.problem.tasks[0].id);void compare(s,FIXED,false,[]);
  }).catch(()=>{if(!controller.signal.aborted)setMessage('Fictional operator service unavailable. Start the operator-enabled synthetic service and reload.');});
  return()=>{controller.abort();current.current?.abort();exporting.current?.abort();};},[]);
 function changeScenario(id:string){const s=catalog?.scenarios.find(s=>s.scenario_id===id);if(!s)return;
  setBefore(s.problem.tasks[0].id);setAfter(s.problem.tasks[1]?.id??s.problem.tasks[0].id);void compare(s,FIXED,experimental,[]);}
 async function review(){
  if(!comparison||dirty||!ackKeys.every(k=>ack[k]))return;
  const c=comparison;const rev=revision.current;const controller=new AbortController();exporting.current=controller;setReviewBusy(true);
  try{const result=await json<Export>('/api/v2/operator/review-export',AbortSignal.any([controller.signal,AbortSignal.timeout(10000)]),
   {request:c.request,result_fingerprint:c.result_fingerprint,reason,acknowledgements:ack});
   if(controller.signal.aborted||revision.current!==rev)return;
   if(result.artifact.comparison.result_fingerprint!==c.result_fingerprint||result.artifact.review.result_fingerprint!==c.result_fingerprint||result.artifact.review.selected_policy!==policy)
    throw new Error('Export binding mismatch. Review again.');
   setReviewed(result);setMessage('Reviewed in demo. Sanitized exports are ready; no operational action occurred.');
  }catch{if(!controller.signal.aborted){setReviewed(null);setMessage('Review export rejected. Refresh and acknowledge the current comparison.');}}
  finally{if(exporting.current===controller)setReviewBusy(false);}
 }
 const selected=comparison?.results.find(r=>r.policy===policy);
 return <><a className="skip-link" href="#operator-main">Skip to operator review</a>
 <header className="prep-header"><a href="/">GridGuide</a><span>Fictional operator review</span><a href="/preparedness/">Preparedness kit</a></header>
 <main id="operator-main"><span className="eyebrow">Inspect · compare · review</span><h1>Review fictional repair plans</h1>
 <p>No dispatch, notifications, utility confirmation or authenticated operational approval. Review state stays in this session; only explicit downloads persist it.</p>
 <p role="status" className="notice">{message}</p>
 <section className="operator-panel" aria-labelledby="scenario-title"><h2 id="scenario-title">1. Set the declared scope</h2>
 <label>Fictional scenario<select value={scenario?.scenario_id??''} onChange={e=>changeScenario(e.target.value)} disabled={!catalog}>
 <option value="" disabled>Select a scenario</option>{catalog?.scenarios.map(s=><option key={s.scenario_id} value={s.scenario_id}>{s.label}</option>)}</select></label>
 <label className="check"><input type="checkbox" checked={experimental} disabled={!scenario} onChange={e=>scenario&&void compare(scenario,FIXED,e.target.checked,edges)}/>Include optional frozen CP-SAT comparison</label>
 <p>The fixed release/person-hour baseline remains the recommendation. G3’s 5% median promotion target failed. CP-SAT is experimental; its protected result includes a best-of-four baseline safeguard.</p>
 <p>In the published G3 experiment, mean improvement was 0.351% for the combined best-of-four incumbent plus CP-SAT versus the strongest fixed baseline, and 0.174% incrementally beyond per-instance best-of-four. These are historical synthetic findings, not gains established by this view or a blind holdout.</p>
 {scenario&&<details><summary>Tasks, customer dependencies and evidence</summary><p>Independent fiction. Effort/topology/crews: scenario assumptions. Scheduling: prototype policy. Overrides: user-declared. Observed outcomes, actual efficiency and unknown clearance: unavailable.</p>
 <p>{scenario.problem.crews.length} declared crews; one effective worker per crew is the elapsed-time assumption. Additional crews do not split a task. No extra AEP labor multiplier.</p>
 <ul>{scenario.problem.tasks.map(t=><li key={t.id}>{t.id}: {t.total_person_hours??'Unavailable'} total person-hours; access {t.access}; original prerequisites {t.prerequisites?.join(', ')||'none'}.</li>)}</ul>
 <ul>{scenario.problem.groups.map(g=><li key={g.id}>{g.id}: {g.customer_ids.length} fictional customers; requires {g.required_tasks.join(', ')}; {g.unresolved_dependency?'unresolved connection':'declared dependencies'}; {g.critical_service?'fictional critical service':'no critical-service designation'}.</li>)}</ul></details>}
 <fieldset disabled={!scenario||busy}><legend>Additional repair precedence (maximum 16)</legend>
 <label>Repair first<select value={before} onChange={e=>{invalidate();setBefore(e.target.value);setDirty(true);setMessage('Unapplied precedence edit. Review invalidated. Apply or discard the edit.');}}>{scenario?.problem.tasks.map(t=><option key={t.id}>{t.id}</option>)}</select></label>
 <label>Then repair<select value={after} onChange={e=>{invalidate();setAfter(e.target.value);setDirty(true);setMessage('Unapplied precedence edit. Review invalidated. Apply or discard the edit.');}}>{scenario?.problem.tasks.map(t=><option key={t.id}>{t.id}</option>)}</select></label>
 <button disabled={edges.length>=16} onClick={()=>scenario&&void compare(scenario,policy,experimental,[...edges,{before,after}])}>Add precedence and recompute</button>
 <button onClick={()=>{setDirty(false);invalidate();setMessage('Draft discarded. Review the current comparison again.');}}>Discard unapplied edit</button>
 </fieldset>
 <ul>{edges.map((e,i)=><li key={i}>{e.before} → {e.after} <button disabled={busy} onClick={()=>scenario&&void compare(scenario,policy,experimental,edges.filter((_,j)=>j!==i))}>Remove constraint {i+1}</button></li>)}</ul>
 <button disabled={!scenario||busy} onClick={()=>scenario&&void compare(scenario,FIXED,experimental,[])}>Reset constraints and recompute</button>
 </section>
 {comparison&&<><section className="operator-panel" aria-labelledby="compare-title"><h2 id="compare-title">2. Compare identical assumptions</h2><p>{comparison.explanation}</p>
 <p>Per-instance best-of-four reference: {names[comparison.best_of_four_policy]}. Selection uses completed customer-seconds when all customer outcomes are finite, otherwise restricted-horizon customer-seconds; ties use executable makespan then policy ID. This reference does not change the fixed recommendation.</p>
 {comparison.experimental_status==='unsupported_override'&&<p className="notice">CP-SAT unavailable for changed precedence: no matching approved frozen artifact. No new solver run or silent substitution.</p>}
 <div className="comparison-scroll" role="region" aria-label="Policy comparison table" tabIndex={0}><table><caption>Conditional fictional costs and tradeoffs. Unavailable is distinct from zero.</caption><thead><tr><th scope="col">Policy</th><th scope="col">Completed customer-hours</th><th scope="col">Restricted 168h customer-hours</th><th scope="col">Makespan (h)</th><th scope="col">Critical latency (h)</th><th scope="col">Branch disparity (h)</th><th scope="col">Small-group wait (h)</th><th scope="col">Unresolved / censored customers</th></tr></thead>
 <tbody>{comparison.results.map(r=><tr key={r.policy}><th scope="row">{names[r.policy]}{r.policy===FIXED?' · default':''}</th><td>{number(r.metrics.modeled_customer_outage_hours)}</td><td>{number(r.metrics.restricted_horizon_customer_hours)}</td><td>{number(r.metrics.makespan_hours)}</td><td>{Object.entries(r.metrics.critical_service_latency_hours).map(([k,v])=><div key={k}>{k}: {number(v)}</div>)}{!Object.keys(r.metrics.critical_service_latency_hours).length&&'Unavailable — none designated'}</td><td>{number(r.metrics.branch_mean_disparity_hours)}</td><td>{number(r.metrics.small_group_mean_wait_hours)}</td><td>{r.metrics.unresolved_customers} / {r.metrics.censored_customers}</td></tr>)}</tbody></table></div>
 <label>Selected policy<select value={policy} onChange={e=>scenario&&void compare(scenario,e.target.value as Policy,experimental,edges)}>{comparison.results.map(r=><option key={r.policy} value={r.policy}>{names[r.policy]}</option>)}</select></label>
 {selected&&<div className="selected-plan"><h3>Selected plan: {names[selected.policy]}</h3><p>{selected.explanation}</p><p>Feasibility: independently validated. Solver: {selected.solver_status??'Not used'}. Returned source: {selected.returned_source}. Fallback: {selected.fallback_reason??'None'}. Proven primary optimality: {selected.primary_optimal?'Yes, for this encoded problem':'Not claimed'}.</p>
 <p>Baseline provenance: {names[selected.baseline_policy]}. Recorded computation time: {number(selected.recorded_seconds)} seconds ({selected.timing_scope==='historical_g3_wrapper'?'historical G3 wrapper; not current request latency':'not recorded'}). Primary bound: {number(selected.best_bound_ticks)} customer-seconds. Relative gap (fraction): {number(selected.relative_gap)}.</p>
 <ul aria-label="Selected policy tradeoffs">{selected.tradeoffs.map(t=><li key={t}>{tradeoffLabel(t)}</li>)}</ul>
 <p>Customer-weighted waiting: median {number(selected.metrics.weighted_median_hours)} h; p95 {number(selected.metrics.weighted_p95_hours)} h; maximum {number(selected.metrics.maximum_wait_hours)} h.</p>
 <h4>Assignments (seconds from modeled response start)</h4><ul>{selected.schedule.assignments.map(a=><li key={a.task_id}>{a.task_id} → {a.crew_id}: {a.start_tick}–{a.end_tick} seconds</li>)}</ul>
 <p>Unscheduled tasks: {selected.schedule.unscheduled_tasks.join(', ')||'None'}. Unreleased at horizon: {selected.metrics.unreleased_customers_at_horizon}.</p>
 <h4>Conditional dependency release milestones</h4><ol>{selected.metrics.milestones.map(m=><li key={m.tick}>{m.tick} seconds: {m.additional_customers} additional, {m.cumulative_customers} cumulative fictional customers</li>)}</ol>
 <p>Known-later censoring is separate from unresolved completion. A 168-hour scoring horizon does not assign an ETR to unresolved work.</p></div>}
 <p>G5 intervals are not integrated here. Future displays must distinguish stable, unstable, unresolved and unsupported/unassessed results. All 15 unstable findings remain preserved; synthetic intervals are not empirically calibrated confidence.</p>
 </section>
 <section className="operator-panel" aria-labelledby="review-title"><h2 id="review-title">3. Review and export</h2>
 <p>Result revision {comparison.request.revision}. Changing inputs, policy, draft constraints, reason or acknowledgements invalidates export readiness.</p>
 <label>Structured reason<select value={reason} onChange={e=>{invalidate();setReason(e.target.value as Reason);setMessage('Reason changed. Acknowledge the review again.');}}><option value="conservative-baseline-preference">Conservative baseline preference</option><option value="lowest-modeled-customer-hours">Lowest modeled customer-hours</option><option value="critical-service-tradeoff">Critical-service tradeoff</option><option value="fairness-consideration">Fairness consideration</option><option value="demonstration-comparison">Demonstration comparison</option></select></label>
 <fieldset disabled={dirty||busy||reviewBusy}><legend>Explicit human acknowledgements</legend>{ackKeys.map(k=><label className="check" key={k}><input type="checkbox" checked={ack[k]} onChange={e=>{exporting.current?.abort();setReviewed(null);setAck({...ack,[k]:e.target.checked});}}/>{acknowledgements[k]}</label>)}</fieldset>
 <button disabled={dirty||busy||reviewBusy||!ackKeys.every(k=>ack[k])} onClick={()=>void review()}>Mark reviewed in demo and prepare export</button>
 {reviewed&&<section aria-labelledby="reviewed-title"><h3 id="reviewed-title">Reviewed in demo</h3><pre className="review-summary">{reviewed.summary}</pre><div className="actions"><button onClick={()=>download(JSON.stringify(reviewed.artifact,null,2),'application/json','gridguide-fictional-review.json')}>Download review JSON</button><button onClick={()=>download(reviewed.summary,'text/plain','gridguide-fictional-review.txt')}>Download readable summary</button></div></section>}
 <p>Hashes detect content changes; they are not authenticated signatures, proof of reviewer identity or protection against an actor rewriting the artifact. No identity or free text is collected.</p>
 </section></>}
 </main><footer>GridGuide · Fictional operator decision support · No dispatch or messaging</footer></>;
}
