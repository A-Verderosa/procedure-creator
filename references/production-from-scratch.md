# Production From Scratch — Contrat minimal depuis la BDD DOX

> Session 2026-08-04 : génération de M1-P3-02 (Instruction des demandes ponctuelles) sans contenu préexistant.
> Le pipeline `publish_procedure.py` crée la page MYTHIQUE et ses satellites, mais **plusieurs étapes manuelles** sont nécessaires après la publication pour obtenir un résultat complet.

---

## Workflow complet

```
Étape 0:  Interroger la BDD DOX pour trouver une procédure candidate
              ↓
Étape 1:  Construire un contrat JSON minimal
              ↓
Étape 2:  publish_procedure.py <contrat.json> --publish
              ↓
Étape 3:  Créer entrées PMRI (1 script dédié)
              ↓
Étape 4:  Créer entrées FAQ (1 script dédié)
              ↓
Étape 5:  Renseigner Impact/Probabilité des SBRX
```

---

## Étape 0 — Trouver une procédure dans la BDD DOX

**ID BDD DOX** : `3351d81e-4c39-827e-88a4-817c2739bbff`

Filtre API :
```json
{
  "filter": {
    "and": [
      {"property": "Niveau", "select": {"equals": "Procédure"}},
      {"property": "Statut", "status": {"equals": "À créer"}}
    ]
  }
}
```

Propriétés à extraire :
| Propriété API | Type | Usage |
|---|---|---|
| `Nom` | title | Titre de la procédure |
| `Code` | rich_text | Code hiérarchique (ex: `M1-P3-02`) |
| `Description` | rich_text | Description / objectif |
| `Niveau` | select | `Procédure` |
| `Mission` | select | `M1` à `M5` |
| `Parent item` | relation | → Processus parent (DOX) |

**⚠️ Piège** : le `Code` et la `Description` utilisent `rich_text`, pas `title`. Vérifier le type de chaque propriété via `GET /v1/databases/{id}` avant d'écrire le filtre.

---

## Étape 1 — Structure du contrat JSON minimal

```json
{
  "procedure": {
    "procedure_id": "M1-P3-02",
    "titre": "Instruction des demandes ponctuelles",
    "description": "Analyser recevabilité, pertinence, moyens nécessaires et risques associés.",
    "niveau": "Procédure",
    "service": "ÉVALUATEUR PUBLIC",
    "mission": "M1",
    "processus": "P3",
    "direction": "Évaluateur public",
    "acteurs_cles": [
      {"nom": "Chef de projet", "role": "Pilote"},
      {"nom": "Évaluateur", "role": "Réalisateur"},
      {"nom": "Responsable qualité", "role": "Validateur"},
      {"nom": "Commanditaire", "role": "Approbateur"}
    ],
    "phases": [
      {"titre": "Étape 1 — Titre", "description": "...", "acteurs": "..."},
      {"titre": "Étape 2 — Titre", "description": "...", "acteurs": "..."},
      {"titre": "Étape 3 — Titre", "description": "...", "acteurs": "..."},
      {"titre": "Étape 4 — Titre", "description": "...", "acteurs": "..."}
    ],
    "risks_detail": [
      {"code": "R1", "title": "R1 — Titre du risque", "impact": 3, "probabilite": 3},
      {"code": "R2", "title": "R2 — Titre du risque", "impact": 2, "probabilite": 2},
      {"code": "R3", "title": "R3 — Titre du risque", "impact": 2, "probabilite": 3},
      {"code": "R4", "title": "R4 — Titre du risque", "impact": 4, "probabilite": 1}
    ],
    "pmri_mesures": [
      {"titre": "Mesure X", "risque": "R1", "effet_impact": 1, "effet_probabilite": 1},
      {"titre": "Mesure Y", "risque": "R2", "effet_impact": 0, "effet_probabilite": 1}
    ],
    "faq": [
      {"question": "Question ?", "reponse": "Réponse..."}
    ]
  }
}
```

### Propriétés minimales obligatoires pour le pipeline

| Champ | Requis | Valeur par défaut |
|---|---|---|
| `procedure_id` | ✅ Oui | — |
| `titre` | ✅ Oui | — |
| `niveau` | ✅ Oui | `Procédure` |
| `service` | ✅ Oui | — |
| `direction` | ✅ Oui | — |
| `acteurs_cles` | ⚠️ Recommandé | 4 acteurs par défaut |
| `phases` | ⚠️ Recommandé | 4 phases génériques |
| `risks_detail` | ⚠️ Recommandé | Sinon 0 risques SBRX |

