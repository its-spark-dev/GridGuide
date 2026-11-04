import csv
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from research.outage_ml.audit import EVENT, MERGED, audit_csv, county_id, number, summary, timestamp, xlsx_rows
from research.outage_ml.report import table_report
from research.outage_ml.sources import fetch, validate


def encoded(rows, fields=MERGED):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def episode(**updates):
    row = dict(zip(MERGED, ["1001", "Example", "Fictional", "2020-12-31 23:45:00", "0.5", "200", "300", "250"]))
    row.update(updates)
    return row


class SourceContractTests(unittest.TestCase):
    def test_string_fips_retains_zeroes_and_rejects_float_spelling(self):
        self.assertEqual(county_id("01001"), "01001")
        self.assertEqual(county_id("1001"), "01001")
        for value in ["1001.0", "100001", "-1", "abc"]:
            with self.assertRaises(ValueError):
                county_id(value)

    def test_missing_is_distinct_from_zero_and_nonfinite_rejected(self):
        self.assertIsNone(number("NA"))
        self.assertEqual(number("0"), 0)
        with self.assertRaises(ValueError):
            number("inf")

    def test_no_invented_timezone(self):
        self.assertIsNone(timestamp("2020-01-01 00:00:00").tzinfo)
        self.assertIsNone(timestamp("NA"))

    def test_duplicate_links_are_not_independent_episodes(self):
        row = episode()
        a = audit_csv(encoded([row, row]), "fixture_merged.csv")
        self.assertEqual(a["rows"], 2)
        self.assertEqual(a["unique_county_start_keys"], 1)
        self.assertEqual(a["repeated_county_start_rows"], 1)
        self.assertEqual(a["flags"]["exact_duplicate_rows"], 1)

    def test_year_boundary_is_flag_not_censoring_imputation(self):
        a = audit_csv(encoded([episode()]), "fixture_merged.csv")
        self.assertEqual(a["flags"]["implied_end_crosses_year"], 1)
        self.assertEqual(a["duration_hours"]["median"], .5)

    def test_same_event_id_can_have_conflicting_incident_definitions(self):
        row = episode(event_id="Example-0", state_event="Example", **{
            "Datetime Event Began": "2020-12-31 12:00:00",
            "Datetime Restoration": "2020-12-31 12:00:00",
            "Event Type": "Example", "end_time": "2021-01-01 00:15:00"})
        other = {**row, "Datetime Event Began": "2020-12-30 12:00:00"}
        a = audit_csv(encoded([row, other], EVENT), "with_events_2020.csv")
        self.assertEqual(a["event_ids_with_multiple_definitions"], 1)
        self.assertEqual(a["flags"]["parent_end_not_after_start_rows"], 1)
        self.assertEqual(a["flags"]["end_time_disagrees_with_duration_rows"], 0)

    def test_customer_order_violation_is_exposed(self):
        a = audit_csv(encoded([episode(mean_customers="400")]), "fixture_merged.csv")
        self.assertEqual(a["flags"]["customer_order_violation_rows"], 1)

    def test_schema_drift_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_csv(b"fips,duration\n1001,3\n", "fixture_merged.csv")

    def test_truncated_row_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_csv((",".join(MERGED)+"\n1001,Example\n").encode(), "fixture_merged.csv")

    def test_pin_rejects_changed_source(self):
        with self.assertRaises(ValueError):
            validate(b"changed", 7, "0" * 64)

    def test_download_budget_reads_only_limit_plus_one(self):
        class Response(io.BytesIO):
            status = 200
            url = "https://example.invalid/source"
            headers = {}
        with patch("research.outage_ml.sources.urlopen", return_value=Response(b"123456")):
            with self.assertRaisesRegex(ValueError, "byte budget"):
                fetch("https://example.invalid/source", 4)

    def test_nearest_rank_quantiles_and_empty_support(self):
        self.assertEqual(summary([8, 1, 2, 3])["median"], 2)
        self.assertEqual(summary([]), {"n": 0})

    def test_workbook_reads_cached_formula_without_evaluation(self):
        ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture.xlsx'
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('xl/sharedStrings.xml', f'<sst xmlns="{ns}"><si><t>01001</t></si></sst>')
                z.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{ns}"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1"><f>1/0</f><v>7</v></c></row></sheetData></worksheet>')
            rows = xlsx_rows(path)
            self.assertEqual(rows[0][:3], ['01001', '7', ''])


class CommittedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(Path("docs/outage-ml/evidence/source-audit.json").read_text())

    def test_every_pnnl_csv_and_year_is_audited(self):
        tables = self.data["pnnl"]["tables"]
        self.assertEqual(len(tables), 50)
        self.assertEqual(len({t["member"] for t in tables}), 50)
        self.assertEqual(sum(t["rows"] for t in tables if "_merged" in t["member"]), self.data["pnnl"]["merged_rows"])

    def test_no_model_or_holdout_claim(self):
        self.assertEqual(self.data["fitted_models"], 0)
        self.assertEqual(self.data["sealed_evaluations"], 0)
        self.assertFalse(self.data["zenodo"]["full_observation_data_downloaded"])
        text = table_report(self.data)
        self.assertIn("stopped before training", text)

    def test_complete_table_regeneration(self):
        expected = Path("docs/outage-ml/presentation/MEASURED.md").read_text()
        self.assertEqual(expected, table_report(self.data))

    def test_link_row_decomposition(self):
        d = self.data["pnnl"]
        self.assertEqual(d["unlagged_link_rows"], d["unlagged_unique_county_start_keys_within_year"] + d["unlagged_repeated_county_start_rows"])


if __name__ == "__main__":
    unittest.main()
