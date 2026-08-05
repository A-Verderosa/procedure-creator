# BDD COMP (COMPOSANTS) — Référentiel des composants réutilisables

## Identifiants

- **Database ID** : `1e9c9e7b-8a6b-4d8a-942f-ee80a930b5f3`
- **Type** : database (API `/v1/databases/{id}/query`)
- **Propriétaire** : aveconsultings Notion workspace

## Rôle

La BDD COMP est le **point unique de vérité pour les composants réutilisables** : diagrammes Mermaid, templates DOX, registres, et blocs fonctionnels. Chaque composant est une spécification normative qui définit la grammaire, les règles de validation (QG) et les bonnes pratiques.

**Hiérarchie dans la doctrine PROC** : Source ⭐ — au-dessus des 3 sources traditionnelles.

## Inventaire complet (16 composants)

### Diagrammes Mermaid (10)

| Composant | Usage | Niveau requis |
|-----------|-------|---------------|
| `COMP.MERMAID.SEQUENCE_MULTI_ACTOR` | Diagramme de séquence multi-acteur (interactions chronologiques) | Ultra+ |
| `COMP.MERMAID.SWIMLANE_MULTI_ACTOR` | Couloirs d'acteurs BPMN-like | Or+ |
| `COMP.MERMAID.PROCEDURE_FLOW` | Flowchart logigramme + étapes | Argent+ |
| `COMP.MERMAID.RUNTIME_LOOP_DOD_QG_L2` | Boucle runtime + DoD + QG L2 | Platine+ |
| `COMP.MERMAID.GANTT_TIMELINE` | Planning de déploiement (timeline/Gantt) | Platine+ |
| `COMP.MERMAID.SANKEY_FLOW_LOSS` | Flux et déperdition des dossiers | Mythique |
| `COMP.MERMAID.DATABASE_RELATION_FLOW` | Relations entre BDD/entités | Platine+ |
| `COMP.MERMAID.RISK_MATRIX_PI` | Matrice de criticité risques | Platine+ |
| `COMP.MERMAID.ROUTING_MAP` | Routage et décisionnel | Or+ |
| `COMP.MERMAID.CANON` | Chaîne de résolution canonique | Akuma |

### Composants DOX (3)

| Composant | Usage 
|-----------|-------|
| `CMP-DOX-BLOCK-LIBRARY` | Bibliothèque de blocs DOX réutilisables (PHASE_HUMAN_LAYER, etc.) |
| `CMP-PDT-DUAL-LAYER-TEMPLATE` | Gabarit standard PDT Dual Layer DOX |
| `CMP-PDT-ANTI-REGRESSION` | Checklist anti-régression PDT |

### Registres (3)

| Composant | Usage |
|-----------|-------|
| `U1` | Navigation bidirectionnelle |
| `M3` | Radar de criticité RB/RN/RC |
| `BADGE` | Activation ULTRA |

## Règles d'utilisation

1. **Toujours consulter le composant COMP avant de produire un diagramme Mermaid** — ne jamais produire un sequenceDiagram sans vérifier SEQUENCE_MULTI_ACTOR
2. **Ne pas modifier les composants COMP** — ce sont des normes ; les adapter dans le template de la procédure, pas dans la source
3. **QG spécifique au composant** — chaque composant COMP définit ses propres quality gates (ex: SEQ_QG pour sequenceDiagram)
4. **Les 9 briques MYTHIQUE (M1→M9)** sont documentées dans le composant COMP.MERMAID et instanciées dans CGSS 118 MYTHIQUE §23
5. **Pour le niveau Mythique** : intégrer les composants correspondant aux briques M1→M9 (Bow-tie, Ishikawa, Radar, Swimlane, SIPOC, Sankey, Timeline, Cockpit KPI, Heatmap RACI)

## Consultation via API

```python
import os, requests
headers = {'Authorization': f'Bearer {os.environ["NOTION_API_KEY"]}', 
           'Notion-Version': '2022-06-28'}

# Lister les composants
r = requests.post('https://api.notion.com/v1/databases/1e9c9e7b-8a6b-4d8a-942f-ee80a930b5f3/query',
                  headers=headers, json={'page_size': 100})

# Lire le contenu d'un composant spécifique
page_id = '<id_du_composant>'
blocks = requests.get(f'https://api.notion.com/v1/blocks/{page_id}/children',
                      headers=headers, params={'page_size': 100})
```
