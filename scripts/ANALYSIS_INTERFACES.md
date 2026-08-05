# Analyse d'Interface — Agent PROC Orchestrator
# Généré par tâche kanban t_c32d9bce847e
# Date: 2026-08-01

## 1. Matrice des interfaces scripts

| Script | Args d'entrée | Format entrée | Format sortie | Modes batch |
|--------|--------------|--------------|--------------|-------------|
| consult_bdd.py | --check, --list, --proc, --filter, --schema, --output, --limit, --page | ID/titre | JSON stdout/fichier | Non |
| sync_notion.py | --push, --pull, --update, --set-relations, --output | JSON fichier | JSON stdout/fichier | Non |
| generate_contract.py | --from-file, --niveau, --interactive, --validate, --output, --check, --notion-format, --batch/--glob/--dir-output, --verify-unique | JSON fichier | JSON fichier | Oui (JSON) |
| bullet_proof.py | --file, --diff-with, --angle, --output, --check, --notion-verify, --batch/--glob/--dir-output | JSON fichier | JSON fichier | Oui (JSON) |
| qg_validator.py | --file, --niveau, --report, --json, --check, --notion-id, --batch/--glob/--dir-output, --validate-sections | MD fichier | JSON stdout + rapport MD | Oui (MD) |

## 2. Flux de données pipeline

```
[1] INTAKE
    │ Paramètres : titre, niveau, type_rh, perimetre, acteurs, mode
    ▼
[2] ANTI_DUPLICATE
    │ consult_bdd.py --list --filter Titre "<titre>"
    │ consult_bdd.py --list --filter "Procedure_ID" "<prefix>"
    ▼
[3] CONSULT_BDD_CANONIQUES
    │ consult_bdd.py --proc "<id>" --output /tmp/proc_data.json
    ▼
[4] DESIGN
    │ Sélection template : templates/<niveau>_template.md
    │ Sources doctrine : références/niveaux.yaml, qg_matrix.yaml
    │ Golden example : CGSS 118 ULTRA
    ▼
[5] GENERATE → generate_contract.py
    │ --from-file /tmp/proc_data.json --niveau <n> --output /tmp/contract.json
    ▼
[6] LOCAL_QG → qg_validator.py
    │ --file /tmp/procedure.md --niveau <n> --json --report
    ▼
[7] BULLET_PROOFING → bullet_proof.py
    │ --file /tmp/contract.json --output /tmp/bullet_report.json
    ▼
[8] SYNC_NOTION → sync_notion.py
    │ --push /tmp/contract.json --output /tmp/sync_result.json
    │ (ou --update <id> --push ...)
    ▼
[9] REPORT + EXEC_CLOSE
    │ Compilation : score QG + bullet + sync result → rapport final
```

## 3. Mapping DOX_EXEC_CORE → Scripts

| Étape | Script(s) | Condition |
|-------|-----------|-----------|
| [1] INTAKE | Aucun (parser interne) | Toujours |
| [2] ANTI_DUPLICATE | consult_bdd.py --list --filter | Si mode=create ou upgrade |
| [3] CONSULT_BDD | consult_bdd.py --proc --output | Si mode=create ou upgrade |
| [4] DESIGN | Aucun (logique template) | Si mode=create ou upgrade |
| [5] GENERATE | generate_contract.py --from-file | Si mode=create ou upgrade |
| [6] LOCAL_QG | qg_validator.py --file --json | Toujours (sauf --list/--check) |
| [7] BULLET_PROOF | bullet_proof.py --file --output | Toujours (sauf --list/--check) |
| [8] SYNC_NOTION | sync_notion.py --push ou --pull | Si mode=create/upgrade/resync |
| [9] REPORT | Aucun (compilation interne) | Toujours |

## 4. Répertoire de travail pipeline

```
/tmp/proc_<uuid>/
├── 01_intake_params.json       # Paramètres d'entrée normalisés
├── 02_antiduplicate.json       # Résultat vérification doublons
├── 03_bdd_canoniques.json      # Données BDD chargées
├── 04_design.md                # Note de conception/doctrine
├── 05_contract.json            # DOX Contract généré
├── 06_procedure.md             # Procédure markdown générée (si applicable)
├── 07_qg_report.md             # Rapport Quality Gates
├── 07_qg_results.json          # Résultats QG structurés
├── 08_bullet_report.json       # Résultats bullet proofing
├── 09_sync_result.json         # Résultat sync Notion
└── 10_final_report.md          # Rapport final consolidé
```

## 5. Modes de l'orchestrateur

| Mode | Pipeline exécuté | Usage |
|------|-----------------|-------|
| create | [1]→[2]→[3]→[4]→[5]→[6]→[7]→[8]→[9] | Nouvelle procédure de zéro |
| upgrade | [1]→[2]→[3]→[4]→[5]→[6]→[7]→[8]→[9] (charge existante) | Monter de niveau |
| audit | [1]→[3]→[6]→[7]→[9] | Auditer sans modifier |
| resync | [1]→[8]→[9] | Sync bidirectionnelle |
| list | consult_bdd.py --list | Lister les procédures |
| check | [check] tous les scripts | Vérifier connexions |
