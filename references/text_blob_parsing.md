# Parsing des blobs texte contrat → placeholders individuels

## Contexte

Le template Évaluateur attend des valeurs individuelles (`{{REGLE_G1}}`, `{{CONSIGNE_C1}}`, `{{RISQUE_1_TITRE}}`) mais le contrat stocke ces données sous forme de **blobs texte libres** (un champ `regles: "G1 : enregistrement 2 jours ; G2 : suspension délai"`).

Le parseur de blocs dans `build_placeholder_map()` de `render_procedure.py` comble cette différence.

## Règles parsées

### 1. Règles de gestion (G1→G10)

**Source contrat** : `procedure.regles` ou `metadata.regles`
**Format attendu** : `"G1: enregistrement 2 jours ; G2: suspension délai ; G5: délai 15 jours"`
**Placeholders générés** : `REGLE_G1`, `REGLE_G2`, ..., `REGLE_G10`
**Algorithme** : Split sur `;` → pour chaque segment, extraire `G\d+` comme clé, le reste comme valeur.

### 2. Consignes opérationnelles (C1→C5)

**Source contrat** : `procedure.consignes`
**Format attendu** : `"C1: vérifier complétude ; C2: accuser réception"`
**Placeholders** : `CONSIGNE_C1` → `CONSIGNE_C5`

### 3. Risques SBRX

**Source contrat** : `procedure.risques`
**Format attendu** : `"R1: Délai dépassé (G:3, P:2) ; R2: Document non conforme (G:4, P:2)"`
**Placeholders** : `RISQUE_1_TITRE`, `RISQUE_1_DESC`, `RISQUE_1_CRIT`, `RISQUE_1_ACTION`, etc.

### 4. Mapping direct (header)

Les champs `titre`, `procedure_id`, `objet`, `champ_application`, `definitions`, `direction`, `pilote`, `version`, `date_actualisation`, etc. sont mappés directement via le dict `direct_mappings` dans `build_placeholder_map()`.

## Vérification

```bash
# Compter les placeholders résolus vs totaux
python3 scripts/render_procedure.py contrat.json --check-only
# → Rapport : "placeholders_filled: 75, placeholders_total: 504"
```

## Ajout d'un nouveau champ blob

Si un nouveau champ texte du contrat doit être parsé en placeholders individuels :

1. Ajouter la clé dans `build_placeholder_map()` dans `render_procedure.py`
2. Créer la fonction parseur dédiée (pattern : `regex split + mapping`)
3. Ajouter l'alias dans `evaluateur_aliases` si le template utilise des noms différents
4. Tester avec `--check-only` sur un contrat qui a ce champ
