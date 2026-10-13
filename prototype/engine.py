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
    """Une étape utilisateur : une question ou une capture donnant 1..n observations."""
    key: str
    obs: tuple      # ((variable, écart-type du bruit), ...)
    cost: float     # effort utilisateur
    label: str
    needs: str = ""  # capteur requis ("lidar") ou ""

    @property
    def var(self) -> str:  # compat : première variable observée
        return self.obs[0][0]


def _q(key, var, noise, label):
    return Candidate(key, ((var, noise),), 1.0, label)


def default_candidates(lidar: bool = False) -> list[Candidate]:
    """Étapes disponibles avec un smartphone seul (sans mètre ruban)."""
    c = [
        _q("ask_height", "height", 1.0, "Quelle est votre taille ?"),
        _q("ask_weight", "weight", 1.5, "Quel est votre poids ?"),
        _q("ask_neck_usual", "neck", 1.2, "Quel est votre col de chemise habituel ?"),
        _q("ask_sleeve_usual", "sleeve", 1.5, "Quelle est votre longueur de manche habituelle ?"),
        _q("ask_size_usual", "chest", 4.0, "Quelle est votre taille habituelle (S, M, L...) ?"),
        # questions « bonne » ou « très bonne » (hypothèses de bruit à valider)
        Candidate("ask_pants_waist", (("waist", 2.0), ("hip", 3.5)), 1.0,
                  "Quelle est votre taille de pantalon (tour de taille) ?"),
        Candidate("ask_arm_reach", (("sleeve", 1.8),), 1.0,
                  "Bras le long du corps, vos doigts arrivent où (hanche, milieu de cuisse, genou) ?"),
        Candidate("ask_shirt_fit", (("shoulder", 1.5), ("chest", 2.5), ("waist", 2.5)), 1.5,
                  "Votre chemise actuelle serre-t-elle aux épaules, à la poitrine, au ventre ?"),
        # photo en pied de face : plusieurs mesures d'un coup, bruitées
        Candidate("photo_front", (("height", 1.5), ("shoulder", 1.5), ("sleeve", 2.0),
                                  ("length", 2.0), ("chest", 3.0), ("waist", 3.5),
                                  ("hip", 3.0), ("neck", 2.5), ("bicep", 3.0),
                                  ("wrist", 4.0)), 2.0, "Photo en pied, de face"),
        # photo de profil : donne la profondeur donc les tours
        Candidate("photo_side", (("chest", 2.0), ("waist", 2.0), ("hip", 2.0)), 1.0,
                  "Photo de profil"),
        # chemise bien ajustée posée à plat à côté d'une carte bancaire
        Candidate("photo_shirt", (("neck", 0.8), ("shoulder", 0.8), ("sleeve", 0.8),
                                  ("length", 0.8), ("chest", 1.5), ("wrist", 0.8)), 2.0,
                  "Photo d'une chemise qui vous va bien, à plat, avec une carte"),
    ]
    if lidar:  # iPhone Pro / iPad Pro : capteur de profondeur
        c.append(Candidate("scan_depth", (("height", 0.8), ("shoulder", 1.0), ("sleeve", 1.2),
                                          ("length", 1.2), ("chest", 1.0), ("waist", 1.0),
                                          ("hip", 1.0), ("neck", 1.2), ("bicep", 1.2),
                                          ("wrist", 1.5)), 3.0, "Scan 3D (LiDAR)", "lidar"))
    return c


def tape_candidates() -> list[Candidate]:
    """Référence uniquement (mètre ruban) : non proposé à l'utilisateur."""
    return [Candidate(f"tape_{v}", ((v, 0.4),), 3.0, f"Mesurez : {v}") for v in TARGETS]


def _apply(mu, sigma, obs):
    """Mise à jour gaussienne séquentielle ; mu peut être None (variance seule)."""
    sigma = sigma.copy()
    for var, noise in obs:
        i = IDX[var]
        col = sigma[:, i].copy()
        gain = col / (sigma[i, i] + noise ** 2)
        sigma -= np.outer(gain, col)
    return sigma


class Estimator:
    def __init__(self, candidates=None, max_questions=6, targets=None):
        self.mu = MEAN.copy()
        self.sigma = prior_covariance()
        self.candidates = {c.key: c for c in (candidates or default_candidates())}
        self.asked: list[str] = []
        self.max_questions = max_questions
        self.targets = targets or TARGETS

    # --- contrat du moteur -------------------------------------------------
    def update(self, key: str, values) -> None:
        """values : dict {variable: valeur observée} (ou un float si une seule variable)."""
        c = self.candidates[key]
        if not isinstance(values, dict):
            values = {c.obs[0][0]: values}
        for var, noise in c.obs:
            if var not in values:
                continue
            i = IDX[var]
            col = self.sigma[:, i].copy()
            gain = col / (self.sigma[i, i] + noise ** 2)
            self.mu = self.mu + gain * (values[var] - self.mu[i])
            self.sigma = self.sigma - np.outer(gain, col)
        self.asked.append(key)

    def result(self) -> dict:
        out = {}
        for k in self.targets:
            i = IDX[k]
            sd = float(np.sqrt(max(self.sigma[i, i], 0)))
            out[k] = {"mean": float(self.mu[i]), "std": sd,
                      "ci90": (self.mu[i] - 1.645 * sd, self.mu[i] + 1.645 * sd)}
        return out

    def _met(self, sigma, k):
        return 1.645 * np.sqrt(max(sigma[IDX[k], IDX[k]], 0)) <= self.targets[k][0]

    def done(self) -> bool:
        return all(self._met(self.sigma, k) for k in self.targets)

    def next_question(self) -> Candidate | None:
        if self.done() or len(self.asked) >= self.max_questions:
            return None
        best, best_score = None, 0.0
        for c in self.candidates.values():
            if c.key in self.asked:
                continue
            after = _apply(None, self.sigma, c.obs)
            red = 0.0
            for k, (tol, w) in self.targets.items():
                j = IDX[k]
                if self._met(self.sigma, k):
                    continue  # cible déjà atteinte : ne compte plus
                # gain d'information (log-ratio) : saturant
                red += 0.5 * w * np.log(self.sigma[j, j] / max(after[j, j], 1e-9))
            score = red / c.cost
            if score > best_score:
                best, best_score = c, score
        return best
