# 📘 Playbook Agent PROC

> **Version** : 1.0.0  
> **Date** : 2026-08-01  
> **Workflow** : DOX_EXEC_CORE  
> **Standard** : DOX v6.0 — 7 niveaux, 21 Quality Gates

---

## 1. Présentation

L'**Agent PROC** est un système de création, d'audit et de synchronisation de procédures administratives/RH/qualité, connecté aux 10 BDD Notion canoniques du système DOX.

### Architecture

```
┌───────────────────────────────────────────────────────┐
│                    Agent PROC                          │
│                                                        │
│  📐 Orchestrateur (proc_orchestrator.py)               │
│  ├── Étape 1: INTAKE         — Analyse de la demande   │
│  ├── Étape 2: ANTI_DUPLICATE — Vérification doublons   │
│  ├── Étape 3: CONSULT_BDD    — Chargement BDD Notion   │
│  ├── Étape 4: DESIGN         — Doctrine + template     │
│  ├── Étape 5: GENERATE       — DOX Contract            │
│  ├── Étape 6: LOCAL_QG       — Quality Gates G1-G21    │
│  ├── Étape 7: BULLET_PROOF   — 4 angles sécurisation   │
│  ├── Étape 8: SYNC_NOTION    — Push/Pull Notion         │
│  └── Étape 9: REPORT         — Rapport final            │
│                                                        │
│  5 scripts spécialisés                                  │
│  ├── consult_bdd.py         — Consultation BDD          │
│  ├── generate_contract.py   — Génération contrat        │
│  ├── qg_validator.py        — Validation QG             │
│  ├── bullet_proof.py        — Vérification 4 angles     │
│  └── sync_notion.py         — Sync bidirectionnelle     │
│                                                        │
│  Module partagé                                         │
│  └── notion_shared.py       — Token, requêtes, props    │
│                                                        │
│  Références                                             │
│  ├── references/niveaux.yaml     — 7 niveaux de prod    │
│  ├── references/qg_matrix.yaml   — G1-G21 critères      │
│  ├── references/bdd_canoniques.yaml — IDs BDD Notion    │
│  └── references/plan_evaluateur.md — Plan évaluateur    │
│                                                        │
│  Templates (7 niveaux)                                  │
│  └── templates/{niveau}_template.md                     │
└───────────────────────────────────────────────────────┘
```

---

## 2. Modes d'utilisation

### 2.1 Création (`--mode create`)

Pipeline complet pour créer une nouvelle procédure depuis zéro.

```bash
python3 proc_orchestrator.py --mode create \
    --niveau argent \
    --titre "Gestion des absences" \
    --type-rh "temps_travail" \
    --perimetre "DGAT, DGSP" \
    --acteurs "responsable_rh,gestionnaire_paie"
```

### 2.2 Mise à jour (`--mode upgrade`)

Monter une procédure existante d'un niveau (ex: Argent → Or).

```bash
python3 proc_orchestrator.py --mode upgrade \
    --proc PRH-042 \
    --niveau or
```

### 2.3 Audit (`--mode audit`)

Auditer une procédure sans la modifier (QG + Bullet Proof).

```bash
python3 proc_orchestrator.py --mode audit \
    --proc PRH-042
```

### 2.4 Resynchronisation (`--mode resync`)

Synchronisation bidirectionnelle Notion.

```bash
python3 proc_orchestrator.py --mode resync \
    --proc PRH-042
```

### 2.5 Liste (`--mode list`)

Lister les procédures dans la BDD.

```bash
python3 proc_orchestrator.py --mode list --limit 20
python3 proc_orchestrator.py --mode list --filter-prop Titre --filter-val "CGSS"
```

### 2.6 Vérification (`--mode check`)

Vérifier l'état de tout le système.

```bash
python3 proc_orchestrator.py --mode check
```

---

## 3. Les 7 niveaux de production DOX

