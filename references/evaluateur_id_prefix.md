# Préfixe ID dynamique — Implémentation (session 2026-08-03)

## Fonction `_derive_prefix()`

Ajoutée dans `scripts/generate_contract.py` :

```python
def _derive_prefix(direction: str) -> str:
    """Retourne le préfixe ID selon la direction de la procédure."""
    if not direction:
        return "EVP"  # fallback
    direction_lower = direction.strip().lower()
    if "évaluateur" in direction_lower or "evaluateur" in direction_lower:
        return "EVP"
    if direction_lower in ("rh", "ressources humaines"):
        return "PRH"
    return "EVP"  # fallback
```

## Regex de validation (dans `bullet_proof.py` et `generate_contract.py`)

**Avant :** `r"^PRH-\d{3}$"` — bloquait tout ID avec un préfixe différent
**Après :** `r"^[A-Z]{3}-\d{3}$"` — accepte tout préfixe de 3 lettres majuscules

## Contrats wrappés — déwrapper obligatoire

Les fichiers contrat JSON utilisent le format `{"procedure": {...}}`. Les deux fonctions `_cmd_validate()` et `render_contract()` doivent faire `data.get("procedure", data)` avant d'utiliser les champs, sinon `_derive_prefix()` reçoit `None` comme direction et retourne `EVP` par défaut (fallback).

## Propriété "Code procédure" dans Notion (session 2026-08-03)

Le `procedure_id` (ex: `EVP-001`) est désormais stocké comme propriété **rich_text** nommée `"Code procédure"` dans la BDD MYTHIQUE. Ceci permet la recherche par ID via `find_page_by_id.py`.

**Implémentation :** Dans `sync_notion.py`, la clé `"procedure_id"` a été ajoutée à `rich_text_keys` dans `build_properties()`. À chaque sync, la propriété `"Code procédure"` est remplie avec l'ID de la procédure.

**Script de détection V4.5 :** `scripts/find_page_by_id.py`

```bash
python3 scripts/find_page_by_id.py "EVP-001"
# Retourne le page_id si trouvé, ou "NOT_FOUND"
```

Ce script interroge `POST /v1/databases/0a1689d5-ec35-4422-95cb-188a1dd35113/query` avec un filtre `contains` sur le champ `"Code procédure"`.

**Workflow V4.5 dans verrouiller.sh :**
1. Exécute `find_page_by_id.py` avec l'ID du contrat
2. Si page trouvée → passe `--update <page_id>` à V5 (sync = mise à jour)
3. Si non trouvée → V5 créé une nouvelle page

## Pipeline verrouillé — test sur M1-P3-01

Commande complète :
```bash
cd /data/skills/software-development/procedure-creator
bash scripts/verrouiller.sh flux_evaluateur/procedures_prioritaires/M1-P3-01_data.json --skip-structure --publish
```

**Résultat :** V1 ✅ Validation contrat → V2 ✅ Rendu (1100 lignes, 47087 octets) → V3 ⚠️ Skip (Évaluateur auto-détecté) → V4 ✅ Diff → V5 ✅ Sync Notion (page créée)

## Templates mis à jour

- `templates/platine_template.md` : G1 changé de `(format PRH-xxx)` → `(EVP-xxx, PRH-xxx)`
- `templates/ultra_template.md` : G1 changé de `(PRH-xxx)` → `(EVP-xxx, PRH-xxx)`
- `scripts/render_procedure.py` : valeur par défaut `PRH-000` → `EVP-000`

## Vérification après création d'un contrat

```bash
# 1. Vérifier le préfixe dans l'ID généré
grep '"procedure_id"' nouveau_contrat.json
# Doit retourner "EVP-XXX" pour Évaluateur public

# 2. Vérifier que la direction est bien présente
grep '"direction"' nouveau_contrat.json
# Doit retourner "Évaluateur public" (ou "RH", etc.)
```
