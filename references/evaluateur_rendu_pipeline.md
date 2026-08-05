# Pipeline de rendu Évaluateur public — Verrouillage reproductible

## Contexte

Ce document détaille le pipeline déterministe pour produire des procédures Mythique Évaluateur public, depuis le contrat JSON jusqu'à la synchronisation Notion, avec les 3 verrous (contractuel → structurel → diff Golden) garantissant la reproductibilité.

## Architecture template

| Fichier | Rôle | Emplacement |
|---------|------|-------------|
| `mythique_template_evaluateur.md` | Template Évaluateur (504 placeholders, 1083 lignes) | `scripts/` |
| `render_procedure.py` | Résout les placeholders contrat→template | `scripts/` |
| `generate_contract.py` | Valide et génère le DOX Contract | `scripts/` |
| `check_structure.py` | 21 Quality Gates structurels | `scripts/` |

**Auto-détection du template** : si le contrat JSON contient `"direction": "Évaluateur public"`, `render_procedure.py` charge automatiquement `mythique_template_evaluateur.md`. Forçage possible via `--template evaluateur`.

## Contrat d'entrée (data.json)

Format attendu par le pipeline Évaluateur :

```json
{
  "procedure": {
    "id": "CEV-P02",
    "titre": "Traitement d'une saisine d'évaluation",
    "niveau": "mythique",
    "direction": "Évaluateur public",
    "objet": "Définir le circuit standardisé...",
    "champ_application": "Services concernés : Évaluateur public...",
    "definitions": "Saisine : demande formelle...",
    "abbreviations": "CEV : Conseil Évaluateur...",
    "responsabilites": "Le Directeur valide...",
    "risques_principaux": "Dépassement délai...",
    "documents_attaches": "CEV-F01 Formulaire...",
    "modules": ["00_HUB", "01_CADRAGE", "02_ACTEURS", "03_FLUX", "04_REGLES", "05_RISQUES", "06_DOCUMENTS", "07_QG"],
    "acteurs": [
      {"nom": "Secrétariat", "role": "réceptionne et enregistre"},
      {"nom": "Évaluateur", "role": "instruit et rédige"},
      {"nom": "Directeur", "role": "valide"},
      {"nom": "Rapporteur", "role": "présente au CEV"}
    ],
    "phases": [
      {
        "titre": "Réception de la saisine",
        "acteur": "Secrétariat",
        "delai": "48h",
        "action": "Réceptionner, vérifier complétude, enregistrer",
        "vigilance": "G2 (suspension délai), G5 (délai 15 jours), G1 (enregistrement 2 jours)",
        "documents": "CEV-F01 · Registre des saisines"
      },
      {
        "titre": "Instruction par l'évaluateur",
        "acteur": "Évaluateur",
        "delai": "10 jours",
        "action": "Analyser, investiguer, rédiger note",
        "vigilance": "G3 (confidentialité), G7 (impartialité)",
        "documents": "Note d'instruction · Grille d'analyse"
      }
    ],
    "scorecard": {
      "S1_modules": 7,
      "S2_acteurs": 6,
      "S3_flux": 5,
      "S4_composants": 6,
      "total": 24,
      "max": 30
    },
    "date_actualisation": "2026-08-03",
    "periode_revue": "annuelle"
  }
}
\`\`\`

> **6 phases canoniques** pour toutes les procédures Mythique Évaluateur — les placeholders `{{ETAPE_1_*}}` à `{{ETAPE_6_*}}` attendent exactement 6 entrées dans `phases[]`. Le contrat modèle `CEV-P02_data.json` contient les 6 phases de référence.

## Pipeline 3 verrous — Commande unique

```bash
# Usage : bash verrouiller.sh CHEMIN_DATA.JSON [niveau]
# Par défaut : niveau=mythique

DATA=$1
NIVEAU=${2:-mythique}
DIR=$(dirname "$DATA")
BASE=$(basename "$DATA" .json)

echo "🔐 VERROU 1/3 — Contrat"
python3 scripts/generate_contract.py --from-file "$DATA" --validate-only \
  || { echo '❌ CONTRACT INVALIDE'; exit 1; }

echo "🔐 VERROU 2/3 — Rendu + Structure"
CONTRACT=$(python3 scripts/generate_contract.py --from-file "$DATA" --json-only)
echo "$CONTRACT" | python3 scripts/render_procedure.py -o "${DIR}/${BASE}_MYTHIQUE.md" - \
  || { echo '❌ RENDU ÉCHOUÉ'; exit 1; }