---

## Étape 2 — Pipeline de publication

```bash
python3 scripts/publish_procedure.py /data/contrat_M1-P3-02.json --publish
```

Ce que fait le pipeline :
1. **DOX** — Trouve l'entrée hiérarchique par code (M1-P3 → Mission M1 → Processus P3)
2. **MYTHIQUE** — Trouve ou crée la page, met à jour les 32 propriétés
3. **SBRX** — Parse les risques via `parse_risks()` (texte ou structuré) et crée les entrées
4. **GED** — Parse les documents si présents dans le contrat
5. **Dashboard** — Génère 10-11 blocs (4 diagrammes Mermaid + phases + liens + callouts)

**⚠️ Piège** : `parse_risks()` supporte maintenant les deux formats (`risques` texte et `risks_detail` structuré). Si le contrat utilise `risks_detail`, vérifier que le patch est présent dans `publish_procedure.py`.

---

## Étape 3 & 4 — PMRI et FAQ

Ces BDD ne sont **pas** alimentées par le pipeline principal. Scripts séparés nécessaires.

### BDD PMRI — Propriétés

| Propriété API | Type | Valeur |
|---|---|---|
| `Titre` | title | Nom de la mesure |
| `Procédure Source` | relation → MYTHIQUE | ID de la page MYTHIQUE |
| `Risque Traité` | relation → SBRX | ID du risque SBRX ciblé |
| `Effet attendu sur impact` | number | 0-3 (réduction) |
| `Effet attendu sur probabilité` | number | 0-3 (réduction) |

### BDD FAQ METIER — Propriétés

| Propriété API | Type | Valeur |
|---|---|---|
| `Question` | title | Texte de la question |
| `Réponse` | rich_text | Texte de la réponse |

**⚠️ Piège** : la FAQ n'a pas de `Catégorie` ni de `Procédure source`. Si le script tente d'écrire ces propriétés, l'API Notion renvoie une 400.

### Script type de création PMRI

```python
# 1. Récupérer l'ID MYTHIQUE via filter Code procédure
# 2. Récupérer les IDs SBRX via filter Procédure Mère
# 3. Pour chaque mesure, POST /v1/pages dans PMRI_DB
#    avec relation → MYTHIQUE + relation → SBRX
```

---

## Étape 5 — Renseigner les cotations SBRX

Le pipeline crée les pages SBRX avec `Code risque`, `Titre` et `Procédure Mère`, mais **laisse Impact, Probabilité et Cotation vides**.

Ces champs doivent être mis à jour après publication :

```python
PATCH /v1/pages/{sbrx_id}
{
  "properties": {
    "Impact": {"number": N},
    "Probabilité": {"number": N}
  }
}
```

**⚠️ Piège** : le code du risque est stocké dans `Code risque` (rich_text), pas dans `Code`. Toujours vérifier via `GET /v1/databases/SBRX_DB`.

---

## Pièges Notion API (accents)

Les propriétés Notion utilisent leur nom **exact** dans l'API — accents compris. Les erreurs 400 silencieuses sont souvent dues à des fautes d'accentuation :

| Nom correct | Nom erroné (⛔) |
|---|---|
| `Code procédure` | `Code procedure` |
| `Procédure Mère` | `Procedure Mere` |
| `Procédure Source` | `Procedure source` |
| `Risque Traité` | `Risque traite` |
| `Analyse des risques` | `Risques` |
| `🚧 En cours` | `En cours` (sans emoji) |
| `🔲 À faire` | `À faire` (sans emoji) |
| `✅ Terminé` | `Terminé` (sans emoji) |

Pour le champ `Statut` (type `status`), le nom exact inclut l'emoji (`🚧 En cours`). Utiliser le `name` de l'option, pas le `id`.

---

## BDD SBRX — Propriétés clés

| Propriété API | Type | Rempli par |
|---|---|---|
| `Code risque` | rich_text | Pipeline (depuis risks_detail) |
| `Titre` | title | Pipeline |
| `Impact` | number | ❌ Manuelle (étape 5) |
| `Probabilité` | number | ❌ Manuelle (étape 5) |
| `Cotation` | formula | Automatique (P×I) |
| `Niveau` | select | ❌ Manuelle |
| `Procédure Mère` | relation | Pipeline |

Les champs marqués ❌ doivent être renseignés **après** le pipeline.
