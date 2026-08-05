# BDD Structures et Relations — Procédures Évaluateur Public

## Base MYTHIQUE (0a1689d5-ec35-4422-95cb-188a1dd35113)

32 propriétés. Page = dashboard avec vues liées, pas de corps de page rédigé.

### Relations bidirectionnelles — état après pipeline v2 (2026-08-04)

Le pipeline `publish_procedure.py` crée les satellites ET peuple automatiquement les relations inverses.

| Champ MYTHIQUE | Satellite | Direction entrante | Inverse peuplé via pipeline ? |
|---|---|---|---|
| `Risques liés` | SBRX | `Procédure Mère` | ✅ Étape 3 + 4b |
| `Mesures PMRI` | PMRI | `Procédure Source` | ✅ Étape 3b + 4b |
| `FAQ liée` | FAQ | *(aucune)* | ❌ FAQ n'a pas de champ relation |
| `Rapport de lecture` | RAPPORTS LECTURE | `Procédure mythique` | ➡️ Pas de rapport généré automatiquement |
| `Document GED` | GED MAIN | `Procédures liées` | ✅ Étape 4 |
| `Rédacteur` | Annuaire | *(aucun)* | ❌ Manuel — pipeline ne devine pas |
| `Validateur` | Annuaire | *(aucun)* | ❌ Manuel — pipeline ne devine pas |

### Vérification post-publication

```python
# Vérifier les relations inverses
page = notion_get(f"https://api.notion.com/v1/pages/{page_id}", token)
props = page["properties"]
sbrx_count = len(props.get("Risques liés", {}).get("relation", []))
pmri_count = len(props.get("Mesures PMRI", {}).get("relation", []))
print(f"Risques liés: {sbrx_count}, Mesures PMRI: {pmri_count}")
```

Valeurs attendues :
- `Risques liés` → 4+ (une par risque)
- `Mesures PMRI` → N (une par mesure créée)
- `FAQ liée` → toujours 0 (FAQ = pool global sans relation)

## BDD SBRX (8e0efb57-8ac1-4a5d-9a6e-8a59431f9603)

Propriétés :
- `Titre` (title) — ex: "R1 — Non-respect des délais"
- `Code risque` (rich_text) — ex: "R1"
- `Impact` (number, 1-4) — peuplé depuis `risks_detail[].impact`
- `Probabilité` (number, 1-4) — peuplé depuis `risks_detail[].probabilite`
- `Cotation` (formula, Impact × Probabilité)
- `Procédure Mère` (relation → MYTHIQUE)
- `Hypothèse RC` (rich_text) — optionnel
- `Hypothèse RN` (rich_text) — optionnel
- `Statut` (status) — 🔲 À faire

## BDD PMRI (6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9)

Propriétés utilisées par le pipeline :
- `Titre` (title) — description de la mesure
- `Procédure Source` (relation → MYTHIQUE) — auto depuis étape 3b
- `Risque Traité` (relation → SBRX) — auto depuis étape 3b
- `Effet attendu sur impact` (number) — depuis `pmri_mesures[].effet_impact`
- `Effet attendu sur probabilité` (number) — depuis `pmri_mesures[].effet_probabilite`
- `Contribution risque` (select) — RB→RN (défaut)
- `Famille de mesure` (multi_select) — optionnel
- `Statut` (status) — 🔲 À faire (défaut)

## BDD FAQ METIER (3c44d2d1-ee87-44ed-b991-bab4d1e94442)

Propriétés :
- `Question` (title) — la question
- `Réponse` (rich_text) — la réponse

⚠️ **Pas de relation** vers MYTHIQUE ou SBRX. Pool global de questions/réponses.
→ `FAQ liée` sur MYTHIQUE reste toujours vide.

## BDD RAPPORTS LECTURE DOX (bca72a91-852e-48da-bcbb-b8ab60a67cc4)

Propriétés principales :
- `Rapport` (title) — nom du rapport
- `Procédure mythique` (relation → MYTHIQUE, simple)
- `Procédure` (relation → ancienne base, simple)
- `Date lecture` (date)
- `Score lecture` (number)
- `Verdict global` (select)
- `Niveau DOX évalué` (select)
- `Niveau cible` (select)
- `Statut` (status)
- `Version évaluée` (rich_text)
- `Synthèse` (rich_text)
- `Périmètre d'analyse` (rich_text)
- `Nb risques analysés` (number)
- `Nb risques hauts` (number)
- `Nb risques hors cible` (number)
- `Nb réserves ouvertes` (number)
- `Nb mesures analysées` (number)
- `État DRY rapport` (select)
- `Date de gel des données` (date)
- `Source de vérité utilisée` (select)

## Pipeline — Étape 4b (Relations inverses automatiques)

Depuis le patch 2026-08-04, la fonction `publish_procedure()` dans `publish_procedure.py` inclut **automatiquement** les relations inverses SBRX + PMRI :

```python
# Étape 4b : Relations inverses (bidirectionnelles)
# Automatique — plus besoin de script séparé
if sbrx_pages or pmri_pages:
    props = {}
    if sbrx_pages:
        sbrx_ids = [p["id"] for p in sbrx_pages]
        props["Risques liés"] = {"relation": [{"id": sid} for sid in sbrx_ids]}
    if pmri_pages:
        pmri_ids = [p["id"] for p in pmri_pages]
        props["Mesures PMRI"] = {"relation": [{"id": pid} for pid in pmri_ids]}
    if props:
        notion_patch(f"https://api.notion.com/v1/pages/{page_id}",
                     {"properties": props}, token)
```

## Piège récurrent

Le pipeline peuple `Procédure Mère` (SBRX → MYTHIQUE) et `Procédure Source` (PMRI → MYTHIQUE) automatiquement lors de la création des satellites. Mais **l'inverse** (`Risques liés` et `Mesures PMRI` sur MYTHIQUE) n'est peuplé que si l'étape 4b s'exécute. Si elle n'est pas appelée (par ex. mode sans `--publish`), les champs restent vides.

Toujours utiliser `--publish` pour un run complet.
