# Deeproject · Configurable behavioral evaluation

Define how a human-facing AI system should behave, execute explicit checks, and inspect event evidence and history in a Workbench or 3D Garden. RHCA is a starter profile; dimensions are customizable.

## Version 0.2.0a10

- Four-step authoring: task/boundaries, behaviors/dimensions, rules/evidence, review/package. Agent behavior, RHCA and blank profiles. Add/remove dimensions and criteria; versioned local specifications and exports.
- Event schema 2: ordered user, assistant, goal_update, permission, requirement_update, action, observation, verification, completion and metric events. Stable IDs and validated source references.
- Six behavior templates: goal alignment by explicit ID, authorization flags, action outcome flags, current requirement fields, verification flags and completion verification. Optional numeric resource limits and custom local Python evaluators.
- Binary, ordinal and numeric result formats. Built-in event rules are deterministic pass/fail; ordinal judgment uses a custom local Python evaluator. Unknown, unobserved, not-applicable and evaluator errors remain distinct.
- Findings retain historical violations independently of current checks. New relevant actions invalidate artifact verification. Recovery requires the configured number of consecutive applicable passes (minimum 2); unknown/error interrupts the streak. This is a narrow recorded-check protocol, not general behavioral recovery or causal diagnosis.
- Workbench links findings to exact event evidence. Garden filters by module and creates one planting per criterion. A keyboard-operable event list provides equivalent evidence. The camera entry transition remains skippable and respects reduced motion.
- Event comparison requires equal specification, external scenario protocol/environment and execution mode. Agent paths may differ; results describe failing checkpoint counts, not general reliability.
- Schema 1 remains supported: fixed multi-turn scripts, generic Python/HTTP targets, required-text checks and custom prior-turn Python judges. Original nine conversations, A ratings and human/LLM disagreement records remain intact.

This alpha checks **recorded fields**. A matching goal ID does not prove semantic alignment; a tool success flag does not prove task correctness. Imported permission and verification records are assumed accurate, not authenticated. The toolkit does not independently inspect an external environment, provide runtime enforcement, infer hidden chain-of-thought, or include a calibrated semantic judge. No participant usability or accessibility study has been conducted for this implementation.

## Install and evaluate events

Download `deeproject_rhca-0.2.0a10-py3-none-any.whl` from Docs. Python 3.10+; runtime uses only the standard library. The distribution name remains compatible with the earlier package.

```bash
python -m pip install ./deeproject_rhca-0.2.0a10-py3-none-any.whl
deeproject init my-agent-evaluation --profile agent
cd my-agent-evaluation
deeproject validate spec.json --executable
deeproject evaluate events.json --spec spec.json --out results/violation
deeproject evaluate reference-events.json --spec spec.json --out results/reference
deeproject compare results/reference results/violation --out comparison.json
deeproject view results/violation
```

The generated event logs are **author-constructed fixtures, not model runs**. They exercise goal changes, permission revocation, tool failure and verification. Both end with successful artifact checks, while their historical behavior differs. Fixtures do not demonstrate model performance or real-world deployment.

Replace the event log with your own records. Events require unique `id`, consecutive `sequence`, supported `type`, readable `text` and `data`. `observation.data.action_id` references a preceding action. The examples in `dist/data/agent-*.json` define the field contract. Each imported log must accurately represent the intended task/episode; state is not automatically isolated across unrelated tasks. Use separate logs/specifications for separate scopes.

Only configured triggers are covered. A task with no applicable events is **unobserved**, not a pass. Missing verification is unknown; failed or stale verification contradicts a completion claim. Partial or missing logs cannot establish the absence of violations.

## Custom event evaluator

Use `evaluator: {"type":"python","callable":"my_judge:check","version":"1"}` in schema 2. The callable receives `(events_through_current, criterion)` and returns:

```python
{
    "status": "pass",  # pass, fail, unknown, not_applicable
    "explanation": "Explain the judgment against the configured anchors.",
    "evidence": [{"event_id": "action-1", "quote": "exact recorded event text"}],
    # "value": 3  # required for ordinal or numeric result types
}
```

Evidence must reference exact text available at or before the current event. Invalid/future evidence and exceptions become errors. Python functions execute in your own process: review imported bindings before running them. No provider-specific semantic evaluator is bundled.

## Existing conversation workflows

```bash
deeproject init conversation-example --profile rhca
cd conversation-example
deeproject run suite.json --spec spec.json --target example_target:reply --fixture --out results/example
```

The generated target is synthetic. A schema-1 application function receives full actual message history and returns assistant text. HTTP targets receive `{"messages": [...]}` and return `{"assistant":"..."}`. `DEEPROJECT_TARGET_TOKEN` supplies optional authentication; `--timeout` applies to HTTP. These adapters do not run agent event workflows. Schema-2 event evaluation consumes existing logs through `evaluate`.

Schema-1 custom Python judges receive `(prior_turns, criterion)` and return `score` (1/2/3), `explanation`, and exact `turn`/`role`/`quote` evidence. Existing source annotations are preserved. Conversation correction checkpoints do not establish sustained recovery.

## Viewer, exports and provenance

### BTV and the synthetic batch (0.2.0a10)

`python/deeproject/btv.py` and `dist/btv.js` implement the supplied ICLR 2027
submission §3.2 Eq. (1). Complete R/H/C/A integer anchors are equally weighted;
the inverse-power mean is reduced by the maximum drop from an earlier peak.
Defaults: p=1, lambda=0.5, passing threshold=2. Any Anchor 1 is reported
separately even if BTV passes. The verifier consumes ratings; it does not infer
semantic scores, authenticate event logs, or diagnose clinical correctness.

