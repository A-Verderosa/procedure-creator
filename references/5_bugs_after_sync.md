# 5 Bugs identifiés après sync Notion de M1-P3-01

## Évolution : 3 résolus (sessions 2026-08-04/05), 2 persistants

| Bug | Statut | Solution |
|-----|--------|----------|
| Bug 1 — Doublons pages (V4.5) | ✅ **RÉSOLU** | `procedure_id` ajouté à `rich_text_keys` → "Code procédure" alimenté après 1re sync → runs suivants détectent la page |
| Bug 2 — Relations absentes | ✅ **RÉSOLU par V6** | `create_satellite_pages.py` crée les pages satellites + relations depuis le contrat |
| Bug 3 — LINKED_VIEW ignorés | ✅ **RÉSOLU par V2** | `generate_satellite_summary_tables()` crée des tableaux inline dans le rendu markdown (remplace `link_to_page`) |
| Bug 4 — Renumérotation Akuma | ✅ **RÉSOLU** | Sections renumérotées : 11→11, 24→12, SAM sans numéro |
| Bug 5 — G{{N}}/C{{N}} → `—` | 🔄 **DÉLIBÉRÉ** | `—` est le comportement attendu pour les cellules non renseignées (pas un bug) |

---

## Bug 1 — Détection V4.5 : filtre `rich_text` sur propriété `unique_id` → ✅ RÉSOLU

### Cause initiale

`find_page_by_id.py` filtrait `Code procédure` avec `rich_text` mais la propriété était de type `unique_id`. Le filtre échouait silencieusement → toujours `NOT_FOUND` → 4 pages en double.

### Correction

`procedure_id` a été ajouté à la liste `rich_text_keys` dans `build_properties()` (`sync_notion.py`). Désormais, à chaque sync :
- **Premier run** : "Code procédure" est vide → V4.5 retourne `NOT_FOUND` → création nouvelle page ✅
- **Runs suivants** : "Code procédure" est rempli → V4.5 trouve la page → mise à jour ✅

### Pages existantes (avant le fix)

Leur "Code procédure" est vide et ne sera jamais rempli par le script. Pour activer la détection :
- Les supprimer et recréer (run avec `--publish`)
- Ou mettre à jour manuellement la propriété "Code procédure" dans Notion

### Scripts concernés

- `scripts/find_page_by_id.py` — inchangé (le filtre rich_text fonctionne maintenant car la propriété est alimentée)
- `scripts/sync_notion.py` — `rich_text_keys` inclut `"procedure_id"`
- `scripts/verrouiller.sh` — V4.5 intégré

---

## Bug 2 — Relations absentes → ✅ RÉSOLU par V6

### Cause initiale

`set_relations()` n'était pas appelée par `verrouiller.sh`. Les relations (Risques liés, Documents GED, FAQ) restaient vides après sync.

### Correction (session 2026-08-04)

**V6** ajoutée au pipeline : `create_satellite_pages.py` parse les champs du contrat (`risques`, `documents_supports`, `faq`, `mesures_pmri`) et pour chaque item :
1. Vérifie si une page existe déjà dans la BDD satellite (dédoublonnage par titre)
2. Si non : crée la page avec les propriétés minimales
3. Établit la relation Notion (`Risques liés`, `Document GED`, etc.) sur la page procédure

### ⚠️ Bug 2b découvert (session 2026-08-05) — Relations non bidirectionnelles → ✅ RÉSOLU

**Problème :** les pages satellites (SBRX, GED, PMRI) étaient créées avec une relation FROM procédure → satellite, mais SANS relation inverse (satellite → procédure). Résultat : impossible de filtrer les "vues liées" dans la BDD satellite par procédure.

**Correction :** `REVERSE_RELATION_MAP` ajouté dans `create_satellite_pages.py` :

| BDD satellite | Champ relation inverse | Statut |
|--------------|----------------------|--------|
| SBRX | `Procédure Mère` | ✅ Injecté à la création |
| GED | `Procédures liées` | ✅ Injecté à la création |
| PMRI | `Procédure Source` | ✅ Injecté à la création |
| FAQ | `None` | ❌ Aucun champ — pas de relation possible |

De plus, les **pages existantes** (créées avant la correction) sont mises à jour rétroactivement : quand `process_contract_field` trouve une page satellite existante par titre, elle PATCH la relation inverse sur cette page.

**Règle :** « Aucune page ne doit être créée dans une base liée sans que la référence à la procédure ne soit injectée. »

**Vérification :**
```python
# Interroger une page satellite et vérifier la relation inverse
page = notion_request("GET", f"https://api.notion.com/v1/pages/{satellite_page_id}")
props = page.get("properties", {})
rev_rel = props.get("Procédure Mère", {}).get("relation", [])
assert any(r["id"].startswith(procedure_id[:12]) for r in rev_rel)
```

### Usage

```bash
# Automatique dans verrouiller.sh (après V5)
bash verrouiller.sh contrat.json --publish

# Ou manuel
python3 scripts/create_satellite_pages.py contrat.json <procedure_page_id>

# Pour désactiver
bash verrouiller.sh contrat.json --publish --skip-satellites
```

### Scripts concernés

- `scripts/create_satellite_pages.py` — créé (402 lignes, approche contractuelle)
- `scripts/verrouiller.sh` — V6 intégré, flag `--skip-satellites`
- `scripts/notion_shared.py` — IDs des BDD satellites

---

## Bug 3 — `LINKED_VIEW` marqueurs → ✅ RÉSOLU par V2 (tableaux inline)