python3 scripts/check_structure.py "${DIR}/${BASE}_MYTHIQUE.md" --niveau "$NIVEAU" \
  || { echo '❌ STRUCTURE INVALIDE'; exit 1; }

echo "🔐 VERROU 3/3 — Qualité (post-rendu)"
# Vérifications post-rendu obligatoires
! grep -q '|</details>' "${DIR}/${BASE}_MYTHIQUE.md" || { echo '❌ FUITE TABLEAUX'; exit 1; }
! grep -q '{{' "${DIR}/${BASE}_MYTHIQUE.md" || { echo '❌ PLACEHOLDERS NON RÉSOLUS'; exit 1; }

# Comparaison structurelle avec CEV-P02 (Golden)
GOLDEN_HEADERS=$(grep -c '^## ' flux_evaluateur/procedures_prioritaires/CEV-P02_MYTHIQUE.md 2>/dev/null || echo 0)
NEW_HEADERS=$(grep -c '^## ' "${DIR}/${BASE}_MYTHIQUE.md")
[ "$NEW_HEADERS" -ge "$GOLDEN_HEADERS" ] || echo '⚠️  Moins de sections que le Golden — vérifier template'

echo "✅ PIPELINE VALIDE — Procédure prête pour sync_notion"
```

## Utilisation

```bash
# Pour une nouvelle procédure
bash verrouiller.sh flux_evaluateur/procedures_prioritaires/M1.P3.01_data.json

# Pour la procédure de référence (vérification pipeline)
bash verrouiller.sh flux_evaluateur/procedures_prioritaires/CEV-P02_data.json
```

## Bugs connus (corrigés)

### Fuite VIGILANCE dans les toggles `<details>` — §5.3, §6.1, §6.2 (Session 2026-08-03)

**Symptômes :**

- **§6.1 (Règles de gestion dans les dépliants) :** Le contenu de la vigilance fuyait en dehors du tableau dans chaque titre dépliant. Le `s appliquées : G2...` apparaissait après `</details>` au lieu d'être à l'intérieur du tableau.
- **§5.3 (Acteurs) :** La balise `<details>` d'ouverture manquait, fusionnant le toggle avec le contenu adjacent.
- **§6.2 (Étapes) :** 5 lignes de tableau mal formées — cellules fusionnées, en-tête et balises restaurées.

**Exemple** (incorrect, §6.1) :
```
||</details>s appliquées** : G2 (suspension délai)
```
Le `Rè` de **Rè**gles est absorbé par le séparateur `|`, le `</details>` fusionne avec le texte.

**Causes racines :**
1. Le template avait `{{ETAPE_1_VIGILANCE}}` sans séparateur `|` de fermeture de cellule
2. `replace_placeholders()` n'avait pas de filtre HTML — les valeurs pouvaient contenir `</details>` résiduel
3. Le header `**⚠️ Points de vigilance**` n'était pas concaténé avant la valeur résolue dans la cellule

**Corrections :**
1. **Template source corrigé** — chaque ligne de tableau dans les toggles `<details>` a maintenant la forme canonique :
   ```
   || **⚠️ Points de vigilance** | {{ETAPE_1_VIGILANCE}} |
   ```
   Les `|` de début ET de fin de cellule sont obligatoires. Le header fixe `**⚠️ Points de vigilance**` est dans la même cellule que le placeholder.

2. **`replace_placeholders()` modifié** — HTML safety filter : strip automatiquement `<details>` et `</details>` de toutes les valeurs injectées avant substitution. Ceci élimine définitivement le risque de fuite de balises dans les cellules de tableau.

3. **`generate_contract.py --validate` corrigé** — le validateur déwrappe maintenant les contrats `{"procedure": {...}}` avant validation (bug : les métadonnées `objet`, `champ_application`, etc. étaient vides car le wrapper n'était pas extrait).

4. **`render_procedure.py render_contract()` corrigé** — déwrapper `data.get("procedure", data)` appliqué au renderer aussi, pas seulement au validateur.

**Vérifications post-rendu (3 tests obligatoires) :**
```bash
grep -n '|</details>' procedure.md      # 0 résultat = OK
grep -n '{{' procedure.md               # 0 résultat = tous placeholders résolus
OPEN=$(grep -c '<details>' procedure.md)
CLOSE=$(grep -c '</details>' procedure.md)
[ "$OPEN" -eq "$CLOSE" ] && echo "✅ Toggles équilibrés" || echo "❌ Déséquilibre"
```

**Correction manuelle (si le renderer produit encore le bug sur une procédure existante) :**
Dans chaque toggle concerné, chercher la ligne `||</details>s appliquées**` et la remplacer par :
```
| **⚠️ Points de vigilance** | G2 (suspension délai), G5 (délai 15 jours) |
```
Puis s'assurer que la ligne au-dessus a bien `| |` vide suivi de `<details>` ou du header de toggle approprié.

### Piège Identifiant BDD (cross-database)

Le fichier `sync_notion.py` utilise `--database mythique` qui sélectionne automatiquement `MYTHIQUE_DATABASE_ID` (`0a1689d5-...`) et `MYTHIQUE_PROP_MAP`. Si une page est créée dans la mauvaise BDD, vérifier que `--database mythique` est bien passé dans `proc_orchestrator.py`.

## Test de non-régression

Avant chaque nouveau rendu, valider que le pipeline produit une sortie structurellement correcte :

```bash
# Test 1 : Pipeline complet sur Golden Example
bash verrouiller.sh flux_evaluateur/procedures_prioritaires/CEV-P02_data.json
# Attendu : ✅ PIPELINE VALIDE

