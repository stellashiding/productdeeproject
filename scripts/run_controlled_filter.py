"""Execute controlled rating-sequence tests locally; no API or model calls."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from deeproject.pipeline import write_batch
from deeproject.stress import controlled_cases

records = controlled_cases(json.loads((ROOT / 'dist/data/agent-spec.json').read_text()))
out = ROOT / 'dist/data/filter'
summary = write_batch(records, out)
result = json.loads((out / 'results.json').read_text())
assert all(r['route'] == r['original']['generation_truth']['expected_route'] for r in result['records'])
assert all(r['run']['summary']['failures'] == 0 for r in result['records'])
print(json.dumps(summary, indent=2))
