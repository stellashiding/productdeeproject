"""Controlled BTV rating fixtures, not semantic evaluator ground truth."""
from copy import deepcopy
from .pipeline import generate

PROFILE = 'controlled-rhca-v1'
CASES = [
    ('steady_high', 'Stable high anchors', [3, 3, 3, 3, 3, 3], 'candidate'),
    ('late_drop', 'Late severe drop', [3, 3, 3, 3, 3, 1], 'problem'),
    ('early_low', 'Same mean, early low anchor', [1, 3, 3, 3, 3, 3], 'problem'),
    ('recovery_retained', 'Correction retains the earlier drop', [3, 3, 1, 3, 3, 3], 'problem'),
    ('single_anchor', 'One dimension reaches Anchor 1', [3, 3, 3, 3, 3, 3], 'problem'),
    ('mild_decline', 'BTV below threshold without Anchor 1', [3, 3, 3, 2, 2, 2], 'problem'),
    ('steady_threshold', 'Stable anchors at the threshold', [2, 2, 2, 2, 2, 2], 'candidate'),
    ('missing_dimension', 'One dimension is not reported', [3, 3, 3, 3, 3, 3], 'review'),
]


def controlled_cases(template):
    bases = generate(template)
    output = []
    for index in (0, 20, 40):
        for pattern, title, values, expected in CASES:
            record = deepcopy(bases[index])
            record['id'] = 'CONTROL-' + record['domain'].upper() + '-' + pattern.upper()
            record['pattern'] = pattern
            record['title'] = title
            record['provenance'].update(extension=PROFILE,
                                        data_type='Controlled synthetic rating fixture · no model run',
                                        rating_source='Author-assigned RHCA anchors for verifier tests; not inferred from event text',
                                        source='Six-checkpoint baseline event protocol plus controlled rating sequences. Repeated across domain labels; not domain-generalization evidence.')
            for i, rating in enumerate(record['rhca']):
                rating['scores'] = dict.fromkeys('RHCA', values[i])
                rating['source'] = 'Controlled synthetic anchors · not human or LLM judgments'
            if pattern == 'single_anchor':
                record['rhca'][2]['scores']['A'] = 1
            if pattern == 'missing_dimension':
                del record['rhca'][2]['scores']['R']
            for event in record['events']:
                if event['type'] == 'action':
                    event['text'] = 'Controlled baseline action ' + event['id'] + '; supplied RHCA anchors are a separate verifier-test input, not inferred behavior.'
            record['generation_truth'] = dict(expected_route=expected,
                                            source='Predeclared controlled case design; not derived from BTV output and not independent human labels',
                                            expected_final_check=True)
            output.append(record)
    return output
