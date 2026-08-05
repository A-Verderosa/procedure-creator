# Notion API — Particularités des endpoints

## Endpoints disponibles pour interroger les bases

### 1. Database endpoint
```
POST /v1/databases/{database_id}/query
```
- **✅ Accepte les requêtes sans filtre** (payload: `{"page_size": 100}`)
- Retourne toutes les pages de la base
- Utiliser pour les listes complètes, parcours, diagnostics
- `database_id` = ID natif Notion (UUID avec tirets)

### 2. Data source endpoint
```
POST /v1/data_sources/{data_source_id}/query
```
- **❌ REFUSE les requêtes sans filtre** → HTTP 400 `invalid_request_url`
- **❌ REFUSE les filtres sur propriété** → HTTP 400 si `filter` est présent et non supporté
- Comportement constaté : ne fonctionne qu'avec des filtres très spécifiques (type `data_source`) ou pas du tout pour les queries libres
- Certains data_sources Notion (partagés via intégration) ne supportent que `page_size` sans `filter`

### Règle empirique
| Usage | Endpoint | Payload |
|-------|----------|---------|
| Lister toutes les procédures | `/v1/databases/{id}/query` | `{"page_size": 100}` |
| Filtrer par titre/propriété | `/v1/databases/{id}/query` | `{"filter": {...}}` |
| Requête via data_source | `/v1/data_sources/{id}/query` | Uniquement `page_size` (si supporté) |

## Endpoints pour les blocs enfants

### 1. Lister les blocs enfants
```
GET /v1/blocks/{block_id}/children?page_size=100
GET /v1/blocks/{block_id}/children?page_size=100&start_cursor={cursor}
```
- Retourne les blocs enfants d'une page (contenu du body, pas les propriétés)
- **Pagination** : max 100 par page. Champ `has_more` + `next_cursor` pour paginer
- Résultat : `results[]` avec `id`, `type`, `has_children`, `type: {...}`
- ⚠️ Pas de paramètre `token` — la fonction `notion_request("GET", url)` de `notion_shared.py` lit le token automatiquement depuis les variables d'env

### 2. Supprimer un bloc
```
DELETE /v1/blocks/{block_id}
```
- Supprime définitivement un bloc enfant
- **Rate limiting** : imposer `time.sleep(0.35)` entre chaque DELETE (Notion tolère ~3/s)
- Exemple pattern :
```python
def delete_children(block_ids):
    for bid in block_ids:
        notion_request("DELETE", f"https://api.notion.com/v1/blocks/{bid}")
        time.sleep(0.35)
```

### 3. Pas de "replace children"
- **Il n'existe pas** d'endpoint pour remplacer atomiquement tous les enfants d'une page
- La stratégie est donc : **DELETE tout → re-APPEND** en une passe
- Pattern implémenté dans `publish_procedure.py` (étape 5) :
```python
existing_children = fetch_children(page_id)   # GET paginé
delete_children(child_ids)                     # DELETE séquentiel
time.sleep(BATCH_DELAY)
notion_patch(f".../blocks/{page_id}/children", {"children": new_blocks}, token)  # APPEND
```

### Résolution des IDs
- `data_source_id` = ID du wrapper (trouvable dans la page Notion → ... → Connect to → nom de l'intégration)
- `database_id` = ID natif de la base (trouvable dans l'URL du navigateur ou extrait du parent d'une page)
- Les deux peuvent être différents. Toujours utiliser `database_id` pour les POST/PATCH pages.

## Appels API utiles dans le pipeline

| Fonction | Endpoint | Usage |
|----------|----------|-------|
| `fetch_children(page_id)` | `GET /v1/blocks/{id}/children` paginé | Récupérer les blocs dashboard existants |
| `delete_children(block_ids)` | `DELETE /v1/blocks/{id}` | Supprimer les anciens blocs avant rebuild |
| `notion_patch(url, payload, token)` | `PATCH …/children` avec body `{"children": […]}` | Ajouter les nouveaux blocs dashboard |
