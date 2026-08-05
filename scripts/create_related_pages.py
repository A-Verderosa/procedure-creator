#!/usr/bin/env python3
"""
create_related_pages.py — Crée les pages satellites (SBRX, PMRI, GED, FAQ, GLOSSAIRE)
dans les BDD Notion dédiées et établit les relations sur la page procédure hub.

Usage:
  python3 create_related_pages.py \
    --md   procedure_mythique.md \
    --procedure-page-id <notion_page_id> \
    [--output result.json]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Importer les IDs depuis notion_shared
sys.path.insert(0, str(Path(__file__).resolve().parent))
from notion_shared import (
    get_notion_token, build_headers, notion_request, notion_query,
    extract_prop, extract_title,
    SBRX_MYTHIQUE_DB, PMRI_MYTHIQUE_DB, GED_MAIN_DB,
    FAQ_METIER_DB, GLOSSAIRE_MAIN_DB, MYTHIQUE_DATABASE_ID,
)


# ═══════════════════════════════════════════════════════════════════
# Parsing du .md rendu
# ═══════════════════════════════════════════════════════════════════


def parse_md_section(text, section_title, header_prefix="##", table=True):
    """
    Extrait une section du .md et parse son tableau Markdown.

    Args:
        text: Contenu entier du .md.
        section_title: Titre de la section (ex: "4. RISQUES").
        header_prefix: Niveau de titre (##, ###).
        table: Si True, tente de parser un tableau Markdown dans la section.

    Returns:
        dict contenant la section brute et les lignes parsées.
    """
    # Trouver la section
    pattern = rf"{re.escape(header_prefix)}\s+.*{re.escape(section_title)}.*?\n(.*?)(?=\n{header_prefix}\s+|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return {"found": False, "raw": "", "rows": []}

    raw_section = match.group(1).strip()

    rows = []
    if table:
        rows = parse_markdown_table(raw_section)

    return {"found": True, "raw": raw_section, "rows": rows}


def parse_markdown_table(text):
    """
    Parse un tableau Markdown en liste de dicts.

    Exemple :
    | Champ | Valeur1 | Valeur2 |
    |-------|---------|---------|
    | R1    | Desc1   | ...     |

    Returns:
        list[dict] — lignes du tableau.
    """
    lines = text.strip().split("\n")
    # Trouver la première ligne de tableau
    table_lines = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            if not in_table:
                in_table = True
            table_lines.append(stripped)
        elif in_table and not stripped:
            # Fin du tableau
            break
        elif in_table:
            table_lines.append(stripped)

    if len(table_lines) < 2:
        return []

    # Ligne d'en-tête
    header = [h.strip() for h in table_lines[0].strip("|").split("|")]

    # Sauter la ligne de séparation (|---|)
    data_lines = table_lines[2:] if len(table_lines) > 2 else []

    rows = []
    for line in data_lines:
        cols = [c.strip() for c in line.strip("|").split("|")]
        row = {}
        for i, h in enumerate(header):
            if i < len(cols):
                row[h] = cols[i]
            else:
                row[h] = ""
        rows.append(row)

    return rows


def extract_risks_from_md(text):
    """
    Extrait les risques depuis la section 4 du .md.

    Retourne une liste de dicts avec les clés normalisées.
    """
    section = parse_md_section(text, "4. RISQUES", header_prefix="##", table=True)
    if not section["found"]:
        return []

    risks = []
    for row in section["rows"]:
        # Détection de la colonne titre
        keys = list(row.keys())
        if not keys:
            continue

        risk = {
            "titre": row.get(keys[0], ""),
            "description": row.get(keys[1] if len(keys) > 1 else "", ""),
            "probabilite": _parse_number(row.get("Probabilité", row.get(keys[2] if len(keys) > 2 else "", ""))),
            "impact": _parse_number(row.get("Impact", row.get(keys[2] if len(keys) > 2 else "", ""))),
            "mitigation": row.get("Mitigation", row.get(keys[-1], "")),
        }
        if risk["titre"] and len(risk["titre"]) > 1:
            risks.append(risk)

    # Si rien trouvé via le tableau structuré, essayer le parsing libre
    if not risks:
        # Chercher des lignes avec R1, R2, etc.
        risk_pattern = re.findall(
            r'\|\s*(\w+\s*\d*)\s*\|\s*(.*?)\s*\|\s*(\d+[\/\d]*)\s*\|\s*(\d+[\/\d]*)\s*\|',
            section["raw"],
        )
        for code, desc, prob, impact in risk_pattern:
            risks.append({
                "titre": code.strip(),
                "description": desc.strip(),
                "probabilite": _parse_number(prob),
                "impact": _parse_number(impact),
                "mitigation": "",
            })

    return risks


def extract_faq_from_md(text):
    """
    Extrait la FAQ depuis la section 7 du .md.
    """
    section = parse_md_section(text, "7. FAQ", header_prefix="##", table=True)
    if not section["found"]:
        return []

    faqs = []
    for row in section["rows"]:
        keys = list(row.keys())
        if len(keys) < 2:
            continue

        question = row.get("Question", row.get(keys[1], ""))
        reponse = row.get("Réponse", row.get(keys[2] if len(keys) > 2 else keys[-1], ""))

        if question and len(question) > 3:
            faqs.append({
                "question": question,
                "reponse": reponse,
            })

    return faqs


def extract_documents_from_md(text):
    """
    Extrait les documents depuis la section 5 du .md.
    Parcourt TOUS les sous-tableaux (5.1 Documents de référence, 5.2 Documents d'enregistrement, etc.).
    """
    # Récupérer toute la section 5 brute
    section = parse_md_section(text, "5. DOCUMENTS", header_prefix="##", table=False)
    if not section["found"]:
        return []

    raw = section["raw"]

    docs = []

    # Méthode 1: Chercher tous les tableaux dans la section
    # Un tableau commence par | et a au moins une ligne de séparation |---|---|
    table_pattern = re.compile(r'(\|[^\n]+\n\|[-| ]+\n(?:\|[^\n]+\n?)*)', re.MULTILINE)
    tables = table_pattern.findall(raw)

    seen_codes = set()
    for table in tables:
        rows_data = parse_markdown_table(table)
        for row in rows_data:
            keys = list(row.keys())
            if not keys:
                continue
            code = row.get(keys[0], "").strip()
            if not code or len(code) < 2:
                continue
            # Ignorer les en-têtes de table
            if code.lower() in ("réf.", "code", "ref.", "#", "n°"):
                continue
            # Deuxième colonne comme description
            desc = row.get(keys[1] if len(keys) > 1 else "", "").strip()
            if code not in seen_codes:
                seen_codes.add(code)
                docs.append({
                    "code": code,
                    "description": desc,
                    "lien": "",
                })

    if not docs:
        # Méthode 2: fallback sur le parsing simple de la première table
        section_t = parse_md_section(text, "5. DOCUMENTS", header_prefix="##", table=True)
        for row in section_t.get("rows", []):
            keys = list(row.keys())
            if not keys:
                continue
            doc = {
                "code": row.get(keys[0], ""),
                "description": row.get(keys[1] if len(keys) > 1 else "", ""),
                "lien": row.get(keys[-1], ""),
            }
            if doc["code"] and len(doc["code"]) > 2 and doc["code"] not in seen_codes:
                seen_codes.add(doc["code"])
                docs.append(doc)

    return docs


def extract_glossary_from_md(text):
    """
    Essaie d'extraire des définitions / glossaire depuis le .md.
    Cherche une section 'Définitions', 'Glossaire', ou des termes en **gras** avec explication.
    """
    # Méthode 1: Section dédiée
    for section_name in ["Glossaire", "Définitions", "Définition", "Lexique"]:
        section = parse_md_section(text, section_name, header_prefix="##", table=True)
        if section["found"] and section["rows"]:
            terms = []
            for row in section["rows"]:
                keys = list(row.keys())
                if len(keys) >= 2:
                    term = row.get(keys[0], "").strip()
                    if term and len(term) > 1:
                        terms.append({
                            "terme": term,
                            "explication": row.get(keys[1], "").strip(),
                        })
            if terms:
                return terms

    # Méthode 2: Lignes avec terme en gras suivi d'une explication
    # Format: **Terme** : explication
    # Exclure le contenu des balises <details>...</details> (contient des labels comme **Rôle**, **Responsabilités**)
    clean_text = re.sub(r'<details>.*?</details>', '', text, flags=re.DOTALL)

    bold_terms = re.findall(r'\*\*([^*]+)\*\*\s*[:–-]\s*(.+?)(?:\n|$)', clean_text)
    if bold_terms:
        # Filtrer les termes trop génériques
        noise = {"rôle", "responsabilités", "compétences requises", "légende",
                 "objet", "acteurs clés", "délais pivots", "risques majeurs",
                 "indicateur cible", "réf.", "code", "version"}
        result = []
        seen = set()
        for term, expl in bold_terms:
            t = term.strip()
            if len(t) > 2 and t.lower() not in noise and t.lower() not in seen:
                seen.add(t.lower())
                result.append({"terme": t, "explication": expl.strip()})
        if result:
            return result

    return []


def extract_mesures_from_md(text):
    """
    Extrait les mesures PMRI depuis la section 4.2 ou autre section pertinente.
    Cherche dans la section risque la colonne 'Mitigation'.
    """
    # Les mesures sont souvent dans la colonne Mitigation du tableau risques
    risks = extract_risks_from_md(text)
    mesures = []
    for risk in risks:
        if risk.get("mitigation"):
            mesures.append({
                "titre": f"Mesure: {risk['mitigation'][:80]}",
                "description": risk["mitigation"],
                "risque_associe": risk["titre"],
            })
    return mesures


def _parse_number(val):
    """Parse une valeur numérique depuis une chaîne."""
    if isinstance(val, (int, float)):
        return val
    val = str(val).strip()
    # Supprimer les suffixes
    val = re.sub(r'[^\d.,]', '', val)
    val = val.replace(",", ".")
    try:
        return float(val)
    except ValueError:
        return None


# ═══════════════════════════════════════════════════════════════════
# Création dans les BDD satellites
# ═══════════════════════════════════════════════════════════════════


def notion_create_page(database_id, properties, icon=None):
    """
    Crée une page dans une BDD Notion.

    Args:
        database_id: ID de la BDD cible.
        properties: Dict des propriétés Notion.
        icon: Emoji optionnel.

    Returns:
        dict: Réponse API (contient id, url).
    """
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }
    if icon:
        payload["icon"] = {"type": "emoji", "emoji": icon}

    return notion_request("POST", "https://api.notion.com/v1/pages", payload)


def notion_update_page(page_id, properties):
    """Met à jour les propriétés d'une page Notion."""
    payload = {"properties": properties}
    return notion_request("PATCH", f"https://api.notion.com/v1/pages/{page_id}", payload)


def notion_set_relations(page_id, property_name, relation_ids):
    """
    Définit les relations d'une propriété de type relation.

    Args:
        page_id: ID de la page à modifier.
        property_name: Nom de la propriété relation (ex: "Risques liés").
        relation_ids: Liste d'IDs de pages cibles.
    """
    payload = {
        "properties": {
            property_name: {
                "relation": [{"id": rid} for rid in relation_ids],
            }
        }
    }
    return notion_request("PATCH", f"https://api.notion.com/v1/pages/{page_id}", payload)


def find_existing_in_db(database_id, title_prop_name, title_value):
    """
    Cherche une page existante dans une BDD par son titre.

    Args:
        database_id: ID de la BDD.
        title_prop_name: Nom de la propriété titre.
        title_value: Valeur du titre à chercher.

    Returns:
        str | None: ID de la page si trouvée, None sinon.
    """
    if not title_value:
        return None

    try:
        resp = notion_query(
            database_id=database_id,
            filter_prop=title_prop_name,
            filter_value=title_value[:200],
            page_size=5,
        )
    except RuntimeError:
        return None

    results = resp.get("results", []) if isinstance(resp, dict) else []
    for page in results:
        props = page.get("properties", {})
        existing_title = extract_title(props)
        if existing_title.strip().lower() == title_value.strip().lower():
            return page.get("id")

    return None


def find_glossary_term(database_id, terme):
    """
    Cherche un terme dans la BDD Glossaire avec matching exact et fuzzy.

    Args:
        database_id: ID de la BDD Glossaire.
        terme: Terme à chercher.

    Returns:
        str | None: ID de la page si trouvée.
    """
    # Exact match d'abord
    page_id = find_existing_in_db(database_id, "Terme", terme)
    if page_id:
        return page_id

    # Fuzzy : chercher tous les termes et comparer en lowercase
    try:
        resp = notion_query(database_id=database_id, page_size=100)
    except RuntimeError:
        return None

    results = resp.get("results", []) if isinstance(resp, dict) else []
    terme_lower = terme.strip().lower()

    for page in results:
        props = page.get("properties", {})
        t = extract_title(props)
        if t.strip().lower() == terme_lower:
            return page.get("id")

    return None


# ═══════════════════════════════════════════════════════════════════
# Création par type de BDD satellite
# ═══════════════════════════════════════════════════════════════════


def create_sbrx_pages(risks, procedure_page_id, dry_run=False):
    """
    Crée des pages risques dans SBRX MYTHIQUE.
    """
    created = []
    for i, risk in enumerate(risks):
        titre = risk.get("titre", f"Risque {i+1}")
        desc = risk.get("description", "")
        prob = risk.get("probabilite")
        impact = risk.get("impact")

        if dry_run:
            created.append({
                "titre": titre,
                "page_id": None,
                "url": None,
                "action": "dry_run",
            })
            continue

        # Vérifier dédoublonnage
        existing = find_existing_in_db(SBRX_MYTHIQUE_DB, "Titre", titre)
        if existing:
            created.append({
                "titre": titre,
                "page_id": existing,
                "url": None,
                "action": "already_exists",
            })
            continue

        properties = {
            "Titre": {"title": [{"type": "text", "text": {"content": titre[:200]}}]},
            "Procédure Mère": {"relation": [{"id": procedure_page_id}]},
        }
        if desc:
            properties["Code risque"] = {"rich_text": [{"type": "text", "text": {"content": desc[:2000]}}]}
        if prob is not None:
            properties["Probabilité"] = {"number": prob}
        if impact is not None:
            properties["Impact"] = {"number": impact}

        try:
            resp = notion_create_page(SBRX_MYTHIQUE_DB, properties, icon="⚠️")
            created.append({
                "titre": titre,
                "page_id": resp.get("id"),
                "url": resp.get("url"),
                "action": "created",
            })
        except RuntimeError as e:
            created.append({
                "titre": titre,
                "page_id": None,
                "error": str(e),
                "action": "error",
            })

    return created


def create_pmri_pages(mesures, procedure_page_id, sbrx_pages_ids=None, dry_run=False):
    """
    Crée des pages mesures dans PMRI MYTHIQUE.
    """
    created = []
    for i, mesure in enumerate(mesures):
        titre = mesure.get("titre", f"Mesure {i+1}")
        desc = mesure.get("description", "")

        if dry_run:
            created.append({
                "titre": titre,
                "page_id": None,
                "action": "dry_run",
            })
            continue

        existing = find_existing_in_db(PMRI_MYTHIQUE_DB, "Titre", titre)
        if existing:
            created.append({
                "titre": titre,
                "page_id": existing,
                "action": "already_exists",
            })
            continue

        properties = {
            "Titre": {"title": [{"type": "text", "text": {"content": titre[:200]}}]},
            "Procédure Source": {"relation": [{"id": procedure_page_id}]},
        }
        if desc:
            properties["Type de mesure"] = {"rich_text": [{"type": "text", "text": {"content": desc[:2000]}}]}

        # Lier au risque associé si trouvé
        risque_associe = mesure.get("risque_associe", "")
        if risque_associe and sbrx_pages_ids:
            # Associer au premier SBRX qui correspond
            for sbrx_id in sbrx_pages_ids:
                properties["Risque Traité"] = {"relation": [{"id": sbrx_id}]}
                break

        try:
            resp = notion_create_page(PMRI_MYTHIQUE_DB, properties, icon="🛡️")
            created.append({
                "titre": titre,
                "page_id": resp.get("id"),
                "url": resp.get("url"),
                "action": "created",
            })
        except RuntimeError as e:
            created.append({
                "titre": titre,
                "page_id": None,
                "error": str(e),
                "action": "error",
            })

    return created


def create_ged_pages(documents, dry_run=False):
    """
    Crée des pages documents dans GED MAIN.
    """
    created = []
    for doc in documents:
        code = doc.get("code", "")
        desc = doc.get("description", "")

        if not code:
            continue

        if dry_run:
            created.append({
                "code": code,
                "page_id": None,
                "action": "dry_run",
            })
            continue

        existing = find_existing_in_db(GED_MAIN_DB, "Code & Document", code)
        if existing:
            created.append({
                "code": code,
                "page_id": existing,
                "action": "already_exists",
            })
            continue

        properties = {
            "Code & Document": {"title": [{"type": "text", "text": {"content": code[:200]}}]},
        }
        if desc:
            properties["Catégorie"] = {
                "select": {"name": desc[:100]}
            }

        try:
            resp = notion_create_page(GED_MAIN_DB, properties, icon="📄")
            created.append({
                "code": code,
                "page_id": resp.get("id"),
                "url": resp.get("url"),
                "action": "created",
            })
        except RuntimeError as e:
            created.append({
                "code": code,
                "page_id": None,
                "error": str(e),
                "action": "error",
            })

    return created


def create_faq_pages(faqs, dry_run=False):
    """
    Crée des pages FAQ dans FAQ METIER.
    """
    created = []
    for faq in faqs:
        question = faq.get("question", "")
        reponse = faq.get("reponse", "")

        if not question:
            continue

        if dry_run:
            created.append({
                "question": question[:60],
                "page_id": None,
                "action": "dry_run",
            })
            continue

        existing = find_existing_in_db(FAQ_METIER_DB, "Question", question)
        if existing:
            created.append({
                "question": question[:60],
                "page_id": existing,
                "action": "already_exists",
            })
            continue

        properties = {
            "Question": {"title": [{"type": "text", "text": {"content": question[:200]}}]},
        }
        if reponse:
            properties["Réponse"] = {"rich_text": [{"type": "text", "text": {"content": reponse[:2000]}}]}

        try:
            resp = notion_create_page(FAQ_METIER_DB, properties, icon="❓")
            created.append({
                "question": question[:60],
                "page_id": resp.get("id"),
                "url": resp.get("url"),
                "action": "created",
            })
        except RuntimeError as e:
            created.append({
                "question": question[:60],
                "page_id": None,
                "error": str(e),
                "action": "error",
            })

    return created


def create_glossary_pages(glossary_terms, dry_run=False):
    """
    Crée des pages glossaire dans GLOSSAIRE MAIN avec dédoublonnage exact + fuzzy.
    """
    created = []
    for term in glossary_terms:
        terme = term.get("terme", "")
        explication = term.get("explication", "")

        if not terme:
            continue

        if dry_run:
            created.append({
                "terme": terme[:60],
                "page_id": None,
                "action": "dry_run",
            })
            continue

        # Dédoublonnage exact puis fuzzy
        existing = find_glossary_term(GLOSSAIRE_MAIN_DB, terme)
        if existing:
            created.append({
                "terme": terme[:60],
                "page_id": existing,
                "action": "already_exists",
            })
            continue

        # Déterminer la lettre initiale
        lettre = terme[0].upper() if terme else ""

        properties = {
            "Terme": {"title": [{"type": "text", "text": {"content": terme[:200]}}]},
        }
        if explication:
            properties["Explication"] = {"rich_text": [{"type": "text", "text": {"content": explication[:2000]}}]}
        if lettre and lettre.isalpha():
            properties["Lettre"] = {"select": {"name": lettre}}

        try:
            resp = notion_create_page(GLOSSAIRE_MAIN_DB, properties, icon="📖")
            created.append({
                "terme": terme[:60],
                "page_id": resp.get("id"),
                "url": resp.get("url"),
                "action": "created",
            })
        except RuntimeError as e:
            created.append({
                "terme": terme[:60],
                "page_id": None,
                "error": str(e),
                "action": "error",
            })

    return created


# ═══════════════════════════════════════════════════════════════════
# Relations sur la page procédure
# ═══════════════════════════════════════════════════════════════════


def set_procedure_relations(procedure_page_id, relations_map):
    """
    Établit les relations sur la page procédure vers les pages satellites.

    Args:
        procedure_page_id: ID Notion de la page procédure.
        relations_map: Dict {nom_propriete: [liste_ids_pages]}
            Ex: {"Risques liés": ["id1", "id2"], "Mesures PMRI": ["id3"]}
    """
    results = {}
    for prop_name, target_ids in relations_map.items():
        if not target_ids:
            continue
        try:
            notion_set_relations(procedure_page_id, prop_name, target_ids)
            results[prop_name] = {"ok": True, "count": len(target_ids)}
        except RuntimeError as e:
            results[prop_name] = {"ok": False, "error": str(e)}

    return results


# ═══════════════════════════════════════════════════════════════════
# Orchestrateur principal
# ═══════════════════════════════════════════════════════════════════


def run(md_path, procedure_page_id, satellite_data=None, dry_run=False):
    """
    Exécute la création complète des pages satellites.

    Args:
        md_path: Chemin du .md rendu.
        procedure_page_id: ID Notion de la page procédure.
        satellite_data: Optionnel, dict JSON structuré (permet de sauter le parsing).
        dry_run: Si True, simule sans créer.

    Returns:
        dict: Résultat complet.
    """
    result = {
        "procedure_page_id": procedure_page_id,
        "dry_run": dry_run,
        "sbrx": [],
        "pmri": [],
        "ged": [],
        "faq": [],
        "glossaire": [],
        "relations": {},
    }

    # Charger et parser le .md
    md_text = ""
    if md_path and os.path.isfile(md_path):
        with open(md_path, "r") as f:
            md_text = f.read()

    # Extraire les données structurées
    if satellite_data:
        risks = satellite_data.get("risques", [])
        faqs = satellite_data.get("faq", [])
        documents = satellite_data.get("documents", [])
        glossary = satellite_data.get("glossaire", [])
        mesures = satellite_data.get("mesures", [])
    else:
        risks = extract_risks_from_md(md_text) if md_text else []
        faqs = extract_faq_from_md(md_text) if md_text else []
        documents = extract_documents_from_md(md_text) if md_text else []
        glossary = extract_glossary_from_md(md_text) if md_text else []
        mesures = extract_mesures_from_md(md_text) if md_text else []

    # Créer les pages
    if risks or dry_run:
        sbrx_created = create_sbrx_pages(risks, procedure_page_id, dry_run=dry_run)
        result["sbrx"] = sbrx_created
        sbrx_ids = [r["page_id"] for r in sbrx_created if r.get("page_id")]
    else:
        sbrx_ids = []

    if mesures or dry_run:
        pmri_created = create_pmri_pages(mesures, procedure_page_id, sbrx_ids, dry_run=dry_run)
        result["pmri"] = pmri_created
        pmri_ids = [r["page_id"] for r in pmri_created if r.get("page_id")]
    else:
        pmri_ids = []

    if documents or dry_run:
        ged_created = create_ged_pages(documents, dry_run=dry_run)
        result["ged"] = ged_created
        ged_ids = [d["page_id"] for d in ged_created if d.get("page_id")]
    else:
        ged_ids = []

    if faqs or dry_run:
        faq_created = create_faq_pages(faqs, dry_run=dry_run)
        result["faq"] = faq_created
        faq_ids = [f["page_id"] for f in faq_created if f.get("page_id")]
    else:
        faq_ids = []

    if glossary or dry_run:
        gloss_created = create_glossary_pages(glossary, dry_run=dry_run)
        result["glossaire"] = gloss_created
        gloss_ids = [g["page_id"] for g in gloss_created if g.get("page_id")]
    else:
        gloss_ids = []

    # Établir les relations sur la page procédure
    if not dry_run and procedure_page_id:
        relations_map = {}
        if sbrx_ids:
            relations_map["Risques liés"] = sbrx_ids
        if pmri_ids:
            relations_map["Mesures PMRI"] = pmri_ids
        if ged_ids:
            relations_map["Document GED"] = ged_ids
        if faq_ids:
            relations_map["FAQ liée"] = faq_ids
        # GLOSSAIRE MAIN n'a pas de relation directe dans PROCÉDURES MYTHIQUES
        # (la relation existe dans BDD - 1 Procédures RH uniquement)

        if relations_map:
            rel_results = set_procedure_relations(procedure_page_id, relations_map)
            result["relations"] = rel_results

        # ── Lien inverse GED → Procédure (bidirectionnel) ──
        if ged_ids and procedure_page_id:
            ged_reverse_results = []
            for gid in ged_ids:
                try:
                    notion_set_relations(gid, "Procédures liées", [procedure_page_id])
                    ged_reverse_results.append({"page_id": gid, "ok": True})
                except RuntimeError as e:
                    ged_reverse_results.append({"page_id": gid, "ok": False, "error": str(e)})
            result["ged_reverse_relations"] = ged_reverse_results

    return result


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="Crée les pages satellites Notion et établit les relations",
    )
    parser.add_argument("--md", type=str, default=None,
                        help="Chemin du fichier .md rendu")
    parser.add_argument("--procedure-page-id", type=str, required=True,
                        help="ID Notion de la page procédure")
    parser.add_argument("--satellite-data", type=str, default=None,
                        help="Fichier JSON optionnel avec données structurées")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Fichier de sortie pour le résultat JSON")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulation sans création API")

    args = parser.parse_args()

    # Charger les données satellites si fournies
    satellite_data = None
    if args.satellite_data:
        if not os.path.isfile(args.satellite_data):
            print(json.dumps({
                "status": "error",
                "message": f"Fichier satellite_data introuvable : {args.satellite_data}",
            }))
            sys.exit(1)
        with open(args.satellite_data, "r") as f:
            satellite_data = json.load(f)

    # Exécuter
    result = run(
        md_path=args.md,
        procedure_page_id=args.procedure_page_id,
        satellite_data=satellite_data,
        dry_run=args.dry_run,
    )

    result["status"] = "ok"

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Résultat sauvegardé dans {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
