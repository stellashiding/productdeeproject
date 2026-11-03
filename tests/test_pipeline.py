from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from deeproject.pipeline import generate, assess, write_batch

ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = generate(json.loads((ROOT / 'dist/data/agent-spec.json').read_text()))

    def test_balanced_reproducible_and_injected_evidence(self):
        self.assertEqual(len(self.inputs), 60)
        self.assertEqual(self.inputs, generate(json.loads((ROOT / 'dist/data/agent-spec.json').read_text())))
        result = assess(self.inputs)
        for source, item in zip(self.inputs, result):
            self.assertEqual(item['task_success'], source['generation_truth']['expected_final_check'])
            bad_steps = source['generation_truth']['injected_action_steps']
            actions = [e for e in source['events'] if e['type'] == 'action']
            expected_ids = [actions[i - 1]['id'] for i in bad_steps]
            found = next((i['failing_events'] for i in item['run']['issues'] if i['criterion_id'] == 'authorization'), [])
            self.assertEqual(found, expected_ids)
            self.assertEqual(item['route'], 'problem' if bad_steps else 'candidate')

    def test_invalid_missing_duplicate_and_partial_ratings_retained(self):
        valid = deepcopy(self.inputs[0])
        missing = deepcopy(valid); missing['id'] = 'missing'; missing['rhca'][0]['scores'].pop('R')
        broken = deepcopy(valid); broken['id'] = 'broken'; broken['events'][0]['sequence'] = 2
        results = assess([valid, deepcopy(valid), missing, broken, None])
        self.assertEqual([r['route'] for r in results], ['candidate', 'review', 'review', 'review', 'review'])
        self.assertEqual(results[2]['original'], missing)
        self.assertEqual(results[3]['original'], broken)
        self.assertEqual(results[2]['btv']['status'], 'insufficient_input')

    def test_artifact_outputs_reconcile(self):
        with tempfile.TemporaryDirectory() as folder:
            summary = write_batch(self.inputs[:4], folder)
            self.assertEqual(sum(summary['routes'].values()), 4)
            self.assertTrue(Path(folder, 'synthetic-pipeline-results.zip').exists())
            records = json.loads(Path(folder, 'results.json').read_text())['records']
            self.assertEqual([r['original'] for r in records], self.inputs[:4])
