# `sections_or` — Propriété multi_select dans MYTHIQUE_PROP_MAP

## Contexte

La propriété **Sections OR** dans la BDD MYTHIQUE (champ `sections_or`) est de type **`multi_select`** — elle liste les domaines/secteurs RH couverts par la procédure (ex: SIRH, Paie, Rémunération, Carrière, etc.).

## Format data JSON

```json
{
  "procedure": {
    "sections_or": [
      "SIRH",
      "Paie",
      "Rémunération",
      "Carrière",
      "Formation",
      "Temps de travail",
      "Santé",
      "Social",
      "Masse salariale",
      "Organisation",
      "Immobilier",
      "Marchés",
      "Commandes",
      "Finances",
      "Communication"
    ]
  }
}
```

## Format payload Notion

```python
properties[prop_map["sections_or"]["name"]] = {
    "multi_select": [{"name": s} for s in sections_or_list]
}
```

Chaque élément est un objet `{"name": "..."}` — pas une liste de strings brutes.

## Handler dans `build_properties()`

```python
# Dans sync_notion.py, build_properties()
if prop_map.get("sections_or"):
    sections_or = contract_data.get("sections_or", []) or procedure_data.get("sections_or", [])
    if sections_or and isinstance(sections_or, list):
        properties[prop_map["sections_or"]["name"]] = {
            "multi_select": [{"name": s} for s in sections_or]
        }
```

## Piège

- `sections_or` n'existe que dans `MYTHIQUE_PROP_MAP`, pas dans `PROP_MAP` canonique. Si `build_properties()` utilise PROP_MAP (ancienne BDD), la clé `sections_or` lève `KeyError`.
- Le data JSON peut stocker `sections_or` sous `procedure_data["procedure"]["sections_or"]` ou directement dans `contract_data["sections_or"]` selon l'étape du pipeline. Vérifier les deux.
- La liste complète des 15 sections est utilisée pour les procédures généralistes. Les procédures spécialisées n'en ont que quelques-unes.
