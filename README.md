# TailShirt

Détermination de la chemise sur-mesure adaptée avec un minimum de mesures.

- Spécifications : [docs/SPECIFICATIONS.md](docs/SPECIFICATIONS.md)
- Prototype du moteur (jalon M0) : [prototype/](prototype/)

## Lancer le prototype

```bash
python3 -m venv .venv && .venv/bin/pip install numpy pytest
.venv/bin/python -m pytest -q tests
.venv/bin/python prototype/simulate.py
```

## Résultats de simulation (M0)

Population **synthétique** (modèle à facteurs latents, paramètres plausibles, pas des données réelles) ;
2000 personnes ; bruit : mètre ruban 0,4 cm, photo 1,5–3,5 cm, réponses déclaratives 1–1,5 cm.

| Politique | Questions | Mesures dans la tolérance |
|-----------|-----------|---------------------------|
| Adaptative, plafond 8 | 8 | 7/9 à ≥ 99 % ; cou 30 %, poignet 45 %, biceps 50 % |
| Adaptative, plafond 12 | 12 | 9/9 ≥ 83 %, la plupart ≥ 98 % |
| Aléatoire, plafond 8 | 8 | 57–76 % partout |

Enseignements :

1. **Les mesures corporelles sont peu prédictibles les unes par les autres** (résidu spécifique important). Avec les tolérances du cahier des charges (±0,5 cm cou/poignet), il faut quasiment une mesure directe par cible ; le modèle statistique sert surtout à choisir lesquelles et à ordonner.
2. Le critère d'arrêt à 90 % n'est jamais atteint avec un bruit de ruban de 0,4 cm pour cou et poignet (1,645 × 0,4 > 0,5) : tolérance ou bruit à revoir.
3. L'objectif glouton « réduction de variance pondérée » concentrait l'effort sur une seule cible ; le **gain d'information (log-ratio) restreint aux cibles non atteintes** répartit mieux et bat l'ordre aléatoire.
4. Ces chiffres dépendent entièrement des paramètres synthétiques : à **recalibrer sur ANSUR II** puis sur données réelles avant toute conclusion produit.
