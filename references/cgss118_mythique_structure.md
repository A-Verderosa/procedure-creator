# Structure CGSS 118 MYTHIQUE — Modèle de référence

Procédure : `PROC-MYTHIQUE-118-Attestation-de-Salaires-CGSS`
URL : `https://app.notion.com/p/aveconsultings/PROC-MYTHIQUE-118-Attestation-de-Salaires-CGSS-0c61d81e4c398267919401751deb2f81`
Niveau : 🔮 MYTHIQUE (dérivé de PROC-ULTRA-118, ID 497)

## Propriétés Notion

| Propriété | Valeur |
|-----------|--------|
| Statut | En révision |
| Validation | 2-Production |
| Direction | DIRECTION DE LA GESTION STATUTAIRE DU PERSONNEL |
| Pôle | PRH |
| Service | SERVICE RÉMUNÉRATION |
| Pilote | AVerderosa |
| Date actualisation | 2025-12-28 |
| Vérifiée | Non |
| Domaine | Documentation et Conformité Salariale |
| Activités | Attestation de Salaires CGSS |

## Acteurs

| Acteur | Rôle | Responsabilités |
|--------|------|-----------------|
| 🔴 Agent | Déclarant arrêt | Transmet avis (48h), CERFA |
| 🔵 Service Gestionnaire | Traitement admin | Vérifie (24h), saisit SIRH (48h), arrêté (5j) |
| 🟢 Service Rémunération | Transmission CGSS | Attestation Net Entreprise (M+1), contrôle (J+30) |
| 🟣 CGSS | Organisme payeur | Calcule et verse IJ |

## Sections complètes (341 blocs)

```
§0  📍 Localisation CRAIE
§1  Objet + Objectif opérationnel
§2  Champ d'application (2.1 Périmètre, 2.2 Inclusions, 2.3 Exclusions)
§3  Définitions & Glossaire (3.1 Définitions, 3.2 Acronymes)
§4  Documents de référence (4.1 Textes législatifs, 4.2 Textes réglementaires,
     4.3 Documents internes, 4.4 Traçabilité Phase 0)
§5  Acteurs responsables (5.1 Matrice RACI, 5.2 Détail par acteur, 5.3 Réformes)
§6  PROCÉDURE — ÉTAPES (CŒUR)
│   6.0    Vue par acteur — sequenceDiagram (exigence autorité de contrôle)
│   6.1    Synoptique express et navigation par phase
│   6.2    Détail des Étapes (toggle: 11 étapes détaillées avec acteur, durée, actions, doc, vigilance)
│   6.3-6.6 Vue détaillée par acteur, Format synoptique, Qualité par phase, Instructions
├── §7  Règles de gestion (G1→G10)
├── §8  Consignes opérationnelles (C1→C8)
├── §9  Analyse des risques (SBRX)
│   9.1  Mapping CRAIE, 9.2 Synthèse, 9.3 Tableau vue liée, 9.4 Dashboard,
│   9.5  Journal RB→RN→RC, 9.6 Matrice Risque↔Consigne↔Règle
├── §10 Documents support (DS1-DS4 sources, DE1-DE4 exploitation, 10.3 Modèles courrier)
├── §11 Documents d'enregistrement
├── §12 [libre]
├── §13 Cas pratiques & FAQ (3 cas, 3+ FAQ)
├── §14 Points de contrôle & Audit trail (14.1 Checkpoints, 14.2 Audit Trail, 14.3 Indicateurs)
├── §15 Formation & Support
├── §16 Pilotage & KPIs (16.1 Tableau de bord, 16.2 Alertes, 16.3 PDCA, 16.4 Améliorations, 16.5 OKR)
├── §17 Rapport groupe de lecture (17.1 Composition, 17.2 Analyse multidim., 17.3 Avis)
├── §18 Mise en œuvre, déploiement & plan de communication
│   18.1 Phases, 18.2 Plan com, 18.3 Gantt, 18.4 Ressources/budget, 18.5 Suivi
├── §19 Continuité de service & PCA (19.1 Scénarios, 19.2 Plan reprise, 19.3 Protocole urgence)
├── §20 Protection des données RGPD
├── §21 Conformité & référentiels normatifs (21.1 Matrice, 21.2 Score, 21.3 Plan action)
├── §22 Assurance qualité & maintenance (22.1 Quality Gate 7 crit., 22.2 VERSION-CHECK, 22.3 Glossaire)
├── §23 🔮 Visualisation avancée & intelligence décisionnelle (M1→M9)
│   23.1 M1 Bow-tie, 23.2 M2 Ishikawa, 23.3 M3 Radar (vue liée),
│   23.4 M4 Swimlane, 23.5 M5 SIPOC, 23.6 M6 Sankey,
│   23.7 M7 Timeline, 23.8 M8 Cockpit KPI, 23.9 M9 Heatmap RACI
├── Workflow : WF-PROC-PLATINE-2026
├── 📜 Historique des versions (V2.0 Mythique, V1.0 Ultra)
├── 🏆 Scorecard MYTHIQUE (90/100 → 💎 Chef-d'œuvre)
└── 🎚️ Matrice de couverture documentaire par niveau
```

## Structure du §6.0 (sequenceDiagram)

Le diagramme de séquence est en §6.0, immédiatement avant le synoptique express §6.1.
Intitulé : **"Vue par acteur — sequenceDiagram (exigence autorité de contrôle)"**

Caractéristiques :
- 4 participants (pas de `box`, pas de `init`)
- `autonumber` présent
- `Note over [acteur pivot]` pour chaque phase (A→D)
- `alt/else` pour subrogation (condition unique)
- Pas de `par/and`, `critical/option`, `break`
- Pas d'`actor Usager` — `participant` pour tous
- Icons emoji dans les labels : `🔴 Agent`, `🔵 Service Gestionnaire`, `🟢 Service Remuneration`, `🟣 CGSS`

## Structure détaillée des étapes (§6.2)

Chaque étape suit ce format en toggle :

```
Acteur : <rôle> → <rôle> | Durée : <durée>
Actions :
1. <action 1>
2. <action 2>
Documents : <référence document>
⚠️ Points de vigilance :
- <vigilance 1>
- <vigilance 2>
```

## Le Golden Example

Cette procédure est le **Golden Example** pour le niveau MYTHIQUE. Toute nouvelle procédure MYTHIQUE doit :
1. Respecter la même structure de sections
2. Positionner le sequenceDiagram en §6.0
3. Intégrer les 9 briques M1→M9 en §23
4. Afficher une scorecard (seuil ≥90 pour 💎 Chef-d'œuvre)
5. Avoir le verrou cycle de vie complet
