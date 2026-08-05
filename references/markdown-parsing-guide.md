# Guide de parsing Markdown → Notion (procédures)

## Principe

Le pipeline PROC produit un `.md` complet via `render_procedure.py` (RENDER, étape 6).
Les pages satellites (SBRX, PMRI, GED, FAQ, Glossaire) sont créées **en parsant ce .md** — pas
en régénérant les données depuis le contrat.

Avantage : ce qui est parsé est exactement ce qui a été validé par CHECK_STRUCTURE + QG.

## Sections parsées par `create_related_pages.py`

### 1. Risques SBRX — Section `4. RISQUES`

```markdown
## 4. RISQUES

| Code | Intitulé | Gravité | Probabilité | Mitigation |
|------|----------|---------|-------------|------------|
| R1   | Erreur saisie | 4 | 3 | Double contrôle |
```

**Parsing :** `parse_markdown_table()` après avoir isolé la section avec `parse_md_section(md, "4. RISQUES")`.

**Mapping Notion :**
| Propriété | Source | Type |
|-----------|--------|------|
| Code | colonne 1 | title |
| Intitulé | colonne 2 | rich_text |
| Gravité | colonne 3 | number |
| Probabilité | colonne 4 | number |
| Mitigation | colonne 5 | rich_text |

### 2. Mesures PMRI — Colonne `Mitigation` du tableau risques

Même source que les risques, mais chaque `| | | | | Texte |` sur une ligne = 1 mesure.

### 3. Documents GED — Section `5. DOCUMENTS`

```markdown
## 5. DOCUMENTS

### 5.1 Documents de référence

| Réf | Titre | Version | Émetteur |
|-----|-------|---------|----------|
| REF-01 | Guide utilisateur | V2.1 | DGSP |

### 5.2 Documents d'enregistrement

| Réf | Titre | Support | Conservation |
|-----|-------|---------|--------------|
| ENR-01 | Formulaire saisie | Papier | 5 ans |
```

**Parsing :** `extract_documents_from_md()` parcourt tous les sous-tableaux (5.1, 5.2, 5.3…)
avec une regex `r`\n### (\d+\.\d+)` pour détecter chaque sous-section, puis `parse_markdown_table()` sur chacune.

**Détection automatique :** première colonne = référence (title), les autres deviennent des propriétés.
Si l'en-tête contient `Version`, `Émetteur`, `Support`, `Conservation` → créées comme propriétés rich_text.

### 4. FAQ Métier — Section `7. FAQ`

```markdown
## 7. FAQ

| Question | Réponse |
|----------|---------|
| Quel délai ? | 5 jours ouvrés |
```

**Parsing :** `parse_md_section(md, "7. FAQ")` + `parse_markdown_table()`.
Question → title, Réponse → rich_text.

### 5. Glossaire — Termes en **gras** avec séparateur

```markdown
**AR** – Arrêt de travail
**DSI** : Direction des systèmes d'information
<details>Rôle: Non pertinent</details>
```

**Parsing :** `extract_glossary_from_md()`:

```python
# 1. Stripper les balises <details>...</details>
md_clean = re.sub(r'<details>.*?</details>', '', md, flags=re.DOTALL)

# 2. Regex termes en gras + séparateur
pattern = r'\*\*(.*?)\*\*\s*[:–-]\s*(.*?)(?:\n|$)'
matches = re.findall(pattern, md_clean)

# 3. Filtrer le bruit (collections de propriétés)
noise_terms = {'Rôle', 'Responsabilités', 'Indicateurs', 'Cibles', ...}
glossary = [(t.strip(), d.strip()) for t, d in matches if t.strip() not in noise_terms]
```

**Dédoublonnage :** avant création, interroger la BDD GLOSSAIRE MAIN sur le champ `Nom`
(insensible à la casse). Si trouvé, réutiliser l'ID au lieu de créer une nouvelle page.

## Techniques de parsing

### `parse_md_section(md, section_header) → str`

```python
def parse_md_section(md: str, header: str) -> str:
    """Extrait le contenu d'une section entre deux ## headers."""
    pattern = rf'##\s*{re.escape(header)}\s*\n(.*?)(?=\n##\s|\Z)'
    m = re.search(pattern, md, re.DOTALL)
    return m.group(1).strip() if m else ''
```

### `parse_markdown_table(text) → list[dict]`

```python
def parse_markdown_table(text: str) -> list[dict]:
    """Convertit un tableau markdown en liste de dicts."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    table_start = None
    for i, line in enumerate(lines):
        if line.startswith('|') and line.endswith('|') and not set(line) <= {'|', '-', ':'}:
            table_start = i
            break
    if table_start is None:
        return []
    headers = [h.strip() for h in lines[table_start].strip('|').split('|')]
    rows = []
    for line in lines[table_start+2:]:  # +2 pour sauter ligne de séparation
        if not line.startswith('|'):
            break
        cells = [c.strip() for c in line.strip('|').split('|')]
        rows.append(dict(zip(headers, cells)))
    return rows
```

## Règle d'or : toujours tester en `--dry-run` d'abord

```bash
python3 scripts/create_related_pages.py \
    --md /tmp/proc_create_xxx/06_rendered_procedure.md \
    --procedure-page-id "test" --dry-run
```

Vérifier les comptes extraits :
- SBRX : N risques (lignes du tableau section 4)
- PMRI : N mesures (1 par ligne de mitigation)
- GED : N documents (total des sous-tableaux 5.x)
- FAQ : N questions/réponses
- Glossaire : N termes (filtrés, dédupliqués)

Si les comptes sont corrects, le format est bon.
