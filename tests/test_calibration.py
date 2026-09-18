import math

from agentredteamer.calibration import cohens_kappa


def test_perfect_agreement_is_kappa_one():
    a = [True, False, True, True, False]
    assert cohens_kappa(a, a) == 1.0


def test_no_variance_and_full_agreement_is_kappa_one():
    # Every case labeled True by both judges: observed agreement is 100% but
    # kappa's expected-agreement term also hits 1, which would divide by zero
    # without the explicit guard — this is the case that guard protects.
    a = [True, True, True]
    assert cohens_kappa(a, a) == 1.0


def test_systematic_disagreement_is_negative():
    a = [True, True, False, False]
    b = [False, False, True, True]
    assert cohens_kappa(a, b) < 0


def test_empty_input_returns_nan():
    assert math.isnan(cohens_kappa([], []))


def test_opposite_constant_judges_score_zero_not_negative_one():
    # Judge A always says True, judge B always says False: raw agreement is 0%,
    # but each judge's marginal rate makes that exactly what chance predicts
    # (one judge is 100% True, the other 100% False) — kappa should read this
    # as "no better or worse than chance", not as maximal disagreement.
    a = [True] * 10
    b = [False] * 10
    assert cohens_kappa(a, b) == 0.0
