# BDD DOX — Architecture Database-Centric (V2)

> Référentiel de l'architecture décidée le 2026-08-03 : passage du modèle **document-centric** au modèle **database-centric**.
> La BDD DOX (Missions-Processus) est la colonne vertébrale hiérarchique de tout le système.

---

## BDD DOX — Missions Processus

**ID Notion** : `3351d81e-4c39-827e-88a4-817c2739bbff`

### Propriétés

| Propriété | Type | Usage |
|-----------|------|-------|
| `Nom` | Title | Nom de l'entité (Mission, Processus ou Procédure) |
| `Code` | Rich text | Code hiérarchique (ex: `M1`, `M1-P3`, `M1-P3-01`) |
| `Niveau` | Select | `Mission` / `Processus` / `Procédure` |
| `Mission` | Select | `M1`, `M2`, `M3`, `M4`, `M5` |
| `Parent item` | Relation → DOX | Lien vers l'entité parente (auto-référence) |
| `Sub-item` | Relation ← DOX | Lien vers les entités enfants (auto-référence) |
| `Processus parent` | Relation | Processus rattaché |
| `Description` | Rich text | Description de l'entité |
| `Statut` | Select | Actif / Inactif / Archivé |

### Hiérarchie auto-référencée

```
Mission (M1)
  ├── Processus (M1-P1)
  │     ├── Procédure (M1-P1-01)
  │     └── Procédure (M1-P1-02)
  ├── Processus (M1-P2)
  │     ├── Procédure (M1-P2-01)
  │     └── Procédure (M1-P2-02)
  └── Processus (M1-P3)
        ├── Procédure (M1-P3-01)  ← M1-P3-01
        └── Procédure (M1-P3-02)
```

La relation `Parent item` (auto-référence) pointe vers le niveau supérieur :
- Procédure → Processus → Mission
- `Sub-item` est l'inverse (lien retour)

---

## Architecture Database-Centric

### Paradigme

| Avant (Document-Centric) | Après (Database-Centric) |
|--------------------------|--------------------------|
| Corps de page = 146 blocs de contenu | Corps de page = dashboard visuel |
| Données noyées dans le corps | Données = propriétés structurées |
| Sections = sous-titres dans le document | Sections = BDD dédiées liées par relation |
| Pas de référentiel central | DOX = arbre hiérarchique unique |
| Mermaid = inline dans le corps | Mermaid = image uploadée + BDD diagrammes |

### Composition de la page procédure

```
┌──────────────────────────────────────────────────────────────┐
│  ╔══════════════════════════════════════════════════════════╗  │
│  ║          ZONE PROPRIÉTÉS (Notion UI)                    ║  │
│  ║  Organisée en tabs/sections une fois dans le template   ║  │
│  ╠══════════════════════════════════════════════════════════╣  │
│  ║  [Info générales]   [Relations]   [Statut]   [Dates]   ║  │
│  ║  Titre              SBRX Risques   Statut     Création  ║  │
│  ║  Code               GED Docs       Version    Révision  ║  │
│  ║  Direction          Objet          Niveau               ║  │
│  ║  Mission (DOX)      Consignes                           ║  │
│  ║  Processus (DOX)    Règles                              ║  │
│  ║                     FAQ                                 ║  │
│  ║                     Mermaid                             ║  │
│  ╚══════════════════════════════════════════════════════════╝  │
│                                                                │
│  ╔══════════════════════════════════════════════════════════╗  │
│  ║        CORPS DE PAGE = DASHBOARD VISUEL                ║  │
│  ╠══════════════════════════════════════════════════════════╣  │
│  ║  # 🃏 Flash Card (callout)                              ║  │
│  ║  # 📊 Diagramme Mermaid (image)                         ║  │
│  ║  # 📋 Tableau synoptique (inline table)                  ║  │
│  ║  # 🎯 Vues liées SAM (héritées de la duplication)       ║  │
│  ║  # 🔗 Liens vers BDD sections (link_to_page)            ║  │
│  ╚══════════════════════════════════════════════════════════╝  │
└──────────────────────────────────────────────────────────────┘
```

