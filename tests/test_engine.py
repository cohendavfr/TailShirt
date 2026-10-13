import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "prototype"))
import numpy as np
from engine import Estimator, IDX, prior_covariance


def test_prior_covariance_is_psd():
    assert np.linalg.eigvalsh(prior_covariance()).min() > 0


def test_update_reduces_variance_and_moves_mean():
    est = Estimator()
    before = est.sigma[IDX["sleeve"], IDX["sleeve"]]
    est.update("ask_height", 190.0)
    assert est.sigma[IDX["sleeve"], IDX["sleeve"]] < before
    assert est.mu[IDX["sleeve"]] > 64.0  # grand => manche plus longue


def test_precise_observation_pins_value():
    est = Estimator()
    est.update("tape_neck", 42.0)
    r = est.result()["neck"]
    assert abs(r["mean"] - 42.0) < 0.3 and r["std"] < 0.4


def test_never_asks_same_question_twice():
    est = Estimator(max_questions=20)
    seen = set()
    while (q := est.next_question()):
        assert q.key not in seen
        seen.add(q.key)
        est.update(q.key, float(est.mu[IDX[q.var]]))
