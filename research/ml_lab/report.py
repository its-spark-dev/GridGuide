"""Reproducible static research presentation from completed, immutable evidence.

This module reads saved results only. It never imports model fitting, loads executable
model artifacts, computes schedules, or changes selection/evaluation decisions.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from benchmarks.policies import POLICIES
from .artifacts import digest, file_hash, read_json, read_rows, validate_hashes, write_json

REPORT_VERSION = 'ml-static-report-v1'
POLICY_NAMES = dict(zip(POLICIES, ('FIFO', 'Customer count', 'Release / effort', 'Critical first')))
PARTITION_NAMES = {'final_id': 'In-distribution holdout', 'final_shift': 'Structural-shift holdout'}
COLORS = {'fixed': '#172E4D', 'majority': '#91A2B7', 'heuristic': '#B47837',
          'logistic': '#367FA1', 'forest': '#40917C', 'boosting': '#7767A5',
          'champion': '#0B756D', 'hindsight': '#AAB7C0'}


def _label(name: str, training: dict) -> str:
    if name == 'fixed': return 'Best fixed'
    if name == 'majority': return 'Majority'
    if name == 'heuristic': return 'Structural rule'
    if name == 'hindsight': return 'Hindsight reference'
    if name == 'champion': return 'Frozen champion'
    if name.startswith('logistic'): return 'Logistic regression'
    if name.startswith('forest'): return 'Random forest'
    if name.startswith('boosting'): return 'Gradient boosting'
    return name


def _color(name: str) -> str:
    return COLORS.get(name, COLORS.get(name.split('-')[0], '#367FA1'))


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None: return '—'
    if isinstance(value, int): return f'{value:,}'
    return f'{value:,.{digits}f}'


def _pct(value: float | None) -> str:
    return '—' if value is None else f'{value * 100:.2f}%'


def _interval(value: list[float] | None) -> str:
    return '—' if value is None else f'[{_fmt(value[0])}, {_fmt(value[1])}]'


def _mean(entry: dict) -> float | None:
    moments = entry['metrics']['absolute_regret_customer_hours']
    return moments['mean'] if moments else None


def _regret(row: dict, selector: str) -> float:
    selected = row['predictions'][selector]
    return (row['outcomes'][selected]['cost_ticks'] - min(
        outcome['cost_ticks'] for outcome in row['outcomes'].values())) / 3600


def _save(fig, output: Path, name: str) -> None:
    fig.savefig(output/'figures'/f'{name}.png', dpi=180, facecolor=fig.get_facecolor(),
                metadata={'Software': 'GridGuide ML Lab'})
    fig.savefig(output/'figures'/f'{name}.svg', facecolor=fig.get_facecolor(),
                metadata={'Date': None, 'Creator': 'GridGuide ML Lab'})
    # Matplotlib emits harmless trailing spaces in path data; normalize for clean diffs.
    svg = output/'figures'/f'{name}.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close(fig)


def _canvas(title: str, subtitle: str, *, width=13.5, height=6.6, columns=2):
    fig, axes = plt.subplots(1, columns, figsize=(width, height), squeeze=False)
    fig.patch.set_facecolor('#F8FAFC')
    fig.text(.055, .955, 'GRIDGUIDE  /  ML LAB', color='#0B756D', size=10, weight='bold')
    fig.text(.055, .895, title, color='#172E4D', size=22, weight='bold')
    fig.text(.055, .845, subtitle, color='#536479', size=10)
    for ax in axes.flat:
        ax.set_facecolor('#F8FAFC')
        ax.spines[['top','right']].set_visible(False)
        ax.spines[['left','bottom']].set_color('#CBD5E1')
        ax.tick_params(colors='#536479', labelsize=9)
        ax.set_axisbelow(True)
    fig.subplots_adjust(left=.16, right=.965, bottom=.17, top=.735, wspace=.38)
    return fig, list(axes.flat)


def _performance(training: dict, report: dict, output: Path) -> None:
    selectors = ['fixed','majority','heuristic'] + list(training['family_winners'].values()) + ['champion']
    fig, axes = _canvas('Which selector incurs less regret?',
        'Mean excess modeled customer-hours over the best of four policies. Lower is better; oracle regret is zero.')
    for ax, (partition, data) in zip(axes, report['partitions'].items()):
        entries = data['selectors']
        values = [_mean(entries[name]) for name in selectors]
        y = np.arange(len(selectors))
        ax.barh(y, [v if v is not None else 0 for v in values], height=.58,
                color=[_color(name) for name in selectors], zorder=3)
        ax.set_yticks(y, [_label(name, training) for name in selectors], fontsize=9)
        ax.invert_yaxis()
        maximum = max((v for v in values if v is not None), default=1) or 1
        ax.set_xlim(0,maximum*1.32)
        for i,value in enumerate(values):
            ax.text((value or 0)+maximum*.025, i, _fmt(value,1), va='center', color='#172E4D', size=9)
        ax.set_xlabel('Mean regret (customer-hours)', color='#536479', labelpad=9)
        m = entries['fixed']['metrics']
        ax.set_title(f"{PARTITION_NAMES[partition]}\nn = {m['predicted']} eligible / {m['cases']} total", loc='left',
                     color='#172E4D', size=12, weight='bold', pad=15)
        ax.grid(axis='x',color='#E2E8F0',linewidth=.7)
    fig.text(.055,.055,f"Synthetic outcomes • Frozen champion: {training['champion']} • Identical cases within each panel • Panel scales differ",
             size=9,color='#536479')
    _save(fig,output,'performance')


def _distribution(training: dict, report: dict, rows: list[dict], output: Path) -> None:
    fig,axes = _canvas('Look beyond the average',
        'Empirical regret distributions retain ties at zero and the largest failures. Higher curves indicate less regret.')
    selectors = ['fixed','heuristic',training['best_ml']]
    for ax,(partition,data) in zip(axes,report['partitions'].items()):
        eligible = [r for r in rows if r['partition']==partition and r['eligible']]
        for name in selectors:
            regrets = [_regret(r,name) for r in eligible]
            if regrets:
                values, counts = np.unique(regrets, return_counts=True)
                cumulative = np.cumsum(counts) / len(regrets)
                if values[0] > 0:
                    values, cumulative = np.r_[0,values], np.r_[0,cumulative]
                ax.step(values,cumulative,where='post',linewidth=2.1,
                        color=_color(name),label=_label(name,training))
                ax.scatter([values[0]],[cumulative[0]],s=14,color=_color(name))
        ax.set_xscale('symlog',linthresh=1)
        ax.set_xlim(left=0)
        ax.set_ylim(0,1.03)
        ax.set_yticks([0,.25,.5,.75,1],['0%','25%','50%','75%','100%'])
        ax.set_xlabel('Regret (customer-hours; symlog)',labelpad=9,color='#536479')
        ax.set_ylabel('Share of eligible cases',color='#536479')
        ax.set_title(f'{PARTITION_NAMES[partition]}\nn = {len(eligible)} eligible cases',loc='left',
                     size=12,weight='bold',color='#172E4D',pad=15)
        ax.grid(color='#E2E8F0',linewidth=.7)
        ax.legend(loc='lower right',frameon=False,fontsize=8)
    fig.text(.055,.055,'The x-axis is linear from 0 to 1 customer-hour and logarithmic above 1. No tail cases are clipped.',size=9,color='#536479')
    _save(fig,output,'regret-distribution')


def _confusion(training: dict, report: dict, output: Path) -> None:
    best = training['best_ml']
    fig,axes = _canvas('What does the learned selector choose?',
        f"Development-selected ML candidate: {best}. Rows are deterministic best-policy labels; columns are predictions.",height=7.2)
    fig.subplots_adjust(left=.12,right=.94,bottom=.22,top=.74,wspace=.42)
    for ax,(partition,data) in zip(axes,report['partitions'].items()):
        m = data['selectors'][best]['metrics']
        values = np.array(m['confusion_matrix'])
        maximum = max(int(values.max()),1)
        ax.imshow(values,cmap='Blues',vmin=0,vmax=maximum)
        labels = [POLICY_NAMES[p] for p in m['confusion_policy_order']]
        ax.set_xticks(range(4),labels,rotation=28,ha='right',rotation_mode='anchor')
        ax.set_yticks(range(4),labels)
        for i in range(4):
            for j in range(4):
                ax.text(j,i,str(values[i,j]),ha='center',va='center',weight='bold',size=13,
                        color='white' if values[i,j]>maximum*.55 else '#172E4D')
        ax.set_title(f"{PARTITION_NAMES[partition]}\nExact {_pct(m['exact_accuracy'])} · tie-aware {_pct(m['tie_aware_accuracy'])} · n = {m['predicted']}",
                     loc='left',size=11,weight='bold',color='#172E4D',pad=15)
    fig.text(.055,.055,'Lexicographic policy-ID tie-breaking can create class dominance. An off-diagonal prediction may still tie for best cost.',
             size=9,color='#536479')
    _save(fig,output,'confusion')


def _importance(training: dict, output: Path) -> None:
    best = training['best_ml']
    interpretation = training['candidates'][best]['interpretation']
    values = sorted(interpretation['magnitude_by_feature'].items(),key=lambda item:(-item[1],item[0]))[:12]
    logistic = interpretation['method']=='standardized_logistic_coefficients'
    subtitle = ('Mean absolute standardized coefficients across learned classes; coefficient signs and full table are in training.json.'
                if logistic else 'Training impurity importance; this ranking is not a causal explanation or a measure of utility impact.')
    fig,axes = _canvas('Which inputs does the model use?',subtitle,height=7.2,columns=1)
    ax=axes[0]
    fig.subplots_adjust(left=.30,right=.93,top=.74,bottom=.17)
    y=np.arange(len(values))
    ax.barh(y,[value for _,value in values],height=.65,color='#367FA1')
    ax.set_yticks(y,[name.replace('_',' ') for name,_ in values],fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel('Mean absolute standardized coefficient' if logistic else 'Impurity importance (unitless)',
                  color='#536479',labelpad=9)
    ax.set_title(f'{best} · top {len(values)} of {len(interpretation["magnitude_by_feature"])} static features',
                 loc='left',color='#172E4D',size=11,pad=13)
    ax.grid(axis='x',color='#E2E8F0',linewidth=.7)
    fig.text(.055,.055,'Training-derived interpretation • Correlated features can share or distort importance • No final-set feature selection',
             size=9,color='#536479')
    _save(fig,output,'feature-importance')


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join(
        '| '+' | '.join(str(item).replace('|',' / ').replace('\n',' ') for item in row)+' |\n' for row in rows)


def _report(training: dict, report: dict, rows: list[dict], training_runtime: dict,
            final_runtime: dict, training_path: Path, final_path: Path, output: Path) -> str:
    best=training['best_ml']
    fixed=training['baselines']['fixed']
    train_link=os.path.relpath(training_path/'training.json',output)
    final_link=os.path.relpath(final_path/'results.json',output)
    cases_link=os.path.relpath(final_path/'cases.jsonl.gz',output)
    lines=['# ML-assisted restoration policy selection\n',
        '**Fictional scheduling research. No real outage prediction, calibrated restoration time, or utility dispatch claim.**\n',
        'A supervised classifier chooses among four unchanged scheduling policies using pre-decision structural features. '
        'The target is the independently validated lowest modeled completed customer-hours. The best-of-four hindsight '
        'reference is unavailable at prediction time and is not a deployable selector.\n',
        f"Development selected **`{best}`** as the strongest learned candidate and **`{training['champion']}`** as the frozen experimental champion. "
        f"The training-only fixed policy is **`{fixed}`**. These choices were frozen before this evaluation.\n",
        '## Measured findings\n']
    for partition,data in report['partitions'].items():
        entry=data['selectors'][best]; paired=entry['versus_fixed']; m=entry['metrics']
        improvement=paired['relative_regret_improvement']
        finding=('percentage improvement is undefined because baseline regret is zero or unavailable' if improvement is None else
                 f"mean regret is {_pct(abs(improvement))} {'lower' if improvement>0 else 'higher' if improvement<0 else 'unchanged'} versus fixed")
        lines.append(f"- **{PARTITION_NAMES[partition]}:** {m['predicted']}/{m['cases']} eligible cases; "
            f"learned mean regret {_fmt(_mean(entry))} customer-hours, fixed {_fmt(paired['fixed_mean_regret_customer_hours'])}; "
            f"{finding}. Preregistered gate: **{paired['gate']}**. Paired mean improvement interval "
            f"{_interval(paired['group_bootstrap_95_interval_customer_hours'])} customer-hours across {paired['configuration_groups']} configuration groups. "
            f"Mean critical-latency increase: {_fmt(paired['critical_max_latency']['mean_increase_hours'])} hours "
            f"on {paired['critical_max_latency']['paired_cases']} paired supported cases.\n")
    if any(data['selectors'][best]['versus_fixed']['gate']!='PASS' for data in report['partitions'].values()):
        lines.append('\n**No learned-selector promotion is supported.** Retain the fixed-policy baseline as the prudent '
                     'recommendation. The frozen champion remains the experimental identity; failed final gates do not '
                     'trigger retuning, a replacement champion, or a positive performance claim.\n')
    lines += ['\n![Model and baseline comparison](figures/performance.png)\n',
        'Success requires at least 5% lower mean absolute regret, positive measurable baseline regret, a positive lower '
        'endpoint of the grouped 95% paired-improvement interval, and mean critical-latency and branch-disparity increases '
        'no greater than 0.25 hour each. Missing support is untestable. A failed gate remains a negative finding; '
        'engineering completion does not establish scientific success. No final result changes the selected champion.\n',
        '## Task, data and model development\n',
        'Each row represents one independently authored fictional scheduling problem. Four in-distribution graph '
        'mechanisms vary topology, effort, customer dependency overlap, group size, report order, crews and availability. '
        'Shifted mechanisms also increase task scale; the shift therefore combines topology and scale and does not isolate '
        'either effect. Related crew variants share a configuration group and stay in one partition. Historical G2 evidence '
        'is background, never this final test. No AEP challenge data supplies features or labels.\n',
        'The 41 static features summarize task effort, DAG structure, customer groups, dependencies, crew availability and '
        'missingness. IDs, family labels, seeds, partitions, schedules and policy outcomes are excluded. Complete task scope '
        'and known customer releases are required; incomplete cases abstain. Known release after 168 hours remains eligible '
        'for full-completion scoring, separately reported as known-later censoring.\n',
        'Eight predefined candidates cover multinomial logistic regression, random forest and gradient boosting. '
        'Preprocessing fits within training-only pipelines, with three-fold grouped cross-validation. Every final candidate '
        'fits training only; development mean absolute regret selects hyperparameters and the champion without refitting '
        'on development. Same-environment repeated fits check deterministic predictions and serialized artifacts.\n',
        _table(['Development partition','Total cases','Eligible cases','Withheld cases'],[
            [partition,data['cases'],data['eligible'],data['cases']-data['eligible']]
            for partition,data in training.get('support',{}).items()]),
        '\n',
        _table(['Figure policy label','Exact unchanged policy ID'],[[short,policy] for policy,short in POLICY_NAMES.items()]),
        '\n',
        _table(['Development candidate','Mean regret (customer-h)','Grouped CV mean regret (customer-h)','Artifact bytes'],[
            [name,_fmt(c['development']['absolute_regret_customer_hours']['mean']),
             _fmt(c['grouped_cv']['absolute_regret_customer_hours']['mean']),_fmt(c['model_size_bytes'])]
            for name,c in training['candidates'].items()]),
        '\nTraining deterministic-label class counts: '+', '.join(f"{POLICY_NAMES.get(p,p)} {n}" for p,n in training['class_counts'].items())+'.\n',
        '## Final metrics and coverage\n']
    for partition,data in report['partitions'].items():
        lines.append(f"### {PARTITION_NAMES[partition]}\n")
        support=data['support']
        lines.append(f"{support['cases']} cases; {support['eligible']} eligible; "
                     f"{support['cases']-support['eligible']} abstentions. Ineligible reasons: `{support['ineligible_reasons']}`.\n")
        lines.append(_table(['Selector','n','Mean / median / p95 regret (customer-h)','Mean / median / p95 relative regret',
                             'Exact / tie-aware accuracy','Coverage','Gate'],[
            [name,e['metrics']['predicted'],
             ' / '.join(_fmt(e['metrics']['absolute_regret_customer_hours'][k]) for k in ('mean','median','p95'))
                if e['metrics']['absolute_regret_customer_hours'] else '—',
             ' / '.join(_pct(e['metrics']['relative_regret'][k]) for k in ('mean','median','p95'))
                if e['metrics']['relative_regret'] else '—',
             _pct(e['metrics']['exact_accuracy'])+' / '+_pct(e['metrics']['tie_aware_accuracy']),
             _pct(e['metrics']['coverage']),e['versus_fixed']['gate']]
            for name,e in data['selectors'].items()]))
        lines.append('\nEvery selector uses the same eligible cases. Hindsight is an unattainable reference. '
                     'Relative-regret denominator is max(oracle cost, 1/3600 customer-hour).\n')
        lines.append(_table(['Selector','Completed mean (customer-h)','Restricted 168h mean on predicted cases (customer-h)',
                             'Wins / ties / losses vs fixed','Paired improvement 95% interval (customer-h)'],[
            [name,_fmt(e['metrics']['mean_completed_customer_hours']),
             _fmt(e['metrics']['mean_restricted_customer_hours_on_predicted']),
             f"{e['versus_fixed']['wins']} / {e['versus_fixed']['ties']} / {e['versus_fixed']['regressions']}",
             _interval(e['versus_fixed']['group_bootstrap_95_interval_customer_hours'])]
            for name,e in data['selectors'].items()]))
        lines.append('\nAll-case policy support (restricted values include unresolved waiting through 168h, '
                     'not fabricated finite restoration times; customer-case mass can repeat customers across fictional variants):\n')
        lines.append(_table(['Policy','Unresolved cases / customer-case mass','Known-later cases / customer-case mass',
                             'All-case restricted mean (customer-h)'],[
            [POLICY_NAMES[p],f"{s['cases_with_unresolved_customers']} / {s['unresolved_customer_case_mass']}",
             f"{s['cases_with_known_later_censoring']} / {s['known_later_customer_case_mass']}",
             _fmt(s['mean_restricted_customer_hours_all_cases'])] for p,s in support['policies'].items()]))
        lines.append('\nPaired secondary outcomes: positive differences mean worse than fixed. Critical latency is the '
                     'maximum wait among explicitly fictional critical groups per case, not a real facility metric.\n')
        lines.append(_table(['Selector','Critical: n / mean Δh / regressions','Branch disparity: n / mean Δh / regressions',
                             'Small-group wait: n / mean Δh / regressions'],[
            [name]+[f"{e['versus_fixed'][key]['paired_cases']} / {_fmt(e['versus_fixed'][key]['mean_increase_hours'])} / "
                    f"{e['versus_fixed'][key]['regression_cases']}" for key in ('critical_max_latency','branch_disparity','small_group_wait')]
            for name,e in data['selectors'].items()]))
        for kind in ('families','scales'):
            lines.append(f"\n**By {'generation mechanism' if kind=='families' else 'task-count scale'}** — best learned versus fixed:\n")
            lines.append(_table(['Group','n','Learned / fixed mean regret (customer-h)','Mean paired gain (customer-h)',
                                 'Grouped 95% interval','Gate'],[
                [group,entries[best]['metrics']['predicted'],
                 _fmt(_mean(entries[best]))+' / '+_fmt(_mean(entries['fixed'])),
                 _fmt(entries[best]['versus_fixed']['mean_improvement_customer_hours']),
                 _interval(entries[best]['versus_fixed']['group_bootstrap_95_interval_customer_hours']),
                 entries[best]['versus_fixed']['gate']]
                for group,entries in data[kind].items()]))
        bm=data['selectors'][best]['metrics']
        lines.append(f"\nPolicy ties: {bm['tied_cases']}/{bm['predicted']} eligible cases. Label counts: "
                     f"`{bm['label_counts']}`. Learned prediction counts: `{bm['predicted_policy_counts']}`.\n")
    lines += ['\n## Failure analysis and interpretation\n',
              '![Regret distributions](figures/regret-distribution.png)\n',
              '![Policy selection confusion](figures/confusion.png)\n',
              'The confusion matrix uses deterministic tie-broken labels. High exact accuracy can reflect a dominant '
              'class; tie-aware accuracy recognizes equal-cost choices. The primary objective remains cost regret. '
              'A good mean can conceal rare severe failures, so the table below retains the largest learned regrets.\n']
    for partition in report['partitions']:
        worst=sorted((r for r in rows if r['partition']==partition and r['eligible']),
                     key=lambda r:(-_regret(r,best),r['case_id']))[:8]
        lines.append(f'**{PARTITION_NAMES[partition]} — largest learned errors**\n')
        lines.append(_table(['Case','Family / tasks','Learned choice','Best tie-broken policy',
                             'Learned / fixed regret (customer-h)'],[
            [r['case_id'],f"{r['family']} / {r['task_count']}",POLICY_NAMES[r['predictions'][best]],
             POLICY_NAMES[r['label']],_fmt(_regret(r,best))+' / '+_fmt(_regret(r,'fixed'))] for r in worst]))
        eligible=[r for r in rows if r['partition']==partition and r['eligible']]
        disagreements=sum(r['predictions'][best]!=r['predictions']['fixed'] for r in eligible)
        lines.append(f'\nLearned/fixed policy disagreements: {disagreements}/{len(eligible)} eligible cases.\n')
    lines += ['\n![Training feature importance](figures/feature-importance.png)\n',
              'Importance is descriptive of the fitted synthetic classifier. Correlated features, class imbalance and '
              'simulator conventions can drive it; it does not explain utility causality or validate dispatch decisions.\n',
              '## Resources and reproduction\n',
              f"Training process: {_fmt(training_runtime.get('elapsed_seconds'))} seconds; peak RSS "
              f"{_fmt(training_runtime.get('peak_process_rss_bytes'))} bytes. Final evaluation: "
              f"{_fmt(final_runtime.get('elapsed_seconds'))} seconds; peak RSS "
              f"{_fmt(final_runtime.get('peak_process_rss_bytes'))} bytes. These are measured process values, not portable SLAs.\n"]
    lines.append(_table(['Candidate','Training + CV + replay seconds','Dev batch inference seconds / case','Final inference seconds / case'],[
        [name,_fmt(runtime.get('training_cv_replay_seconds'),6),
         _fmt(runtime.get('batch_inference_seconds_per_case'),8),
         _fmt(final_runtime.get('inference_seconds',{}).get(name,0)/final_runtime['inference_denominator_cases'],8)
            if final_runtime.get('inference_denominator_cases') else '—']
        for name,runtime in training_runtime.get('models',{}).items()]))
    lines += [f"\nTraining environment: `{training.get('environment',{})}`. Final inference denominator includes all "
              'cases (including cheap abstentions); development timing is batch prediction on eligible feature rows.\n',
              f"Dataset hash: `{training.get('dataset_hash', 'not supplied')}`. Training source revision: "
              f"`{training.get('source_revision', 'not supplied')}`. The training manifest preserves per-file source hashes, "
              'feature schema, parameters and individual model hashes; the final completion manifest binds the evaluation receipt.\n',
              f"[Training evidence]({train_link}) · [Complete final comparisons]({final_link}) · "
              f"[Per-case outcomes and errors]({cases_link}) · [Presentation hash manifest](manifest.json).\n",
              'Regenerate with `python -m research.ml_lab report --training TRAINING --final FINAL --output NEW_DIRECTORY`. '
              'The renderer only reads evidence; it never retrains or reopens model selection. It refuses existing output. '
              'The final directory must have a sibling `selection-freeze.json`; completion status, final artifact hashes, '
              'numerical digests and frozen training/model hashes must validate before rendering. '
              'Figures have deterministic metadata and are reproducible byte-for-byte in the same pinned environment. '
              'Cross-platform font/raster byte equivalence is not assumed.\n',
              '## Limits and preserved negative findings\n',
              '- The final set is procedurally sealed by the same development team, not an externally independent blind test. '
              'Hashes establish consistency, not independence or authenticity.\n',
              '- The four-policy oracle is not the global scheduling optimum. The model cannot improve the policies themselves.\n',
              '- Generator groups support conditional bootstrap uncertainty; authored mechanisms and correlated variants '
              'do not represent independent utility events. Candidate and subgroup intervals are descriptive, without multiplicity correction.\n',
              '- Incomplete scope is withheld from supervised labels and predictions. Coverage is explicit; restricted-horizon '
              'descriptive outcomes do not fill missing full-completion labels.\n',
              '- Structural summaries discard detailed graph information. Topology and scale shift jointly; findings cannot '
              'establish real-world generalization or identify which shift factor caused a regression.\n',
              '- No interactive UI, production integration, deployment, v1.2.0 release or real-data predictor is introduced. '
              'Original G2/G3/G4/G5 conclusions, default policies and historical artifacts remain unchanged.\n',
              '- Contributor-authored synthetic code/data are covered by the repository MIT scope; no AEP data permission '
              'is inferred. Dependency licenses remain separately documented.\n']
    return '\n'.join(lines)


def build_report(training: Path, final: Path, output: Path) -> dict:
    """Render sealed evidence; the freeze must be final.parent/selection-freeze.json.

    Validation binds saved evidence to its local freeze without loading model objects.
    This checks consistency, not authorship or externally independent review.
    """
    training,final,output=map(Path,(training,final,output))
    if output.exists():
        raise FileExistsError('Report output exists; choose a fresh directory')
    freeze_path=final.parent/'selection-freeze.json'
    completion_path=final/'completion.json'
    frozen=read_json(freeze_path)
    completion=read_json(completion_path)
    if completion.get('status')!='COMPLETE':
        raise ValueError('Report requires a completed final evaluation')
    if completion.get('freeze_sha256')!=file_hash(freeze_path):
        raise ValueError('Completion/freeze binding mismatch')
    if not {'results.json','cases.jsonl.gz'} <= completion.get('artifacts',{}).keys():
        raise ValueError('Completion manifest omits required report evidence')
    validate_hashes(final,completion['artifacts'])
    if 'training.json' not in frozen.get('training_files',{}):
        raise ValueError('Freeze does not bind training metadata')
    validate_hashes(training,frozen['training_files'])
    trained=read_json(training/'training.json')
    results=read_json(final/'results.json')
    rows=read_rows(final/'cases.jsonl.gz')
    if digest(rows)!=completion.get('numerical_rows_sha256') or digest(results)!=completion.get('results_sha256'):
        raise ValueError('Completed numerical evidence digest mismatch')
    if trained.get('dataset_hash')!=frozen.get('dataset_hash') or completion.get('dataset_hash')!=frozen.get('dataset_hash'):
        raise ValueError('Completed/training/freeze dataset identity mismatch')
    for key in ('best_ml','champion','baselines','family_winners'):
        if trained[key]!=frozen.get(key):
            raise ValueError(f'Frozen training selection mismatch: {key}')
    if results['acceptance']!=frozen.get('acceptance'):
        raise ValueError('Frozen acceptance criteria mismatch')
    for candidate in trained['candidates'].values():
        relative=candidate['model_file']
        if frozen['training_files'].get(relative)!=candidate['model_sha256']:
            raise ValueError('Candidate model hash not bound by selection freeze')
    if trained['best_ml']!=results['best_ml'] or trained['champion']!=results['champion']:
        raise ValueError('Training/final selector identity mismatch')
    if trained['baselines']!=results['baselines']:
        raise ValueError('Training/final baseline identity mismatch')
    if set(results['partitions'])!={'final_id','final_shift'}:
        raise ValueError('Expected separate final-ID and structural-shift results')
    for partition,data in results['partitions'].items():
        subset=[r for r in rows if r['partition']==partition]
        if len(subset)!=data['support']['cases'] or sum(r['eligible'] for r in subset)!=data['support']['eligible']:
            raise ValueError('Per-case/support denominator mismatch')
    paths=[training/'training.json',final/'results.json',final/'cases.jsonl.gz',freeze_path,completion_path]
    runtimes=[]
    for directory in (training,final):
        path=directory/'runtime.json'
        if path.exists() and 'runtime.json' not in (frozen['training_files'] if directory==training else completion['artifacts']):
            raise ValueError('Runtime evidence is not bound by the completed experiment')
        runtimes.append(read_json(path) if path.exists() else {})
        if path.exists(): paths.append(path)
    output.mkdir(parents=True)
    (output/'figures').mkdir()
    with plt.rc_context({'font.family':'DejaVu Sans','svg.hashsalt':REPORT_VERSION,
                         'axes.formatter.useoffset':False,'axes.unicode_minus':False,
                         'savefig.bbox':None,'figure.dpi':100}):
        _performance(trained,results,output)
        _distribution(trained,results,rows,output)
        _confusion(trained,results,output)
        _importance(trained,output)
    (output/'REPORT.md').write_text(_report(trained,results,rows,*runtimes,training,final,output))
    manifest={'version':REPORT_VERSION,'renderer_sha256':file_hash(Path(__file__)),
              'source_evidence':{os.path.relpath(p,output):file_hash(p) for p in paths},
              'artifacts':{str(p.relative_to(output)):file_hash(p) for p in sorted(output.rglob('*')) if p.is_file()},
              'render_environment':{'matplotlib':matplotlib.__version__,'numpy':np.__version__,
                                    'font':'DejaVu Sans','svg_hashsalt':REPORT_VERSION},
              'interpretation':'saved synthetic results; renderer performs no fitting, scheduling or policy selection'}
    write_json(output/'manifest.json',manifest)
    return manifest
