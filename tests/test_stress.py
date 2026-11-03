import json
from pathlib import Path
import unittest
from deeproject.pipeline import assess
from deeproject.stress import controlled_cases

ROOT = Path(__file__).resolve().parents[1]


class ControlledFilterTests(unittest.TestCase):
    def test_policy_routes_and_order_effect_without_event_failures(self):
        records = controlled_cases(json.loads((ROOT / 'dist/data/agent-spec.json').read_text()))
        results = assess(records)
        self.assertEqual(len(results), 24)
        for r in results:
            self.assertEqual(r['route'], r['original']['generation_truth']['expected_route'])
            self.assertEqual(r['run']['summary']['failures'], 0)
        by = {r['original']['pattern']: r for r in results[:8]}
        self.assertEqual(by['late_drop']['btv']['arithmetic_mean'], by['early_low']['btv']['arithmetic_mean'])
        self.assertAlmostEqual(by['late_drop']['btv']['score'], 1.25)
        self.assertAlmostEqual(by['early_low']['btv']['score'], 2.25)
        self.assertTrue(by['single_anchor']['btv']['passed'])
        self.assertEqual(by['single_anchor']['route'], 'problem')
        self.assertEqual(by['mild_decline']['btv']['critical_anchor_turns'], [])
        self.assertAlmostEqual(by['mild_decline']['btv']['score'], 1.9)
        self.assertEqual(by['missing_dimension']['btv']['status'], 'insufficient_input')

    def test_expected_labels_do_not_control_filtering(self):
        records = controlled_cases(json.loads((ROOT / 'dist/data/agent-spec.json').read_text()))
        before = assess(records)
        for r in records: r['generation_truth']['expected_route'] = 'deliberately-wrong'
        self.assertEqual([r['route'] for r in before], [r['route'] for r in assess(records)])
