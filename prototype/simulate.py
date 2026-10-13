"""Simulation sans mètre ruban : smartphone et questions simples uniquement."""
import numpy as np
from engine import (Estimator, IDX, LOAD, MEAN, STD, TARGETS, default_candidates)

# tolérances « made-to-measure » réalistes pour un usage sans ruban (cou/poignet : pas de 1 cm)
RELAXED = {**TARGETS, "neck": (1.0, 1.0), "wrist": (1.0, 0.6)}


def sample_people(n, rng):
    z = rng.standard_normal((n, 3))
    spec = rng.standard_normal((n, len(MEAN)))
    resid = np.sqrt(np.clip(1 - (LOAD ** 2).sum(axis=1), 0, None))
    return MEAN + STD * (z @ LOAD.T + spec * resid)


def run(person, rng, cands, max_steps, targets):
    est = Estimator(cands, max_questions=max_steps, targets=targets)
    cost = 0.0
    while (c := est.next_question()):
        est.update(c.key, {v: person[IDX[v]] + rng.normal(0, s) for v, s in c.obs})
        cost += c.cost
    r = est.result()
    return list(est.asked), cost, {k: r[k]["mean"] - person[IDX[k]] for k in TARGETS}


def scenario(name, cands, max_steps=5, targets=RELAXED, n=1000, seed=0):
    rng = np.random.default_rng(seed)
    P = sample_people(n, rng)
    out = [run(p, rng, cands, max_steps, targets) for p in P]
    steps = np.mean([len(o[0]) for o in out]); cost = np.mean([o[1] for o in out])
    print(f"\n{name} | étapes {steps:.1f} | effort {cost:.1f}")
    print(f"  {'mesure':9s} {'MAE':>5s} {'tol spec':>8s} {'ok spec':>8s} {'tol rel.':>8s} {'ok rel.':>8s}")
    for k in TARGETS:
        e = np.abs([o[2][k] for o in out])
        print(f"  {k:9s} {e.mean():5.2f} {TARGETS[k][0]:8.1f} {100*(e<=TARGETS[k][0]).mean():7.0f}% "
              f"{RELAXED[k][0]:8.1f} {100*(e<=RELAXED[k][0]).mean():7.0f}%")


if __name__ == "__main__":
    base = [c for c in default_candidates() if c.key.startswith("ask_")]
    nolidar = default_candidates()
    old = [c for c in base if c.key not in ("ask_pants_waist", "ask_arm_reach", "ask_shirt_fit")]
    scenario("A0. questions de base seules", old)
    scenario("A. questions seules (avec pantalon, envergure, ajustement)", base)
    scenario("B. questions + photos (sans LiDAR)", nolidar)
    scenario("C. avec LiDAR", default_candidates(lidar=True))
