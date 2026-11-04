# README preparedness screenshot

[preparedness-desktop.png](preparedness-desktop.png) is an authentic, unedited desktop
capture of the approved source-free package, added for the product-first README.
The existing integrated recording's desktop preparedness frames show snapshot interactions
mid-page; this capture shows the page heading, navigation and complete generic kit.
The original recording, screenshots, captions and provenance are unchanged.

- Application: `3c53d8e9429318f121c210d148f7d2b35ae52147` (unchanged through documentation base `6e50896c455f1d74663be2d7c5ed606be77d7834`).
- Rebuilt 47-file package matched the [approved manifest](../v1.1.0-integrated/package.json) exactly: SHA-256 `dbf1c3251fd5e297f223b424898f35f18ac27cbb182b24dd1656486cffc32ebf`.
- Viewport: 1440×1420, device scale 1, reduced motion, fresh browser context.
- Real `/preparedness/` page and same-origin Python responses; external requests blocked.
- Default fictional scenario, online, no saved snapshot or installed offline kit.
- No DOM edits, fabricated responses, compositing, cropping or data changes.
- [Capture metadata and image hash](capture.json); [capture script](capture.mjs).

To reproduce, install the existing frontend dependencies and Google Chrome. Acquire,
inspect and extract the approved package using the [reproduction guide](../../REPRODUCING_V1_1.md),
and install its hash-locked dependencies into an environment outside the extraction.
From the repository root, with port 18194 free:

```sh
GRIDGUIDE_PACKAGE=/absolute/path/to/inspected-package \
GRIDGUIDE_PUBLIC_PYTHON=/absolute/path/to/runtime/bin/python \
node docs/media/readme/capture.mjs
```

The script launches the real public app on loopback, captures this screenshot and writes
fresh metadata here, then stops the server. This is documentation capture, not a public
deployment or a new browser/accessibility acceptance test. Browser/font rendering can
change image hashes on another environment. Existing Chromium/VoiceOver limitations remain.