### Historique

1. **Version 1** (session 2026-08-04) : `render_procedure.py` insérait `<!-- LINKED_VIEW:xxx -->` → ignorés par `_markdown_to_notion_blocks()` → aucune relation Notion
2. **Version 2** (session 2026-08-05) : `sync_notion.py` convertissait les commentaires en blocs `link_to_page` (lien cliquable vers la BDD) → ⛔ **Rejeté par l'utilisateur** : « Il manque la vue liée à la base de données des risques. Trouves une autre approche »
3. **Version 3 (actuelle)** : `generate_satellite_summary_tables()` dans `render_procedure.py` génère des **tableaux markdown inline** avec les données réelles du contrat

### Solution actuelle

```python
# Dans render_procedure.py, appelée après insert_linked_view_markers()
filled_md = generate_satellite_summary_tables(filled_md, contract)
```

La fonction :
1. Parse les champs du contrat (`risques`, `documents_supports`, `faq`, `mesures_pmri`)
2. Génère un tableau markdown formaté par satellite
3. Supprime les anciens commentaires `<!-- LINKED_VIEW:xxx -->`
4. Insère le tout dans la section SAM (avant `## 12. HISTORIQUE`)

### Résultat sur Notion

Les tableaux sont convertis en blocs `table` Notion avec leurs lignes de données. Les `link_to_page` ne sont plus nécessaires.

```
[136] heading_3        🛡️ Risques SBRX liés
[137] table            table (2 cols) × [5 rows]    ← 4 risques + 1 en-tête
[138] paragraph        🔗 Données alimentées depuis la base SBRX MYTHIQUE
[139] divider          ———
[140] heading_3        📄 Documents GED liés
[141] table            table (1 cols) × [5 rows]    ← 4 docs + 1 en-tête
[142] paragraph        🔗 Données alimentées depuis la base GED MAIN
```

### Détail technique

**Parsing risques** : Regex `r'^.*?(?=R\d+\s*[:])'` supprime le préfixe "4 risques (R1-R4) cotés P×I." avant "R1: ...". Split par `;`. Mapping code/titre via `r'^(R\d+)\s*[:\–\.\-—]\s*(.*)'`.

**Parsing documents** : Split par `;`, pas de code extrait.

**Parsing FAQ** : JSON array `[{"question": "...", "reponse": "..."}]`, limité à 5 items.

### Limites

- Les données sont **statiques** (figées au moment du rendu)
- Pas de filtrage dynamique (contrairement aux vues `@` Notion)
- Les contrats pauvres en données produisent des tableaux vides (la section est automatiquement omise)

---

## Bug 4 — Renumérotation Akuma → ✅ RÉSOLU

### Correction appliquée

Dans `scripts/mythique_template_evaluateur_akuma.md` :

```
## 10. DOCUMENTS SUPPORT          ← inchangé
## 11. CAS PRATIQUES & FAQ        ← ancien 13
## 🔗 VUES LIÉES SAM               ← sans numéro
## 12. HISTORIQUE DES VERSIONS    ← ancien 24
```

### Vérification

```bash
grep -E '^## ' scripts/mythique_template_evaluateur_akuma.md
# Séquence : 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 🔗, 12
```

---

## Bug 5 — G{{N}}/C{{N}} → `—` dans Matrice de couverture → 🔄 DÉLIBÉRÉ

### Analyse

`clean_final_placeholders()` remplace `G{{N}}` et `C{{N}}` par `—` (non applicable). C'est **délibéré** pour les contrats qui ne fournissent pas ces champs.

### Comportement actuel

| Résidu | Remplacé par | Raison |
|--------|--------------|--------|
| `G{{N}}` | `—` | Règle non applicable |
| `C{{N}}` | `—` | Consigne non applicable |

### Si le contrat a des règles partielles

Si `regles: "G1 (enregistrement 2 jours); G2 (suspension délai)"` → `REGLE_G1` et `REGLE_G2` sont résolus par le parseur de blob. Les cellules `G3{{N}}` deviennent `—`. La matrice est mixte : règles réelles + tirets pour les absentes. C'est correct et transparent.

### Aucune correction prévue

Tant que le parseur de matrice d'association (risque × règle) n'est pas implémenté, `G{{N}}` → `—` reste le comportement attendu. Ne pas changer en « À définir » — cela créerait des alertes inutiles.

---

## Résumé des correctifs appliqués

| Fichier | Correction |
|---------|-----------|
| `scripts/sync_notion.py` | `rich_text_keys` inclut `"procedure_id"` ; `_append_blocks_batch` avec délai 1.5s ; retour propagé |
| `scripts/create_satellite_pages.py` | Créé : parsing contrat → pages satellites + relations |
| `scripts/verrouiller.sh` | V4.5 (find_page_by_id) + V6 (create_satellite_pages) + flags `--skip-satellites` |
| `scripts/mythique_template_evaluateur_akuma.md` | Renumérotation + tableau SAM corrigé (`||` → `\|`) |
| `scripts/render_procedure.py` | `clean_final_placeholders()` : G{{N}}/C{{N}} → `—` ; `generate_satellite_summary_tables()` : tableaux inline |
| `scripts/find_page_by_id.py` | Réécrit avec fallback titre `unique_id` |

### Vérification finale

```bash
bash scripts/verrouiller.sh contrat.json --publish
# V4.5 → détecte ou crée
# V5 → sync Notion (lots de 50, délai 1.5s)
# V6 → pages satellites + relations
# Retour: "✅ VERROUILLÉ — Procédure prête"
```
