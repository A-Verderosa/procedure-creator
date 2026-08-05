# BDD Satellites Mythique — Architecture des pages liées

## Résumé

Les procédures MYTHIQUE sont liées à **5 BDD satellites** via des propriétés `relation` :
SBRX (risques), PMRI (mesures), GED (documents), FAQ (questions/réponses), Glossaire (termes/définitions).

⚠️ **Correction session 2026-08-02** : Le glossaire a sa propre BDD dédiée (GLOSSAIRE MAIN, pas un champ `rich_text`).

## Database IDs résolus (2026-08-02)

| BDD | database_id | Nom complet | Propriétés clés |
|---|---|---|---|
| PROCÉDURES MYTHIQUES | `0a1689d5-ec35-4422-95cb-188a1dd35113` | DOX BDD - PROCEDURES MYTHIQUES | 32 props |
| SBRX Risques | `8e0efb57-8ac1-4a5d-9a6e-8a59431f9603` | DOX BDD - SBRX MYTHIQUE | 40 props |
| PMRI Mesures | `6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9` | DOX BDD - PMRI MYTHIQUE | 22 props |
| GED Documents | `3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e` | DOX BDD - GED MAIN | 3 props |
| FAQ Métier | `3c44d2d1-ee87-44ed-b991-bab4d1e94442` | DOX BDD - FAQ METIER | 2 props |
| **Glossaire** | **`1481d81e-4c39-808a-b304-fd1857c29329`** | **DOX BDD - GLOSSAIRE MAIN** | **2 props (Nom + Définition)** |
| Snapshots Risques | `3f1733bb-da2d-48ae-8eaf-e5bd4cd25564` | DOX BDD - SNAPSHOTS RISQUES MYTHIQUES | — |
| Snapshots Mesures | `a654a947-e7fe-47d0-ba2a-3994014d5388` | DOX BDD - SNAPSHOTS MESURES MYTHIQUES | — |
| Snapshots Procédures | `a0be02f5-3128-46c4-8558-256f2e9b1cc0` | DOX BDD - SNAPSHOTS PROCÉDURES MYTHIQUES | — |

### Glossaire — BDD dédiée (corrigé)

Le glossaire a **sa propre BDD** : `DOX BDD - GLOSSAIRE MAIN` (ID `1481d81e-4c39-808a-b304-fd1857c29329`).
Propriétés : `Nom` (title) et `Définition` (rich_text).
→ Les termes sont créés comme pages individuelles avec dédoublonnage par nom exact (insensible à la casse).
→ Les pages créées sont liées à la procédure via la relation `Glossaire lié` (relation multi).

## Schémas de création (tels qu'implémentés dans `create_related_pages.py`)

### Glossaire — `1481d81e-4c39-808a-b304-fd1857c29329`

```python
page = {
    "parent": {"database_id": "1481d81e-..."},
    "properties": {
        "Nom":        {"title": [{"text": {"content": "terme"}}]},
        "Définition": {"rich_text": [{"text": {"content": "définition"}}]},
    }
}
```

Dédoublonnage : avant création, interroge la BDD sur `Nom` == terme (insensible à la casse). Si trouvé, réutilise l'ID existant.

### SBRX Risques — `8e0efb57-8ac1-4a5d-9a6e-8a59431f9603`

```python
page = {
    "parent": {"database_id": "8e0efb57-..."},
    "properties": {
        "Titre":          {"title": [{"text": {"content": "Nom du risque"}}]},
        "Code risque":    {"rich_text": [{"text": {"content": "R-01"}}]},
        "Probabilité":    {"number": 3},
        "Impact":         {"number": 4},
        "Procédure Mère": {"relation": [{"id": procedure_id}]},
    }
}
```

### PMRI Mesures — `6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9`

```python
page = {
    "parent": {"database_id": "6f39b3cc-..."},
    "properties": {
        "Titre":            {"title": [{"text": {"content": "Nom mesure"}}]},
        "Procédure Source": {"relation": [{"id": procedure_id}]},
        "Risque Traité":    {"relation": [{"id": risk_id}]},
    }
}
```

### GED MAIN — `3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e`

```python
page = {
    "parent": {"database_id": "3c36a4d6-..."},
    "properties": {
        "Code & Document": {"title": [{"text": {"content": "DOC-001 - Guide"}}]},
    }
}
```

### FAQ METIER — `3c44d2d1-ee87-44ed-b991-bab4d1e94442`

```python
page = {
    "parent": {"database_id": "3c44d2d1-..."},
    "properties": {
        "Question": {"title": [{"text": {"content": "Question?"}}]},
        "Réponse":  {"rich_text": [{"text": {"content": "Réponse."}}]},
    }
}
```

## Pipeline — étape CREATE_RELATED_PAGES [11]

Entre SYNC_NOTION [10] et REPORT [12] :

```
[10] SYNC_NOTION          — Crée la page procédure dans Notion
[11] CREATE_RELATED_PAGES — Crée risques, mesures, doc, FAQ, glossaire liés
[12] REPORT               — Rapport final
```

### Logique glossaire (BDD dédiée)

```python
def sync_glossary(procedure_id, terms):
    for terme, definition in terms:
        # 1. Vérifier doublon : query BDD sur Nom == terme (insensible casse)
        existing = query_glossary(terme)
        if existing:
            page_id = existing["id"]
        else:
            page = notion_create(glossary_db_id, {
                "Nom": terme,
                "Définition": definition,
            })
            page_id = page["id"]
        created_ids.append(page_id)
    # Lier la procédure aux termes créés/trouvés
    notion_update(procedure_id, {"Glossaire lié": created_ids})
```

### Logique risques SBRX

```python
def create_risks(procedure_id, risks):
    ids = []
    for r in risks:
        page = notion_create("8e0efb57-...", {
            "Titre": r["nom"],
            "Code risque": r.get("code"),
            "Probabilité": r.get("probabilite"),
            "Impact": r.get("impact"),
            "Procédure Mère": [procedure_id],
        })
        ids.append(page["id"])
    # Lier la procédure aux risques créés
    notion_update(procedure_id, {"Risques liés": ids})
    return ids
```

### Logique mesures PMRI (avec lien risque)

```python
def create_mesures(procedure_id, mesures, risk_ids):
    ids = []
    for m in mesures:
        mes_risk_ids = [risk_ids[i] for i in m.get("risk_indices", [])]
        page = notion_create("6f39b3cc-...", {
            "Titre": m["nom"],
            "Procédure Source": [procedure_id],
            "Risque Traité": mes_risk_ids,
        })
        ids.append(page["id"])
    notion_update(procedure_id, {"Mesures PMRI": ids})
    return ids
```
