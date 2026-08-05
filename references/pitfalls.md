# Pièges et correctifs connus

## 1. Duplication du dashboard
**Problème** : `notion_patch` sur `.../children` ajoute des blocs, ne les remplace pas.
**Correctif** : Toujours appeler `fetch_children(page_id)` puis `delete_children(block_ids)` avant d'ajouter de nouveaux blocs dashboard.

```python
existing_children = fetch_children(page_id)
if existing_children:
    delete_children([c["id"] for c in existing_children])
```

## 2. Regex de code GED trop large ou trop stricte

**Problème initial** : `r'([A-Z]+-?\\w*)\\s+(.+)'` capture "Grille" comme code pour "Grille d'analyse..."
→ Correctif provisoire : `r'([A-Z]+-?\\d+)\\s+(.+)'` (chiffres obligatoires)

**Problème final** : Le correctif provisoire ne capturait pas les codes avec lettres après le tiret comme `CEV-F01`.
→ **Correctif final** : `r'([A-Z][A-Z0-9-]*\\d+)\\s+(.+)'` — commence par une lettre majuscule, accepte lettres/chiffres/tirets, doit finir par au moins un chiffre.

Captures : `CEV-F01`, `D1`, `REF1`, `R5`, `M1P3`.
Ignore : mots simples sans chiffres comme "Grille", "Décret", "Registre".

## 3. Phases sans numéro dans le corps
**Problème** : `phase.get("nom")` affiche juste le nom, pas "Phase N — Titre".
**Correctif** : Construire `titre_phase = f"Phase {phase['numero']} — {phase.get('titre', phase.get('nom', 'Sans nom'))}"` pour le heading_3.

## 4. Documents de référence non parsés

**Problème** : `parse_documents()` ne lisait que `documents_supports`.
**Correctif** : Parser les deux champs :
```python
docs += _parse_text(proc.get("documents_supports", ""), "D", "Document support")
docs += _parse_text(proc.get("documents_reference", ""), "REF", "Document référence")
```

Les documents de référence reçoivent la catégorie "Document référence" (select option ajoutée dans GED MAIN).

## 5. Catégorie GED non renseignée — RÉSOLU
**Problème** : Les documents étaient créés sans `Catégorie` (select) dans GED MAIN.
**Correctif** : Ajouter `Catégorie` aux propriétés si `doc.get("category")` est défini.

## 6. Relation Mesures PMRI sur MYTHIQUE
Le champ bidirectionnel `Mesures PMRI` sur la page MYTHIQUE est conservé — il offre une lisibilité directe sans navigation dans la BDD PMRI. La donnée reste aussi accessible via la BDD PMRI (champ `Procédure Source`).

## 7. `notion_request` vs `notion_patch` (token)
`notion_request()` dans notion_shared.py lit le token via `get_notion_token()` en interne — ne pas passer `token=` en paramètre.
`notion_patch()` et `notion_post()` dans publish_procedure.py acceptent `token` en paramètre.

## 8. `parse_risks()` jette impact/probability/hyp_rc/hyp_rn — RÉSOLU (août 2026)
**Problème** : `parse_risks()` (ligne ~311) ne gardait que `code` et `title` de `risks_detail`, jetant `impact`, `probability`, `hyp_rc`, `hyp_rn`.
```python
# AVANT — données perdues
return [{"code": r.get(...), "description": r.get("title", ""), "index": i} ...]
```
**Correctif** : Étendre le dict retourné pour propager tous les champs.
```python
return [{
    "code": r.get("code", f"R{i+1}"),
    "description": r.get("title", ""),
    "impact": r.get("impact"),
    "probability": r.get("probability"),
    "hyp_rc": r.get("hyp_rc"),
    "hyp_rn": r.get("hyp_rn"),
} for i, r in enumerate(risks_detail)]
```
**Vérification** : après correction, `populate_sbrx` reçoit bien tous les champs — vérifier avec un contrat qui a `risks_detail` complet.

## 9. `populate_sbrx` et `populate_pmri` écrivent partiellement leurs champs — RÉSOLU (août 2026)
**Problème** : Les fonctions `populate_sbrx()` et `populate_pmri()` ne remplissaient que le strict minimum :
- **SBRX** : Titre, Code risque, Procédure Mère — ❌ Impact, Probabilité, Hypothèse RC, Hypothèse RN manquants (4 champs)
- **PMRI** : Titre, Procédure Source, Risque Traité, Effets attendus — ❌ Famille de mesure, Fréquence contrôle, Type contrôle, Responsable manquants

