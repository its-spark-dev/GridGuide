# Authentic v1.1.0 release-candidate demonstration

**Recorded:** approximately 4 minutes 7 seconds of silent, unedited browser footage from
the actual final application package. [Watch/download WebM](gridguide-1.1.0-rc.webm).
[Captions](captions.vtt), [actual timestamps](shots.json), [provenance/hashes](provenance.json),
[downloaded review JSON](review.json) and [actual replay transcript](replay.txt) are preserved.
No generated screenshots, mocked API responses or older-version captures are substituted.

For captioned playback, run a loopback-only static server **from this media directory**:

```sh
python3 -m http.server 18191 --bind 127.0.0.1
```

Open http://127.0.0.1:18191/player.html. This serves only the demonstration files locally;
it does not deploy GridGuide. Recording is complete, not pending. Narration is absent;
WebVTT captions explain the scene and its limitations.

| Actual start | Shot | Explanation |
|---|---|---|
| 00:00 | 01-introduction | GridGuide 1.1.0 release candidate. Independently authored fictional examples, not live utility observations. No deployment or safety certification. |
| 00:20 | 02-path | Declared power paths distinguish repair prerequisites from customer dependencies. Python prepared these milestone results. |
| 00:45 | 03-completed | Completed means the fictional dependency repairs are complete at this modeled milestone. It does not mean utility-confirmed restoration. |
| 01:10 | 04-blocked | Blocked access has unknown clearance. Full modeled completion stays unavailable; it is never converted to a finite ETR. |
| 01:35 | 05-unresolved | Unresolved evidence stays visible. No validated outage probability or empirically calibrated restoration confidence is available. |
| 02:00 | 06-tradeoff | Four policies use identical assumptions. Critical-first improves one critical latency but worsens total customer-hours. Release/person-hour remains the default; optional CP-SAT is frozen and experimental. |
| 02:25 | 07-override | This supported precedence override is recomputed by Python and independently validated. Changing the scenario or review invalidates earlier acknowledgement. |
| 02:51 | 08-review | Explicit acknowledgements produce a reproducible fictional review record. Checksums establish consistency, not authenticated reviewer identity or tamper-proof history. |
| 03:16 | 09-replay | Actual CLI output from the downloaded JSON. Replay recomputes baselines and validates metrics; it does not rerun CP-SAT. |
| 03:37 | 10-offline | Actual server shutdown and browser networking disabled. Only the reviewed kit and explicitly saved historical fiction remain. No browser numerical engine or live outage awareness. |

The CLI scene displays a real transcript produced by replaying the downloaded JSON,
not a fabricated terminal or product screen. The final scene stops the actual service,
disables browser networking, reopens the cached page and loads an explicitly saved
historical snapshot. Production tests separately verify a complete browser restart.
These are automated demonstrations, not a new manual VoiceOver acceptance record.

## Repeat the recording

Build/extract the candidate using the [reproduction guide](../../REPRODUCING_V1_1.md).
Keep exports and recording output outside that immutable package. From `frontend/`,
with installed Chrome and free port 18190:

```sh
npx playwright install ffmpeg
GRIDGUIDE_PACKAGE=/tmp/gridguide-public \
GRIDGUIDE_PUBLIC_PYTHON=/tmp/gridguide-runtime/bin/python \
GG_RECORD_DIR=/tmp/gridguide-recording \
node scripts/record-release.mjs
```

The source script is [record-release.mjs](../../../frontend/scripts/record-release.mjs).
It captures ten real states, saves JSON/replay evidence and produces WebM, PNG, timestamp
JSON and WebVTT files. Fresh timestamps/video compression naturally change hashes; no
bitwise video-reproduction claim is made. The application package hash must still match.

An initial selector error and a post-capture duplicate shutdown wait were fixed only in
the recording harness; the final capture completed successfully. Incomplete/interrupted
attempts are not the published media and are not counted as successful checks. No product
feature or numerical outcome was changed to accommodate the storyboard.

Original v1.0.0 screenshots remain in their historical directory with original attribution.
