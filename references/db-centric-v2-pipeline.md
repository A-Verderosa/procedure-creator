# DB-Centric V2 — Pipeline de publication Notion-Native

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Contrat JSON                         │
│  { "procedure": { "id": "...", "titre": "...", ... } │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  scripts/publish_procedure.py                        │
│                                                      │
│  1. 🔍 DOX       → find_dox_entry(pid)              │
│  2. 📄 MYTHIQUE  → find_or_create(pid) + properties  │
│  3. ⚠️ SBRX      → populate_sbrx(risks, page_id)    │
│  4. 📁 GED       → populate_ged(docs, page_id)       │
│  5. 🎨 Dashboard → append 7 blocks to page body      │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  Page Notion MYTHIQUE                                 │
│  ┌─ Propriétés (32) ──────────────────────────┐     │
│  │ Titre | Code | Statut | Service | Niveau    │     │
│  │ Objet | Champ | Consignes | Règles | ...   │     │
│  │ Relations: →DOX →SBRX →GED →PMRI →FAQ     │     │
│  ├─ Dashboard (corps) ─────────────────────────┤     │
│  │ 🎯 Callout récap (procédure N/N)            │     │
│  │ 🔄 Toggle phases (N étapes)                 │     │
│  │ ⚠️ Toggle risques (N risques liés)          │     │
│  │ 📁 Toggle documents (N docs liés)           │     │
│  │ 🗄️ Bases liées (callout 5 liens BD)        │     │
│  └─────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

## BDD canoniques (IDs vérifiés)

| BDD | database_id (parent) | data_source_id (query) | Propriété clé |
|-----|---------------------|----------------------|---------------|
| **DOX** | `3351d81e-4c39-827e-88a4-817c2739bbff` | idem | `Code` (title) |
| **MYTHIQUE** | `0a1689d5-ec35-4422-95cb-188a1dd35113` | idem | `Code procédure` (rich_text) |
| **SBRX** | `8e0efb57-8ac1-4a5d-9a6e-8a59431f9603` | idem | `Code risque` (rich_text) |
| **GED MAIN** | `3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e` | idem | `Code & Document` (title) |
| **PMRI** | `6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9` | idem | `Titre` (title) |
| **FAQ** | `3c44d2d1-ee87-44ed-b991-bab4d1e94442` | idem | `Question` (title) |
| **Glossaire** | `1481d81e-4c39-808a-b304-fd1857c29329` | idem | `Terme` (title) |

## Mapping contrat → propriétés MYTHIQUE

```python
TITLE_PROP = "Titre"           # title
ID_PROP = "Code procédure"     # rich_text
SERVICE_PROP = "Service"       # select
STATUT_PROP = "Statut"         # status (requires emoji prefix)
NIVEAU_PROP = "Niveau DOX"     # select
DOX_PROP = "DOX"               # relation
SBRX_PROP = "Risques"          # relation
GED_PROP = "Documents GED"     # relation
PMRI_PROP = "Mesures PMRI"     # relation
FAQ_PROP = "FAQ"               # relation
GLOSSAIRE_PROP = "Glossaire"   # relation

# Rich text properties (content sections)
RICH_TEXT_PROPS = [
    "Objet", "Champ d'application", "Définitions & glossaire",
    "Documents de référence", "Documents support", 
    "Consignes opérationnelles", "Règles de gestion",
    "Analyse des risques", "Acteurs responsables"
]
```

### Valeurs Status valides

```python
{"status": {"name": "🔲 À faire"}}
{"status": {"name": "🚧 En cours"}}
{"status": {"name": "✅ Terminé"}}
```

**⚠️ Les émojis font partie du nom.** C'est le nom exact de l'option dans la BDD Notion — les omettre = 400 Bad Request.

### Valeurs Niveau DOX valides

```python
{"select": {"name": "🔮 Mythique"}}
{"select": {"name": "💎 Ultra"}}
{"select": {"name": "💎 Platine"}}
{"select": {"name": "🥇 Or"}}
{"select": {"name": "🥈 Argent"}}
{"select": {"name": "🥉 Bronze"}}
```

## Dashboard — 7 blocks Notion

Le dashboard est ajouté dans le corps de la page via `PATCH /v1/blocks/{page_id}/children`. Les 7 blocks sont :

### 1. Callout récapitulatif
```json
{
  "object": "block", "type": "callout",
  "callout": {
    "icon": {"type": "emoji", "emoji": "🎯"},
    "color": "blue_background",
    "rich_text": [{"type": "text", "text": {"content": "Procédure N/N — N étapes, N risques, N documents"}}]
  }
}
```

### 2. Toggle phases
```json
{
  "object": "block", "type": "toggle",
  "toggle": {
    "rich_text": [{"type": "text", "text": {"content": "🔄 Phases", "bold": true}}]
  },
  "children": [
    {"object": "block", "type": "paragraph",
     "paragraph": {"rich_text": [{"type": "text", "text": {"content": "❶ Étape 1 — Acteur (délai)"}}]}},
    {"object": "block", "type": "paragraph",
     "paragraph": {"rich_text": [{"type": "text", "text": {"content": "❷ Étape 2 — Acteur (délai)"}}]}}
  ]
}
```

### 3. Toggle risques
```json
{
  "object": "block", "type": "toggle",
  "toggle": {
    "rich_text": [{"type": "text", "text": {"content": "⚠️ Risques SBRX", "bold": true}}]
  },
  "children": [
    {"object": "block", "type": "paragraph",
     "paragraph": {"rich_text": [{"type": "text", "text": {"content": "R1 — Description"}}]}}
  ]
}
```

### 4. Toggle documents
```json
{
  "object": "block", "type": "toggle",
  "toggle": {
    "rich_text": [{"type": "text", "text": {"content": "📁 Documents GED", "bold": true}}]
  },
  "children": [
    {"object": "block", "type": "paragraph",
     "paragraph": {"rich_text": [{"type": "text", "text": {"content": "DOC-01 — Titre"}}]}}
  ]
}
```

### 5–7. Callout bases liées (3 lignes)
```json
{
  "object": "block", "type": "callout",
  "callout": {
    "icon": {"type": "emoji", "emoji": "🗄️"},
    "color": "gray_background",
    "rich_text": [
      {"type": "text", "text": {"content": "🔗 "}},
      {"type": "text", "text": {"content": "SBRX Risques", "link": {"url": "https://notion.so/..."}}}
    ]
  }
}
```

## Parsing du contrat

### Risques (format `"R1 : Desc ; R2 : Desc"`)
```python
for item in str(risks_raw).split(";"):
    item = item.strip()
    if not item:
        continue
    match = re.match(r'^([A-Z]+\d*)\s*:\s*(.+)$', item)
    if match:
        code = match.group(1).strip()
        desc = match.group(2).strip()
```

### Documents (format `"CODE - Titre; CODE2 - Titre2"`)
```python
for item in str(docs_raw).split(";"):
    item = item.strip()
    if not item:
        continue
    match = re.match(r'^([\w/-]+)\s*[-–—]\s*(.+)$', item)
    if match:
        code = match.group(1).strip()
        title = match.group(2).strip()
```

## Propriétés SBRX (schéma réel)

| Propriété | Type | Valeur typique |
|-----------|------|---------------|
| `Titre` | title | `R1 — Retard de traitement` |
| `Code risque` | rich_text | `R1` |
| `Description` | rich_text | _optionnel_ |
| `Vraisemblance` | select | `2-Faible`, `3-Moyen`, `4-Élevé` |
| `Gravité` | select | `2-Faible`, `3-Moyen`, `4-Élevé` |
| `Criticité` | select | `Vert`, `Orange`, `Rouge` |
| `Proposer par` | rich_text | _nom du proposeur_ |
| `Statut` | select | `Identifié`, `En traitement`, `Traité` |

**⚠️ Titre est la title property**, pas `Code risque`. Le titre doit être unique ou le second item échoue silencieusement.

## Propriétés GED MAIN (schéma réel)

| Propriété | Type | Valeur typique |
|-----------|------|---------------|
| `Code & Document` | title | `CEV-F01 - Formulaire de saisine` |
| `Titre` | rich_text | `Formulaire de saisine` |
| `Type` | select | `Rapport`, `Formulaire`, `Note`, `Modèle` |
| `Source GED` | select | `Interne`, `Externe` |
| `Nature` | select | `Fichier`, `Lien` |
| `Date création` | date | `2026-01-15` |
| `Fichier lié` | files | _fichier uploadé_ |

**⚠️ La title property est `Code & Document`**, format `"CODE - Titre complet"`. Pas de simple `"Titre"`.

## Gestion des erreurs

### 400 Bad Request — Statut
```json
{"status": 400, "message": "body failed validation: body.properties.Statut.status.name should be one of ..."}
```
→ Le nom exact du status (avec émoji) ne correspond pas aux options de la BDD. Inspecter le schéma via GET `/v1/data_sources/{id}`.

### 409 Conflict — Duplicate title
```json
{"status": 409, "message": "Could not create page because the property \"Titre\" already exists"}
```
→ Une page SBRX avec ce titre existe déjà. Soit enrichir l'existante, soit générer un titre unique (append un suffixe).

### DELETE retourne 204
Notion's `DELETE /v1/blocks/{id}` retourne HTTP **204 No Content** (pas de body JSON). Le handler Python doit vérifier `resp.status == 204`, pas parser le body.

### Query retourne vide silencieusement
```json
{"results": [], "has_more": false}
```
→ Le filtre ne correspond à aucune entrée. Causes probables :
- Mauvaise propriété (ex. `"Code"` au lieu de `"Code procédure"`)
- Mauvais type de filtre (`"title"` sur un champ `rich_text`)
- Mauvais ID de database

## Workflow de production

```bash
# 1. Créer le contrat
cp flux_evaluateur/procedures_prioritaires/CEV-P02_data.json \
   flux_evaluateur/procedures_prioritaires/NOUVEAU_CODE_data.json

# 2. Éditer : id, titre, objet, risques, documents, phases

# 3. Vérifier JSON
python3 -m json.tool flux_evaluateur/procedures_prioritaires/NOUVEAU_CODE_data.json

# 4. Publier (création page + propriétés + dashboard)
python3 scripts/publish_procedure.py \
   flux_evaluateur/procedures_prioritaires/NOUVEAU_CODE_data.json \
   --publish

# 5. Vérifier dans Notion : ouvrir la page → propriétés + dashboard
```

**Pour les procédures en mise à jour** (page déjà existante) : le pipeline met à jour les 32 propriétés et ajoute le dashboard en fin de corps. Les anciens blocs ne sont pas supprimés automatiquement — un `--clean` optionnel peut être ajouté.
