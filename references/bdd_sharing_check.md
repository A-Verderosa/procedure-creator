# Vérification du partage BDD avec l'intégration Notion

## Contexte

Les BDD Notion sont accessibles via deux endpoints différents, avec des vérifications de permissions différentes :

| Endpoint | Comportement | Vérifie les droits ? |
|---|---|---|
| `GET /v1/databases/{id}` | Retourne les métadonnées (nom, propriétés) | ❌ OUI mais PAS les droits d'écriture |
| `POST /v1/databases/{id}/query` | Exécute une requête sur la BDD | ✅ Oui |
| `POST /v1/data_sources/{id}/query` | Exécute une requête (ancien format) | ✅ Oui, avec message clair si BDD non partagée |

## Statut des BDD MYTHIQUE

**Testé et confirmé le 2026-08-02** : toutes les BDD MYTHIQUES sont partagées avec l'intégration « Hostinger n8n » et accessibles en écriture. Le test réel de `create_related_pages.py` a créé 22 pages (5 SBRX + 5 PMRI + 5 GED + 7 FAQ + 3 Glossaire) avec relations établies sur la page procédure — **succès 100%** ✅.

| BDD | database_id | Statut |
|---|---|---|
| DOX BDD - PROCÉDURES MYTHIQUES | `0a1689d5-ec35-4422-95cb-188a1dd35113` | ✅ Partagée |
| DOX BDD - SBRX MYTHIQUE | `8e0efb57-8ac1-4a5d-9a6e-8a59431f9603` | ✅ Partagée |
| DOX BDD - PMRI MYTHIQUE | `6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9` | ✅ Partagée |
| DOX BDD - GED MAIN | `3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e` | ✅ Partagée |
| DOX BDD - FAQ METIER | `3c44d2d1-ee87-44ed-b991-bab4d1e94442` | ✅ Partagée |
| DOX BDD - GLOSSAIRE MAIN | `1481d81e-4c39-808a-b304-fd1857c29329` | ✅ Partagée |

## Procédure de vérification systématique

### 1. Test rapide (toutes les BDD canoniques)

```python
from notion_shared import notion_query, MYTHIQUE_DATABASE_ID, SBRX_MYTHIQUE_DB, PMRI_MYTHIQUE_DB, GED_MAIN_DB, FAQ_METIER_DB, GLOSSAIRE_MAIN_DB

bdds = {
    'PROC MYTHIQUES': ('database_id', MYTHIQUE_DATABASE_ID),
    'SBRX MYTHIQUE':  ('database_id', SBRX_MYTHIQUE_DB),
    'PMRI MYTHIQUE':  ('database_id', PMRI_MYTHIQUE_DB),
    'GED MAIN':       ('database_id', GED_MAIN_DB),
    'FAQ METIER':     ('database_id', FAQ_METIER_DB),
    'GLOSSAIRE MAIN': ('database_id', GLOSSAIRE_MAIN_DB),
}

for nom, (_, db_id) in bdds.items():
    try:
        resp = notion_query(database_id=db_id, page_size=1)
        pages = resp.get('results', [])
        print(f'✅ {nom}: {len(pages)} page(s)')
    except Exception as e:
        print(f'❌ {nom}: {e}')
```

### 2. Test différentiel GET vs POST (pour diagnostique)

```python
from notion_shared import notion_request

db_id = '8e0efb57-8ac1-4a5d-9a6e-8a59431f9603'  # SBRX

# GET /v1/databases/{id} — fonctionne même si BDD non partagée
resp = notion_request('GET', f'https://api.notion.com/v1/databases/{db_id}')
print(f"Nom BDD : {resp.get('title', [{}])[0].get('plain_text', '?')}")

# POST /v1/databases/{id}/query — vérifie les droits réels
try:
    notion_query(database_id=db_id, page_size=1)
except RuntimeError as e:
    if 'object_not_found' in str(e):
        print("🔴 BDD NON partagée avec l'intégration")
    elif 'invalid_request_url' in str(e):
        print("⚠️ L'ID est peut-être un data_source_id, pas un database_id")
```

### 3. Lecture des métadonnées (vérifie le titre)

```python
from notion_shared import notion_request

ids = {
    'MYTHIQUE': '0a1689d5-ec35-4422-95cb-188a1dd35113',
    'SBRX': '8e0efb57-8ac1-4a5d-9a6e-8a59431f9603',
    'PMRI': '6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9',
    'GED': '3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e',
    'FAQ': '3c44d2d1-ee87-44ed-b991-bab4d1e94442',
    'GLOSSAIRE': '1481d81e-4c39-808a-b304-fd1857c29329',
}

for nom, db_id in ids.items():
    try:
        url = f'https://api.notion.com/v1/databases/{db_id}'
        resp = notion_request('GET', url)
        title = resp.get('title', [{}])[0].get('plain_text', '?')
        print(f'✅ {nom}: "{title}"')
    except Exception as e:
        print(f'❌ {nom}: {str(e)[:120]}')
```

## Solution : partager chaque BDD

Dans Notion UI, pour chaque BDD concernée :

1. Ouvrir la BDD
2. Cliquer **Share** (coin supérieur droit)
3. Ajouter l'intégration (ex. « Hostinger n8n »)
4. Donner les droits **Can Edit** (ou Full Access)
5. Cliquer **Invite**

⚠️ **Ne pas oublier** : le recoller du token API dans hPanel Environment ne partage pas les BDD automatiquement. C'est une action distincte par BDD.

## Erreurs typiques

| Message d'erreur | Cause | Solution |
|---|---|---|
| `invalid_request_url` (400) | L'ID passé à `POST /v1/databases/{id}/query` est invalide | Vérifier que c'est bien un database_id (UUID) |
| `object_not_found` (404) avec `"Make sure the relevant pages and databases are shared with your integration"` | BDD non partagée avec l'intégration | Partager la BDD dans l'UI Notion |
| `validation_error` (400) | Propriété API mal formée (payload incorrect) | Vérifier le schéma de la BDD (propriétés exactes) |
