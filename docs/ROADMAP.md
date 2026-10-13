# TailShirt — Suite du projet

État au 2026-10-14 : spécifications v0.2, prototype M0 du moteur (Python), simulation sur population **synthétique**. Aucune donnée réelle, aucune application.

## 1. Décisions à prendre (bloquantes)

| # | Décision | Pourquoi | Recommandation |
|---|----------|----------|----------------|
| D1 | Fabricant / tailleur partenaire et format de fiche de mesures | Définit les sorties exactes et les marges d'aisance | Un partenaire pilote avant tout développement mobile |
| D2 | Cible : homme seul ou mixte | Un modèle statistique par sexe | Homme d'abord |
| D3 | Tolérances acceptées sans ruban (cou/poignet ±1 cm ?) | Conditionne la promesse produit | Valider avec le partenaire |
| D4 | Framework mobile (Flutter / React Native / natif) | Accès caméra, LiDAR, pose estimation | Natif iOS d'abord (LiDAR, Apple Vision, Santé) |
| D5 | Jeu de données anthropométriques de référence | Remplace les paramètres synthétiques | ANSUR II si la licence et la population conviennent |

## 2. Étapes

### M0.5 — Recalage sur données réelles (1 à 2 semaines)
- Importer ANSUR II (ou équivalent), estimer `μ` et `Σ` réels pour les 11 variables.
- Remplacer les facteurs latents synthétiques de `prototype/engine.py`.
- Relancer la simulation et mettre à jour README et spécifications.

### M1 — Mesure du bruit réel des captures (2 à 3 semaines)
- Protocole : 30 à 50 volontaires, mesures de référence par un tailleur, puis questions, photos face/profil, photo de chemise à plat, scan LiDAR si disponible.
- Estimer l'écart-type réel de chaque observation, remplacer les hypothèses du tableau §3.3.
- Évaluer MediaPipe / Apple Vision pour l'estimation de pose et le passage pixels → cm (échelle : carte bancaire ou taille).
- Mesurer l'écart entre les réponses déclaratives (pantalon, veste) et les mesures réelles.

### M2 — Application mobile (4 à 6 semaines)
- Moteur porté sur l'appareil (algèbre linéaire seule : ≈ 200 lignes), contrat `update` / `next_question` / `result`.
- Parcours : consentement → import Santé (taille, poids, âge, sexe) → questions → captures → récapitulatif avec intervalles d'incertitude.
- Traitement des photos sur l'appareil, aucune image envoyée sans consentement.
- Tests : moteur (existants), parcours, accessibilité.

### M3 — Pilote (4 semaines)
- 20 à 30 chemises confectionnées chez le partenaire, avec retour « va / ne va pas » par mesure.
- Métriques : % de mesures dans la tolérance, nombre d'étapes, taux d'abandon, retouches.
- Ré-estimation de `μ`, `Σ` et des bruits sur les données collectées.

## 3. Risques

| Risque | Impact | Parade |
|--------|--------|--------|
| Bruit des photos supérieur aux hypothèses | Mesures hors tolérance | M1 avant M2 ; repli sur plus d'étapes ou LiDAR |
| Réponses déclaratives biaisées (vêtements portés trop serrés/larges) | Biais systématique | Question de correction d'aisance, recalage au pilote |
| Photos = données sensibles | RGPD, confiance | Traitement local, consentement, suppression |
| Population de référence ≠ clients | Estimations décalées | Recalage sur données propres dès M3 |
| Biceps et longueur de chemise mal couverts sans LiDAR | Retouches | Surveiller au pilote ; ajouter des questions si besoin |

## 4. Critères de sortie du projet pilote

- ≥ 85 % des mesures dans la tolérance sur les 9 cibles avec ≤ 5 étapes.
- ≤ 10 % de chemises à retoucher.
- Temps médian de parcours ≤ 5 minutes.

## 5. Prochaine action immédiate

Recaler le moteur sur un jeu anthropométrique réel (M0.5), en parallèle de la décision D1 avec un partenaire.
