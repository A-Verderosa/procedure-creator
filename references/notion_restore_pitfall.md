# Piège : Base ou page Notion restaurée → Intégration perdue

## Symptômes

### Cas 1 : Base inaccessible (erreur 400)

L'API Notion retourne une erreur 400 pour une base qui fonctionnait avant :

```json
{
  "object": "error",
  "status": 400,
  "code": "validation_error",
  "message": "Database with ID ... does not contain any data sources accessible by this API bot."
}
```

### Cas 2 : Page invisible (erreur 404)

Une page apparaît dans l'interface Notion (via un lien URL avec paramètre `t=...`) mais l'API retourne 404 :

```json
{
  "object": "error",
  "status": 404,
  "code": "object_not_found",
  "message": "Could not find page with ID: ... Make sure the relevant pages and databases are shared with your integration."
}
```

## Cause commune

Quand l'utilisateur restaure manuellement une page ou base Notion (depuis la corbeille ou une version antérieure), **l'intégration API n'est pas automatiquement reconnectée**. Même si la base avait l'intégration avant la suppression, après restauration les connexions sont perdues.

L'ID de la base reste le même — le code n'a pas besoin d'être modifié.

## Diagnostic rapide

### Vérifier la base

```bash
curl -s -X GET "https://api.notion.com/v1/databases/<DATABASE_ID>" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28" | python3 -m json.tool
```

- ✅ **200** + propriétés → la base est accessible, l'intégration est connectée
- ❌ **400** + `"does not contain any data sources"` → l'intégration n'a pas accès

### Vérifier une page spécifique (paramètre `t=` dans l'URL)

```bash
curl -s -X GET "https://api.notion.com/v1/pages/<PAGE_ID>" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28" | python3 -m json.tool
```

- ✅ **200** → la page existe et est accessible
- ❌ **404** → soit la page n'existe pas, soit sa base parent n'est pas partagée avec l'intégration

### Investigation du paramètre `t=` dans les URLs Notion

Format d'URL Notion :
```
https://app.notion.com/p/<workspace>/<base_id>?v=<view_id>&t=<page_token>
```

Le paramètre `t` est un **page token** — l'ID d'une page spécifique affichée dans une vue de base. Il peut pointer vers :
- Une page dans la base courante
- Une page liée (relation) depuis une autre base

**Quand l'API retourne 404 sur le `t`**, vérifier :
1. Dans quelle base vit cette page (le `base_id` du path)
2. Si l'intégration a accès à cette base (test ci-dessus)
3. Si la page elle-même a été supprimée (vérifier via les pages liées dans les BDD satellites : SBRX, GED, PMRI, FAQ)

### Procédure complète de diagnostic

Quand l'utilisateur signale qu'une page restaurée n'est pas trouvée :

1. **Extraire les IDs** de l'URL partagée : `base_id` (path), `t` param
2. **Vérifier la base** : si erreur 400 → intégration manquante
3. **Vérifier la page `t`** : si erreur 404 → même cause probable
4. **Scanner les BDD satellites** connues (SBRX, GED MAIN, PMRI, FAQ) pour confirmer l'état des pages liées
5. **Consulter la base originale** (ex: MYTHIQUE) qui a toujours les pages fonctionnelles

## Correction

1. Ouvrir la base dans Notion
2. Cliquer sur **⋯** (menu « ... » en haut à droite)
3. Aller dans **Connect to** (ou **Add connections** selon la locale)
4. Chercher et sélectionner l'intégration (ex: `Hostinger n8n`, `aveconsultings`, ou le nom configuré)
5. La base et toutes ses pages sont maintenant accessibles par l'API

**Aucune modification de code ni d'ID n'est nécessaire.**

## Prévention

- **Après toute restauration** de base depuis la corbeille, reconnecter l'intégration immédiatement
- **Vérifier après une restauration** : lancer `python3 scripts/check_sync.py` (ou équivalent) pour valider l'accès API
- **Garder une base MYTHIQUE de référence** toujours connectée à l'intégration, même si l'utilisateur restaure une copie ailleurs

## Exemple réel (session M1-P3-01)

L'utilisateur a restauré une page depuis la corbeille. L'URL partagée :
```
https://app.notion.com/p/aveconsultings/4779a142-93ed-4fff-9765-20060862aa09?v=...&t=3b11d81e-4c39-80c9-bc15-00a9b2d4efe4
```

- Base `4779a142...` → 400 (intégration absente)
- Page `3b11d81e-4c39-80c9...` → 404 (même cause)
- Original MYTHIQUE `0a1689d5...` → 200 ✅ (toujours fonctionnel)
- GED MAIN `3c36a4d6...` → 200 ✅ avec 4 documents liés

**Conclusion** : la page restaurée vit dans une base non partagée. Solution simple : re-sharer l'intégration.