### BDD du système

| BDD | ID Notion | Rôle | Relations |
|-----|-----------|------|-----------|
| **DOX** | `3351d81e-4c39-827e-88a4-817c2739bbff` | Arbre hiérarchique (Mission→Processus→Procédure) | Parent item auto |
| **MYTHIQUE** | `0a1689d5-...` | Dashboard des procédures | → toutes les BDD |
| **SBRX** | `8e0efb57-...` | Risques évalués | ← MYTHIQUE |
| **GED MAIN** | `3c36a4d6-...` | Documents supports | ← MYTHIQUE |
| **PMRI** | `6f39b3cc-...` | Mesures de maîtrise | ← MYTHIQUE |
| **FAQ** | `3c44d2d1-...` | Questions fréquentes | ← MYTHIQUE |
| **Glossaire** | `1481d81e-...` | Définitions & sigles | ← MYTHIQUE |
| **Objet** | *(à créer)* | Description & périmètre | ← MYTHIQUE |
| **Champ application** | *(à créer)* | Services concernés & exclusions | ← MYTHIQUE |
| **Consignes op.** | *(à créer)* | Consignes par étape | ← MYTHIQUE |
| **Règles de gestion** | *(à créer)* | Règles G1-G10 | ← MYTHIQUE |
| **Mermaid** | *(à créer)* | Diagrammes (logigramme, sequence, Gantt) | ← MYTHIQUE |

---

## Workflow de duplication

### Pourquoi la duplication ?

L'API Notion **ne peut pas** :
- Créer des vues liées (linked database views)
- Appliquer un template à une page existante
- Organiser l'affichage des propriétés en tabs

Le contournement : **créer une page modèle manuellement**, la dupliquer N fois, puis le pipeline remplit chaque duplicata.

### Étapes

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. CRÉATION DU TEMPLATE (utilisateur, UI Notion, 1 seule fois)    │
│                                                                     │
│  a. Créer une page dans BDD MYTHIQUE                               │
│  b. Configurer les propriétés en tabs/sections                     │
│  c. Ajouter les vues liées filtrées (SBRX, GED, Objet, etc.)      │
│     avec le filtre "Relation → Cette page"                         │
│  d. Ajouter les blocs visuels (callout Flash Card, emplacements    │
│     diagrammes, tableaux récapitulatifs)                           │
│  e. 🔖 Définir le code procédure (ex: TEMPLATE) dans les props    │
├─────────────────────────────────────────────────────────────────────┤
│  2. DUPLICATION (utilisateur, UI Notion, 2 clics × N)              │
│                                                                     │
│  a. Faire un clic droit sur la page template                       │
│  b. "Dupliquer" → répéter pour chaque procédure à créer            │
│  c. Renommer la copie (optionnel — le pipeline détectera par code) │
├─────────────────────────────────────────────────────────────────────┤
│  3. PIPELINE (Hermes, automatisé, N fois)                          │
│                                                                     │
│  V4.5  find_page_by_id.py → trouver la page par code_procedure    │
│  V6    sync_notion.py → mettre à jour les propriétés              │
│  V7    Créer/retrouver l'entrée DOX correspondante                │
│  V8    Créer les lignes dans SBRX, GED, Objet, Consignes...       │
│        (populate via API → vues liées du template les affichent)  │
│  V9    Générer/Remplacer les éléments visuels du dashboard        │
│        (callouts, tableaux, images Mermaid)                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Recherche de page existante

Le script `find_page_by_id.py` interroge la BDD MYTHIQUE filtrée par `"Code procédure"` (rich_text). Si trouvée → `PATCH` (update) ; sinon → `POST` (create).

**Propriété cible** : `code_procedure` (rich_text) — doit être remplie par `sync_notion.py` via `rich_text_keys`.

---

## API Notion — Capacités pour ce projet

### ✅ Possibles

