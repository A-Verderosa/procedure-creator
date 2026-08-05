# Formats d'en-têtes par niveau

Référence des formats d'en-têtes produits par `render_procedure.py` et les regex correspondantes dans `check_structure.py`.

## Problème

`render_procedure.py` génère des en-têtes de formats DIFFÉRENTS selon le niveau de la procédure. 
`check_structure.py` doit avoir des regex adaptées à chaque niveau sous peine de signaler
faussement des sections manquantes.

## Mapping niveau → format header

| Niveau | Format header | Exemple | Regex check_structure |
|--------|--------------|---------|----------------------|
| **Argent** | `## **§N. Titre**` | `## **§1. Objet**` | `^## \\*\\*§1\\.` |
| **Or** | `## **§N — Titre**` | `## **§1 — Objet**` | `^## \\*\\*§1 —` |
| **Platine** | `## N. Titre` | `## 1. Objet` | `^## 1\\.` |
| **Ultra** | `## **§N. Titre**` | `## **§1. Objet**` | `^## \\*\\*§1\\.` |
| **Mythique** | `## **§N. Titre**` | `## **§1. Objet**` | `^## \\*\\*§1\\.` |

## Règle générale

Les niveaux Argent, Ultra et Mythique utilisent des headers en `## **§N. Titre**`
avec **gras + point**. Or utilise `## **§N — Titre**` avec **gras + tiret**.
Platine utilise `## N. Titre` sans gras ni §.

## Script de diagnostic

Pour déterminer le format réel d'un fichier .md :

```python
import re
with open('procedure.md') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    m = re.match(r'^(#{1,3})\s*(.*)', line)
    if m and m.group(2).strip():
        print(f'{i+1}: {m.group(1)} |{m.group(2)}|')
```

Cela affiche le niveau de header et le texte brut — permet de voir exactement
ce que `check_structure.py` doit matcher.

## Pattern de rattrapage (fallback)

Si un niveau non listé produit un format inconnu, utiliser un pattern large :

```python
SECTIONS = [
    (r'^##\s+\*\*?§?0?\s*[–\.]\s*\*\*?.*?(?:crai|localis)', 'CRAIE'),
    (r'^##\s+\*\*?§?1\s*[–\.]\s*\*\*?.*?(?:objet|objectif)', 'Objet'),
    # etc.
]
```

Ce pattern capture `## **§1. Objet**`, `## §1 — Objet`, `## 1. Objet`,
indépendamment du niveau.

## Section count par niveau

| Niveau | Sections obligatoires | Notes |
|--------|----------------------|-------|
| Argent | 14 | |
| Or | 17 | |
| Platine | 23 | |
| Ultra | 31 | |
| Mythique | 31 + 9 briques | |
