# Architecture modulaire — Modules services + Pages Bus

> **Statut** : Partiellement implémenté (août 2026)
> - ✅ **PAGES BUS** : base créée, propriétés configurées, 4 entités initiales enregistrées
> - ✅ **Relations modules→Bus** : Glossaire Main, GED MAIN, Annuaire DOX liés bidirectionnellement
> - ✅ **Kanban Migration** : base créée avec 10 tickets de suivi
> - ⚠️ **Skills modules** : design validé, à extraire (voir kanban)
> - **Source** : Session août 2026 — implémentation de l'architecture modulaire multi-projets

## Le Pattern COMP (modèle canonique)

La base **DOX BDD - COMPOSANTS (Smart)** (`1e9c9e7b-8a6b-4d8a-942f-ee80a930b5f3`) est le modèle de conception pour tous les modules partagés. Ses caractéristiques :

- **16 composants** : diagrammes Mermaid, templates, registres
- **Auto-suffisant** : chaque page contient son ID canonique, sa version, son contrat, son contenu
- **Aucune relation mono-projet** : pas de `Procédures liées` ou `CR liés` — c'est un registre pur
- **Consumer Policy** : champ rich_text qui décrit comment utiliser le composant
- **Versionné** : champ `Version` (ex: `DOX:v10 FDL`)
- **Contract-driven** : champ `DOX Contract` avec le contrat complet FDL

### Schéma COMP

| Propriété | Type | Rôle |
|:--|:--|:--|
| `Composant` | title | ID canonique |
| `Component ID` | rich_text | Identifiant technique |
| `Component Type` | select | Mermaid, Template, Runtime Contract, Risk Matrix... |
| `Description` | rich_text | Descriptif |
| `Consumer Policy` | rich_text | Mode d'emploi pour les consommateurs |
| `DOX Contract` | rich_text | Contrat FDL complet |
| `Template Family` | rich_text | Famille de template |
| `Version` | rich_text | Version DOX |
| `Layer` | select | Property Contract / Body Representation / Fused Dual Layer |
| `Last QG` | select | GO, GO_RESERVES, NO_GO, PENDING |
| `Statut` | status | État du composant |
| `Source of Truth` / `No Local Copy` / `Resync Required` | checkbox | Gouvernance |

## Architecture modulaire proposée (DB-Centric V3)

Chaque domaine partagé devient un **module autonome** calqué sur COMP :

```
📦 Module COMP (existant)        📦 Module Glossaire (à extraire)
├── DB: DOX BDD - COMPOSANTS      ├── DB: Glossaire Main
├── Skill: (dans pipeline)         ├── Skill: glossaire.skill
└── API: find_component()          └── API: add_term(), search_term()

📦 Module GED (à extraire)        📦 Module Annuaire (à extraire)
├── DB: GED MAIN                   ├── DB: Annuaire DOX
├── Skill: ged.skill               ├── Skill: annuaire.skill
└── API: add_doc(), find_by_code() └── API: find_person(), add_person()

📦 Module FAQ (à extraire)        📦 Module Pages Bus (à créer)
├── DB: FAQ Métier                 ├── DB: DOX BDD - PAGES BUS (Smart)
├── Skill: faq.skill               ├── Skill: pages-bus.skill
└── API: add_faq(), search_faq()   └── API: register(), link()
```

### Le Pages Bus (liant inter-projets)

Pour résoudre la limitation de Notion (une relation pointe vers UNE SEULE base), on introduit une **base Pages Bus** sur le modèle COMP :

```
DOX BDD - PAGES BUS (Smart)  [ID: 3b21d81e-4c39-81fe-b6f9-c9b661368c7a]
├── Nom page (title) — "M1-P3-01", "CR #42", "Projet Alpha"
├── ID canonique (rich_text) — PAGE.M1.P3.01
├── Type entité (select) — Procédure, CR, GTD, Projet...
├── Version (rich_text)
├── Description (rich_text)
├── Statut (select) — Active, Archivé, Migration...
├── Consumer Policy (rich_text)
└── Relations inverses → (auto-générées par les modules)
```

Chaque module partagé a **un seul champ relation** : `Pages liées (Bus)` → Pages Bus.
Plus besoin d'ajouter un champ relation par nouveau projet.

Quand un pipeline crée une entité (procédure, CR, projet GTD) :
1. Enregistre l'entité dans Pages Bus → obtient un `page_id`
2. Linke les ressources partagées via ce `page_id` vers les modules
3. Les modules n'ont jamais besoin de connaître le type du projet

### ⚠️ API Notion — dual_property et inverses invisibles

Lors de la création des relations `Pages liées (Bus)` sur chaque module, la syntaxe API est :

```python
"Pages liées (Bus)": {
    "type": "relation",
    "relation": {
        "database_id": "3b21d81e-4c39-81fe-b6f9-c9b661368c7a",
        "dual_property": {"property_name": "Pages liées (Bus)"}
    }
}
```

