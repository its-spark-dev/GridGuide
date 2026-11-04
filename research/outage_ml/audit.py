"""Reproducible descriptive audit. No fitting, splitting or label imputation."""
from __future__ import annotations

import csv
import io
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

from . import VERSION
from .sources import SOURCES, digest, validate

MERGED = ["fips", "state", "county", "start_time", "duration", "min_customers", "max_customers", "mean_customers"]
EVENT = ["event_id", "state_event", "Datetime Event Began", "Datetime Restoration", "Event Type", *MERGED[:5], "end_time", *MERGED[5:]]
GROUP = ["state", "year", "month", "outage_count", "max_outage_duration", "customer_weighted_hours"]
MISSING = {"", "NA", "N/A", "NaN", "nan", "None", "null"}


def number(value: str) -> float | None:
    if value in MISSING:
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Nonfinite source value")
    return result


def timestamp(value: str) -> datetime | None:
    if value in MISSING:
        return None
    return datetime.fromisoformat(value)


def county_id(value: str) -> str:
    if not re.fullmatch(r"[0-9]{1,5}", value):
        raise ValueError("Invalid FIPS spelling")
    return value.zfill(5)


def summary(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    def q(p: float) -> float:
        # Nearest-rank empirical quantile; no hidden numerical dependency.
        return ordered[max(0, math.ceil(p * len(ordered)) - 1)]
    return {"n": len(values), "min": ordered[0], "median": q(.5), "p90": q(.9),
            "p99": q(.99), "max": ordered[-1]}


def audit_csv(data: bytes, name: str) -> dict:
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    expected = EVENT if "with_events" in name else MERGED if "merged" in name else GROUP
    if "lag" in name:
        expected = [c for c in EVENT if c != "end_time"]
    if reader.fieldnames != expected:
        raise ValueError(f"Source schema drift: {name}: {reader.fieldnames}")
    missing = Counter({k: 0 for k in expected})
    flags = Counter()
    exact, episodes = set(), Counter()
    states, counties = set(), set()
    parents = defaultdict(set)
    parent_rows = Counter()
    durations, minima = [], []
    months = Counter()
    earliest = latest = None
    histogram = [0] * 6
    n = 0
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("Malformed CSV row")
        n += 1
        missing.update(k for k, v in row.items() if v in MISSING)
        row_hash = digest(json.dumps(row, sort_keys=True).encode())
        flags["exact_duplicate_rows"] += row_hash in exact
        exact.add(row_hash)
        states.add(row["state"])
        if "duration" not in row:
            continue
        fips = county_id(row["fips"])
        counties.add(fips)
        start, duration = timestamp(row["start_time"]), number(row["duration"])
        if start is None or duration is None:
            flags["missing_episode_time_or_duration"] += 1
            continue
        flags["timezone_unspecified_rows"] += start.tzinfo is None
        durations.append(duration)
        flags["nonpositive_duration_rows"] += duration <= 0
        flags["off_quarter_hour_duration_rows"] += abs(duration * 4 - round(duration * 4)) > 1e-8
        histogram[next((i for i, edge in enumerate([1, 4, 12, 24, 72]) if duration <= edge), 5)] += 1
        months[str(start.month)] += 1
        earliest = min(start, earliest) if earliest else start
        latest = max(start, latest) if latest else start
        end = start + timedelta(hours=duration)
        flags["implied_end_crosses_year"] += end.year != start.year
        flags["starts_january_1_midnight"] += start.month == 1 and start.day == 1 and start.hour == 0 and start.minute == 0
        flags["implied_end_december_31_or_january_1"] += (end.month, end.day) in {(12, 31), (1, 1)}
        episodes[(fips, row["start_time"])] += 1
        counts = [number(row[c]) for c in MERGED[5:]]
        if all(v is not None for v in counts):
            lo, hi, mean = counts
            minima.append(lo)
            flags["customer_order_violation_rows"] += not (0 <= lo <= mean <= hi)
        if "event_id" in row:
            parent = (row["Datetime Event Began"], row["Datetime Restoration"], row["Event Type"], row["state_event"])
            parents[row["event_id"]].add(parent)
            parent_rows[parent] += 1
            a, b = timestamp(parent[0]), timestamp(parent[1])
            if a is None or b is None:
                flags["missing_parent_timestamp_rows"] += 1
            else:
                flags["parent_end_not_after_start_rows"] += b <= a
                flags["episode_starts_before_parent_rows"] += start < a
                flags["episode_starts_after_parent_end_rows"] += start > b
            if "end_time" in row:
                given = timestamp(row["end_time"])
                flags["end_time_disagrees_with_duration_rows"] += given != end
    return {"member": name, "bytes": len(data), "sha256": digest(data), "schema": expected,
            "rows": n, "missing_cells": dict(missing), "flags": dict(sorted(flags.items())),
            "state_labels": len(states), "county_ids": len(counties),
            "duration_hours": summary(durations), "minimum_customers": summary(minima),
            "duration_histogram": {k: v for k, v in zip(["(0,1]", "(1,4]", "(4,12]", "(12,24]", "(24,72]", ">72"], histogram)},
            "first_start": earliest.isoformat() if earliest else None,
            "last_start": latest.isoformat() if latest else None, "start_month_counts": dict(sorted(months.items())),
            "unique_county_start_keys": len(episodes), "repeated_county_start_rows": sum(v-1 for v in episodes.values()),
            "event_id_count": len(parents), "event_ids_with_multiple_definitions": sum(len(v) > 1 for v in parents.values()),
            "distinct_parent_definitions": len(parent_rows)}


def xlsx_rows(path: Path) -> list[list[str]]:
    """Read cached OOXML values only; never execute formulas or external links."""
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist()) > 10_000_000:
            raise ValueError("Workbook expansion exceeds budget")
        strings = ["".join(node.itertext()) for node in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("x:si", ns)]
        result = []
        for row in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).findall("x:sheetData/x:row", ns):
            cells = [""] * 57
            for c in row:
                # Cached values are source evidence. Formulas are never evaluated.
                col = re.match(r"[A-Z]+", c.attrib["r"]).group()
                index = 0
                for char in col:
                    index = 26 * index + ord(char) - 64
                if index > 57:
                    raise ValueError("Workbook column count changed")
                value = c.findtext("x:v", default="", namespaces=ns)
                cells[index-1] = strings[int(value)] if c.get("t") == "s" else value
            result.append(cells)
        return result


