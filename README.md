# Procédure Creator — Évaluateur Public

Système de gestion automatisée de procédures qualité pour l'**Évaluateur Public**, architecturé autour de l'écosystème **Notion ↔ Hermes Agent**.

## Architecture

```
┌──────────────────────────────────────────┐
│           Notion (DB-Centric V2)          │
│  Page MYTHIQUE → BDD dédiées (95+ proc.) │
└────────────────┬─────────────────────────┘
                 │ API
┌────────────────▼─────────────────────────┐
│         Hermes Agent (Pipeline)           │
│  Scripts Python → Création / Mise à jour │
└────────────────┬─────────────────────────┘
                 │
┌────────────────▼─────────────────────────┐
│         GitHub (versioning)               │
│      Traçabilité et backup du code        │
└──────────────────────────────────────────┘
```

## Structure du repo

```
procedure-creator/
├── scripts/              # Pipeline principal (Python)
│   ├── publish_procedure.py   # Orchestrateur de publication
│   ├── modules_service.py     # Modules (glossary, faq, ged, annuaire)
│   ├── sync_notion.py         # Synchronisation Notion ↔ Hermes
│   ├── notion_shared.py       # Helpers API Notion
│   ├── bullet_proof.py        # Vérification structurelle
│   ├── check_structure.py     # Validation des sections MYTHIQUE
│   ├── generate_contract.py   # Génération contrat
│   ├── generate_defaults.py   # Valeurs par défaut pipeline
│   ├── render_procedure.py    # Rendu markdown → Notion
│   ├── qg_validator.py        # Quality Gate validation
│   ├── consult_bdd.py         # Consultation BDD Notion
│   ├── create_satellite_pages.py  # Pages satellites
│   ├── create_related_pages.py     # Pages liées
│   ├── verrouiller.sh         # Script verrouillage pipeline
│   └── ...                    # + scripts batch et utilitaires
├── templates/             # Templates MYTHIQUE par niveau
│   ├── akuma_template.md       # Niveau Akuma (100% automatisé)
│   ├── platine_template.md     # Niveau Platine
│   ├── argent_template.md      # Niveau Argent (assisté)
│   ├── or_template.md          # Niveau Or (assisté)
│   ├── bronze_template.md      # Niveau Bronze
│   └── ultra_template.md       # Niveau Ultra
├── references/            # Documentation technique
│   ├── bdd_canoniques.yaml     # Schémas BDD canoniques
│   ├── db-centric-v2-pipeline.md  # Architecture DB-Centric V2
│   ├── bdd_mapping.md          # Mapping des BDD Notion
│   ├── pitfalls.md             # Pièges et anti-patterns
│   ├── pipeline.md             # Documentation du pipeline
│   └── ...
└── flux_evaluateur/       # Procédures prioritaires
    ├── charte_evaluation.md
    └── procedures_prioritaires/
        ├── CEV-P02_*           # Saisine évaluateur
        ├── CEV-P04_*           # Note de cadrage
        ├── CEV-P07_*           # Collecte et analyse de données
        ├── CEV-P08_*           # Phase contradictoire
        ├── CEV-P09_*           # Suivi des recommandations
        └── M1-P3-01_*          # Macro-processus
```

## Niveaux d'automatisation

| Niveau | Taux | Description |
|--------|------|-------------|
| **Akuma** | 100% | Pipeline complet, zéro intervention humaine |
| **Platine** | ~80% | Automatisé, validation ponctuelle requise |
| **Argent/Or** | Assisté | Génération assistée, rédaction humaine |
| **Bronze** | Manuel | Templates seulements |

## Pipeline de publication

1. **Analyse** — Parse le document source et extrait la structure
2. **Glossaire** — Crée/met à jour les entrées glossaire dans Notion
3. **FAQ** — Génère les Q/R dans la base FAQ
4. **GED** — Enregistre les documents supports et références
5. **Pages BUS** — Publication automatique des pages de service
6. **Rapport de lecture** — Génération du rapport qualité
7. **Verrouillage** — 3 verrous (contrat → structure → diff Golden)

## Prérequis

- Hermes Agent configuré avec les skills :
  - `procedure-creator`
  - `notion`
  - `faq-service`
  - `ged-service`
  - `glossary-service`
  - `annuaire-service`
- Token API Notion avec accès aux BDD du workspace
- Token Google (pour Google Tasks / Google Workspace)

## Utilisation

```bash
# Lancer le pipeline complet pour une procédure
hermes run "Publie la procédure CEV-P02"

# Vérification structure
python3 scripts/check_structure.py --input procedure.md

# Quality Gate
python3 scripts/qg_validator.py --procedure procedure.md
```

## Licence

Projet interne — Usage réservé à l'Évaluateur Public.
