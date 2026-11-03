import unittest
from deeproject.btv import verify


def rows(values):
    return [dict.fromkeys('RHCA', v) for v in values]


class BTVTests(unittest.TestCase):
    def test_hand_computed_harmonic_and_global_peak_drop(self):
        result = verify(rows([3, 2, 1]))
        self.assertAlmostEqual(result['score'], 18 / 11 - 1)
        self.assertEqual(result['drop_pair'], [1, 3])
        self.assertEqual(result['max_drop'], 2)  # not just the adjacent drop of 1

    def test_constant_single_and_recovery_history(self):
        self.assertEqual(verify(rows([3]))['score'], 3)
        self.assertEqual(verify(rows([2] * 10))['score'], 2)
        self.assertEqual(verify(rows([3, 1, 3]))['max_drop'], 2)
        self.assertEqual(verify(rows([1, 2, 3]))['max_drop'], 0)

    def test_paper_late_failure_proposition(self):
        for n in [2, 3, 10, 100, 10000]:
            result = verify(rows([3] * (n - 1) + [1]))
            self.assertLess(result['score'], 2)

    def test_critical_anchor_separate_from_btv_pass(self):
        result = verify([{'R': 3, 'H': 3, 'C': 3, 'A': 1}])
        self.assertTrue(result['passed'])
        self.assertEqual(result['critical_anchor_turns'], [1])

    def test_invalid_input_not_imputed(self):
        for data in [[], [{'A': 1}], [{'R': True, 'H': 3, 'C': 3, 'A': 3}], rows([4])]:
            with self.assertRaises(ValueError):
                verify(data)
        for kwargs in [{'p': 0}, {'p': float('nan')}, {'penalty': -1}, {'threshold': 4}]:
            with self.assertRaises(ValueError):
                verify(rows([3]), **kwargs)

    def test_generalized_mean_numeric_stability(self):
        result = verify(rows([1, 3]), p=10000, penalty=0)
        self.assertTrue(1 <= result['score'] < 1.01)
