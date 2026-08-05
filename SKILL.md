---
name: procedure-creator
description: "Agent PROC — Créer, améliorer, auditer et synchroniser des procédures administratives/RH/qualité de niveau Bronze à Akuma, connecté aux BDD Notion canoniques"
version: 2.4.0
author: Hermes Agent
metadata:
  hermes:
    tags: [proc, procedure, notion, dox, quality-gate, rh, evaluation]
    related_skills: [notion, systematic-debugging, plan, proc-orchestrator]
---

# Agent PROC — Expert Procédures

Agent spécialisé dans la création et la gestion de procédures, implémentant le workflow **DOX_EXEC_CORE** et la **Doctrine PROC** (DOX v6.0).

## Principes

- **Notion = PUV** (Point Unique de Vérité)
- **Hermes = Moteur d'exécution** (skills + scripts Python + cron)
- **DOX Standard** — grille modulaire 7 niveaux + QG G1-G21
- **BDD-Native** — relations dynamiques Organigramme/Annuaire/GED/SBRX
- **Modulaire (DB-Centric V3)** — chaque domaine partagé (Glossaire, GED, Annuaire, FAQ) devient un module autonome sur le modèle COMP avec Pages Bus pour le liant inter-projets. Voir `references/modular-architecture.md`
- **DB-Centric V2** — page MYTHIQUE = dashboard (props + vues liées), sections = BDD dédiées

## Pipeline DB-Centric V2 (11 étapes)

Voir `references/pipeline.md` pour le détail complet de chaque étape, fonctions, formats de contrat.

Étapes : DOX → MYTHIQUE → **PAGES BUS** (enregistrement automatique) → **Rapport lecture** (création initial) → SBRX (risques) → PMRI (mesures) → FAQ → Glossaire → Règles/Consignes (Exigences) → GED (supports + références) → Relations inverses (dont BUS inverse MYTHIQUE←PAGES BUS) → Dashboard.

**Depuis la refonte v2.4.0**, les opérations sur Glossaire, GED, FAQ et Annuaire passent par `modules_service.py` (skills modulaires) plutôt que par des appels API bruts. `populate_glossary()` → `glossary_create()`, `populate_ged()` → `ged_create()`, `populate_faq()` → `faq_create()`, rédacteur/valideur → `annuaire_get_default_author()`.

## Base de données

Voir `references/databases.md` pour les IDs et propriétés de toutes les BDD Notion (DOX, MYTHIQUE, SBRX, PMRI, FAQ, Glossaire Main, Exigences, GED MAIN, RAPPORTS LECTURE DOX, ANNUAIRE DOX).
Voir `references/modular-architecture.md` pour l'architecture modulaire (Pages Bus, skills par module, migration depuis le mono-projet).

## Pièges et correctifs

Voir `references/pitfalls.md` pour la liste à jour des bugs connus et leur résolution.

Points critiques :
1. Toujours nettoyer les anciens blocs dashboard avant d'en ajouter (fetch_children + delete_children)
2. Regex des codes GED : `[A-Z][A-Z0-9-]*\\d+` (commence par lettre, finit par chiffre) — capte `CEV-F01`, `D1`, `REF1`. Évite les mots simples sans chiffres
3. Les phases doivent être formatées "Phase N — Titre" dans le heading_3
4. `parse_documents()` parse **les deux champs** : `documents_supports` (catégorie "Document support") et `documents_reference` (catégorie "Document référence", code REF-N)
5. Les champs `definitions`, `regles`, `consignes` doivent être formatés avec des `\\n` entre chaque entrée (pas `;`). `parse_glossary` attend `**Terme :** Définition` par ligne ; `parse_exigences` attend `N. Titre\\n...`
6. Les helpers locaux (`notion_get`/`post`/`patch`/`delete`) dans `publish_procedure.py` sont des **shims** vers `notion_request()` de `notion_shared.py`. Le paramètre `token` est optionnel et ignoré. Toute nouvelle fonction doit appeler `notion_request()` ou `notion_query()` directement.
7. Le champ **MPPC (mesures)** dans l'ancienne BDD Procédures RH est **déprécié**. PMRI MYTHIQUE (via `populate_pmri`) fait le travail avec relations bidirectionnelles, Famille, Fréquence, Type, Responsable structurés.
8. `parse_risks()` doit propager `impact`, `probability`, `hyp_rc`, `hyp_rn` — cf. `references/pitfalls.md` #8 (résolu août 2026)
9. `populate_sbrx()` écrit 7 champs : Titre, Code risque, Procédure Mère, Impact (number), Probabilité (number), Hypothèse RC (rich_text), Hypothèse RN (rich_text). Cf. `references/pipeline.md` pour le détail.
10. `populate_pmri()` écrit jusqu'à 9 champs : Titre, Procédure Source, Risque Traité, Effets attendus (2× number), Famille de mesure (multi_select), Fréquence contrôle (select), Type de contrôle (select), Responsable (relation). Cf. `references/pipeline.md` pour les mappings contrat→Notion.
11. **Rédacteur/Validateur par défaut** : le pipeline utilise `annuaire_get_default_author()` depuis `modules_service.py` (fallback AVR2 `12f1d81e-4c39-81af-b875-e5c5364a397c`). Plus d'ID hardcodé dans le pipeline.
12. **Relation `dual_property` API Notion** : Quand on crée une relation avec `dual_property`, la propriété inverse sur la base cible (e.g. PAGES BUS) est créée mais n'apparaît PAS dans `GET /v1/databases/{target}`. Elle est fonctionnelle mais pas listée dans la réponse GET. Voir `references/pitfalls.md` #12.
13. **Kanban Migration** : Pour suivre un chantier multi-étapes (ex: migration modulaire), créer une base KANBAN dédiée avec `Statut` (select: À faire, En cours, Bloqué, Fait) + relation optionnelle vers PAGES BUS. Ajouter une vue Kanban groupée par Statut dans Notion.
14. **Responsable PMRI nécessite des entrées préexistantes** dans l'Annuaire DOX (base contacts `6e9d978c-b165-490c-a6c5-a4de5eaa5e56`) pour être lié. Si la base est vide, le pipeline log un avertissement et skip le champ. Créer manuellement ou via script avant la première procédure qui utilise Responsable.

## Fichiers du pipeline

Tous les scripts sont dans `scripts/` :
- `publish_procedure.py` — orchestre le pipeline complet
- `render_procedure.py` — génère les blocs dashboard (incl. `generate_risk_matrix()` en quadrantChart Mermaid)
- `notion_shared.py` — connecteurs API Notion, IDs des BDD
- `create_satellite_pages.py` — création des pages satellites (SBRX, PMRI, FAQ)
- `modules_service.py` — module de service pour les opérations CRUD sur Glossaire, GED, FAQ, Annuaire, PAGES BUS (consumé par publish_procedure.py)

## Génération du contrat

```bash
cd /data/skills/software-development/procedure-creator
python3 scripts/generate_contract.py --procedure "M1-P3-XX" --output /data/contrat_M1-P3-XX.json
python3 scripts/publish_procedure.py /data/contrat_M1-P3-XX.json --publish
```

## Paramètres d'exécution

- Token Notion : variable d'environnement `NOTION_API_KEY`
- Rate limiting : `BATCH_DELAY = 0.35` (entre chaque appel API)
- Pagination enfants : 100 blocs par requête (limite Notion)
- Défauts : Rédacteur/Validateur via `annuaire_get_default_author()` depuis modules_service (fallback AVR2), Dernière revue = date du jour
