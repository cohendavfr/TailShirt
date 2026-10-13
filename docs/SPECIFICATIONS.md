# TailShirt — Spécifications techniques

Version 0.2 (brouillon) — 2026-10-14

## 1. Objectif

Application mobile native qui détermine les **mesures de fabrication d'une chemise sur-mesure** (made-to-measure) en demandant à l'utilisateur le **nombre minimum d'informations**, par questions simples et/ou photo/scan.

Principe : on ne mesure pas tout le corps ; on pose uniquement les questions qui réduisent le plus l'incertitude sur les mesures de la chemise, et on s'arrête dès que la précision cible est atteinte.

### Hors périmètre (v1)
- Prêt-à-porter / tailles standard (S, M, L).
- Paiement, commande, logistique de fabrication.
- Autres vêtements que la chemise.

## 2. Sorties : mesures de la chemise

| Code | Mesure | Unité | Tolérance cible (±) |
|------|--------|-------|---------------------|
| `neck` | Tour de cou | cm | 0,5 |
| `chest` | Tour de poitrine | cm | 1,5 |
| `waist` | Tour de taille | cm | 1,5 |
| `hip` | Tour de bassin (bas de chemise) | cm | 2,0 |
| `shoulder` | Carrure / largeur d'épaules | cm | 1,0 |
| `sleeve` | Longueur de manche | cm | 1,0 |
| `bicep` | Tour de biceps | cm | 1,5 |
| `wrist` | Tour de poignet | cm | 0,5 |
| `length` | Longueur de la chemise | cm | 1,5 |

Pour chaque mesure, l'algorithme retourne : valeur estimée, écart-type, intervalle de confiance à 90 %. Les marges d'aisance (confort, coupe slim/regular/ample) sont ajoutées **après** estimation, par règles métier configurables.

## 3. Entrées utilisateur

> **Contrainte v0.2 : aucun mètre ruban.** Tout passe par des questions simples et le smartphone. Les sections 3.3 et 4.5 remplacent les références au ruban.

### 3.1 Questions simples (sans mètre ruban)
Taille, poids, âge, sexe (pour le choix du modèle statistique), morphologie perçue (ventre, épaules, etc.), taille de chemise habituelle, tour de cou habituel s'il est connu.

### 3.2 Photo / scan
- Photo(s) de face (et profil optionnel) avec le téléphone, utilisateur en vêtements près du corps.
- Échelle : taille déclarée de l'utilisateur ou objet de référence (carte bancaire).
- Extraction de points clés corporels (pose estimation) : épaules, bras, torse, hanches ; largeurs et longueurs en pixels converties en cm.
- Les mesures issues de la photo sont traitées comme des **observations bruitées** (avec leur propre écart-type), pas comme des vérités.
- Traitement **sur l'appareil** par défaut ; aucune photo n'est envoyée au serveur ni conservée sans consentement explicite.

### 3.3 Étapes disponibles (v0.2)

| Étape | Effort | Observations | Précision supposée (σ) |
|-------|--------|--------------|------------------------|
| Questions : taille, poids, col et manche habituels, taille S/M/L | 1 chacune | variable correspondante | 1–4 cm |
| Photo en pied de face | 2 | 10 mesures d'un coup | 1,5–4 cm |
| Photo de profil | 1 | poitrine, taille, bassin (profondeur) | 2 cm |
| Photo d'une chemise qui va bien, à plat, avec une carte bancaire | 2 | col, épaules, manche, longueur, poitrine, poignet | 0,8–1,5 cm |
| Scan 3D LiDAR (appareils compatibles, optionnel) | 3 | toutes les mesures | 1,0–1,5 cm |

Limite connue : la chemise photographiée mesure la **chemise**, pas le corps (aisance, rétrécissement) ; son biais est à modéliser.

## 4. Algorithme

### 4.1 Modèle probabiliste
Les mesures corporelles sont modélisées par une loi **gaussienne multivariée** conditionnée aux variables démographiques :

`m | d ~ N(μ(d), Σ(d))`

- `m` : vecteur des mesures cibles + mesures intermédiaires (poitrine, etc.).
- `d` : taille, poids, âge, sexe.
- `μ(d)` : régression linéaire (puis éventuellement non linéaire) sur `d`.
- `Σ` : matrice de covariance entre mesures (ex. cou ↔ poitrine ↔ poids fortement corrélés).