def audit_purdue(path: Path) -> dict:
    rows = xlsx_rows(path)
    header_index = next(i for i, r in enumerate(rows) if r[:3] == ["variables", "OBS", "YEAR"])
    header = rows[header_index]
    data = [dict(zip(header, r)) for r in rows[header_index+2:] if r[1] not in MISSING]
    missing = {k: sum(r[k] in MISSING for r in data) for k in header if k != "variables"}
    flags = Counter()
    durations = []
    starts, ids = Counter(), Counter()
    years = Counter()
    timestamp_differences = Counter()
    for r in data:
        ids[r["OBS"]] += 1
        years[r["YEAR"]] += 1
        d = number(r["OUTAGE.DURATION"])
        if d is not None:
            durations.append(d / 60)
            flags["nonpositive_duration_rows"] += d <= 0
        values = [number(r[k]) for k in ["OUTAGE.START.DATE", "OUTAGE.START.TIME", "OUTAGE.RESTORATION.DATE", "OUTAGE.RESTORATION.TIME"]]
        if values[0] is not None and values[1] is not None:
            starts[(r["U.S._STATE"], round((values[0] + values[1]) * 1440))] += 1
        if d is not None and all(v is not None for v in values):
            a, b, c, e = values
            flags["duration_and_four_timestamps_present"] += 1
            difference = ((c + e) - (a + b)) * 1440
            flags["duration_timestamp_mismatch_over_one_minute"] += abs(difference - d) > 1
            if abs(difference - d) > 1:
                timestamp_differences[str(round(difference - d))] += 1
            flags["restoration_before_start"] += difference < 0
    with zipfile.ZipFile(path) as z:
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        xml = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        formulas = [c for c in xml.findall(".//x:c", ns) if c.find("x:f", ns) is not None]
        formula_columns = Counter(re.match(r"[A-Z]+", c.attrib["r"]).group() for c in formulas)
        texts = z.read("xl/sharedStrings.xml").decode()
        license_mentions = bool(re.search(r"creative commons|redistribut|licen[cs]e", texts, re.I))
    return {"rows": len(data), "schema": header[1:], "missing_cells": missing,
            "duration_hours": summary(durations), "flags": dict(flags), "year_rows": dict(sorted(years.items())),
            "timestamp_minus_duration_minutes": dict(sorted(timestamp_differences.items())),
            "duplicate_observation_ids": sum(v-1 for v in ids.values()),
            "repeated_state_start_rows": sum(v-1 for v in starts.values()),
            "state_labels": len({r['U.S._STATE'] for r in data}),
            "timezone": "not specified in workbook or reviewed descriptor",
            "formula_cached_values_by_column": dict(sorted(formula_columns.items())),
            "license_keywords_in_workbook": license_mentions,
            "license_status": "article CC-BY-4.0; workbook-specific grant not established"}


