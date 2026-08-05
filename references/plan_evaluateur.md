# Évaluateur public — Plan de déploiement des procédures

## Architecture documentaire — 3 niveaux

```
Niveau 1 — Charte / Cadre de référence
└── Charte de l'évaluateur public (fondateur, validé DG)

Niveau 2 — Processus (macro-processus)
└── 5 missions (M1→M5), 17 processus (P1→P17)

Niveau 3 — Procédures et modes opératoires
└── 95 procédures détaillées (dans BDD Planning)
```

> **Note** : La BDD Planning (ID `3351d81e-4c39-827e-88a4-817c2739bbff`) contient l'inventaire complet : 117 items = 5 Missions + 17 Processus + 95 Procédures, tous avec statut « À créer ». Voir `references/planning_bdd_automation.md` pour l'analyse détaillée et la matrice d'automatisation.

---

## Les 5 missions (M1→M5)

| Code | Mission | Nb processus |
|------|---------|-------------|
| **M1** | Pilotage stratégique et programmation | P1-P3 |
| **M2** | Conduite d'une évaluation | P4-P10 |
| **M3** | Restitution et valorisation | P11-P13 |
| **M4** | Suivi des recommandations et impact | P14-P15 |
| **M5** | Fonctionnement transverse et amélioration continue | P16-P17 |

---

## Les 17 processus (P1→P17)

```
M1 — Pilotage stratégique
├── P1  Élaboration du programme annuel d'évaluation
├── P2  Traitement d'une saisine
└── P3  Instruction et cadrage préalable

M2 — Conduite d'une évaluation
├── P4  Élaboration de la note de cadrage
├── P5  Installation du comité de pilotage
├── P6  Lancement de la consultation (appel d'offres)
├── P7  Collecte et analyse des données
├── P8  Réunions techniques et entretiens
├── P9  Élaboration des conclusions et recommandations
└── P10 Assurance qualité et revue interne

M3 — Restitution
├── P11 Rédaction et validation du rapport
├── P12 Phase contradictoire
└── P13 Restitution et communication

M4 — Suivi
├── P14 Suivi des recommandations par la direction
└── P15 Évaluation d'impact à N+1

M5 — Transverse
├── P16 Gestion documentaire et des référentiels
└── P17 Veille méthodologique et amélioration continue
```

---

## Procédures prioritaires (Phase 1)

Ces 6 procédures sont identifiées pour le déploiement initial :

| Priorité | Procédure | Type | Niveau cible |
|----------|-----------|------|-------------|
| **P1** | Programme annuel d'évaluation | Pilotage | Or |
| **P2** | Traitement d'une saisine d'évaluation | Pilotage | Or |
| **P4** | Note de cadrage d'évaluation | Conduite | Platine |
| **P7** | Collecte et analyse des données | Conduite | Ultra |
| **P11** | Rédaction et validation du rapport | Restitution | Platine |
| **P15** | Évaluation d'impact à N+1 | Suivi | Ultra |

### Outils associés à créer

| Outil | Usage | Priorité |
|-------|-------|----------|
| Fiche de saisine d'évaluation | Standardiser les demandes | Haute |
| Note d'opportunité | Justifier le lancement | Haute |
| Guide d'entretien semi-directif | Cadrer les entretiens | Moyenne |
| Modèle de rapport d'évaluation | Standardiser la rédaction | Haute |
| Grille de notation QG évaluateur | Qualité interne | Moyenne |

---

## Structuration des pages Notion

Chaque procédure dans BDD 1 Procédures doit avoir :

```
Propriétés spécifiques évaluateur :
├── Mission : M1..M5 (select)
├── Processus : P1..P17 (select)
├── Type évaluation : Politique publique | RH | Performance
├── Périmètre évaluateur : Interne | Externe | Mixte
├── DG cible : direction concernée
└── Cycle : Programmation | Exécution | Restitution | Suivi

Relations :
├── Organigramme → évaluateur / directions évaluées
├── Annuaire → référent évaluation / pilotes
├── SBRX → risques méthodologiques / déontologiques
├── GED → guides, modèles, rapports antérieurs
└── Glossaire → définitions spécifiques évaluation
```