**Correctif** (deux étapes) :
1. Assurer que `parse_risks()` propage `impact`, `probability`, `hyp_rc`, `hyp_rn` (cf. pitfall #8)
2. Ajouter les champs manquants dans les fonctions `populate_*` :
   - `populate_sbrx` → écrit `Impact` (number), `Probabilité` (number), `Hypothèse RC` (rich_text), `Hypothèse RN` (rich_text)
   - `populate_pmri` → écrit `Famille de mesure` (multi_select), `Fréquence contrôle` (select), `Type contrôle` (select), `Responsable` (relation, si trouvé)
3. Ajouter un chemin **PATCH** pour les pages existantes : `notion_patch` avec les champs manquants

**Mappings Notion** (contrat → DB) :
```
Fréquence : "Quotidien"→"Quotidienne", "Mensuel"→"Mensuelle", "Annuel"→"Annuelle", "Trimestriel"→"Trimestrielle"
Type contrôle : "Automatique"→"Préventif", "Manuel"→"Détectif", "Semi-automatique"→"Détectif"
```

**Dépendance Responsable** : la base contacts (ID `6e9d978c-b165-490c-a6c5-a4de5eaa5e56`) doit contenir des entrées pour que la relation soit liée. Sans entrées, le pipeline log un avertissement et skip le champ.

## 10. Enrichissement rétroactif après correction
Quand une fonction `populate_*` est enrichie, les procédures déjà créées ne reçoivent pas les nouveaux champs automatiquement — le pipeline les skipe car les pages existent déjà.
**Correctif** : Ajouter une branche `else`/`patch` dans la détection d'existant :
```python
if existing and existing.get("results"):
    # PATCH des champs manquants sur la page existante
    patch_fields = { ... nouveaux champs ... }
    notion_patch(f"https://api.notion.com/v1/pages/{page_id}",
        {"properties": patch_fields}, token)
```
C'est implémenté dans les deux fonctions `populate_sbrx` et `populate_pmri`.

## 12. Relation `dual_property` API Notion — inverse invisible dans le GET

**Problème** : Quand on crée une relation avec `dual_property` (ex: Glossaire Main → `Pages liées (Bus)` → PAGES BUS), la propriété inverse sur la base cible (PAGES BUS) est créée par l'API MAIS n'apparaît PAS dans la réponse `GET /v1/databases/{target_id}`. La propriété existe au niveau du schéma (les pages peuvent être liées) mais n'est pas listée dans `properties`.

**Cause** : Comportement connu de l'API Notion v2022-06-28. Les relations inverses créées automatiquement via `dual_property` portent un nom auto-généré comme `From Pages liées (Bus) (Glossaire Main)` et ne sont pas retournées dans la réponse GET immédiate de la cible. Cela ne signifie pas qu'elles sont absentes — elles fonctionnent au niveau page.

**Correctif** : 
- Ne pas tenter de les renommer via API (la propriété n'est pas listée donc pas modifiable)
- Renommer manuellement dans l'interface Notion si nécessaire
- Ou accepter le nom auto-généré — il est fonctionnel même si invisible dans la vue schéma API

```python
# Ce code fonctionne — la relation est créée
notion_patch(db_url, {
    "properties": {
        "Pages liées (Bus)": {
            "type": "relation",
            "relation": {
                "database_id": PAGES_BUS_DB,
                "dual_property": {"property_name": "Pages liées (Bus)"}
            }
        }
    }
}, token)
# ✅ La propriété avant est créée dans les deux directions
# ⚠️ La propriété sur PAGES BUS n'apparaît pas dans GET /v1/databases/PAGES_BUS
# ✅ Mais les pages peuvent être liées bidirectionnellement via l'API
```

**Alternative** : Créer d'abord la relation inverse manuellement dans la base cible via l'API (PATCH direct sur la base cible avec `single_property`), puis créer la relation avant avec `dual_property` qui référence cette propriété existante.

## 13. Base Annuaire DOX vide empêche le lien Responsable
**Problème** : `populate_pmri()` tente de lier le champ `Responsable` (relation) vers l'Annuaire DOX (`6e9d978c-b165-490c-a6c5-a4de5eaa5e56`). Si cette base est vide, `query_database` ne trouve aucune correspondance pour les noms (Évaluateur public, Contrôle qualité, etc.) et le champ est ignoré.

**Correctif** : Pré-populer l'Annuaire DOX avec les acteurs courants avant le premier run qui utilise Responsable :
```python
acteurs = [
    {"nom": "Évaluateur public", "contexte": "PRO"},
    {"nom": "Contrôle qualité", "contexte": "PRO"},
    {"nom": "Directeur de l'évaluation", "contexte": "PRO"},
]
for a in acteurs:
    notion_post(f"https://api.notion.com/v1/pages", {
        "parent": {"database_id": "6e9d978c-b165-490c-a6c5-a4de5eaa5e56"},
        "properties": {
            "Nom Prénom": {"title": [{"text": {"content": a["nom"]}}]},
            "Contexte": {"select": {"name": a["contexte"]}},
        }
    }, token)
```

**Vérification** : après création, relancer `publish_procedure.py --publish` — les lignes "Responsable lié" apparaissent dans les logs PMRI. La base peut être enrichie avec d'autres acteurs (chefs de bureau, etc.) au besoin.
