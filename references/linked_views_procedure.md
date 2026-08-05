# Vues liées et relations Notion dans les procédures

## Résumé
Les « vues liées » dans les procédures DOX MYTHIQUE ne sont PAS des blocs `child_database` inline. Ce sont des **propriétés `relation`** en haut de page, qui affichent les items liés depuis d'autres BDD canoniques (SBRX, PMRI, GED, FAQ, Snapshots).

## Analyse de MYTH-SIRH-PROC-002 (référence)

Requête : `GET /v1/pages/{page_id}` → inspecter `properties` pour types `relation`/`rollup`.

### Relations détectées

| Propriété | Type | Items | BDD source | database_id | Section associée | Usage |
|-----------|------|-------|-----------|-------------|-----------------|-------|
| `Risques liés` | relation | 8 | DOX BDD - SBRX MYTHIQUE | `8e0efb57-8ac1-4a5d-9a6e-8a59431f9603` | §9.1 Cartographie P×I | 8 risques cotés P×I |
| `Mesures PMRI` | relation | 24 | DOX BDD - PMRI MYTHIQUE | `6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9` | §9.3 Score PMRI crédité | Plan de traitement des risques |
| `Document GED` | relation | 6 | DOX BDD - GED MAIN | `3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e` | §10 Documents support | Documents source + exploitation |
| `FAQ liée` | relation | 5 | DOX BDD - FAQ METIER | `3c44d2d1-ee87-44ed-b991-bab4d1e94442` | §13 FAQ | Cas pratiques |
| `Snapshots procédures` | relation | 1 | DOX BDD - SNAPSHOTS PROCÉDURES MYTHIQUES | `a0be02f5-3128-46c4-8558-256f2e9b1cc0` | §22 Anti-obsolescence | Snapshot de version |

### Relations vides (non utilisées sur cette procédure)
`Rédacteur` (0), `Validateur` (0), `Rapport de lecture` (0), `Dernier rapport de lecture` (0)

### Bloc types répartis (198 blocs totaux)
- heading_3: 35, heading_2: 27, heading_1: 1
- table: 28 (toutes simples — **0** `child_database`)
- divider: 27, bulleted_list_item: 23, paragraph: 21
- callout: 14, toggle: 13, code: 9

## Comment les détecter dans une procédure existante

```python
import requests

r = requests.get(f'https://api.notion.com/v1/pages/{page_id}', headers=HEADERS)
page_data = r.json()
for k, v in page_data.get('properties', {}).items():
    if v.get('type') == 'relation':
        items = v.get('relation', [])
        if items:
            print(f'  🔗 {k}: {len(items)} relations → items')
```

## Comment les représenter en markdown (étape RENDER)

```markdown
<!-- LINKED_VIEW: Risques liés → SBRX (8 items) -->
<!-- LINKED_VIEW: Mesures PMRI → PMRI (24 items) -->
<!-- LINKED_VIEW: Document GED → GED (6 items) -->
```

Le SYNC_NOTION interprète ces marqueurs pour :
1. Créer/mettre à jour les propriétés `relation` dans la page Notion
2. Lier les IDs des items distants (stockés dans le DOX Contract)

## Pourquoi pas de bloc child_database ?

Le `child_database` est créé lorsqu'un utilisateur tape `/linked view of database` dans le body de la page. Dans MYTH-SIRH-PROC-002, les liens sont uniquement au niveau **propriétés** — pas de blocs inline. C'est la norme pour les procédures DOX actuelles.

## Implication pour les templates

Les sections §10 (Documents support) et §9 (Risques) utilisent des **tables simples** (bloc `table`) en plus des relations. Les templates doivent prévoir les deux :
- Table simple dans le corps du markdown (copie statique)
- Marqueur `LINKED_VIEW` pour la relation dynamique Notion
