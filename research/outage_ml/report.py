"""Figures describe the source inventory, never predictive performance."""
from __future__ import annotations

import json
from pathlib import Path

from .sources import digest


def render(evidence: Path, output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    data = json.loads(evidence.read_text())
    tables = data["pnnl"]["tables"]
    merged = [t for t in tables if "_merged" in t["member"]]
    linked = [t for t in tables if "with_events" in t["member"] and "lag" not in t["member"]]
    years = list(range(2014, 2024))
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.titleweight": "bold", "savefig.facecolor": "#f7f9fc"})
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.8), facecolor="#f7f9fc")
    ax[0].bar(years, [t["rows"] for t in merged], color="#168577")
    ax[0].set(title="Recorded episode volume changes sharply", ylabel="County episode rows", xlabel="Source file year")
    ax[0].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    ax[1].bar(years, [t["unique_county_start_keys"] for t in linked], color="#244b76", label="Distinct county/start keys")
    ax[1].bar(years, [t["repeated_county_start_rows"] for t in linked], bottom=[t["unique_county_start_keys"] for t in linked], color="#d5933c", label="Additional rows for those keys")
    ax[1].set(title="Incident links are not independent episodes", ylabel="Unlagged linked rows", xlabel="Source file year")
    ax[1].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    ax[1].legend(frameon=False, fontsize=9)
    for a in ax:
        a.set_xticks(years[::2]); a.grid(axis="y", alpha=.15); a.set_axisbelow(True)
    fig.suptitle("ML Lab II · measure the evidence before fitting", x=.06, ha="left", fontsize=17, fontweight="bold", color="#16304b")
    fig.text(.06, .02, "PNNL Outage Dataset v2 · 2014 contains November–December starts only. Volume is not an outage-risk trend.", fontsize=9)
    fig.tight_layout(rect=(.02, .07, 1, .9))
    fig.savefig(output / "source-landscape.png", dpi=160, metadata={"Software": "GridGuide outage-source-audit-v1"})
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5), facecolor="#f7f9fc")
    bins = list(merged[0]["duration_histogram"])
    # JSON serialization sorts keys: use explicit numeric ordering, not lexical order.
    bins = ["(0,1]", "(1,4]", "(4,12]", "(12,24]", "(24,72]", ">72"]
    colors = ["#284c76", "#237e92", "#24a68f", "#8ab66d", "#d4b04c", "#cf7957"]
    left = [0.] * len(merged)
    for name, color in zip(bins, colors):
        values = [100*t["duration_histogram"][name]/t["rows"] for t in merged]
        ax.barh(years, values, left=left, color=color, label=name)
        left = [a+b for a, b in zip(left, values)]
    ax.set(xlim=(0, 100), xlabel="Share of recorded county episodes (%)", ylabel="Source file year", yticks=years)
    ax.legend(title="Recorded duration, hours", ncol=6, loc="lower center", bbox_to_anchor=(.5, 1.01), frameon=False)
    fig.suptitle("Reported duration is not verified restoration time", x=.06, ha="left", fontsize=17, fontweight="bold", color="#16304b")
    fig.text(.06, .025, f"PNNL v2 merged files · n={data['pnnl']['merged_rows']:,} · no imputation · unknown censoring and source coverage", fontsize=9)
    fig.tight_layout(rect=(.02, .07, 1, .89))
    fig.savefig(output / "recorded-duration.png", dpi=160, metadata={"Software": "GridGuide outage-source-audit-v1"})
    plt.close(fig)
    manifest = {"source_sha256": digest(evidence.read_bytes()), "files": {p.name: digest(p.read_bytes()) for p in sorted(output.glob("*.png"))}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def table_report(data: dict) -> str:
    text = ["# Measured source inventory", "", "Generated from `evidence/source-audit.json`. Counts describe files, not independent storms.", "",
            "| Year | Merged episodes | Linked rows (unlagged) | Distinct county/start keys | Repeated linked rows | Ambiguous year/event IDs |", "|---|---:|---:|---:|---:|---:|"]
    tables = data["pnnl"]["tables"]
    for year in range(2014, 2024):
        m = next(t for t in tables if t["member"].endswith(f"_{year}_merged.csv"))
        e = next(t for t in tables if t["member"].endswith(f"with_events_{year}.csv"))
        text.append(f"| {year} | {m['rows']:,} | {e['rows']:,} | {e['unique_county_start_keys']:,} | {e['repeated_county_start_rows']:,} | {e['event_ids_with_multiple_definitions']} |")
    text += ["", "## Purdue workbook checks", "", "| Check | Count |", "|---|---:|"]
    p = data["purdue"]
    for key, value in [("Rows", p["rows"]), ("Missing duration", p["missing_cells"]["OUTAGE.DURATION"]), *p["flags"].items(), ("Repeated state/start rows", p["repeated_state_start_rows"])]:
        text.append(f"| {key} | {value:,} |")
    text += ["", "Missing durations are not zero durations. Timestamp agreement is an internal check, not external validation.", "",
             "## Zenodo bounded inspection", "", "Only metadata, the descriptor and three small sensitivity summaries were acquired. Full observation counts are unmeasured.", "",
             "No train/development/test partition, fitted model, or held-out score exists. The feasibility gate stopped before training.", ""]
    return "\n".join(text)