| Opération | Endpoint | Notes |
|-----------|----------|-------|
| Créer une BDD | `POST /v1/databases` | Propriétés `title`, `rich_text`, `select`, `relation`, `date` |
| Créer une page | `POST /v1/pages` | Avec propriétés pour la BDD cible |
| Mettre à jour propriétés | `PATCH /v1/pages/{id}` | Pour alimenter les champs |
| Ajouter des blocs | `PATCH /v1/blocks/{id}/children` | Par lots de 50 (API Notion limite à 100) |
| Ajouter une relation | Propriété `relation` au format `[{id}]` | Dans create ou update |
| Uploader une image | `PATCH /v1/blocks/{id}/children` avec type `image` | Pour Mermaid rendu |
| Interroger BDD | `POST /v1/databases/{id}/query` | Avec filtres `property` + `rich_text`/`select` |

### ❌ Impossibles (contournements)

| Opération | Pourquoi | Contournement |
|-----------|----------|---------------|
| Créer une vue liée | Pas d'endpoint dans l'API | Duplication du template |
| Appliquer un template existant | Template = one-shot à la création | Duplication |
| Organiser les propriétés en tabs | Pas d'endpoint d'UI layout | Config Notion manuelle une fois |
| Ajouter un bloc `link_preview` | Type non supporté par API | `external` + `url` block |
| Ajouter un `embed` avec source BDD | Nécessite intégration n8n externe | Utiliser `link_to_page` block |

---

## Migration d'une procédure existante

Si une page procédure **existe déjà** avec du contenu en corps de page (ex: M1-P3-01, 146 blocs) :

1. **Option A** : Conserver la page, vider le corps, réorganiser les props, ajouter les relations. *Risque* : les vues liées ne peuvent pas être ajoutées.
2. **Option B (recommandée)** : Créer une page template propre, dupliquer, alimenter. L'ancienne page reste en archive/documentation.

---

## Intégration avec le pipeline existant

### notion_shared.py

Ajouter l'ID DOX dans les constantes :

```python
DOX_DATABASE_ID = "3351d81e4c39827e88a4817c2739bbff"
```

### V7 — Création DOX entry

```python
# Créer une entrée DOX si elle n'existe pas
def ensure_dox_entry(procedure_id, mission, processus, niveau="Procédure"):
    # Vérifier si l'entrée existe déjà
    # Sinon, créer avec les bonnes relations parent
    pass
```

### V8 — Peuplement sections BDD

Pour chaque section (SBRX, GED, Objet, etc.) :
1. Interroger la BDD section pour les entrées liées à cette procédure
2. Créer les entrées manquantes depuis les données du contrat
3. Ajouter la relation inverse vers la procédure MYTHIQUE

### V9 — Dashboard generation

Générer des blocs dans le corps de la page procédure :
- Callout métadonnées (Flash Card)
- Tableau inline synoptique (étapes)
- Image Mermaid (logigramme + sequence + Gantt)
- Callout liens vers BDD sections

---

## Pièges

- **⚠️ Duplication = héritage intégral** : toutes les vues liées, propriétés, blocs et filtres sont copiés. Le pipeline ne doit **pas** recréer les vues liées — seulement remplir les données que les vues existantes affichent.
- **⚠️ Filtre "Cette page"** : dans le template, les vues liées doivent utiliser le filtre `relation → Cette page` pour afficher uniquement les entrées de la procédure courante. Ce filtre est hérité par duplication.
- **⚠️ Pas de recréation de la page** : si la page existe déjà (après duplication), le pipeline fait un PATCH des propriétés, pas un DELETE+CREATE.
- **⚠️ Nombre de duplications** : pour 50+ procédures, la duplication UI est manuelle. Alternative : script de duplication via `POST /v1/pages` avec les mêmes parents/children. Mais les vues liées ne sont pas reproduites par API → nécessite une intervention UI une fois pour configurer le template.
- **⚠️ Sécurité des relations inverses** : quand le pipeline crée une ligne dans SBRX avec `relation: {procedure_id}`, il faut aussi mettre à jour la page procédure pour ajouter la relation inverse (SBRX). Notion gère les relations en **unidirectionnel** → il faut créer les deux côtés (`relation` dans les deux pages).
