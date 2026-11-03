"""Author small fictional graphs from literals; never import or read challenge data."""
import argparse
import hashlib
import json
from pathlib import Path


def definitions():
    def make(name, label, purpose, parent_map, paths, work, *, blocked=(), unresolved=(), critical=()):
        sid = f"syn-{name}"
        ident = lambda kind, key: f"{sid}-{kind}-{key}"
        evidence = [
            dict(id="ev-topology", classification="scenario assumption", origin="synthetic_definition",
                 detail="Equipment, customers and dependencies are independently authored fiction; no real network was copied or transformed."),
            dict(id="ev-scope", classification="scenario assumption", origin="synthetic_definition",
                 detail="The listed fictional repairs are declared damage scope, not observed damage or quantities."),
            dict(id="ev-labor", classification="scenario assumption", origin="synthetic_definition",
                 detail="Literal total repair person-hours are fictional engineering inputs. No workbook rates, elapsed times or extra multipliers are implied."),
            dict(id="ev-access", classification="scenario assumption", origin="synthetic_definition",
                 detail="Access states are declared fiction. Blocked access does not supply a clearance time."),
            dict(id="ev-precedence", classification="prototype policy", origin="prototype_rule",
                 detail="Listed repair prerequisites are an explicit conservative scenario policy, separate from the customer supply path."),
            dict(id="ev-crews", classification="scenario assumption", origin="synthetic_definition",
                 detail="One four-person interchangeable crew is assumed available at modeled response time zero. Actual staffing is unknown."),
            dict(id="ev-supply", classification="scenario assumption", origin="synthetic_definition",
                 detail="Supply is assumed available at an abstract, unlocated fictional terminal."),
            dict(id="ev-unavailable", classification="unavailable", origin="missing_evidence",
                 detail="Actual productivity, current outage confirmation and restoration outcomes are unavailable; unresolved links stay unknown."),
        ]
        if critical:
            evidence.append(dict(id="ev-critical", classification="scenario assumption", origin="synthetic_definition",
                                 detail="Critical-service attachment is explicitly authored fiction, never inferred from geography or a customer's personal needs."))
        names = ["supply", *parent_map]
        assets = [dict(id=ident("asset", a), kind="supply_terminal" if a == "supply" else "unresolved" if a in unresolved else "transformer" if a.startswith("t") else "fuse",
                       identity_status="unresolved" if a in unresolved else "defined_in_fixture",
                       evidence_ref="ev-unavailable" if a in unresolved else "ev-topology") for a in names]
        links = [dict(downstream_id=ident("asset", a), upstream_id=ident("asset", parent),
                      status="unresolved" if a in unresolved or parent in unresolved else "defined_in_fixture",
                      evidence_ref="ev-unavailable" if a in unresolved or parent in unresolved else "ev-topology") for a, parent in parent_map.items()]
        customer_paths = [dict(customer_id=ident("customer", str(i)), asset_ids=[ident("asset", a) for a in path],
                               evidence_ref="ev-unavailable" if set(path) & set(unresolved) else "ev-topology") for i, path in enumerate(paths, 1)]
        repairs = [dict(id=ident("repair", a), asset_id=ident("asset", a), repair_person_hours=hours,
                        access="blocked" if a in blocked else "clear", prerequisite_ids=[ident("repair", p) for p in prerequisites],
                        scope_evidence_ref="ev-scope", labor_evidence_ref="ev-unavailable" if hours is None else "ev-labor",
                        access_evidence_ref="ev-access", precedence_evidence_ref="ev-precedence") for a, hours, prerequisites in work]
        return dict(id=sid, revision=1, label=label, purpose=purpose,
                    topology_status="partial_by_construction" if unresolved else "valid_by_construction",
                    assets=assets, links=links, customer_paths=customer_paths, repairs=repairs,
                    critical_services=[dict(id=ident("service", str(i)), customer_id=ident("customer", str(i)), evidence_ref="ev-critical") for i in critical],
                    crews=dict(count=1, people_per_crew=4, available_at_hours=[0.0], evidence_ref="ev-crews", efficiency_evidence_ref="ev-unavailable"),
                    supply_evidence_ref="ev-supply", operational_evidence_ref="ev-unavailable", evidence=evidence)

    return dict(version="synthetic-catalog-v1", generator_version="fictional-graphs-v1", scenarios=[
        make("simple", "Fictional simple path", "A two-repair serial path with distinct person-hour inputs.",
             {"f1": "supply", "t1": "f1"}, [["t1", "f1", "supply"], ["f1", "supply"]],
             [("f1", 2.0, ()), ("t1", 5.0, ("f1",))]),
        make("branching", "Fictional branching repairs", "Independent branches and a shared upstream prerequisite.",
             {"f1": "supply", "t1": "f1", "t2": "f1", "f2": "supply"},
             [["t1", "f1", "supply"], ["t2", "f1", "supply"], ["f2", "supply"]],
             [("f1", 3.0, ()), ("t1", 4.0, ("f1",)), ("t2", 6.0, ("f1",)), ("f2", 2.0, ())]),
        make("overlap", "Fictional overlapping dependencies", "Three distinct customers share a fuse; two also require its transformer repair. Counts must never be summed across assets.",
             {"f1": "supply", "t1": "f1"}, [["t1", "f1", "supply"], ["t1", "f1", "supply"], ["f1", "supply"]],
             [("f1", 3.5, ()), ("t1", 7.0, ("f1",))]),
        make("blocked", "Fictional blocked access", "An upstream site has unknown clearance; an independent branch remains represented.",
             {"f1": "supply", "t1": "f1", "f2": "supply"}, [["t1", "f1", "supply"], ["f2", "supply"]],
             [("f1", 2.5, ()), ("t1", 4.5, ("f1",)), ("f2", 3.0, ())], blocked=("f1",)),
        make("missing", "Fictional unresolved evidence", "An explicit unresolved upstream device withholds complete dependency coverage; missing effort remains null.",
             {"unknown": "supply", "f1": "unknown", "t1": "f1"}, [["t1", "f1", "unknown", "supply"]],
             [("f1", 2.0, ()), ("t1", None, ("f1",))], unresolved=("unknown",)),
        make("critical", "Fictional critical-service tradeoff", "One explicitly fictional critical service and a larger separate customer group; no proximity or personal-needs inference.",
             {"f1": "supply", "f2": "supply"}, [["f1", "supply"], ["f2", "supply"], ["f2", "supply"], ["f2", "supply"]],
             [("f1", 6.0, ()), ("f2", 2.0, ())], critical=(1,)),
    ])


def catalog_bytes():
    return (json.dumps(definitions(), indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="A new directory, never an existing source directory")
    args = parser.parse_args()
    # Exclusive creation prevents overwriting any existing data or teammate work.
    args.output.mkdir(parents=True, exist_ok=False)
    payload = catalog_bytes()
    (args.output / "catalog.json").write_bytes(payload)
    print("catalog_sha256:", hashlib.sha256(payload).hexdigest())


if __name__ == "__main__":
    main()