```bash
deeproject btv ratings.json --out btv.json
deeproject pipeline --count 60 --out results/batch
deeproject pipeline --input input.json --out results/imported
# From this source checkout:
python scripts/run_synthetic.py
```

`ratings.json` is an array of complete objects such as
`{"R":3,"H":3,"C":3,"A":3}`. Batch inputs are arrays of records containing
`id`, `domain`, `events`, `specification`, and `rhca`; each `rhca` entry has
`event_id` and `scores`. See `dist/data/pipeline/input.json`.

The committed batch consists of 60 **programmatically constructed** logs and
**scripted RHCA anchors**, not real agent runs, human annotations, or LLM-judge
outputs. It crosses 3 domains, 5 patterns and 4 action-checkpoint lengths
(6/8/10/12). Domains extend paper tasks P08 (Coding), P04/P06 (Healthcare),
and P10 (FinTech); new event/tool protocols are not original participant data.
The same failure structures are reused across domains. Seed: 20261102.
This checks processing mechanics, not domain generalization or evaluator accuracy.

The routing policy retains originals. Invalid/duplicate/incomplete records go to
review; event failures, BTV below threshold or any supplied Anchor 1 go to
problem cases; the remainder are candidates, not certified safe examples.
Synthetic expected labels are retained separately and not read by the evaluator.
Runtime measures in `summary.json` cover local assessment only, excluding input
generation, serialization, export and UI rendering; they are not a large-scale
benchmark. No API or model is called. No 10,000-record test has been run here.

From **Workbench → Pipeline & insights**, rerun the batch locally, import a
compatible JSON batch, filter cases, inspect four aligned RHCA rating lanes, open exact event
evidence or the 3D Garden, and export JSON/CSV. The ZIP includes original inputs,
results, summaries and Python source for reproduction. Browser imports are limited
to 5 MB, 1,000 records and 100,000 events. For custom Python bindings use the local
package; browser evaluation never executes Python.

`deeproject view` serves a temporary viewer copy on `127.0.0.1`; Ctrl+C stops it. Results imports preserve records; raw event logs can be evaluated through Run. Design exports specifications; Results exports reports and results JSON. Browser storage is origin-local; export files to preserve work.

The nine original recorded conversations span three domains and three models, with 78 turns and 34 double-rated human turns. Imported ratings cover A only. Six human disagreements are unresolved. Original explanations may involve AI assistance and their provenance remains unconfirmed. These records do not establish model-family rankings or agent tool-use behavior.

Model IDs identify generation; evaluator versions identify assessment. Scenario/specification/evaluator/environment changes must not be presented as target-only improvement. For event comparison, supply an equal `protocol` object with scenario ID/version, environment version and external task inputs. The package does not infer this equivalence from different raw action sequences.

## Develop and package

```bash
npm run check
npm test
npm run test:harness
npm run package:harness
```

Buildless viewer assets live in `dist/`; Python SDK in `python/deeproject/`. The package script copies current viewer assets and excludes previous downloads. Generated wheels and viewer copies are ignored by Git; deployment includes the wheel artifact. Browser and Python event-engine parity is tested with both fixtures.

Licenses for publication of code and supplied datasets have not been selected. No open-source or dataset redistribution license is implied.

Viewer revision 0.2.0a11 makes supplied R/H/C/A ratings visible separately, with shared checkpoint selection and domain-by-dimension anchor distributions. Aggregate BTV and the arithmetic mean remain secondary summaries. Missing ratings remain gaps; no scores or synthetic inputs were altered.

Viewer revision 0.2.0a12 uses a dimension-by-checkpoint matrix as the primary case view. Each selectable cell displays its supplied anchor; the selected dimension and event remain explicit. Missing anchors are shown as a dash and never imputed.

### Controlled filtering and public dataset audit (0.2.0a13)

The left menu has independent Pipeline & Insights and Public Dataset Audit
entries. Workbench retains individual run inspection; it no longer contains a
pipeline entry card.

```bash
deeproject pipeline --controlled --out results/controlled
# From the checkout:
python scripts/run_controlled_filter.py
```

Controlled tests use eight deliberately assigned RHCA rating patterns repeated
across three domain labels (24 fixtures). All baseline event checks pass. Ratings
are separate test inputs, not judgments inferred from the event text. The suite
includes equal-mean reordered sequences, a retained historical drop, a single
Anchor 1 despite BTV passing, a mild decline without Anchor 1, the exact passing
threshold, and incomplete ratings. Predeclared expected routes are not read by
the evaluator. This verifies mechanics and routing, not semantic accuracy or
domain generalization. The original 60-event-fixture batch remains selectable.

The default controlled batch produces 6 candidate, 15 problem and 3 review
records. BTV is computed for 21 records, with 9 below threshold. Six additional
records pass BTV but retain Anchor 1 and are therefore routed to problem cases.
Originals and reasons remain in the full result; filtered raw inputs can be
exported separately and rerun. The decision policy is BTV plus separate Anchor 1
and event/evidence checks, not BTV alone.

Public Dataset Audit displays the completed structural audit of 20,363 records
from OpenMedical/medical-data, pinned to db65d76f894f90463bfbe6a4e8bbda5a7d316746.
18,137 records have no configured flags and 2,226 need review. Flag counts overlap.
This page does not use RHCA/BTV or assess medical correctness. It includes source
row IDs, hashes and review reasons, not the original medical corpus. The 30
prepared staged tasks have no model responses or ratings and remain marked not
run. Source licensing, per-record source attribution and contamination limits
are stated in the page. No model API is used by either demonstration.