# Test 2 : Toggles équilibrés
OPEN=$(grep -c '<details>' output.md)
CLOSE=$(grep -c '</details>' output.md)
[ "$OPEN" -eq "$CLOSE" ] && echo "✅ Toggles équilibrés" || echo "❌ Déséquilibre: $OPEN ouverts, $CLOSE fermés"

# Test 3 : Mermaid sans parenthèses (voir SKILL.md section règles Mermaid)
awk 'BEGIN{inm=0} /```mermaid/{inm=1;next} /```/{inm=0} inm' output.md | grep -n '(' | grep -v '```' \
  || echo "✅ Aucune parenthèse résiduelle dans Mermaid"
```

## Script verrouiller.sh — Interface complète

Le script `scripts/verrouiller.sh` automatise les 3 verrous (contractuel → structurel → diff Golden → sync) en une commande unique, sans dialogue interactif.

### Usage

```bash
bash scripts/verrouiller.sh <contract.json> [options]
```

### Options

| Option | Description | Défaut |
|--------|-------------|--------|
| `--golden GOLDEN.md` | Chemin du Golden Example de référence | `flux_evaluateur/…/CEV-P02_MYTHIQUE.md` |
| `--publish` | Sync Notion après validation (appelle `sync_notion.py --push`) | Désactivé |
| `--update PAGE_ID` | Met à jour une page Notion existante | Création nouvelle page |
| `--output PATH` | Chemin de sortie pour le `.md` | Auto (dossier contrat + `_MYTHIQUE.md`) |
| `--template TYPE` | Force un template (`evaluateur`/`standard`) | Auto-détecté via `direction` |
| `--check-only` | Valide seulement, sans rendu final | Rendu complet |
| `--skip-structure` | Saute le verrou structurel | Désactivé |
| `--skip-diff` | Saute la comparaison Golden | Désactivé |
| `--verbose` | Logs détaillés de chaque étape | Silencieux |
| `--help` | Affiche l'aide complète | — |

### Les 5 étapes du pipeline

| Étape | Commande | Bloque si |
|-------|----------|-----------|
| **V1 — Contrat** | `generate_contract.py --from-file --validate-only` | Champs obligatoires absents, JSON invalide |
| **V2 — Rendu** | `render_procedure.py` avec contrat déwrappé | Erreur de résolution de placeholder |
| **V3 — Structure** | `check_structure.py --niveau` | Score < 80% ou fuites `\|</details>` |
| **V4 — Diff Golden** | Comparaison des `##` headers | Moins de sections que CEV-P02 |
| **V5 — Sync** | `sync_notion.py --push --database mythique` | Optionnel (flag `--publish`) |

### Exemples

```bash
# Validation complète sans publication
bash scripts/verrouiller.sh flux_evaluateur/procedures_prioritaires/M1.P3.01_data.json

# Avec publication Notion automatique
bash scripts/verrouiller.sh flux_evaluateur/procedures_prioritaires/M1.P3.01_data.json --publish

# Mise à jour d'une page existante
bash scripts/verrouiller.sh M1.P3.01_data.json --publish --update PAGE_ID_123

# Vérification rapide (sans rendu ni structure)
bash scripts/verrouiller.sh M1.P3.01_data.json --check-only --skip-structure --skip-diff
```
