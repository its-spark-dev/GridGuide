# Fictional operator catalog v1

`catalog.json` embeds all eight unchanged G2 hand-computable microcases and their
matching protected G3 results from `docs/benchmarks/phase3/published/results.jsonl.gz`.
These cases were independently authored as fiction, not sampled, anonymized or translated
from challenge records. They establish interaction/correctness examples, not utility
outcomes, a new evaluation set or measured operational benefit.

The exact file SHA256 is
`15a7c313cb2c91176abdb09232a7848b75ee08d515533808b62ead9c6e532f29`.
Runtime verifies it before accepting any scenario. Source archive hash, exact problem
fingerprints, policy/schedule versions and original solver provenance are retained.
Historical wrapper timing comes from the unchanged G3 `timings.json`. Nothing is fitted,
optimized or downloaded by this extraction:

```sh
.venv/bin/python scripts/prepare_operator_catalog.py --output /tmp/gridguide-operator-catalog.json
cmp data/operator/catalog.json /tmp/gridguide-operator-catalog.json
```

The output path must be new. A changed frozen input/archive or extraction result fails
the pin check. Replacing fixtures requires a new versioned review, not silently editing
this file. G3's 5% median promotion target failed. Keep the fixed release/person-hour
baseline as default; the optional protected result is supported only on these original
inputs. Additional declared precedence recomputes four baselines and makes the frozen
experimental schedule unavailable. No new solver run or arbitrary graph API is exposed.

The catalog does not grant new redistribution rights or alter project attribution.
It contains no challenge-source identities, real customer membership, contacts, geometry,
credentials, private declarations or field-confirmed restoration outcomes.
See the [G7 review packet](../../docs/planning/V1_1_0_PHASE7.md).
