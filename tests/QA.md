# Internal verification — 2026-10-22

This is implementation QA, not a target-user study.

## Automated regression coverage

Seven Node tests verify the nine recorded runs and 78 turns, 34 human-rated turns, six unresolved human disagreements, R06’s human/LLM mismatch at the final turns, unassessed dimensions, criterion-version invalidation, separate local reviews, authored-demo provenance and invalid-import rejection.

## Browser walkthrough

- All nine scenario/model selections loaded the expected run, turn count and assessment source.
- Garden opens paused. The desktop play control remains visible in the initial viewport.
- R06 Turn 7 shows human agreement on a low score and retains the LLM difference.
- Moving from Garden to diagnostics and back retains run and selected turn.
- Full model IDs, judge IDs and missing generation metadata are displayed separately.
- R07 Turn 8 shows human disagreement rather than an averaged result.
- Editing a criterion makes its imported scores unassessed. Restoring the source criterion restores its records.
- A local test review was saved separately and then removed. The exported JSON retained the original human and LLM scores and the selected turn; no test review remained.
- The authored Responsible AI example labels no model run and disables model switching.
- Software 3D camera rotation changes projected world-marker positions; zoom and overview controls operate. The rendering loop pauses in a hidden tab.
- In a 390 px iframe (375 px content viewport after scrollbar), Garden and diagnostics had no horizontal document overflow. The original-response column scrolls independently.
- Escape closes a native detail dialog and restores trigger focus.

## Remaining verification

The browser environment did not expose WebGL, so the WebGL path has syntax and source checks but no hardware-rendered visual QA. The software perspective renderer was exercised instead. Real screen-reader use, broad browser/device coverage and target-user research remain to be conducted. JSON import schema rejection is unit-tested; a full file-picker import round trip is not included in this walkthrough.


## Evaluation Design and harness implementation (2026-10-22)

Implemented four-step specification authoring, evaluator binding, draft persistence, review cards, specification export, browser synthetic fixtures, local Python SDK/CLI, application/HTTP target adapters, evidence validation, issue checkpoints, comparison, report preview/text export and separate results JSON. Restored skippable Garden entry camera movement and simplified Run details.

Verified:
- 12 JavaScript tests and 8 Python tests pass, including historical data/source regressions, unknown observations, invalid evidence, target failure, HTTP message history and comparison compatibility.
- A clean virtual environment installs the wheel without external runtime dependencies. A specification downloaded from the browser validates and runs in the installed CLI. Function-target runs, log re-evaluation, reports and version comparison work. Wheel viewer assets match the source assets.
- Browser Design steps and specification download work. Both synthetic targets execute; regression fixture fails at turns 2–3 and records a turn-4 correction without claiming sustained recovery. Compare shows the two changed checkpoints.
- Garden and diagnostics preserve the selected run/turn. Entry transition and Skip appear. Playback remains paused.
- Recorded R06 turn 7 remains a human-assessed failure; Run details contains only case/data type/family/version. Results JSON and readable text report downloads were verified; report preview does not invent issue-level diagnoses from imported scores.
- Design layout at a 375 px inner viewport has no horizontal overflow.

Limits:
- The last browser file-chooser import attempt timed out in the automation infrastructure. Do not count that UI import flow as verified. Schema/roundtrip validation and local result loading are covered separately.
- Browser Markdown download did not produce a download event in this environment; the verified browser export uses plain text. The CLI writes Markdown successfully.
- No external paid model/provider call was performed. Python/HTTP adapters were exercised with controlled local targets. There is no bundled calibrated semantic RHCA judge or LangSmith integration.
- Normal WebGL visual rendering, screen-reader use, full mobile interaction coverage and participant usability remain unverified. Existing software 3D and source/trajectory regressions remain available.
- Complex requirement supersession, semantic problem identity, sustained-recovery protocols and multi-user collaboration remain future work.


## Agent behavior update · 2026-10-22

- Schema 2 custom dimensions, event evidence, six deterministic behavior templates, numeric limits and local Python judges implemented. Legacy conversation schema and all nine recorded runs preserved.
- 19 JavaScript tests and 13 Python tests pass, including browser/Python parity, revoked permission, outdated goal and requirement fields, stale verification, unknown/error recovery breaks, future evidence and protocol mismatches.
- Fresh virtual environment installation of 0.2.0a1 exercised agent init, two event evaluations, reports and comparison; packaged viewer bytes matched the working assets.
- Browser checked Design, adding a seventh dimension, rule selection, fixture execution, retained critical violations, evidence links and entering the event Garden with its transition. The event Garden retained the selected event and behavior module.
- Later browser preview connection failed during the final comparison/Garden visual checks. Final screenshot, mobile viewport, browser downloads/import and screen-reader behavior were not verified in this pass. CLI comparison and result/report exports were verified.
- Fixtures are author-constructed, not model runs. No participant usability/accessibility study, semantic calibration, autonomous agent runner, runtime enforcement or external-state authentication is claimed.


## Criteria grouping and labels · 2026-10-22

- Removed the permanent criteria sidebar from event specification authoring. Criteria are nested inside behavior categories in step 2; step 3 retains a small current-criterion context.
- Review uses category disclosures and nested evidence details instead of placing full category names in fixed 28px chips.
- Added editable criterion names with descriptive fallbacks for existing timestamp IDs. Stable IDs are preserved in exports and evidence references. New criteria inherit the category where Add criterion was clicked.
- Browser verified grouped navigation, adding a criterion under Autonomy & human control without exposing its ID, removing the temporary criterion, and expanding that category in Review. Screenshot visually confirms no label/body overlap.
- 19 JS and 13 Python checks pass. Installation package updated to 0.2.0a2 with the same viewer.


## Unified typography · 2026-10-22

- One UI family (DM Sans) across headings, copy, controls, metadata and event fields. Removed Instrument Serif import, heading serif rules and hero italic styling.
- Consolidated font sizes and weights; removed decorative tracking. Monospace remains only for code/preformatted examples. Compact scene labels retain a smaller responsive size.
- Browser checked Review: computed font families for headings, paragraphs and controls resolve to the same stack; no horizontal page overflow. Screenshot visually confirms the unified hierarchy.
- JavaScript syntax checks passed. Viewer installation package advanced to 0.2.0a3. No evaluator or source-data changes.
