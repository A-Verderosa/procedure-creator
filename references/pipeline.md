# Pipeline DB-Centric V2 (9 étapes)

## Étapes

| # | Étape | Fonction(s) | BDD cible |
|---|-------|-------------|-----------|
| 1 | Entrée DOX | `find_dox_entry()` | DOX |
| 2 | Page MYTHIQUE | `create_or_update_mythique()` | MYTHIQUE |
| 3 | Risques SBRX | `parse_risks()` → `populate_sbrx()` | SBRX |
| 3b | Mesures PMRI | `populate_pmri()` | PMRI |
| 3c | FAQ | `populate_faq()` | FAQ |
| 3d | Glossaire | `parse_glossary()` → création termes | Glossaire Main |
| 3e | Règles de gestion | `parse_exigences(type="Règle")` | Exigences |
| 3f | Consignes de sécurité | `parse_exigences(type="Consigne")` | Exigences |
| 4 | Documents GED | `parse_documents()` → `populate_ged()` | GED MAIN |
| 4b | Relations inverses | mise à jour champ relation MYTHIQUE | SBRX, PMRI, FAQ |
| 4c | Rapport de lecture | création état zéro dans BDD RAPPORTS LECTURE DOX | RAPPORTS LECTURE DOX |
| 5 | Dashboard | `build_dashboard_blocks()` → nettoyage + ajout | MYTHIQUE (body) |

## Scripts clés

- `publish_procedure.py` — orchestre tout le pipeline
- `render_procedure.py` — génère les blocs dashboard (incl. `generate_risk_matrix()` en quadrantChart Mermaid)
- `notion_shared.py` — connecteurs API Notion, IDs BDD
- `create_satellite_pages.py` — création pages satellites
- `create_related_pages.py` — création pages liées (Glossaire, Exigences, GED)

## Détail des champs écrits par satellite

### SBRX — populate_sbrx() écrit 7 champs
| Champ Notion | Type | Source contrat |
|---|---|---|
| Titre | title | risks_detail[i].title |
| Code risque | rich_text | risks_detail[i].code |
| Procédure Mère | relation | page_id MYTHIQUE |
| Impact | number | risks_detail[i].impact |
| Probabilité | number | risks_detail[i].probability |
| Hypothèse RC | rich_text | risks_detail[i].hyp_rc |
| Hypothèse RN | rich_text | risks_detail[i].hyp_rn |

AVANT août 2026 : seuls Titre + Code + Procédure Mère étaient écrits (cf. pitfalls #8-#9).

### PMRI — populate_pmri() écrit jusqu'à 9 champs
| Champ Notion | Type | Source contrat | Mapping |
|---|---|---|---|
| Titre | title | pmri_mesures[i].titre | — |
| Procédure Source | relation | page_id MYTHIQUE | — |
| Risque Traité | relation | pmri_mesures[i].risque_code → page SBRX | — |
| Effet attendu sur impact | number | pmri_mesures[i].effet_impact | — |
| Effet attendu sur probabilité | number | pmri_mesures[i].effet_probabilite | — |
| Famille de mesure | multi_select | pmri_mesures[i].famille | Direct (mêmes valeurs) |
| Fréquence contrôle | select | pmri_mesures[i].frequence_controle | Quotidien→Quotidienne, Mensuel→Mensuelle, Annuel→Annuelle, Trimestriel→Trimestrielle |
| Type contrôle | select | pmri_mesures[i].type_controle | Automatique→Préventif, Manuel→Détectif, Semi-automatique→Détectif |
| Responsable | relation | pmri_mesures[i].responsable | Cache de recherche dans base contacts (vide par défaut — créer les entrées avant) |

AVANT août 2026 : seuls Titre + Procédure Source + Risque Traité + Effets étaient écrits.

### Enrichissement rétroactif (PATCH)
Les deux populate_* détectent les pages existantes et exécutent une mise à jour (PATCH) des champs manquants. Le pipeline peut être relancé sur une procédure déjà créée :

    python3 scripts/publish_procedure.py /data/contrat_M1-P3-XX.json --publish

## Fonctions importantes

### parse_documents(contract)
Parse `documents_supports` ET `documents_reference` depuis le contrat.
- **Séparateurs** : `;` ou `\n` (auto-détection)
- **Codes** : regex `[A-Z]+-?\d+` (chiffres obligatoires) — ne capture pas les mots simples
- **Prefixes automatiques** : supports → `D1..DN`, références → `REF1..REFN`
- **Catégorie** : chaque doc reçoit un champ `category` qui alimente `Catégorie` (select) dans GED MAIN

### populate_ged(documents, mythique_page_id, token)
Crée les entrées documents dans GED MAIN, liées à la procédure.
- Supporte le champ `category` pour remplir `Catégorie` (select)
- Documents support → `"Document support"` 
- Documents référence → pas de catégorie (identifiable via code REF-)

### build_dashboard_blocks(page_id, contract, ...)
Génère les blocs Notion du dashboard MYTHIQUE (11+ blocs, 4 diagrammes Mermaid).
- Appelle `fetch_children(page_id)` avant d'ajouter pour supprimer les anciens blocs
- Appelle `delete_children(block_ids)` avec rate limiting (BATCH_DELAY)
- Phases : affichées comme `"Phase N — Titre"` (heading_3), pas le nom nu

### fetch_children(page_id)
Récupère tous les blocs enfants d'une page Notion (pagination 100 par 100).
Utilise `notion_request("GET", url)` (token auto depuis env).

### delete_children(block_ids)
Supprime une liste de blocs enfants. Rate limiting : 350ms entre chaque.
Utilise `notion_request("DELETE", url)` (token auto depuis env).

## parse_risks(contract)
Support **deux formats** :
1. Texte libre : champ `risques` — chaque ligne parsée comme un risque
2. Structuré : champ `risks_detail` — liste de dicts avec code, title, impact, probability, description, hyp_rc, hyp_rn

⚠️ AVANT août 2026 : seuls `code` et `title` étaient extraits du format structuré — `impact`, `probability`, `hyp_rc`, `hyp_rn` étaient jetés par le parseur.
Désormais : `parse_risks()` propage **tous les champs** de `risks_detail` vers `populate_sbrx()`.

Contrat type avec `risks_detail` complet :
```json
"risks_detail": [
  {"code": "R1", "title": "Délai de traitement non respecté",
   "impact": 3, "probability": 3, "description": "...",
   "hyp_rc": "Backlog de saisines non traitées",
   "hyp_rn": "Saisine traitée avec accusé réception automatisé"}
]
```

## Contrat JSON type

```json
{
  "procedure": {
    "code": "M1-P3-02",
    "titre": "Titre de la procédure",
    "domaine": "...",
    "direction": "...",
    "phases": [
      {"numero": "Phase 1", "titre": "Réception", "acteur": "...", "delai": "...", "actions": "...", "documents": "...", "vigilance": "..."}
    ],
    "documents_supports": "- Doc 1\n- Doc 2",
    "documents_reference": "- Ref A\n- Ref B",
    "risks_detail": [{"code": "R1", "title": "...", "impact": 3, "probability": 3, "description": "..."}],
    "definitions": ["Terme: Définition", ...],
    "regles_de_gestion": ["Règle 1", ...],
    "consignes_de_securite": ["Consigne 1", ...],
    "faq": [{"question": "...", "reponse": "..."}],
    "mesures": ["Mesure 1", ...]
  }
}
```
