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

## Résultats de simulation (M0, sans mètre ruban)

Population **synthétique** (pas de données réelles), 1000 personnes, 5 étapes max, tolérances assouplies pour cou et poignet (±1 cm).
Part des mesures dans la tolérance :

| Scénario | Effort | Cou | Poitrine | Taille | Épaules | Manche | Poignet |
|----------|--------|-----|----------|--------|---------|--------|---------|
| A. Questions seules | 5 | 73 % | 36 % | 19 % | 44 % | 58 % | 74 % |
| B. + photos (face, profil, chemise à plat) | 7 | 91 % | 86 % | 64 % | 86 % | 89 % | 92 % |
| C. + LiDAR | 9 | 92 % | 96 % | 92 % | 94 % | 91 % | 95 % |

Enseignements :

1. Les questions seules ne suffisent pas ; les photos sont indispensables, le LiDAR apporte le meilleur gain sur poitrine et taille.
2. Sans ruban, ±0,5 cm sur cou/poignet n'est pas réaliste : viser ±1 cm.
3. La photo d'une chemise existante est la meilleure source pour cou, manche et poignet, mais elle mesure la chemise (aisance), pas le corps.
4. Chiffres liés à des hypothèses de bruit à vérifier avec une vraie estimation de pose, puis à recaler sur ANSUR II.
