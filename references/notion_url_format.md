# URL Notion — Format `app.notion.com`

## Constat (session 2026-08-03)

Depuis mi-2026, l'API Notion renvoie des URLs au format :

```
https://app.notion.com/p/{page_id_sans_tirets}/{slug}-{page_id_avec_tirets}
```

Au lieu de l'ancien format :

```
https://notion.so/{page_id_avec_tirets}
```

## Impact

- L'ancien code `f"https://notion.so/{page_id}"` ne fonctionne plus (timeout ou redirect)
- Le nouveau format utilise `app.notion.com` (pas `app.notion.so` — le TLD reste `.com`)
- Le chemin inclut `/p/` puis le `page_id` sans tirets, puis un slug + le `page_id` complet

## Fix dans `sync_notion.py`

```python
# AVANT (obsolète) :
url = f"https://notion.so/{page_id}"
# Problème : domaine notion.so renvoie une 404

# APRÈS (fix) :
url = response.get("url", f"https://app.notion.com/{page_id}")
# Solution : utiliser l'URL retournée par l'API Notion dans la réponse POST /v1/pages
```

La valeur `response.get("url")` renvoie l'URL complète et exacte. Le fallback `f"https://app.notion.com/{page_id}"` est une sécurité mais ne devrait jamais être atteint.

## Vérification

```bash
# Tester qu'une page créée retourne une URL valide
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"database_id": "MYTHIQUE_DATABASE_ID"},
    "properties": {"ID": {"title": [{"text": {"content": "TEST-URL"}}]}}
  }' | python3 -c "import sys,json; print(json.load(sys.stdin).get('url','NO_URL'))"
# Doit commencer par https://app.notion.com/p/
```

## Liens

- Voir `sync_notion.py` ligne ~260 : `_update_page_blocks()` et `_cmd_create()`
- Si le format change à nouveau, utiliser `response.get("url")` qui est toujours la valeur canonique retournée par l'API
