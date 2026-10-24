"""Complete reverse evidence and exact dependency releases, without public IDs."""
from dataclasses import replace
import json
import unittest

from backend.data import CheckpointError, parse_topology, source_hashes
from backend.network import Customer, Equipment, build_network, prepare_network, public_asset_alias


TRANSFORMER = "eo_power_xfrmr_inst"
FUSE = "eo_isolating_eqpt_inst"
CIRCUIT = "eo_circuit"


def fixture():
    topology = parse_topology([
        "001\teo_power_xfrmr_inst*01*Distribution*T1\teo_isolating_eqpt_inst*1*Fuse*F1\teo_circuit*C*Circuit Breaker*C",
        "002\teo_power_xfrmr_inst*02*Distribution*T2\teo_isolating_eqpt_inst*1*Fuse*F1\teo_circuit*C*Circuit Breaker*C",
        "003\teo_power_xfrmr_inst*03*Distribution*T3\teo_isolating_eqpt_inst*2*Fuse*F2\teo_circuit*C*Circuit Breaker*C",
        "004\teo_power_xfrmr_inst*04*Distribution*T4\teo_isolating_eqpt_inst*3*Fuse*F3\teo_isolating_eqpt_inst*2*Fuse*F2\teo_circuit*C*Circuit Breaker*C",
    ])
    nodes = {t.key: t for path in topology.paths.values() for t in path}
    equipment = []
    for i, (key, node) in enumerate(nodes.items(), 1):
        if node.entity == CIRCUIT:
            continue
        parent = nodes[next(iter(topology.parents[key]))]
        equipment.append(Equipment(key, "Transformer_Clip" if node.entity == TRANSFORMER else "Fuse_Bank_Clip",
                                   i, node.kind, node.location_code, "CIRCUIT" if parent.entity == CIRCUIT else parent.location_code,
                                   "C", "alias-c", "station-c", (0.0, 0.0)))
    customers = [Customer(p, i, path[0].location_code, "C", (0.0, 0.0))
                 for i, (p, path) in enumerate(topology.paths.items(), 1)]
    return topology, equipment, customers


class NetworkValidationTests(unittest.TestCase):
    def test_unions_overlap_and_releases_use_distinct_complete_premise_sets(self):
        network = build_network(*fixture())
        first, second, child, transformer = (FUSE, "1"), (FUSE, "2"), (FUSE, "3"), (TRANSFORMER, "01")
        damage = {first, second, child, transformer}
        self.assertEqual(network.dependents(first), frozenset({"001", "002"}))
        self.assertEqual(network.affected_union(damage), frozenset({"001", "002", "003", "004"}))
        self.assertEqual(network.released_premises(damage, {first}), frozenset({"002"}))
        self.assertEqual(network.released_premises(damage, {first, second}), frozenset({"002", "003"}))
        self.assertEqual(network.released_premises(damage, damage), network.affected_union(damage))
        dependencies = network.upstream_damaged_dependencies(damage)
        self.assertEqual(dependencies[first], frozenset())
        self.assertEqual(dependencies[second], frozenset())
        self.assertEqual(dependencies[child], frozenset({second}))
        self.assertEqual(dependencies[transformer], frozenset({first}))
        self.assertEqual(sum(map(len, network.release_groups(damage).values())), 4)
        with self.assertRaises(CheckpointError):
            network.released_premises(damage, {(FUSE, "unknown")})

    def test_unmatched_gis_or_customer_withholds_whole_asset_not_filtered_count(self):
        topology, equipment, customers = fixture()
        for broken_equipment, broken_customers, reason in (
            ([a for a in equipment if a.key != (TRANSFORMER, "02")], customers, "missing_GIS_ID"),
            (equipment, customers[:-3] + customers[2:], "missing_customer"),
            (equipment, customers + [customers[1]], "ambiguous_customer"),
        ):
            with self.subTest(reason=reason):
                network = build_network(topology, broken_equipment, broken_customers)
                self.assertEqual(network.raw_membership((FUSE, "1")), frozenset({"001", "002"}))
                self.assertIsNone(network.dependents((FUSE, "1")))
                self.assertIn(reason, network.rejection_reasons((FUSE, "1")))
                self.assertIsNone(network.affected_union({(FUSE, "1"), (FUSE, "2")}))
                self.assertIsNone(network.release_groups({(FUSE, "1")}))
                self.assertEqual(network.dependents((FUSE, "2")), frozenset({"003", "004"}))

    def test_metadata_parent_identity_and_circuit_conflicts_are_explicit(self):
        topology, equipment, customers = fixture()
        target = next(a for a in equipment if a.key == (TRANSFORMER, "01"))
        for change, reason in (
            ({"location_code": "wrong"}, "GIS_location_conflict"),
            ({"kind": "Step"}, "GIS_type_conflict"),
            ({"upstream_location": "wrong"}, "GIS_parent_conflict"),
            ({"circuit_id": "other"}, "device_customer_circuit_conflict"),
            ({"station_alias": "other"}, "path_alias_station_conflict"),
        ):
            with self.subTest(reason=reason):
                changed = [replace(a, **change) if a == target else a for a in equipment]
                network = build_network(topology, changed, customers)
                self.assertIsNone(network.dependents((FUSE, "1")))
                self.assertIn(reason, network.rejection_reasons((FUSE, "1")))
        duplicate = build_network(topology, equipment + [replace(target, source_layer="other")], customers)
        self.assertIn("ambiguous_GIS_ID", duplicate.rejection_reasons((FUSE, "1")))
        crosswalk = build_network(topology, equipment, customers, circuit_evidence=(("other-code", "alias-c", "station-c"),))
        self.assertIn("circuit_crosswalk_conflict", crosswalk.rejection_reasons((FUSE, "2")))

    def test_unknown_is_null_and_aliases_preserve_typed_leading_zero_identity(self):
        network = build_network(*fixture())
        self.assertIsNone(network.raw_membership((FUSE, "missing")))
        self.assertIsNone(network.dependents((FUSE, "missing")))
        self.assertEqual(network.rejection_reasons((FUSE, "missing")), ("unknown_topology_asset",))
        self.assertNotEqual(public_asset_alias((TRANSFORMER, "01")), public_asset_alias((TRANSFORMER, "1")))
        self.assertNotEqual(public_asset_alias((TRANSFORMER, "01")), public_asset_alias((FUSE, "01")))
        key = (TRANSFORMER, "01")
        self.assertEqual(network.key_for_alias(public_asset_alias(key)), key)
        coverage = json.dumps(network.coverage)
        self.assertNotIn("station-c", coverage)
        self.assertNotIn("alias-c", coverage)
        self.assertEqual(network.coverage["fully_verified_paths"], 4)

    def test_conflicting_parent_is_retained_and_never_promoted_to_verified(self):
        topology, equipment, customers = fixture()
        lines = [premise + "\t" + "\t".join("*".join((t.entity, t.identifier, t.kind, t.location_code)) for t in path)
                 for premise, path in topology.paths.items()]
        lines.append("005\teo_power_xfrmr_inst*05*Distribution*T5\teo_isolating_eqpt_inst*1*Fuse*F1\teo_isolating_eqpt_inst*2*Fuse*F2\teo_circuit*C*Circuit Breaker*C")
        topology = parse_topology(lines)
        equipment.append(Equipment((TRANSFORMER, "05"), "Transformer_Clip", 99, "Distribution", "T5", "F1",
                                   "C", "alias-c", "station-c", (0.0, 0.0)))
        customers.append(Customer("005", 99, "T5", "C", (0.0, 0.0)))
        network = build_network(topology, equipment, customers)
        self.assertEqual(len(network.raw_membership((FUSE, "1"))), 3)
        self.assertIn("multiple_parents", network.rejection_reasons((FUSE, "1")))
        self.assertIsNone(network.dependents((FUSE, "1")))
        self.assertIsNone(network.upstream_damaged_dependencies({(FUSE, "1")}))


class PinnedNetworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes = source_hashes()
        cls.network = prepare_network()

    @classmethod
    def tearDownClass(cls):
        if source_hashes() != cls.hashes:
            raise AssertionError("Source bytes changed")

    def test_full_audit_denominators_and_supported_complete_reverse_coverage(self):
        coverage = self.network.coverage
        self.assertEqual(coverage["customer_rows"], 117642)
        self.assertEqual(coverage["topology_paths"], 117599)
        self.assertEqual(coverage["topology_assets"], 32600)
        self.assertEqual(coverage["topology_memberships"], 490090)
        self.assertEqual(coverage["customer_rows_missing_paths"], 47)
        self.assertEqual(coverage["topology_paths_missing_customers"], 4)
        self.assertEqual(coverage["all_gis_ids_resolved_paths"], 52322)
        self.assertEqual(coverage["fully_verified_paths"], 40779)
        self.assertEqual(coverage["by_kind"]["Distribution"]["fully_verified_reverse_assets"], 6103)
        self.assertEqual(coverage["by_kind"]["Fuse"]["fully_verified_reverse_assets"], 1990)
        self.assertEqual(coverage["by_kind"]["Recloser (Hydraulic)"]["fully_verified_reverse_assets"], 0)
        self.assertIs(self.network, prepare_network())

    def test_golden_and_independent_nested_branches_keep_exact_union_and_releases(self):
        n = self.network
        transformer = n.key_for_locator("Transformer_Clip", 24215)
        golden = n.key_for_locator("Fuse_Bank_Clip", 6096)
        independent = n.key_for_locator("Fuse_Bank_Clip", 6085)
        parent = n.key_for_locator("Fuse_Bank_Clip", 6271)
        child = n.key_for_locator("Fuse_Bank_Clip", 6230)
        self.assertEqual([len(n.dependents(k)) for k in (transformer, golden, independent, parent, child)], [1, 4, 29, 23, 12])
        self.assertTrue(n.dependents(transformer) <= n.dependents(golden))
        self.assertTrue(n.dependents(child) <= n.dependents(parent))
        self.assertFalse(n.dependents(golden) & n.dependents(independent))
        self.assertFalse(n.dependents(independent) & n.dependents(parent))
        damaged = {transformer, golden, independent, parent, child}
        self.assertEqual(len(n.affected_union(damaged)), 56)
        self.assertEqual(len(n.released_premises(damaged, {parent})), 11)
        self.assertEqual(len(n.released_premises(damaged, {parent, child})), 23)
        self.assertEqual(len(n.released_premises(damaged, damaged)), 56)
        prerequisites = n.upstream_damaged_dependencies(damaged)
        self.assertEqual(prerequisites[child], frozenset({parent}))
        self.assertEqual(prerequisites[transformer], frozenset({golden}))
        self.assertEqual(prerequisites[independent], frozenset())
        premise = n.customers[1076].premise
        terminal = n.topology.paths[premise][-1].key
        self.assertEqual(len(n.raw_membership(terminal)), 1563)
        self.assertEqual(sum(not n.path_reasons[p] for p in n.raw_membership(terminal)), 115)
        self.assertIsNone(n.dependents(terminal))


if __name__ == "__main__":
    unittest.main()
