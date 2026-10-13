"""Moteur d'estimation adaptatif TailShirt (prototype M0).

Modèle gaussien conjoint sur les variables corporelles ; chaque observation
est une mesure linéaire bruitée d'une variable. Mise à jour de type Kalman,
sélection de la question suivante par gain de variance pondéré / coût.
"""
from dataclasses import dataclass
import numpy as np

# nom, moyenne (cm/kg), écart-type, charges sur (taille, corpulence, ossature)
VARIABLES = [
    ("height",   175.0, 7.0, (0.95, 0.00, 0.10)),
    ("weight",    78.0, 13.0, (0.35, 0.80, 0.30)),
    ("neck",      38.5, 2.2, (0.30, 0.60, 0.50)),
    ("chest",    100.0, 9.0, (0.20, 0.75, 0.45)),
    ("waist",     88.0, 11.0, (0.10, 0.90, 0.15)),
    ("hip",      100.0, 8.0, (0.15, 0.80, 0.30)),
    ("shoulder",  46.0, 2.5, (0.40, 0.35, 0.65)),
    ("sleeve",    64.0, 3.5, (0.80, 0.05, 0.30)),
    ("bicep",     31.0, 3.5, (0.10, 0.70, 0.40)),
    ("wrist",     17.5, 1.2, (0.30, 0.40, 0.60)),
    ("length",    75.0, 4.0, (0.85, 0.10, 0.20)),
]
NAMES = [v[0] for v in VARIABLES]
IDX = {n: i for i, n in enumerate(NAMES)}
MEAN = np.array([v[1] for v in VARIABLES])
STD = np.array([v[2] for v in VARIABLES])
LOAD = np.array([v[3] for v in VARIABLES])

# cible : tolérance (±cm) du cahier des charges, poids d'importance
TARGETS = {
    "neck": (0.5, 1.0), "chest": (1.5, 1.0), "waist": (1.5, 1.0),
    "hip": (2.0, 0.7), "shoulder": (1.0, 1.0), "sleeve": (1.0, 1.0),
    "bicep": (1.5, 0.6), "wrist": (0.5, 0.6), "length": (1.5, 0.8),
}


def prior_covariance() -> np.ndarray:
    corr = LOAD @ LOAD.T
    np.fill_diagonal(corr, 1.0)  # le reste est la part spécifique à chaque mesure
    return corr * np.outer(STD, STD)


@dataclass(frozen=True)
class Candidate:
    key: str        # identifiant unique
    var: str        # variable observée
    noise: float    # écart-type du bruit d'observation
    cost: float     # effort utilisateur
    label: str


def default_candidates() -> list[Candidate]:
    c = [
        Candidate("ask_height", "height", 1.0, 1.0, "Quelle est votre taille ?"),
        Candidate("ask_weight", "weight", 1.5, 1.0, "Quel est votre poids ?"),
        Candidate("ask_neck_usual", "neck", 1.2, 1.0, "Quel est votre col de chemise habituel ?"),
    ]
    # photo : bruit de l'estimation visuelle, effort moyen
    photo = {"shoulder": 1.5, "sleeve": 2.0, "chest": 3.0, "hip": 3.0, "length": 2.0, "waist": 3.5}
    c += [Candidate(f"photo_{v}", v, s, 2.0, f"Photo : {v}") for v, s in photo.items()]
    # mètre ruban : précis, effort élevé
    c += [Candidate(f"tape_{v}", v, 0.4, 3.0, f"Mesurez : {v}") for v in TARGETS]
    return c


class Estimator:
    def __init__(self, candidates=None, max_questions=8):
        self.mu = MEAN.copy()
        self.sigma = prior_covariance()
        self.candidates = {c.key: c for c in (candidates or default_candidates())}
        self.asked: list[str] = []
        self.max_questions = max_questions

    # --- contrat du moteur -------------------------------------------------
    def update(self, key: str, value: float) -> None:
        c = self.candidates[key]
        i = IDX[c.var]
        s_col = self.sigma[:, i].copy()
        gain = s_col / (self.sigma[i, i] + c.noise ** 2)
        self.mu = self.mu + gain * (value - self.mu[i])
        self.sigma = self.sigma - np.outer(gain, s_col)
        self.asked.append(key)

    def result(self) -> dict:
        out = {}
        for k in TARGETS:
            i = IDX[k]
            sd = float(np.sqrt(max(self.sigma[i, i], 0)))
            out[k] = {"mean": float(self.mu[i]), "std": sd,
                      "ci90": (self.mu[i] - 1.645 * sd, self.mu[i] + 1.645 * sd)}
        return out

    def done(self) -> bool:
        return all(1.645 * np.sqrt(max(self.sigma[IDX[k], IDX[k]], 0)) <= tol
                   for k, (tol, _) in TARGETS.items())

    def next_question(self) -> Candidate | None:
        if self.done() or len(self.asked) >= self.max_questions:
            return None
        best, best_score = None, 0.0
        for c in self.candidates.values():
            if c.key in self.asked:
                continue
            i = IDX[c.var]
            denom = self.sigma[i, i] + c.noise ** 2
            red = 0.0
            for k, (tol, w) in TARGETS.items():
                j = IDX[k]
                var = self.sigma[j, j]
                if 1.645 * np.sqrt(max(var, 0)) <= tol:
                    continue  # cible déjà atteinte : ne compte plus
                var_after = var - self.sigma[j, i] ** 2 / denom
                # gain d'information (log-ratio) : saturant, ne sur-favorise pas une seule cible
                red += 0.5 * w * np.log(var / max(var_after, 1e-9))
            score = red / c.cost
            if score > best_score:
                best, best_score = c, score
        return best
