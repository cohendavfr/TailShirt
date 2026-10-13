"""Simulation : combien de questions, et quelle précision, sur une population synthétique."""
import numpy as np
from engine import Estimator, IDX, LOAD, MEAN, STD, TARGETS


def sample_people(n, rng):
    z = rng.standard_normal((n, 3))
    spec = rng.standard_normal((n, len(MEAN)))
    resid = np.sqrt(np.clip(1 - (LOAD ** 2).sum(axis=1), 0, None))
    return MEAN + STD * (z @ LOAD.T + spec * resid)


def run(person, rng, policy="adaptive", max_q=8):
    est = Estimator(max_questions=max_q)
    order = list(est.candidates)
    if policy == "random":
        rng.shuffle(order)
    cost = 0.0
    while True:
        if policy == "adaptive":
            c = est.next_question()
        else:  # ordre aléatoire, mêmes critères d'arrêt
            c = None
            if not est.done() and len(est.asked) < max_q:
                c = est.candidates[order[len(est.asked)]]
        if c is None:
            break
        est.update(c.key, person[IDX[c.var]] + rng.normal(0, c.noise))
        cost += c.cost
    res = est.result()
    err = {k: res[k]["mean"] - person[IDX[k]] for k in TARGETS}
    return len(est.asked), cost, err, est.done()


def report(policy, n=2000, seed=0, max_q=8):
    rng = np.random.default_rng(seed)
    people = sample_people(n, rng)
    qs, costs, errs, done = [], [], [], 0
    for p in people:
        q, c, e, d = run(p, rng, policy, max_q)
        qs.append(q); costs.append(c); errs.append(e); done += d
    print(f"\n== politique : {policy} (n={n}, plafond {max_q} questions) ==")
    print(f"questions moyennes : {np.mean(qs):.2f} | effort moyen : {np.mean(costs):.1f} "
          f"| critère d'arrêt atteint : {100*done/n:.0f} %")
    print(f"{'mesure':10s} {'MAE cm':>7s} {'tol ±':>6s} {'% dans tol':>11s}")
    for k, (tol, _) in TARGETS.items():
        e = np.abs([x[k] for x in errs])
        print(f"{k:10s} {e.mean():7.2f} {tol:6.1f} {100*(e<=tol).mean():10.0f}%")


if __name__ == "__main__":
    for q in (8, 12):
        report("adaptive", max_q=q)
    report("random", max_q=8)
