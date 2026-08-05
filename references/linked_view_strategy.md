# Stratégie VUES LIÉES — Tableaux inline depuis le contrat

## Évolution : `link_to_page` → Tableaux inline

**2026-08-05** : L'approche `link_to_page` a été abandonnée. L'utilisateur a rejeté les simples liens cliquables vers les bases satellites : « Il manque la vue liée à la base de données des risques. » → Solution : **générer des tableaux récapitulatifs inline** directement dans le markdown, alimentés par les données du contrat.

## Solution actuelle : `generate_satellite_summary_tables()`

Dans `render_procedure.py`, la fonction `generate_satellite_summary_tables(md_content, contract)` :

1. Parse les blobs texte du contrat (risques, documents_supports, faq, mesures_pmri)
2. Génère un tableau markdown par satellite (format Notion-compatible)
3. Supprime les anciens commentaires `<!-- LINKED_VIEW:xxx -->`
4. Insère les tableaux dans la section SAM (avant `## 12. HISTORIQUE`)
5. Ajoute un paragraphe "🔗 Données alimentées depuis la base XXX" sous chaque tableau

Ces tableaux sont automatiquement convertis en blocs `table` Notion par `_markdown_to_notion_blocks()` — pas besoin de `link_to_page`.

### Exemple de rendu

```markdown
### 🛡️ Risques SBRX liés

| Code | Risque |
|------|--------|
| **R1** | Non-respect du délai de traitement |
| **R2** | Saisine incomplète non détectée |

*🔗 Données alimentées depuis la base SBRX MYTHIQUE*

---

### 📄 Documents GED liés

| Document |
|----------|
| Registre des saisines |
| Modèle d'accusé réception |

*🔗 Données alimentées depuis la base GED MAIN*
```

### Résultat sur Notion

```
[136] heading_3        🛡️ Risques SBRX liés
[137] table            table (2 cols) × [5 rows]    ← 4 risques + 1 en-tête
[138] paragraph        🔗 Données alimentées depuis la base SBRX MYTHIQUE
[139] divider          ———
[140] heading_3        📄 Documents GED liés
[141] table            table (1 cols) × [5 rows]    ← 4 docs + 1 en-tête
[142] paragraph        🔗 Données alimentées depuis la base GED MAIN
```

**Total : 150 blocks** sur Notion (contre 146 avant, les 4 blocs supplémentaires sont headings + tables + paragraphs).

## Mapping satellite → bases Notion

| Marqueur | BDD | Nom Notion | database_id |
|---|---|---|---|
| `risques` | SBRX MYTHIQUE | DOX BDD - SBRX MYTHIQUE | `8e0efb57-8ac1-4a5d-9a6e-8a59431f9603` |
| `documents` | GED MAIN | DOX BDD - GED MAIN | `3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e` |
| `mesures_pmri` | PMRI MYTHIQUE | DOX BDD - PMRI MYTHIQUE | `6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9` |
| `faq` | FAQ METIER | DOX BDD - FAQ METIER | `3c44d2d1-ee87-44ed-b991-bab4d1e94442` |

## Parsing des données contrat

### Risques (format blob texte)

Le contrat stocke les risques dans un champ texte `risques`. Formats rencontrés :

```
# Format standard
R1: Non-respect du délai de traitement; R2: Saisine incomplète

# Avec préfixe
4 risques (R1-R4) cotés P×I. R1: Non-respect du délai de traitement; R2: ...
```

**Regex de nettoyage** (utilisé dans `build_placeholder_map` et `generate_satellite_summary_tables`) :
```python
risques_txt_clean = re.sub(r'^.*?(?=R\d+\s*[:])', '', risques_txt)
```
Ce regex supprime tout le texte avant le premier "R1:" (ou "R2:", etc.) en utilisant une lookahead non-greedy.

**Split** : `;` (point-virgule). Attention : le split peut inclure des `;` dans les descriptions, mais en pratique les descriptions n'en contiennent pas.

**Mapping code/titre** : `r'^(R\d+)\s*[:\–\.\-—]\s*(.*)'` → extrait le code (`R1`) et le titre.

### Documents (format blob texte)

```python
docs_txt = contract.get("documents_supports", contract.get("documents", ""))
doc_items = [d.strip() for d in re.split(r'[;]', docs_txt) if d.strip()]
```

Format : `"Registre des saisines; Modèle d'accusé réception; ..."`

### FAQ (format JSON)

```python
faq = contract.get("faq", [])
# Si string, parsed via json.loads
faq_items = [{"question": q.get("question"), "reponse": q.get("reponse")}]
```

Format : `[{"question": "...", "reponse": "..."}, ...]`

### Mesures PMRI (format blob texte)

```python
mesures_txt = contract.get("mesures_pmri", contract.get("mesures", ""))
mesure_items = [m.strip() for m in re.split(r'[;]', mesures_txt) if m.strip()]
```

## Limites et travail futur

1. **Données statiques** : les tableaux sont figés au moment du rendu. Si la BDD satellite change, le tableau n'est pas mis à jour — il faut re-rouler le pipeline.
2. **Pas de filtrage** : contrairement à une vraie "linked view" Notion (touche `@`), il n'y a pas de filtres dynamiques ou de vues multiples.
3. **Données limitées** : le contrat ne contient qu'un sous-ensemble des champs de la BDD satellite (pas d'impact/probabilité pour les risques, pas de dates pour les documents, etc.).
4. **Solution future idéale** : utiliser l'API Notion pour créer des blocs `child_database` avec vues filtrées — non supporté par l'API publique en 2026.

## Relations bidirectionnelles (V6)

⚠️ Les tableaux inline ne suffisent pas pour créer des **vues liées filtrées** dans les bases satellites. Il faut aussi que **les pages satellites aient une relation inverse** vers la procédure.

`create_satellite_pages.py` injecte ces relations via `REVERSE_RELATION_MAP` :

| BDD satellite | Champ relation inverse | Injecté ? |
|--------------|----------------------|-----------|
| SBRX | `Procédure Mère` | ✅ À la création ET mise à jour rétroactive |
| GED | `Procédures liées` | ✅ Idem |
| PMRI | `Procédure Source` | ✅ Idem |
| FAQ | `None` | ❌ Pas de champ — relation impossible |

**Règle absolue :** « Aucune page ne doit être créée dans une base liée sans que la référence à la procédure ne soit injectée. » Sans relation inverse, les vues liées filtrées par procédure sont impossibles dans n'importe quelle base satellite.