| Niveau | Quantité sections | Finalité | QG requis |
|--------|:-:|----------|:-:|
| 🥉 **Bronze** | 11 | Cadrage minimal, ébauche | G1–G7 |
| 🥈 **Argent** | 14 | Procédure interne exploitable | G1–G7, G8 |
| 🥇 **Or** | 17 | Procédure professionnelle stabilisée | G1–G11 |
| 💎 **Platine** | 23 | Audit-ready (gouvernance + déploiement) | G1–G14 |
| 💎 **Ultra** | 31 | Production critique | G1–G18 |
| 🔮 **Mythique** | 31 + 9 briques | Décisionnelle avancée, cockpit KPI | G1–G20 |
| 👹 **Akuma** | Diagnostic/simulation | Auto-évolution contrôlée | G1–G21 |

---

## 4. DOX_EXEC_CORE — Détail des 9 étapes

### [1] INTAKE
**Action** : Analyser la demande utilisateur, normaliser les paramètres.  
**Script** : Interne à l'orchestrateur.  
**Entrée** : Arguments CLI (--titre, --niveau, --type-rh, --perimetre, --acteurs).  
**Sortie** : Fichier `01_intake_params.json`.

### [2] ANTI_DUPLICATE
**Action** : Interroger la BDD Notion pour détecter les doublons.  
**Script** : `consult_bdd.py --list --filter Titre "<titre>"`  
**Entrée** : Titre de la procédure.  
**Décision** : Si doublon → proposer upgrade ; forcer avec `--force`.

### [3] CONSULT_BDD_CANONIQUES
**Action** : Charger les données BDD Notion et les 10 BDD canoniques.  
**Script** : `consult_bdd.py --proc "<id>" --output data.json`  
**Entrée** : ID ou titre de procédure.  
**Sortie** : Données BDD + relations existantes.

### [4] DESIGN
**Action** : Appliquer la doctrine PROC (3 sources) :
1. Fiche technique décideurs
2. Template du niveau demandé
3. Golden Example CGSS 118 ULTRA  
**Références** : `niveaux.yaml`, `qg_matrix.yaml`, `templates/{niveau}_template.md`  
**Règle de non-régression** : Ne jamais supprimer une section du template.

### [5] GENERATE
**Action** : Produire le DOX Contract via le générateur.  
**Script** : `generate_contract.py --from-file data.json --niveau <n> --output contract.json --notion-format`  
**Entrée** : Données BDD enrichies.  
**Sortie** : Contrat DOX structuré (JSON + chemins modules).

### [6] LOCAL_QG
**Action** : Valider les Quality Gates G1–G21.  
**Script** : `qg_validator.py --file procedure.md --niveau <n> --json`  
**Entrée** : Fichier markdown de la procédure (ou notion-id).  
**Sortie** : Score QG structuré + rapport markdown.  
**Seuils** : Bronze → G7, Argent → G8, Or → G11, Platine → G14, Ultra → G18, Mythique → G20, Akuma → G21.

### [7] BULLET_PROOFING
**Action** : Vérifier la robustesse selon 4 angles.  
**Script** : `bullet_proof.py --file contract.json --output bullet_report.json`  
**Angles** :
- 🏗️ **Architectural** — Cohérence BDD-native
- 📜 **Transactionnel** — Traçabilité des modifications
- 🔗 **Systémique** — Compatible 10 BDD canoniques
- ⛔ **Anti-régression** — Pas de perte en upgrade

### [8] SYNC_NOTION
**Action** : Synchronisation bidirectionnelle.  
**Script** : `sync_notion.py --push contract.json --output result.json`  
**Modes** :
- **create** : Nouvelle page dans BDD1 Procédures
- **upgrade** : Mise à jour de la page existante (--update)
- **resync** : Pull depuis Notion (--pull)

### [9] REPORT
**Action** : Compiler le rapport final structuré.  
**Contenu** : Score QG, résultats bullet, statut sync, URL Notion, proposition niveau suivant.  
**Sortie** : `10_final_report.md` + stdout.

---

## 5. Flux de données complet

