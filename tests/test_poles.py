"""Pole recipes, size mapping and the pole-to-mounted-device bridge (offline-safe)."""
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

import openpyxl

from backend.config import RAW
from backend.data import CheckpointError, TopologyToken
from backend.poles import (WORKBOOK_LABELS, MountedDevice, PoleMatcher, PoleRecord, parse_height_ft,
                           pole_replacement_labor, prepare_pole_audit, read_pole_recipes, size_group)

RATES = {"C12": 1.9416103896103902, "D12": 0.763636363636363, "C13": 2.50295207667732, "D13": 0.9274888178913726,
         "C14": 3.368367816091952, "D14": 1.153195402298852, "A3": 0.3741146496815283, "B3": 0.21217834394904417}
XF = ("eo_power_xfrmr_inst", "100")
FU = ("eo_isolating_eqpt_inst", "200")


def workbook(path: Path, **overrides):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Labor time material related"
    for cell, value in {**WORKBOOK_LABELS, **RATES, **overrides}.items():
        ws[cell] = value
    wb.save(path)
    return path


def matcher(devices=(), tokens=None, poles=None):
    poles = poles or (PoleRecord(1, "L1", (0.0, 0.0), 40, "Medium"), PoleRecord(2, "L2", (100.0, 0.0), 35, "Small"),
                      PoleRecord(3, "L3", (200.0, 0.0), None, None))
    tokens = tokens if tokens is not None else {XF: TopologyToken(XF[0], XF[1], "Distribution", "L1"),
                                                FU: TopologyToken(FU[0], FU[1], "Fuse", "L1")}
    return PoleMatcher(tuple(poles), tuple(devices), tokens)


class PoleTests(unittest.TestCase):
    def test_height_parsing_and_workbook_ranges(self):
        self.assertEqual(parse_height_ft("40 Feet"), 40)
        for bad in ("Unknown", "", None, "40", "forty Feet"):
            self.assertIsNone(parse_height_ft(bad))
        cases = {25: "Small", 35: "Small", 40: "Medium", 55: "Medium", 60: "Large", 95: "Large",
                 17: None, 24: None, 36: None, 38: None, 56: None, 59: None, None: None}
        for height, expected in cases.items():
            self.assertEqual(size_group(height), expected, height)

    def test_recipes_are_label_checked_and_exact(self):
        with tempfile.TemporaryDirectory() as d:
            recipes = {r.id: r for r in read_pole_recipes(workbook(Path(d) / "w.xlsx"))}
        self.assertEqual(set(recipes), {"pole-small-replace", "pole-medium-replace", "pole-large-replace", "crossarm-replace"})
        self.assertEqual(recipes["pole-medium-replace"].install_hours, Decimal("2.502952076677"))
        self.assertEqual(recipes["pole-medium-replace"].source_refs,
                         ("Labor time material related!C13", "Labor time material related!D13"))

    def test_changed_label_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path = workbook(Path(d) / "w.xlsx", B13="40-55 feet")
            with self.assertRaises(CheckpointError) as error:
                read_pole_recipes(path)
        self.assertEqual(error.exception.code, "labor_schema_mismatch")

    def test_replacement_labor_applies_multiplier_once(self):
        with tempfile.TemporaryDirectory() as d:
            recipes = read_pole_recipes(workbook(Path(d) / "w.xlsx"))
        labor = pole_replacement_labor(recipes, "Medium", Decimal("4.5"))
        direct = Decimal("2.502952076677") + Decimal("0.927488817891") + Decimal("0.374114649682") + Decimal("0.212178343949")
        self.assertEqual(labor.direct_hours, direct)
        self.assertEqual(labor.person_hours, direct * Decimal("4.5"))
        self.assertEqual(labor.install_hours + labor.remove_hours, labor.direct_hours)
        bare = pole_replacement_labor(recipes, "Medium", Decimal("4.5"), include_crossarm=False)
        self.assertEqual(bare.recipe_ids, ("pole-medium-replace",))
        with self.assertRaises(CheckpointError):
            pole_replacement_labor(recipes, "Medium", Decimal("0"))

    def test_match_with_resolved_mounted_devices(self):
        devices = (MountedDevice(1, "Transformer_Clip", XF, "Distribution", "L1"),
                   MountedDevice(1, "Fuse_Bank_Clip", FU, "Fuse", "L1"))
        result = matcher(devices).match(7, (3.0, 0.0))
        self.assertEqual((result.status, result.pole_row, result.size, result.labor_available), ("spatial_candidate", 1, "Medium", True))
        self.assertEqual(result.impact_basis, "mounted_device_bridge")
        self.assertEqual(result.device_keys, tuple(sorted((XF, FU))))
        self.assertEqual(result.reasons, ())

    def test_pole_without_device_keeps_labor_but_impact_unavailable(self):
        result = matcher().match(1, (101.0, 0.0))
        self.assertEqual((result.status, result.size, result.labor_available), ("spatial_candidate", "Small", True))
        self.assertEqual((result.impact_basis, result.device_keys, result.reasons), ("unavailable", (), ("no_mounted_device_on_pole",)))

    def test_unknown_height_is_not_substituted(self):
        result = matcher().match(1, (199.0, 0.0))
        self.assertEqual((result.size, result.labor_available), (None, False))
        self.assertIn("pole_size_unavailable", result.reasons)

    def test_far_and_ambiguous_damage_are_unavailable(self):
        self.assertEqual(matcher().match(1, (50.0, 30.0)).reasons, ("pole_unmatched",))
        close = (PoleRecord(1, "L1", (0.0, 0.0), 40, "Medium"), PoleRecord(2, "L2", (8.0, 0.0), 40, "Medium"))
        result = matcher(poles=close).match(1, (2.0, 0.0))
        self.assertEqual((result.status, result.reasons), ("unavailable", ("pole_ambiguous",)))

    def test_any_unresolved_mounted_device_withholds_bridge(self):
        stray = ("eo_isolating_eqpt_inst", "999")
        devices = (MountedDevice(1, "Transformer_Clip", XF, "Distribution", "L1"),
                   MountedDevice(2, "Recloser_Bank_Clip", stray, "Recloser", "L1"))
        result = matcher(devices).match(1, (0.0, 0.0))
        self.assertEqual((result.impact_basis, result.device_keys), ("unavailable", ()))
        self.assertIn("unresolved_mounted_device_identity", result.reasons)

    def test_duplicate_pole_label_withholds_bridge(self):
        poles = (PoleRecord(1, "L1", (0.0, 0.0), 40, "Medium"), PoleRecord(2, "L1", (500.0, 0.0), 40, "Medium"))
        devices = (MountedDevice(1, "Transformer_Clip", XF, "Distribution", "L1"),)
        result = matcher(devices, poles=poles).match(1, (0.0, 0.0))
        self.assertEqual(result.reasons, ("pole_location_label_not_unique",))

    @unittest.skipUnless((RAW / "Data1.zip").exists(), "pinned challenge sources not present")
    def test_pinned_sources_summary(self):
        summary = prepare_pole_audit().safe_summary()
        self.assertEqual(summary["arcos_pole_observations"], 355)
        self.assertEqual(summary["pole_inventory"], 107013)
        self.assertLessEqual(summary["candidates_with_device_bridge"], summary["spatial_candidates"])
        self.assertLessEqual(summary["candidates_with_labor"], summary["spatial_candidates"])
        self.assertFalse(summary["direct_identifier_join"])


if __name__ == "__main__":
    unittest.main()