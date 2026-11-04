# Four-candidate geographic gallery: private review, publication blocked

Reviewed November 4, 2026. The requested four-map 2×2 gallery is prepared for **private
local review only**. No new source-derived screenshot, tile copy, coordinate payload or
private gallery has been committed, uploaded to GitHub or included in CI artifacts.
The main README instead reuses the previously published `docs/media/v1.0.0/evidence.png`
unchanged, with its historical scope explicit. It does not claim the four new maps are public.

## What was inspected and captured

The actual detached v1.0.0 application at `b324c1b355cda60035fb11fa32bcddf10931f649`
ran with authorized local pinned challenge files and external AI disabled.
`RestorationDecision.tsx` owns the four candidate selectors and map/evidence/crew workspace;
`CandidateImpactMap.tsx` renders generalized equipment markers, customer cells/counts,
optional OSM tiles, attribution and geographic limitations. Neither file was modified.

These are existing public API aliases, not raw utility asset identifiers:

| Candidate | API alias | Distinguishing evidence in its private capture |
| --- | --- | --- |
| Golden upstream fuse | `asset-1e0e3d979b0f64d6c949` | Declared damage on verified source equipment; four dependent premises in one generalized cell. |
| Golden transformer | `asset-973c492bfd0e358f7d68` | One dependent premise; requires the upstream fuse repair. |
| Historical fuse replay | `asset-4271bb66fe1b6174f491` | 23 dependent premises in two cells; qualified historical spatial hypothesis, not an exact damage-ID match or current outage. |
| Critical-context fuse | `asset-dd55cf26c71b6d415bc7` | One dependent premise; nearby critical-service spatial context, with electrical attachment explicitly unverified. |

The upstream fuse and transformer share the same 0.01° generalized footprint. They are
different candidates with different counts, labor and prerequisite relationships. The
captures retain that overlap instead of moving markers or implying four distinct regions.
Memberships overlap and must not be summed as unique customer releases.

All four captures use 1440×1200 desktop viewports, device scale 1, reduced motion and the
same scroll position. Default critical-proxy policy, one four-person crew and clear
access remain unchanged. Each capture verifies exactly one pressed candidate selector,
the matching inspection heading, loaded map, visible legend and attribution. Twelve
fully decoded OSM tiles were present in each capture; four candidate IDs and four image
SHA-256 hashes are distinct. There were no browser runtime errors. Each image was visually
inspected for selection, markers, counts, areas, street detail and attribution.

The private review folder contains four unedited PNGs, a responsive 2×2 HTML gallery,
a Markdown gallery, capture script/configuration and provenance. Its metadata binds
source-file and implementation hashes, exact application commit, browser, viewport,
settings, API result ID, generalized map payloads and image hashes. It is outside the
repository with owner-only directory access. No local path or private geometry is embedded
in the public README. On mobile the private HTML gallery stacks the four cards and links
to the original full-resolution images.

## Permission decision

**Local inspection is authorized; publication of the new maps is not cleared.**
The [publication audit](../../releases/PUBLIC_RELEASE_AUDIT.md#findings),
[Phase 1 source-use review](../../research/phase1/FEASIBILITY.md#source-licensing-coverage-and-use-are-distinct-gates)
and [third-party notices](../../../THIRD_PARTY_NOTICES.md) still record no verified
redistribution grant for the challenge data or new derived screenshots. The pinned
[upstream README](https://github.com/hackohio/aep_challenge_hack26/blob/28a5520262b71a9fbf753b3031abf67781ca66ff/README.md)
describes the package but supplies no such grant. No new permission document was supplied
for this task. Existing public visibility, the earlier owner retention decision and
coordinate generalization are not treated as new rights clearance.

The captures use normal interactive browser tile loading without bulk download or a tile
archive. Visible attribution is retained. OSM's [copyright page](https://www.openstreetmap.org/copyright),
[static-image attribution guidance](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines#Static_images)
and [tile policy](https://operations.osmfoundation.org/policies/tiles/) were checked;
OSM terms do not grant rights to the overlaid AEP source material.

Before the private four-map gallery can replace the historical image in the public
README, obtain and record applicable source-owner/organizer permission covering derived
portfolio screenshots, then review the exact images for privacy and attribution.
Do not upload private correspondence or infer missing terms. This is a documented
publication blocker, not a request to change source data, weaken validation, anonymize
coordinates further or rewrite history.

The source-free v1.1.0 package remains non-geographic fiction. Its policy comparison and
operator-review screenshots are secondary visuals in the README, clearly separated from
the original geographic workspace. Overview, preparedness, original attribution and all
historical media remain unchanged.