Chaque nouvelle observation (réponse ou photo) met à jour la distribution a posteriori par **conditionnement gaussien** (équivalent d'un filtre de Kalman) :

`μ' = μ + Σ_{·o} (Σ_{oo} + R)^{-1} (y - μ_o)`
`Σ' = Σ - Σ_{·o} (Σ_{oo} + R)^{-1} Σ_{o·}`

où `R` est la variance de bruit de l'observation (faible pour un mètre ruban, plus forte pour une photo ou une réponse subjective).

### 4.2 Choix de la question suivante (sélection adaptative)
Pour chaque observation candidate `c` (liste de questions/mesures possibles) :

`gain(c) = [ Σ_k w_k · (var_k - var'_k(c)) / tol_k² ] / coût(c)`

- `var'_k(c)` : variance a posteriori attendue de la mesure `k` si on observe `c` (calculable en forme close en gaussien, sans connaître la réponse).
- `tol_k` : tolérance cible du tableau §2 ; `w_k` : poids d'importance (le cou compte plus que le biceps).
- `coût(c)` : effort pour l'utilisateur (question simple < photo < mesure au mètre ruban).

On pose la question de plus fort gain.

### 4.3 Critère d'arrêt
L'algorithme s'arrête quand, pour toutes les mesures `k` : `P(|erreur_k| < tol_k) ≥ 90 %`, ou lorsqu'un plafond de questions est atteint (par défaut 8). Dans ce dernier cas, les mesures restantes sont signalées « moins précises » avec proposition d'une mesure supplémentaire.

### 4.4 Amorçage des données (aucune donnée propriétaire au départ)
1. **Phase 0** : paramètres `μ`, `Σ` issus de jeux de données anthropométriques publics (ex. ANSUR II) ; à valider légalement (licence) et statistiquement.
2. **Phase 1** : collecte opt-in dans l'app des mesures réelles prises par un tailleur / mètre ruban + chemises effectivement confectionnées et retours.
3. **Phase 2** : ré-estimation périodique de `μ` et `Σ` sur les données propres ; segmentation par morphologie.

### 4.5 Résultats de simulation sans ruban (population synthétique, 5 étapes max)

| Scénario | Effort moyen | Cou | Poitrine | Taille | Épaules | Manche | Poignet |
|----------|--------------|-----|----------|--------|---------|--------|---------|
| A. Questions seules | 5 | 73 % | 36 % | 19 % | 44 % | 58 % | 74 % |
| B. + photos | 7 | 91 % | 86 % | 64 % | 86 % | 89 % | 92 % |
| C. + LiDAR | 9 | 92 % | 96 % | 92 % | 94 % | 91 % | 95 % |

Part des mesures dans la tolérance ; tolérances assouplies pour cou et poignet (±1,0 cm). Aux tolérances initiales (cou/poignet ±0,5 cm), le cou n'atteint que 59–61 %. **Conclusion : sans ruban, viser ±1 cm sur cou et poignet et ±1,5 cm ailleurs ; prévoir une marge d'aisance et un retour post-livraison.**

## 5. Interface (application mobile native)

### Parcours
1. Accueil et consentement (données personnelles, photo).
2. Profil de base : taille, poids, âge, sexe.
3. Boucle adaptative : une question (ou une invitation à photographier) par écran, avec indicateur « précision estimée » qui monte.
4. Récapitulatif : mesures estimées + intervalle d'incertitude, choix de la coupe (slim / regular / ample).
5. Validation et export (JSON / envoi au fabricant).
6. Retour post-livraison : « la chemise va-t-elle ? » (alimente la phase 1).

### Exigences
- Une seule question par écran, saisie en moins de 10 secondes.
- Fonctionne hors ligne (modèle embarqué).
- Accessibilité (taille de police, VoiceOver/TalkBack) ; français + anglais.

## 6. Architecture technique (proposition)

| Couche | Choix proposé | Remarque |
|--------|---------------|----------|
| App mobile | Flutter ou React Native (iOS + Android) | Un seul code ; accès caméra |
| Moteur d'estimation | Bibliothèque pure (algèbre linéaire) embarquée | Testable, hors ligne |
| Vision | Pose estimation sur appareil (MediaPipe / Apple Vision) | Pas d'envoi de photos |
| Back-end (optionnel) | API REST + base PostgreSQL | Stockage mesures, retours, ré-entraînement |
| Entraînement | Python (NumPy / scikit-learn), notebooks | Export des paramètres `μ`, `Σ` en JSON |

Le moteur est isolé de l'interface et défini par un contrat :

```
estimate(state, observation) -> state'        # mise à jour
next_question(state)         -> Question | None  # None = arrêt
result(state)                -> {measure: {mean, std, ci90}}
```

## 7. Qualité et évaluation

- **Métrique principale** : erreur absolue moyenne par mesure vs. mesure d'un tailleur, avec % de mesures dans la tolérance.
- **Métrique secondaire** : nombre moyen de questions pour atteindre le critère d'arrêt (objectif : ≤ 5).
- Validation sur ≥ 100 sujets avec mesures de référence avant ouverture publique.
- Tests unitaires du moteur (cas synthétiques où la solution exacte est connue) ; tests de non-régression sur jeu de référence.

## 8. Données personnelles (RGPD)

Les mesures corporelles et photos sont des données personnelles sensibles : consentement explicite, minimisation, traitement local des photos, suppression sur demande, pas de réutilisation pour l'entraînement sans opt-in.

## 9. Jalons

| Jalon | Contenu |
|-------|---------|
| M0 | Choix du jeu anthropométrique, prototype du moteur en Python, simulation du nombre de questions |
| M1 | Moteur validé + app mobile avec questions simples |
| M2 | Ajout photo/scan |
| M3 | Pilote avec tailleur, collecte réelle, recalibrage |

## 10. Questions ouvertes

- Quel fabricant / tailleur et quel format exact de fiche de mesures attend-il ?
- Les marges d'aisance par coupe : qui les définit ?
- Cible marché (homme seul ou mixte) : un modèle par sexe est nécessaire.
- Licence et pertinence du jeu de données public (population de référence vs. clients visés).
- Nom de domaine, budget et délais.