**Comportement constaté** : la propriété inverse est créée sur PAGES BUS avec un nom auto-généré (ex: `From Pages liées (Bus) (Glossaire Main)`) mais n'apparaît PAS dans `GET /v1/databases/3b21d81...`. Elle est fonctionnelle au niveau page mais invisible dans le schéma GET de l'API.

**Implication** : Impossible de renommer les inverses via l'API. Solution : soit les renommer manuellement dans l'interface Notion, soit les laisser en l'état. Voir `references/pitfalls.md` #12 pour le détail.

### Relations existantes (août 2026)

| Module | DB ID | Champ relation | Valeur nom |
|:--|:--|:--|:--|
| Glossaire Main | `1481d81e-4c39-808a-b304-fd1857c29329` | `Pages liées (Bus)` → PAGES BUS | ✅ |
| DOX BDD - GED MAIN | `3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e` | `Pages liées (Bus)` → PAGES BUS | ✅ |
| Annuaire DOX | `6e9d978c-b165-490c-a6c5-a4de5eaa5e56` | `Pages liées (Bus)` → PAGES BUS | ✅ |

> Les anciennes relations mono-projet (`Procédures mythiques liées`, `Procédures liées`, `Procédures Rédigées`) sont conservées pour compatibilité pendant la migration. Elles seront supprimées une fois que tous les pipelines utiliseront le Bus.

### Kanban Migration

Pour suivre la transition, créer une **base KANBAN Migration** dédiée (ID: `3b21d81e-4c39-81e7-8c08-f6b9c05f6a54`) :

| Propriété | Type | Rôle |
|:--|:--|:--|
| `Nom tâche` | title | Intitulé de la tâche de migration |
| `Statut` | select | À faire, En cours, Bloqué, Fait |
| `Priorité` | select | Haute, Moyenne, Basse |
| `Module` | select | Glossaire, GED, Annuaire, FAQ, Pages Bus, Pipeline |
| `Description` | rich_text | Détails |
| `Pages liées` | relation | → PAGES BUS (optionnel) |

Dans Notion, ajouter une **vue Kanban** groupée par `Statut` pour un tableau visuel.

**Entrées initiales** (10 tickets créés août 2026) :
- Créer 4 skills Hermes (glossaire.skill, ged.skill, annuaire.skill, faq.skill)
- Extraire les fonctions de publish_procedure.py vers chaque skill
- Adapter publish_procedure.py pour importer depuis les skills
- Créer pages-bus.skill
- Tester le pipeline avec Pages Bus
- Supprimer les anciennes relations mono-projet

### Skills Hermes par module

Chaque module est encapsulé dans un **skill Hermes** réutilisable :

```
glossary.skill → add_terms(terms[], page_id)
  Ajoute des termes au glossaire et les lie à page_id via Pages Bus.

annuaire.skill → find_person(nom) → page_id | None
  Cherche une personne dans l'annuaire et retourne son ID Notion.

ged.skill → add_documents(docs[], page_id)
  Crée les entrées document dans GED MAIN et les lie à page_id.

faq.skill → add_questions(questions[], page_id)
  Ajoute les FAQ et les lie à page_id.

pages-bus.skill → register_entity(nom, type) → page_id
  Crée l'entrée dans Pages Bus et retourne l'ID pour les relations.
```

## Migration depuis l'architecture actuelle

### Étape 1 : Créer Pages Bus
Base Notion avec `Nom page` (title), `Type page` (select), `Page ID canonique` (rich_text).

### Étape 2 : Ajouter `Pages liées` dans chaque module
- Glossaire Main : remplacer `Procédures mythiques liées` → `Pages liées`
- GED MAIN : remplacer `Procédures liées` → `Pages liées`
- Annuaire DOX : remplacer `Procédures Rédigées` → `Pages liées`
- FAQ Métier : ajouter `Pages liées`
- MYTHIQUE : conserver les champs actuels (`Mesures PMRI`, `Risques liés`, `FAQ liée`) pour lisibilité dashboard

### Étape 3 : Extraire les skills Hermes
- Extraire `populate_glossary()` de publish_procedure.py → `glossary.skill`
- Extraire `add_documents()` → `ged.skill`
- Extraire `find_person()` / `query_database` → `annuaire.skill`
- Extraire `add_faq()` → `faq.skill`

### Étape 4 : Adapter le pipeline procédures
- `publish_procedure.py` importe depuis les skills au lieu de fonctions inline
- Crée l'entrée Pages Bus avant de lancer les satellites
- Passe le `page_id` Pages Bus à toutes les fonctions populate

## Avantages du passage en modulaire

| Aspect | Avant (mono-projet) | Après (modulaire) |
|:--|:--|:--|
| Relations | 1 champ par projet | 1 champ unique (`Pages liées`) |
| Ajout nouveau projet | Modifier N bases | Créer une entrée Pages Bus |
| Extraction skill | Fonctions dans pipeline | Skill Hermes autonome |
| Réutilisabilité | Faible (liée aux procédures) | Haute (CR, GTD, Projets...) |
| Couplage | Fort (relations dédiées) | Faible (via Pages Bus) |
