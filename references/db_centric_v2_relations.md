# DB-Centric V2 — Relations & Pipeline

## Base de données Notion

| BDD | ID | Relation inverse sur MYTHIQUE |
|:--|:--|:--|
| **DOX** | `3351d81e-4c39-827e-88a4-817c2739bbff` | — (hiérarchie source) |
| **MYTHIQUE** | `0a1689d5-ec35-4422-95cb-188a1dd35113` | Page hub, 32+ propriétés |
| **SBRX** (Risques) | `8e0efb57-8ac1-4a5d-9a6e-8a59431f9603` | `Procédures MYTHIQUE liées` → peuplé automatiquement |
| **PMRI** (Mesures) | `c153659b-ceab-409f-bf61-659557c9e62a` | `Procédures MYTHIQUE liées` → peuplé automatiquement |
| **GED MAIN** | `3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e` | `Procédures liées` → peuplé automatiquement |
| **FAQ** | `3c44d2d1-ee87-44ed-b991-bab4d1e94442` | ⚠️ **Pas de relation inverse** — liaison unidirectionnelle seulement |
| **Glossaire Main** | `1481d81e-4c39-808a-b304-fd1857c29329` | `Procédures mythiques liées` → peuplé automatiquement |
| **Exigences (G/C)** | `8e25465d-57b6-42cc-b082-879db77c8493` | `Procédures mythiques — règles` / `Procédures mythiques — consignes` |
| **Rapports lecture DOX** | `bca72a91-852e-48da-bcbb-b8ab60a67cc4` | champ relation `Mythique` |

## Champs relations sur MYTHIQUE

| Propriété MYTHIQUE | Type | BDD cible | Pipeline étape |
|:--|:--|:--|:--|
| `Risques liés` | Relation | SBRX | 3 |
| `Mesures PMRI` | Relation | PMRI | 3b |
| `FAQ liée` | Relation | FAQ | 3c (unidirectionnel) |
| `Glossaire lié` | Relation | Glossaire Main | 3d |
| `Règles de gestion liées` | Relation | Exigences (Type=Règle) | 3e |
| `Consignes de sécurité liées` | Relation | Exigences (Type=Consigne) | 3f |
| `Document GED` | Relation | GED MAIN | 4 |
| `Rédacteur` | Relation | Organigramme | 2 (défaut AVR) |
| `Validateur` | Relation | Organigramme | 2 (défaut AVR) |
| `Rapport de lecture` | Relation | Rapports lecture DOX | 4c |
| `Dernier rapport de lecture` | Relation | Rapports lecture DOX | 4c |

## Pipeline : `publish_procedure.py`

```text
Étape 1   🔍 DOX          → find_dox_entry(pid)
Étape 2   📄 MYTHIQUE      → create_mythique_page() — 32 propriétés
                           → Rédacteur/Validateur = AVR (12f1d81e)
                           → Dernière revue = date du jour
Étape 3   ⚠️ SBRX          → populate_sbrx(risks)
Étape 3b  📏 PMRI          → populate_pmri(mesures)
Étape 3c  ❓ FAQ            → populate_faq(faqs)
Étape 3d  📖 Glossaire     → parse_glossary() → populate_glossary()
Étape 3e  ⚖️ Règles        → parse_exigences("regles") → populate_exigences("Regle")
Étape 3f  🔒 Consignes     → parse_exigences("consignes") → populate_exigences("Consigne")
Étape 4   📁 GED           → populate_ged(documents) → lien FAQ liée + Document GED
Étape 4b  🔗 Inverses      → populate_relations_inverses()
Étape 4c  📖 Rapport zéro  → create_rapport_lecture() — état "Initial"
Étape 5   🎨 Dashboard     → build_dashboard_blocks() — 30+ blocs, 4 Mermaid
```

## Pitfalls

### FAQ BDD sans relation inverse
La BDD FAQ n'a **pas** de champ relation pour lier en retour vers MYTHIQUE. On ne peut peupler que `FAQ liée` sur MYTHIQUE (pas de `Procédure liée` sur FAQ). Si un jour Notion ajoute ce champ, il faudra créer un script de rétro-liaison.

### parse_documents séparateur `;` vs `\n`
`parse_documents()` utilise `split(";")` pour découper les documents. Les contrats générés par `build_contrat.py` utilisent `\n` comme séparateur, ce qui fait que seul le premier document est reconnu. Solution : modifier `parse_documents` pour accepter les deux séparateurs.

### Rich text + relations coexist
Les champs `Définitions & glossaire`, `Règles de gestion`, `Consignes opérationnelles` (rich_text) existent encore sur MYTHIQUE en parallèle des nouvelles relations. Le pipeline remplit les deux. Les rich_text peuvent être supprimés de `RICH_TEXT_PROPS` si l'on veut le mode 100% BDD.

### parse_glossary format attendu
Le champ `definitions` du contrat suit ce format :
```
**Terme :** Explication longue. Suite de l'explication.
**Autre terme :** Explication.
```
`parse_glossary()` découpe par `**` pour extraire les paires terme/texte.

### Dashboard duplication (Étape 5)
⚠️ **Chaque exécution du pipeline ajoute de nouveaux blocs dashboard sans supprimer les précédents**, car l'API Notion n'a pas d'endpoint "replace children". Résultat : le récapitulatif s'accumule à chaque traitement.
**Fix (appliqué 2026-08-04)** : avant d'ajouter les nouveaux blocs, le pipeline appelle `fetch_children(page_id)` (GET paginé) puis `delete_children(child_ids)` (DELETE séquentiel avec rate limiting). Pattern dans `publish_procedure.py` étape 5 :
```python
existing_children = fetch_children(page_id)
if existing_children:
    child_ids = [c["id"] for c in existing_children]
    delete_children(child_ids)
    time.sleep(BATCH_DELAY)
```
Ce code est encapsulé dans les helpers `fetch_children()` et `delete_children()` définis juste avant `build_dashboard_blocks()`.
Voir `references/notion_api_endpoints.md` pour les détails des endpoints utilisés.

### parse_exigences format attendu
Les champs `regles` (numéroté) et `consignes` (sections) :
```
1. Première règle. Suite de la règle.
2. Deuxième règle.
```
```
**Sécurité juridique** : Contenu de la consigne.
**Protection des données** : Contenu.
```
