# DOX BDD Canoniques — Workspace PACKAGE HERMES

## Contexte
Le workspace "PACKAGE HERMES" (page container ID: 3b01d81e-4c39-8071-b8e4-d59ef51f5720) contient les BDD canoniques DOX pour les procédures MYTHIQUE.

⚠️ Ce workspace est DIFFÉRENT des IDs listés dans la section `bdd_canoniques` du SKILL.md principal (qui référencent un ancien workspace). Utiliser les IDs ci-dessous.

## BDD identifiées

| Base | data_source_id | database_id | État |
|------|---------------|-------------|------|
| **DOX BDD - PROCÉDURES MYTHIQUES** | `0a1689d5-ec35-4422-95cb-188a1dd35113` | À extraire d'un résultat de query | ✅ 32 props, 3 lignes (MYTH-SIRH-PROC-001/002/003) |
| **DOX BDD - SBRX MYTHIQUE** | `db_id de la BDD SBRX` | — | ✅ 40 props |
| **DOX BDD - PMRI MYTHIQUE** | `db_id de la BDD PMRI` | — | ✅ 22 props |

### Notes sur les IDs
- `data_source_id` = utilisé pour les requêtes (`POST /v1/data_sources/{id}/query`)
- `database_id` = utilisé pour la création de pages (`parent: {"database_id": "..."}`)
- Les deux IDs sont **différents**. Pour obtenir le `database_id` : faire une requête sur le data_source, prendre le premier résultat, et lire `result["parent"]["database_id"]`.

## Propriétés de DOX BDD - PROCÉDURES MYTHIQUES (32 props)

```
Niveau DOX (select), Statut (status), Service (select), Animateur (select),
Priorité DOX (select), Niveau QG (number), Scorecard DOX (number), Trophée (select),
Type de processus (select), Périodicité (select), Objet (rich_text), 
Champ d'application (rich_text), Acteurs responsables (rich_text), 
Définitions glossaire (rich_text), Documents de référence (rich_text), 
Règles de gestion (rich_text), Consignes opérationnelles (rich_text), 
Analyse des risques (rich_text), Documents support (rich_text),
Code procédure (rich_text), Version (rich_text), Date création (date),
Dernière modification (date), Prochaine revue (date), 
Sections OR (multi_select), Actions liées (relation), 
SBRX liés (relation), Documents GED (relation), 
Organigramme lié (relation), Pilote (people),
URL Notion (url), Tags (multi_select)
```

### Valeurs disponibles du select "Service"
ARCHIVES, LOGISTIQUE, SERVICE GESTION PRÉVISIONNELLE DES EMPLOIS, SERVICE RÉMUNÉRATION, SIRH, SERVICE CARRIERES, SERVICE SANTÉ ET HANDICAP, SERVICE ACCOMPAGNEMENT AU CHANGEMENT, SERVICE PRÉVENTION ET CONDITIONS DE TRAVAIL, PILOTAGE, SERVICE RETRAITES, SERVICE FORMATION, COMMUNICATION, SERVICE ACTIONS SOCIALES, SERVICE VEILLE, SERVICE GESTION DES CONTRATS AIDÉS, SERVICE RELATIONS SOCIALES, SERVICE RECRUTEMENT ET MOBILITÉ

### Valeurs du select "Niveau DOX"
🥉 Bronze, 🥈 Argent, 🥇 Or, 💎 Platine, 💎 Ultra, 🔮 Mythique, 👹 Akuma

### Sections OR (multi_select) — valeurs possibles
Les sections sont nommées de §0 à §26 (ex: §1 Objet, §2 Champ d'application, §3 Définitions...)

## Procédures existantes (référence)
- **MYTH-SIRH-PROC-001** — Kelio gestion du temps (22 sections + §23 avec 9 briques M1→M9 + Scorecard)
- **MYTH-SIRH-PROC-002** — Gestion des entretiens de carrière
- **MYTH-SIRH-PROC-003** — Procédure d'optimisation de la masse salariale

## Workflow de création d'une procédure dans cette BDD
1. **Créer la page** avec les propriétés seulement (POST /v1/pages avec parent.database_id)
2. **Ajouter les blocs de contenu** par lots de 50 (PATCH /v1/blocks/{page_id}/children) via `scripts/notion_batch_blocks.py`
3. **Vérifier** en lisant la page via l'API ou Notion UI
4. **Ajouter une relation** aux documents GED, SBRX, etc. si applicable

> **Note :** Les procédures Évaluateur public (ex: CEV-P02) peuvent être créées ici sous le service PILOTAGE si "Évaluateur public" n'est pas encore une option du select.
