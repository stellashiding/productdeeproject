"""BTV, ICLR 2027 submission section 3.2 equation (1).

Consumes supplied RHCA anchors; does not generate or validate semantic ratings.
"""
from math import isfinite, fsum

VERSION = 'btv-equation-1-v1'
DIMENSIONS = ('R', 'H', 'C', 'A')


def verify(ratings, p=1.0, penalty=0.5, threshold=2.0):
    for name, value, lower in [('p', p, 1), ('penalty', penalty, 0), ('threshold', threshold, 1)]:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < lower:
            raise ValueError(name + ' is invalid.')
    if threshold > 3:
        raise ValueError('threshold must be within the RHCA scale.')
    if not isinstance(ratings, list) or not ratings:
        raise ValueError('Provide complete R/H/C/A anchors for at least one turn.')
    scores, critical = [], []
    for i, row in enumerate(ratings, 1):
        if not isinstance(row, dict) or any(type(row.get(d)) is not int or row[d] not in (1, 2, 3) for d in DIMENSIONS):
            raise ValueError('Turn ' + str(i) + ' needs all four integer RHCA anchors (1, 2, 3).')
        scores.append(fsum(row[d] for d in DIMENSIONS) / 4)
        if any(row[d] == 1 for d in DIMENSIONS):
            critical.append(i)
    # Scale by min(q) to avoid underflow for large p.
    low = min(scores)
    generalized = low * (fsum((low / q) ** p for q in scores) / len(scores)) ** (-1 / p)
    peak, drop, peak_turn, drop_pair = scores[0], 0.0, 1, None
    for t, q in enumerate(scores[1:], 2):
        if peak - q > drop:
            drop, drop_pair = peak - q, [peak_turn, t]
        if q > peak:
            peak, peak_turn = q, t
    value = generalized - penalty * drop
    return dict(status='computed', evaluator=VERSION, paper='ICLR 2027 submission §3.2 Eq. (1)',
                dimensions=list(DIMENSIONS), weights=[0.25] * 4, p=p, penalty=penalty,
                threshold=threshold, turn_scores=scores, arithmetic_mean=fsum(scores) / len(scores),
                generalized_mean=generalized, max_drop=drop, drop_pair=drop_pair,
                score=value, passed=value >= threshold, critical_anchor_turns=critical,
                note='Any Anchor 1 is reported separately; BTV passing does not erase it. Ratings supplied by caller.')