```
Demande utilisateur
       │
       ▼
┌─────────────────────────────────────────────┐
│  INTAKE → params.json                       │
├─────────────────────────────────────────────┤
│  ANTI_DUPLICATE → consult_bdd               │
├─────────────────────────────────────────────┤
│  CONSULT_BDD → consult_bdd → data.json      │
├─────────────────────────────────────────────┤
│  DESIGN → sélection template + doctrine     │
├─────────────────────────────────────────────┤
│  GENERATE → generate_contract → contract    │
├─────────────────────────────────────────────┤
│  LOCAL_QG → qg_validator → score QG         │
├─────────────────────────────────────────────┤
│  BULLET_PROOF → bullet_proof → rapport      │
├─────────────────────────────────────────────┤
│  SYNC_NOTION → sync_notion → URL Notion     │
├─────────────────────────────────────────────┤
│  REPORT → Rapport final                     │
└─────────────────────────────────────────────┘
       │
       ▼
   Procédure livrée ✓
```

---

## 6. Répertoire de travail pipeline

Chaque exécution crée un répertoire temporaire `/tmp/proc_<mode>_<uuid>/` avec :

```
01_intake_params.json       # Paramètres d'entrée
02_antiduplicate.json       # Résultat vérification doublons
03_bdd_canoniques_raw.json  # Données brutes BDD
03_procedure_data.json      # Données structurées (JSON)
04_design_note.json         # Note de conception/doctrine
05_contract.json            # DOX Contract généré
07_qg_results.json          # Résultats QG structurés
07_qg_report.md             # Rapport QG markdown
08_bullet_report.json       # Résultats bullet proofing
09_sync_result.json         # Résultat sync Notion
10_final_report.md          # Rapport final consolidé
```

---

## 7. Guide de dépannage

### Symptôme : Connexion Notion échoue
```bash
# Vérifier le token
python3 -c "from notion_shared import get_notion_token; t=get_notion_token(); print(f'OK: {t[:8]}...')"

# Vérifier la connexion
python3 consult_bdd.py --check
```

### Symptôme : Générateur de contrat échoue
```bash
# Vérifier les données d'entrée
python3 generate_contract.py --from-file data.json --check

# Tester un cas minimal
python3 generate_contract.py --interactive
```

### Symptôme : Quality Gates bloquent
```bash
# Voir la matrice complète
python3 qg_validator.py --validate-sections

# Valider un fichier précis
python3 qg_validator.py --file procedure.md --niveau or --report
```

### Symptôme : Sync Notion échoue
```bash
# Vérifier les IDs BDD
python3 consult_bdd.py --schema

# Pull test
python3 sync_notion.py --pull "CGSS 118" --output /tmp/test.json
```

---

## 8. Références Notion (IDs BDD)

| Base | Type | data_source_id |
|------|------|----------------|
| BDD1 Procédures RH | Main | `b6c395ef-19fc-42d4-95ef-2ca586872139` |
| BDD2 Contrats | Relation | `7155819e-29d8-4ba6-be2e-4aaa6b6fee38` |
| BDD3 Audits | Relation | `1a1dd97d-21e9-8199-986a-001aeb8be23d` |
| BDD4 Évaluateur public | Relation | `1a01d81e-4c39-8009-b15f-e5c467275875` |
| Spec AKUMA | Page | `2e11d81e-4c39-80f0-a9ff-d9eef9d2a2c8` |
| Spec PROC | Tâche GTD | `27e40d20-8c9c-4a70-90f8-beb14d91e296` |

Golden Example : **CGSS 118 ULTRA** (ID 497, BDD1 Procédures)

---

## 9. Sécurité et bonnes pratiques

- **Token Notion** : Variable d'environnement `NOTION_TOKEN` (ou fichier `/tmp/notion_token.txt`)
- **Ne jamais** exposer le token dans un fichier versionné
- **Dépendances** : Python 3 stdlib uniquement (pas de packages externes requis)
- **Timeouts** : Chaque script a un timeout de 30-120s dans l'orchestrateur
- **Tolérance aux pannes** : L'orchestrateur continue les étapes suivantes même après un échec d'étape (sauf INTAKE)
- **Idempotence** : `--force` permet de passer outre les avertissements doublons
