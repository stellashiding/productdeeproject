# Deeproject Workbench

A responsive, dependency-free behavioral AI evaluation demo for GitHub Pages.

## Explore
- **Trajectory diagnostics:** four-turn policy-bypass audit, replay, evidence inspection, and downloadable JSON report.
- **Harness & rubrics:** editable RHCA rule, domain, signals, anchors; browser-local saving; JSON export and a downloadable CI starter.
- **Runtime monitor:** synthetic event stream, pause/resume, threshold interception, and session inspection.

## Run locally
`python3 -m http.server 8000`

## Deploy
The Pages workflow deploys `main`. If automatic Pages enablement is unavailable, choose **Settings → Pages → Source → GitHub Actions**, then rerun the workflow.

## Demo integrity
All trajectories, sessions and scores are illustrative fixtures. The 85.4% judge pass-rate and 2.56 reference average are separate illustrative metrics; they are not calculated from the four displayed RHCA anchors. No BTV formula is implemented. Turn 4 corrects the unsafe recommendation; its displayed failure denotes the retained trajectory consistency penalty, not a fresh policy breach. Runtime interception is simulated and no production agent is connected. The CI starter validates JSON only and requires an actual evaluator before use as a behavioral gate.

No API keys, backend, build step, or external JavaScript dependencies. Google Fonts is optional; system fallbacks work offline.
