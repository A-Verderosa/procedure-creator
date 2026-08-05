# Diagrammes Mermaid — État des lieux et intégration pipeline

## Contexte

Le **Golden Example CEV-P02** inclut 4 types de diagrammes Mermaid dans son rendu markdown (fichier `CEV-P02_MYTHIQUE.md`) :
1. **Carte CRAIE** → `flowchart LR` — amont/procédure/aval/norme
2. **Vue par acteur** → `sequenceDiagram` — phases avec acteurs et décisions
3. **Logigramme** → `flowchart TB` — étapes opérationnelles avec points de décision
4. **Matrice des risques** → `quadrantChart` — positionnement impact × probabilité (brut + net)

Ces diagrammes sont **hardcodés** dans le markdown du golden example — ils ne sont pas générés dynamiquement par le pipeline.

## Génération automatique (existant)

Le script `scripts/render_procedure.py` contient **3 générateurs** :

| Fonction | Diagramme | Source |
|----------|-----------|--------|
| `generate_flowchart(contract)` | `flowchart TD` | Phases du contrat + métadonnées (acteurs, délais) |
| `generate_sequence_diagram(contract)` | `sequenceDiagram` | Acteurs clés (metadata) + phases (limité 5) |
| `generate_gantt(contract)` | `gantt` | Phases + délais |

**⚠️ Aucun de ces générateurs n'est intégré à `publish_procedure.py`**. Le pipeline de publication Notion ne produit que des blocs toggle texte sans diagrammes.

## QuadrantChart (matrice des risques) — GAP

**Aucun générateur de `quadrantChart` n'existe dans la codebase.**

Pourtant, la matrice des risques (impact × probabilité) est :
- Une exigence implicite du niveau **Mythique/Akuma** (présente dans CEV-P02)
- Structurable : chaque risque SBRX a `Impact` (1-4) et `Probabilité` (1-4)
- Mappable : Impact × Probabilité → coordonnées [0.0-1.0, 0.0-1.0] dans le quadrant

### Algorithme proposé pour `generate_quadrant_chart(risks)`

```python
# 1. Lire les risques depuis le contrat JSON (section "risques")
# 2. Pour chaque risque : Impact (1-4) → y = (impact-1)/3 * 0.8 + 0.1
#                          Probabilité (1-4) → x = (prob-1)/3 * 0.8 + 0.1
# 3. Quatre quadrants :
#    - Quadrant 1 (haut-droit) : 🔴 Critique (Impact ≥ 3, Probabilité ≥ 3)
#    - Quadrant 2 (haut-gauche) : 🔴 Élevé (Impact ≥ 3, Probabilité < 3)
#    - Quadrant 3 (bas-droit) : 🟡 Moyen (Impact < 3, Probabilité ≥ 3)
#    - Quadrant 4 (bas-gauche) : 🟢 Faible (Impact < 3, Probabilité < 3)
# 4. Générer le bloc Mermaid avec :
#    - Un quadrantChart pour le risque brut (RB)
#    - Un quadrantChart pour le risque net (RN) après mesures
#    - Les points positionnés selon coordonnées calculées
```

## Intégration pipeline — Roadmap

### Phase 1 (immédiat) : Injecter les générateurs existants

Dans `publish_procedure.py`, après la construction du dashboard (étape 5), ajouter :

```python
from render_procedure import generate_flowchart, generate_sequence_diagram

# Générer les diagrammes depuis le contrat
flowchart = generate_flowchart(contract)
sequence = generate_sequence_diagram(contract)

# Créer des blocs Notion code block (language: mermaid)
flowchart_block = {
    "object": "block",
    "type": "code",
    "code": {
        "language": "mermaid",
        "rich_text": [{"type": "text", "text": {"content": flowchart}}]
    }
}
```

**⚠️ Limitation Notion :** Les code blocks `mermaid` dans Notion ne rendent pas le diagramme visuellement en ligne (contrairement à GitHub/Markdown). Le rendu visuel n'est disponible que :
- Dans le markdown exporté (via `render_procedure.py` → fichier .md)
- Via le renderer Notion intégré (si activé — vérifier le workspace)
- Alternative : captures d'écran ou images embed

### Phase 2 (court terme) : Générer le quadrantChart

Créer une fonction `generate_quadrant_chart(risks, title="Matrice des risques")` dans `render_procedure.py` :

```python
def generate_quadrant_chart(risks, title="Matrice des risques", mode="RN"):
    """Génère un quadrantChart Mermaid à partir des risques SBRX."""
    lines = ["quadrantChart"]
    lines.append(f'    title "{title} — {mode}"')
    lines.append('    x-axis "Probabilité faible" --> "Probabilité élevée"')
    lines.append('    y-axis "Impact faible" --> "Impact élevé"')
    lines.append('    quadrant-1 "🔴 Critique"')
    lines.append('    quadrant-2 "🔴 Élevé"')
    lines.append('    quadrant-3 "🟡 Moyen"')
    lines.append('    quadrant-4 "🟢 Faible"')
    
    for risk in risks:
        code = risk.get("code", "R?")
        impact = risk.get("impact", 2)
        prob = risk.get("probabilite", 2)
        # Mapper 1-4 → 0.1-0.9
        x = (prob - 1) / 3 * 0.8 + 0.1
        y = (impact - 1) / 3 * 0.8 + 0.1
        lines.append(f'    {code}-{mode}: [{x:.2f}, {y:.2f}]')
    
    return "\n".join(lines)
```

### Phase 3 (moyen terme) : Dashboard enrichi

Le dashboard Notion MYTHIQUE pourrait inclure :
1. Callout récap + 3 toggles (phases, risques, documents) — **existant**
2. **Bloc Mermaid logigramme** (code block ou embed image)
3. **Bloc Mermaid séquence** (si >2 acteurs)
4. **Bloc Mermaid quadrant** (si risques SBRX avec Impact/Probabilité remplis)
5. Callout bases liées — **existant**

## Références croisées

- `render_procedure.py` → lignes 74-188 : code des 3 générateurs existants
- `CEV-P02_MYTHIQUE.md` → lignes 73-96 (CRAIE), 247-297 (séquence), 381-404 (logigramme), 527-569 (quadrant ×2)
- `db_centric_v2_pipeline.md` → état actuel du pipeline (5 étapes, zéro diagramme)
- `post_pipeline_workflow.md` → étapes post-pipeline (SBRX, PMRI, FAQ, Rapport)
- `sequence_diagram_spec.md` → spécification détaillée du format sequenceDiagram

## Piège connu

**⚠️ Notion ne supporte pas le rendu Mermaid natif dans les code blocks.** Un code block `mermaid` s'affiche comme du texte brut, pas comme un diagramme visuel. Solutions :
1. **Export markdown** : le fichier .md généré par `render_procedure.py` sur GitHub/GitLab rend les Mermaid correctement
2. **Capture + embed** : générer le diagramme en image (via `mmdc` CLI ou Puppeteer) et l'uploader comme fichier Notion
3. **Lien externe** : pointer vers le fichier .md sur le repo GitHub pour voir les diagrammes rendus
4. **Embed service** : utiliser un service comme mermaid.ink pour générer des URLs d'image SVG (⚠️ dépendance externe)
