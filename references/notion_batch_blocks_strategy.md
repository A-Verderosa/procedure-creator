# Stratégie Batch Blocks Notion (Option B)

## Problème

`POST /v1/pages` avec `body.children` refuse > **100 blocks** :
```
body.children.length should be ≤ 100
```

Une procédure Mythique Évaluateur fait ~295 blocks → HTTP 400.

## Solution : Option B (create empty + batch append)

### Principe

1. Créer la page avec **propriétés seules** (pas de `children` dans le POST)
2. Ajouter le contenu par lots de 50 via `PATCH /v1/blocks/{id}/children`

### Implémentation

Fonction helper **partagée** dans `sync_notion.py` :

```python
def _append_blocks_batch(page_id, blocks, chunk_size=50):
    """Append blocks to a Notion page in batches of chunk_size.
    Shared between create_procedure_page and _update_page_blocks.
    Returns True if all batches succeeded, False on any failure."""
    for i in range(0, len(blocks), chunk_size):
        chunk = blocks[i:i + chunk_size]
        try:
            notion_request("PATCH",
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                {"children": chunk})
        except RuntimeError:
            return False
    return True
```

### Appels

**create_procedure_page()** :
```python
# Créer la page VIDE (propriétés seules)
resp = notion_request("POST",
    "https://api.notion.com/v1/pages",
    {"parent": {"database_id": db_id}, "properties": properties})
page_id = resp["id"]
# Ajouter les blocks par lots
_append_blocks_batch(page_id, body_blocks, chunk_size=50)
```

**_update_page_blocks()** :
```python
# Supprimer les anciens blocks
for block_id in old_block_ids:
    notion_request("DELETE", f"https://api.notion.com/v1/blocks/{block_id}")
# Ajouter les nouveaux blocks par lots
_append_blocks_batch(page_id, new_blocks, chunk_size=50)
```

### Pourquoi chunk_size=50 ?

- La limite API Notion pour `PATCH /v1/blocks/{id}/children` est documentée à 50 (parfois 100 selon les endpoints)
- 50 donne une marge de sécurité confortable
- Une procédure de ~295 blocks → 6 appels API (295/50 = 5.9)

### Vérification

La commande pipeline complète :
```bash
bash scripts/verrouiller.sh contrat_data.json --publish
```

Produit V5 ✅ avec page_id retourné. Testé sur M1-P3-01 (~295 blocks, 6 appels batch).

### Migration de l'ancien code

- **Avant :** `_update_page_blocks()` avait son propre batching inline avec `chunk_size=100`
- **Après :** Unifié via `_append_blocks_batch(chunk_size=50)` — les deux chemins (create et update) partagent la même logique
- La **suppression des anciens blocks** (DELETE) reste séparée et non batchée (un appel par block à supprimer)
