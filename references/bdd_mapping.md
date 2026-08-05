# Dual Database Architecture (Mythique vs Canonique)

## Why Two Databases?

The pipeline supports two Notion databases for procedures:

| Database | ID | Usage |
|----------|-----|-------|
| **DOX BDD - PROCÉDURES** (canonique) | `7155819e-29d8-4ba6-be2e-4aaa6b6fee38` | Legacy — original procedure database |
| **DOX BDD - PROCÉDURES MYTHIQUES** (mythique) | `0a1689d5-ec35-4422-95cb-188a1dd35113` | New hub — target for all create operations |

The pipeline create mode pushes to **mythique** by default via `--database mythique`.

## Mapping Files

Both maps are defined in `notion_shared.py`:

### MYTHIQUE_PROP_MAP (complet, vérifié 2026-08-02)

```python
MYTHIQUE_PROP_MAP = {
    "procedure_id":       {"name": "ID", "type": "title"},
    "titre":              {"name": "Titre", "type": "rich_text"},
    "niveau":             {"name": "Niveau", "type": "select"},
    "statut":             {"name": "Statut", "type": "status"},   # ⚠️ type "status" PAS "select" !
    "type_rh":            {"name": "Type RH", "type": "select"},
    "perimetre":          {"name": "Périmètre", "type": "select"},
    "service":            {"name": "Service", "type": "select"},
    "valid":              {"name": "Valid", "type": "select"},
    "version":            {"name": "Version", "type": "number"},
    "date_creation":      {"name": "Créé le", "type": "date"},
    "date_maj":           {"name": "Dernière mise à jour", "type": "date"},
    "redacteur":          {"name": "Rédacteur", "type": "relation"},
    "validateur":         {"name": "Validateur", "type": "relation"},
    "date_actualisation": {"name": "Dernière revue procédure", "type": "date"},
    "periodicite_revue":  {"name": "Périodicité revue", "type": "select"},
    "acteurs":            {"name": "Acteurs", "type": "rich_text"},
    "description":        {"name": "Description", "type": "rich_text"},
}
```

## ⚠️ Statut type "status" — piège Notion API

Dans la BDD MYTHIQUE, la propriété **Statut** est de type `"status"` (pas `"select"`). Les différences :

| Aspect | `select` | `status` |
|--------|----------|----------|
| Type API | `"type": "select"` | `"type": "status"` |
| Payload create | `{"select": {"name": "À faire"}}` | `{"status": {"name": "🔲 À faire"}}` |
| Valeurs avec émojis | Optionnel | **Obligatoire** — les émojis sont encodés dans les options de la BDD |
| Options MYTHIQUE | N/A | `🔲 À faire`, `🚧 En cours`, `✅ Terminé` |

**Mapping automatique** : `sync_notion.py` traduit automatiquement les statuts simples en valeurs avec emoji :

```python
MYTHIQUE_STATUS_MAP = {
    "À faire": "🔲 À faire",
    "En cours": "🚧 En cours", 
    "Terminé": "✅ Terminé",
}
```

Inclure dans `build_properties()` :

```python
if database == "mythique" and prop_type == "status":
    raw_name = value  # ex: "À faire"
    mapped = MYTHIQUE_STATUS_MAP.get(raw_name, raw_name)
    payload[key] = {"status": {"name": mapped}}
elif prop_type == "select":
    payload[key] = {"select": {"name": value}}
```

### MYTHIQUE_REL_MAP

```python
MYTHIQUE_REL_MAP = {
    "organigramme":    {"name": "Organigramme",    "type": "relation"},
    "annuaire":        {"name": "Annuaire",        "type": "relation"},
    "risques":         {"name": "Risques liés",    "type": "relation"},
    "documents":       {"name": "Document GED",    "type": "relation"},
    "faq":             {"name": "FAQ liée",        "type": "relation"},
    "mesures_pmri":    {"name": "Mesures PMRI",    "type": "relation"},
    "glossaire":       {"name": "Glossaire",       "type": "relation"},
    "snapshots":       {"name": "Snapshots procédures", "type": "relation"},
}
```

## How switching works (et piège build_properties)

1. `proc_orchestrator.py` builds args with `"--database", "mythique"` when mode is `create`
2. `sync_notion.py` reads `args.database` and selects the right ID + maps at script level:

```python
if args.database == "mythique":
    DATABASE_ID = MYTHIQUE_DATABASE_ID
    PROP_MAP = MYTHIQUE_PROP_MAP
    REL_MAP = MYTHIQUE_REL_MAP
else:
    DATABASE_ID = CANONIQUE_DATABASE_ID
    PROP_MAP = CANONIQUE_PROP_MAP
    REL_MAP = CANONIQUE_REL_MAP
```

3. Property names are resolved via the map (the MYTHIQUE schema uses different column names than the canonique one)

**⚠️ Piège `build_properties()` (fixé 2026-08-02) :** La fonction `build_properties(data, database='...')` a son propre paramètre `prop_map=None`. Avant le fix, `database='mythique'` ne sélectionnait PAS automatiquement `MYTHIQUE_PROP_MAP` — il ne servait que pour le type `status` du Statut. Les propriétés MYTHIQUE-only (`Rédacteur`, `Validateur`, `Périodicité revue`, `Dernière revue procédure`) étaient silencieusement ignorées car absentes de `PROP_MAP` canonique.

**Fix :** Quand `prop_map=None` et `database='mythique'`, `build_properties()` charge maintenant `MYTHIQUE_PROP_MAP` automatiquement :

## When to add a property

When adding a new property to a procedure:

1. Check the target database schema via `GET /v1/databases/{id}` 
2. Add the entry to `MYTHIQUE_PROP_MAP` (or `PROP_MAP` for canonique)
3. If it's a relation, also add it to `MYTHIQUE_REL_MAP`
4. Update the `build_properties()` function in `sync_notion.py` to populate the new field

## Satellite databases (common to both hubs)

| Role | Name | ID |
|------|------|----|
| Risques | DOX BDD - SBRX MYTHIQUE | `8e0efb57-8ac1-4a5d-9a6e-8a59431f9603` |
| Mesures PMRI | DOX BDD - PMRI MYTHIQUE | `6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9` |
| GED | DOX BDD - GED MAIN | `3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e` |
| FAQ | DOX BDD - FAQ METIER | `3c44d2d1-ee87-44ed-b991-bab4d1e94442` |
| Glossaire | DOX BDD - GLOSSAIRE MAIN | `1481d81e-4c39-808a-b304-fd1857c29329` |
| Annuaire | Annuaire Global | `12f1d81e-4c39-8122-bffe-d61e547e9ea9` |

## Known pitfalls

- **Never use `GET /v1/databases/{id}` alone to verify access** — it returns metadata even when the database isn't shared with your integration. Always test with `POST /v1/databases/{id}/query` or a page creation call.
- **Property names must match EXACTLY** — Notion property names are case-sensitive. If the schema says `"Périmètre"` but you use `"Perimetre"`, the request silently drops the value (HTTP 200 but field is empty).
- **Curly apostrophe (U+2019)** — if a property name uses a curly apostrophe like `Champ d'application`, the map key must use U+2019 too. Straight apostrophe (U+0027) won't match.
- **data_source_id ≠ database_id** — `data_source_id` is the integration-level handle; `database_id` is the actual DB handle used in `/v1/databases/{id}/query`. Never use data_source_id for page creation.
