# Public-release audit — November 3, 2026

**Verdict: documentation can be reviewed locally; the official v1.0.0 release remains BLOCKED on data redistribution and sensitive history disposition.** Existing public visibility is intentional, confirmed by the owner, and is not itself a blocker. No visibility change, remote write, history rewrite, data removal, tag, merge, or GitHub Release was performed.

## Baseline and scope

- Started on clean `main`, matching local `origin/main` and the read-only GitHub `main` response at `bb7c53ce2e0733c6770c9de631a75df094407727`.
- The owner identifies this as the **last known hackathon-period checkpoint**. The exact submitted SHA has not been independently confirmed.
- Created local `chore/v1.0.0-portfolio-polish`. No release tags existed locally or in the GitHub tags response. Existing remote-tracking `pole-replacement` history remains intact.
- GitHub reports the repository as PUBLIC with no recognized project license. No tracked GitHub Actions configuration or public demo-video URL was found in the inspected repository materials.
- Reviewed tracked files, all 28 commits reachable from local refs, and objects reachable through local reflogs: **371 objects / 242 unique blobs** before this documentation pass. Readable XML/text inside ZIP/XLSX archives was also inspected. Remote-only refs, forks, platform caches, deleted remote objects, and external submission systems are outside this scan.

## Findings

| Finding | Evidence | Status / consequence |
| --- | --- | --- |
| AEP redistribution permission is unresolved | Four raw inputs are tracked from `6e35ee6`; upstream at `28a5520262b71a9fbf753b3031abf67781ca66ff` has no license file. READMEs, the challenge DOCX, and inspected archive metadata provide no explicit redistribution grant. | **BLOCKED**: obtain permission covering the actual files, derived data, and intended release assets; public access alone is insufficient. |
| Raw GIS and topology are in the current tree and history | `data/raw/Data1.zip`, `Data2.zip`, `matched_upstream.zip`, and `Install_Labor_HackOHIO.xlsx`. GIS includes premise/equipment identifiers, precise geometry, and facility names/addresses. Topology links premise identifiers to equipment paths. | **BLOCKED**: API minimization does not protect downloadable Git files or older commits. |
| Derived customer table contains sensitive fields | `data/processed/customers.csv`, introduced at `d1e1ad8`, has **117,642 rows**, premise/circuit identifiers, latitude/longitude rounded to five decimals, and `life_support`. `pipeline/build.py` derives that flag from a source attribute; it is not a customer declaration. | **BLOCKED**: assess data permission and disclosure separately from the current runtime, which does not use this table for customer declarations. No individual values are reproduced here. |
| Other derived challenge data remains tracked | `data/processed/circuit_damage.csv` contains **390 rows** of circuit/damage/access summaries. | **BLOCKED** pending the same derived-data rights decision. |
| Source metadata includes workstation paths | XML metadata in **all 12 GIS layers** across Data1/Data2 contains original Windows user-directory paths. | **BLOCKED** as part of the source/history privacy review. Paths and usernames are not copied into these release documents. |
| Source locators can identify records indirectly | Existing `backend/config.py`, tests, data audit, and Q2/Q4 documentation retain reproducible source row locators and circuit references. | Review alongside the raw data; removing a displayed raw ID alone does not make source evidence anonymous when the pinned dataset is available. No locators were added or changed in this pass. |
| No credential matches found in the bounded scan | Scanned provider/GitHub/AWS/Slack token shapes, private-key headers, long quoted credential assignments, authenticated/private URL patterns, and exact local credential values without printing them. | Scan passed within scope; **not** a guarantee of absence. Review remote refs/release assets before publishing. |
| Local credentials and generated artifacts remain excluded | `.env` is ignored, owner-only mode `0600`, and absent from reachable Git history. `.venv`, IDE files, `node_modules`, frontend build/schema outputs, browser traces and reports are ignored and not tracked in inspected history. | **READY** for this local staging scope. New screenshots are an explicit reviewed exception to transient QA assets. |
| Ownership and complete team credits are unconfirmed | Owner confirms three teammates. Git author labels include `Sang Park`, `its-spark-dev`, and `Hasan`; GitHub's contributor response maps activity to only `its-spark-dev` and `hasana2803-art`. | **NEEDS OWNER APPROVAL**: do not treat three author strings as three people or invent a third identity/role. Obtain each teammate's consent and preferred public credit. |
| No root license; third-party materials have separate terms | Barlow OFL/source notices exist; pinned package metadata records other licenses. | **NEEDS OWNER APPROVAL**: choose a license only for work the team can license. See [inventory](../../THIRD_PARTY_NOTICES.md). |

The existing public repository may already have been cloned. Neither a future deletion commit nor a new tag removes data from earlier commits or others' copies. Existing exposure is a reason to make an explicit data-handling decision; this task does not authorize remediation by rewriting history.

The freshly generated frontend bundle remains ignored and untracked. A bounded exact-token comparison of long numeric premise identifiers against non-data tracked files and the generated JS/HTML found no matches. Source review confirms no raw/processed dataset import into the frontend. This complements public-payload tests; it is not a general proof of de-identification or a substitute for the findings above.

## Distribution terms checked

Read-only checks used the upstream tree, metadata, [root README](https://github.com/hackohio/aep_challenge_hack26/blob/28a5520262b71a9fbf753b3031abf67781ca66ff/README.md), [data README](https://github.com/hackohio/aep_challenge_hack26/blob/28a5520262b71a9fbf753b3031abf67781ca66ff/data/README.md), and [challenge DOCX](https://github.com/hackohio/aep_challenge_hack26/blob/28a5520262b71a9fbf753b3031abf67781ca66ff/docs/HackOHIO_2026_AI_Outage_Concierge_Challenge.docx). Upstream `main` still resolved to that pinned revision during review. Its description of publicly available facility data does not establish a grant for the full customer/network package.

The locally referenced user-supplied challenge PDF and Data Guide excerpts are not included as original attachments in this checkout. This audit does not invent their terms or page citations. The upstream structure-drawing PDF was not treated as a redistribution license; no blanket terms document was found in the upstream tree. Additional organizer agreements or source-owner restrictions may exist outside the repository.

GitHub explains the distinction between publishing code and granting a software license in its [licensing documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository). No license or permission is inferred from repository visibility.

## Safe paths for owner review

1. **Permission path:** obtain written confirmation from the applicable data owners/organizers covering raw GIS/topology, the workbook, derived tables, embedded metadata, and portfolio screenshots/aggregates. Separately assess whether identifiable customer data should remain downloadable even if redistribution is permitted. Record the approved scope without adding private correspondence or contact details.
2. **Source-only path if permission is unavailable:** prepare a separately approved distribution containing only cleared code, documentation, and assets. Keep the original implementation/history preserved; do not transfer the data-bearing Git history into the new distribution. Authorized users can privately supply the four exact pinned files, with startup hash checks intact. Full source-dependent tests cannot run without them; no synthetic replacement exists in v1.0.0.
3. A GitHub Release on the current data-bearing history still points to that history and can expose its source archive. A source-only attachment on that release is not a complete solution. Any separate distribution or treatment of already-public history requires an explicit owner decision and additional authorization. Nothing in this pass deletes teammate work or rewrites history.

The [release checklist](CHECKLIST.md) tracks these decisions. Predictive validation, scheduling benchmarks, and product differentiation are future v1.1.0 topics, not remedies implemented by this documentation pass.
