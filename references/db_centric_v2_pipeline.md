# DB-Centric V2 — Pipeline Notion-Native

**Date** : 2026-08-04 (màj 2026-08-04: 8 étapes, 30+ blocs, PMRI + FAQ intégrés)
**Statut** : Actif (remplace `verrouiller.sh` pour les procédures Évaluateur)

## Architecture

La procédure n'existe plus en corps de page. Chaque section devient :
- **Propriété rich_text** dans la page MYTHIQUE (Objet, Champ d'application, Consignes, Règles, etc.)
- **Entrée dans une BDD satellite** liée par relation (SBRX→risques, GED→documents, PMRI→mesures, FAQ)
- **Dashboard visuel** dans le corps de page (30+ blocs : callouts + diagrammes Mermaid + toggles)

## BDD existantes (zéro création)

| BDD | ID Notion | Rôle |
|-----|-----------|------|
| **DOX** | `3351d81e-4c39-827e-88a4-817c2739bbff` | Hiérarchie Mission→Processus→Procédure |
| **MYTHIQUE** | `0a1689d5-ec35-4422-95cb-188a1dd35113` | Page hub avec 32 propriétés (rich text, relations) |
| **SBRX** | `8e0efb57-8ac1-4a5d-9a6e-8a59431f9603` | Risques |
| **GED MAIN** | `3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e` | Documents |
| **PMRI** | `6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9` | Mesures |
| **FAQ** | `3c44d2d1-ee87-44ed-b991-bab4d1e94442` | Questions / FAQ (pool global, pas de relation vers MYTHIQUE) |
| **Glossaire** | `1481d81e-4c39-808a-b304-fd1857c29329` | Définitions |
| **Annuaire Global** | `12f1d81e-4c39-8122-bffe-d61e547e9ea9` | Contacts (Rédacteur, Validateur) |

## Script : `scripts/publish_procedure.py`

Pipeline en **8 étapes** (ne pas utiliser `verrouiller.sh` pour l'Évaluateur) :

```
usage: python3 scripts/publish_procedure.py <contrat.json> [--publish]
```

### Étapes

| Étape | Nom | Description |
|-------|-----|-------------|
| 1 🔍 | **DOX** | Trouve l'entrée hiérarchique par code procédure |
| 2 📄 | **MYTHIQUE** | Trouve ou crée la page. Met à jour les 32 propriétés (rich text + selects + relations) |
| 3 ⚠️ | **SBRX** | Parse les risques (texte `risques` ou struct `risks_detail`) et crée les entrées liées avec cotations P×I |
| 3b 📏 | **PMRI** | Parse `pmri_mesures` et crée les mesures liées aux risques (avec effet sur Impact/Probabilité) |
| 3c ❓ | **FAQ** | Parse `faq` et crée les entrées dans le pool global FAQ |
| 4 📁 | **GED** | Parse `documents_supports` (catégorie "Document support") et `documents_reference` (catégorie "Document référence"), crée les entrées GED liées. Regex code : `[A-Z][A-Z0-9-]*\d+` (capte CEV-F01, D1, REF1). Séparateur : `;` ou `\n`. |
| 4b 🔗 | **Relations inverses** | Met à jour `Risques liés` (←SBRX) et `Mesures PMRI` (←PMRI) sur la page MYTHIQUE |
| 5 🎨 | **Dashboard** | Nettoie les anciens blocs (fetch_children + delete_children) puis ajoute 30+ blocs visuels (callout récap → 4 diagrammes Mermaid → phases → risques → liens satellites → documents) |

### Dashboard — 30+ blocs

- Callout récapitulatif (code, niveau, statut, service, périodicité)
- 🗺️ **Carte CRAIE** (flowchart LR — localisation dans l'organigramme)
- 📋 **Logigramme** (flowchart TB — enchaînement des phases)
- 👥 **Diagramme de séquence** (acteurs × phases)
- 📊 **Matrice des risques** (quadrantChart P×I — modes RB brut / RN net avec fusion des risques aux mêmes coordonnées)
- Détail des phases (callout par phase avec titre, délai, acteurs, vigilance)
- Callout risques (liens SBRX)
- Callout bases liées (PMRI, FAQ, GED)
- Documents (liste depuis GED)

## Fonctions clés

| Fonction | Rôle |
|----------|------|
| `find_dox_entry(pid, token)` | Cherche l'entrée DOX par code |
| `find_mythique_page(pid, token)` | Cherche la page MYTHIQUE par "Code procédure" |
| `create_mythique_page(pid, contract, dox, token)` | Crée une page MYTHIQUE propre avec toutes les propriétés |
| `build_properties(contract, dox)` | Construit le payload Notion des 32 propriétés |
| `populate_sbrx(risks, page_id, token)` | Crée les entrées SBRX liées |
| `populate_pmri(mesures, page_id, sbrx_map, token)` | Crée les mesures PMRI liées aux risques |
| `populate_faq(faqs, token)` | Crée les FAQ (pool global — pas de relation) |
| `populate_ged(documents, page_id, token)` | Crée les entrées GED liées avec catégorie (Document support / Document référence) |
| `update_reverse_relations(page_id, sbrx_pages, pmri_pages, token)` | Met à jour Risques liés + Mesures PMRI sur MYTHIQUE |
| `build_dashboard_blocks(contract, sbrx, pmri, ged)` | Génère les 30+ blocs du dashboard (4 diagrammes Mermaid) |
| `fetch_children(page_id)` | Récupère tous les blocs enfants d'une page (GET paginé) |
| `delete_children(block_ids)` | Supprime une liste de blocs (DELETE séquentiel avec rate limiting) |
| `generate_risk_matrix(risks, mode)` | Génère quadrantChart P×I (RB/RN/RC, fusion, légende) |
| `notion_get/post/patch/delete` | Wrappers HTTP pour l'API Notion |

## Mapping propriétés MYTHIQUE

| Contrat JSON | Propriété Notion | Type |
|-------------|-----------------|------|
| `titre` | Titre | title |
| `procedure_id` | Code procédure | rich_text |
| `service` | Service | select |
| `statut` | Statut | status (🔲🚧✅) |
| `niveau` | Niveau DOX | select (🔮/💎🥇🥈🥉) |
| `objet` | Objet | rich_text |
| `champ_application` | Champ d'application | rich_text |
| `consignes` | Consignes opérationnelles | rich_text |
| `regles` | Règles de gestion | rich_text |
| `definitions` | Définitions & glossaire | rich_text |
| `acteurs` | Acteurs responsables | rich_text |
| `documents_reference` | Documents de référence | rich_text | Listé en `\n` bullet (`- Titre\n- ...`) pour parse par GED |
| `documents_supports` | Documents support | rich_text |
| `risques` | Analyse des risques | rich_text |
| `periodicite_revue` | Périodicité revue | select |
| `version` | Version | rich_text |
| (dox_entry id) | Hiérarchie DOX | relation → DOX |

## Liste RICH_TEXT_PROPS (publish_procedure.py)

Ces champs sont automatiquement traités comme `rich_text` dans `build_properties` :

```python
RICH_TEXT_PROPS = [
    "objet", "champ_application", "definitions", "acteurs",
    "consignes", "regles", "documents_reference", "documents_supports",
]
```

Tout champ de cette liste présent dans le contrat JSON est envoyé comme propriété rich_text Notion.

## Structure du contrat JSON

```json
{
  "procedure": {
    "procedure_id": "M#-P#-##",
    "titre": "...",
    "description": "...",
    "niveau": "mythique",
    "mission": "...",
    "processus": "...",
    "service": "...",
    "version": "1.0",
    "objet": "...",
    "champ_application": "...",
    "definitions": "...",
    "acteurs": "...",
    "regles": "...",
    "consignes": "...",
    "documents_reference": "...",
    "documents_supports": "...",
    "periodicite_revue": "Semestrielle",
    "statut": "À faire",
    "phases": [...],
    "risks_detail": [
      {"code": "R1", "title": "...", "impact": 3, "probabilite": 2}
    ],
    "pmri_mesures": [
      {"titre": "...", "risque_code": "R1", "effet_impact": -1, "effet_probabilite": -1}
    ],
    "faq": [
      {"question": "...", "reponse": "...", "categorie": "..."}
    ]
  }
}
```

## Pièges

- **Relations inverses** : Toujours vérifier que `Risques liés` et `Mesures PMRI` sont peuplés sur MYTHIQUE après publication. L'étape 4b le fait automatiquement depuis la màj 2026-08-04.
- **SBRX** : Attend `Titre` (title) et `Code risque` (rich_text). Les cotations `Impact` et `Probabilité` sont des `number`.
- **PMRI** : La `Procédure Source` (relation vers MYTHIQUE) et `Risque SBRX source` (relation vers SBRX) doivent être peuplées. `Effet attendu sur impact/probabilité` sont des `number` (valeurs -1, 0, +1).
- **GED** : Attend `Code & Document` (title), pas `Titre`.
- **FAQ** : Pool global — pas de relation vers MYTHIQUE (FAQ liée toujours vide). La BDD FAQ n'a que `Question` (title) et `Réponse` (rich_text).
- **Doc GED** : La BDD GED a une propriété `Documents supports` de type relation. L'inverse sur MYTHIQUE (`Documents support`) est un `rich_text`, pas une relation.
- **Statut** : type `status` Notion (pas `select`) — valeurs avec émojis : 🔲 À faire, 🚧 En cours, ✅ Validée.
- **Périodicité revue** : select avec options : Mensuelle, Trimestrielle, Semestrielle, Annuelle, À événement, Non définie.
- **Relation DOX** : La propriété `Hiérarchie DOX` doit exister dans MYTHIQUE avant le run.
- **DOX préexistant** : L'entrée DOX doit exister avant le run.
- **Dashboard duplication** : Chaque exécution ajoutait de nouveaux blocs sans supprimer les précédents (l'API Notion n'a pas de "replace children"). **Depuis 2026-08-04** : le pipeline appelle `fetch_children(page_id)` puis `delete_children(child_ids)` avant d'ajouter les nouveaux blocs. Voir `references/notion_api_endpoints.md` pour les détails des endpoints.
- **Rate limiting** : 300ms entre chaque appel API (`BATCH_DELAY`).
- **Rédacteur / Validateur** : Relations vers l'Annuaire Global — non automatisées par le pipeline (nécessite une intervention manuelle ou une sélection depuis l'Annuaire).
- **Rapport de lecture** : La BDD Rapports de Lecture a une relation `Procédure mythique` vers MYTHIQUE, mais l'inverse n'est pas automatiquement populaire (champs `Rapport de lecture` et `Dernier rapport de lecture` sur MYTHIQUE). À mettre à jour manuellement si un rapport existe.