def run(cache: Path) -> dict:
    for name, (_, size, sha) in SOURCES.items():
        validate((cache / name).read_bytes(), size, sha)
    tables, members = [], []
    with zipfile.ZipFile(cache / "pnnl-v2.zip") as z:
        if len(z.infolist()) != 52 or sum(i.file_size for i in z.infolist()) > 250_000_000:
            raise ValueError("Archive inventory or expansion limit changed")
        for item in z.infolist():
            if item.is_dir():
                continue
            raw = z.read(item)
            members.append({"name": item.filename, "bytes": len(raw), "sha256": digest(raw)})
            if item.filename.endswith(".csv"):
                tables.append(audit_csv(raw, item.filename))
            elif item.filename.endswith("Disclaimer.docx"):
                validate(raw, SOURCES["pnnl-disclaimer.docx"][1], SOURCES["pnnl-disclaimer.docx"][2])
            else:
                raise ValueError("Unexpected embedded artifact")
    merged = [t for t in tables if "_merged" in t["member"]]
    linked = [t for t in tables if "with_events" in t["member"] and "lag" not in t["member"]]
    zenodo = json.loads((cache / "zenodo-metadata.json").read_text())
    sensitivity = {p.name: list(csv.DictReader(io.StringIO(p.read_text()))) for p in sorted(cache.glob("*_Sensitivity_Summary.csv"))}
    return {"version": VERSION, "pnnl": {"members": members, "tables": tables,
            "merged_rows": sum(t["rows"] for t in merged),
            "unlagged_link_rows": sum(t["rows"] for t in linked),
            "unlagged_unique_county_start_keys_within_year": sum(t["unique_county_start_keys"] for t in linked),
            "unlagged_repeated_county_start_rows": sum(t["repeated_county_start_rows"] for t in linked),
            "unlagged_ambiguous_year_event_ids": sum(t["event_ids_with_multiple_definitions"] for t in linked),
            "timezone": "unspecified; naive source timestamps retained; UTC conversion withheld",
            "censoring": "unavailable, not inferred from blank-cell completeness"},
            "purdue": audit_purdue(cache / "purdue.xlsx"),
            "zenodo": {"record_id": zenodo["id"], "doi": zenodo["doi"],
                       "license": zenodo["metadata"]["license"],
                       "files_advertised_not_all_downloaded": [{k: f[k] for k in ["key", "size", "checksum"]} for f in zenodo["files"]],
                       "sensitivity_summaries": sensitivity,
                       "full_observation_data_downloaded": False},
            "fitted_models": 0, "sealed_evaluations": 0}


def save(value: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
