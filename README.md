# Deeproject · Configurable behavioral evaluation

Define how a human-facing AI system should behave, execute explicit checks, and inspect event evidence and history in a Workbench or 3D Garden. RHCA is a starter profile; dimensions are customizable.

## Repository and preview

This repository is synchronized with the AI Garden implementation published at https://deeproject-ai-garden-v2.stellading.chatgpt.site/.

- Current browser application: `dist/`.
- Python evaluation toolkit: `python/deeproject/`.
- GitHub Pages: https://stellashiding.github.io/productdeeproject/.
- Synced Sites source commit: `23469313d86bd8c7516a5751224311335e6065ca`.

Preview the current viewer with:

```bash
python3 -m http.server 8000 --directory dist
```

GitHub Actions checks the browser and Python evaluation logic, builds the downloadable wheel, and publishes `dist/`. The root landing file redirects local previews to `dist/`. Older root-level JavaScript/CSS and `tests/*.cjs` belong to the previous prototype; the current checks are the npm commands below.

## Version 0.2.0a9

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

Download `deeproject_rhca-0.2.0a9-py3-none-any.whl` from Docs. Python 3.10+; runtime uses only the standard library. The distribution name remains compatible with the earlier package.

```bash
python -m pip install ./deeproject_rhca-0.2.0a9-py3-none-any.whl
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
