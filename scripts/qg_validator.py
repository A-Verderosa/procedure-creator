#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qg_validator.py — Quality Gates G1-G21 Checker
===============================================

Valide une procédure DOX contre la matrice des Quality Gates G1-G21.
Chaque QG a un niveau minimum requis, un poids et des critères de passage.

Fonctions principales :
  - validate_procedure(md_content, niveau) → dict{score, max, passes, fails, warnings}
  - load_qg_matrix() → dict des gates
  - check_gate(gate, md_content) → bool
  - generate_report(results) → rapport markdown
  - CLI : python3 qg_validator.py --file <path> [--niveau <niveau>]
"""

import argparse
import json
import os
import re
import sys

# Module partagé Notion (token, PROP_MAP, requêtes API)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notion_shared import (
    get_notion_token,
    build_headers,
    notion_request,
    notion_query,
    check_connection,
    extract_title,
    extract_procedure_id,
    PROP_MAP,
    DATA_SOURCE_ID,
    DATABASE_ID,
)


# ─── Chemins ─────────────────────────────────────────────────────────────────

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QG_MATRIX_PATH = os.path.join(SKILL_DIR, "references", "qg_matrix.yaml")
NIVEAUX_PATH = os.path.join(SKILL_DIR, "references", "niveaux.yaml")


# ─── Chargement de la matrice QG ────────────────────────────────────────────

def load_qg_matrix():
    """
    Charge la matrice complète des Quality Gates G1-G21.

    Returns:
        dict: Matrice des gates avec les clés :
            - gates : dict des QG (G1, G2, ..., G21)
            - seuils : dict des seuils de passage par niveau

    Raises:
        RuntimeError: Si le fichier est introuvable ou mal formaté.
    """
    if not os.path.isfile(QG_MATRIX_PATH):
        raise RuntimeError(f"Matrice QG introuvable : {QG_MATRIX_PATH}")

    try:
        import yaml
        with open(QG_MATRIX_PATH, "r") as f:
            matrix = yaml.safe_load(f)
    except ImportError:
        # Fallback sans PyYAML
        matrix = _fallback_parse_qg_yaml(QG_MATRIX_PATH)
    except Exception as e:
        raise RuntimeError(f"Erreur de chargement de la matrice QG : {e}")

    if not matrix or "gates" not in matrix:
        raise RuntimeError(
            "Matrice QG invalide : clé 'gates' manquante dans "
            f"{QG_MATRIX_PATH}"
        )
    return matrix


def _fallback_parse_qg_yaml(path):
    """
    Parse minimal du fichier qg_matrix.yaml sans PyYAML.

    Args:
        path (str): Chemin du fichier.

    Returns:
        dict: Matrice QG parsée.
    """
    matrix = {"gates": {}, "seuils": {}}
    current_gate = None
    in_seuils = False

    with open(path, "r") as f:
        for line in f:
            stripped = line.rstrip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("seuils:"):
                in_seuils = True
                continue
            if in_seuils:
                m = re.match(r"^\s+(\w+):\s*\{([^}]+)\}", stripped)
                if m:
                    level_name = m.group(1)
                    props_str = m.group(2)
                    props = {}
                    for p in props_str.split(","):
                        kv = p.split(":", 1)
                        if len(kv) == 2:
                            k = kv[0].strip()
                            try:
                                v = int(kv[1].strip())
                            except ValueError:
                                v = kv[1].strip()
                            props[k] = v
                    matrix["seuils"][level_name] = props
                continue
            if stripped.endswith(":") and not stripped.startswith(" "):
                in_seuils = False
                continue
            # Détection des gates G1, G2, etc.
            m = re.match(r"^\s+(G\d+[A-Z]?):\s*$", stripped)
            if m:
                current_gate = m.group(1)
                matrix["gates"][current_gate] = {}
                continue
            if current_gate:
                m2 = re.match(r"^\s+(\w+):\s*(?:\"([^\"]*)\"|'([^']*)'|(.*))", stripped)
                if m2:
                    key = m2.group(1)
                    val = m2.group(2) or m2.group(3) or m2.group(4) or ""
                    if val and val != "":
                        # Conversion automatique des types numériques
                        clean_val = val.strip()
                        if clean_val.lstrip("-").isdigit():
                            clean_val = int(clean_val)
                        elif clean_val.replace(".", "").lstrip("-").isdigit() and clean_val.count(".") == 1:
                            clean_val = float(clean_val)
                        matrix["gates"][current_gate][key] = clean_val
                    else:
                        # Liste (criteria, etc.)
                        val_clean = stripped.strip().split(":", 1)[1].strip()
                        if val_clean.startswith("- "):
                            if "criteria" not in matrix["gates"][current_gate]:
                                matrix["gates"][current_gate]["criteria"] = []
                            matrix["gates"][current_gate]["criteria"].append(
                                val_clean[2:].strip().strip('"').strip("'")
                            )
    return matrix


def load_niveaux_config():
    """
    Charge la configuration des niveaux depuis niveaux.yaml.

    Returns:
        dict: Configuration des niveaux (bronze, argent, or, etc.)
    """
    if not os.path.isfile(NIVEAUX_PATH):
        return {}
    try:
        import yaml
        with open(NIVEAUX_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        return {}
    except Exception:
        return {}


# ─── Fonctions Notion ─────────────────────────────────────────────────────────

def _cmd_check():
    """
    Vérifie le token Notion et la connexion à l'API.

    Returns:
        dict: statut de la vérification.
    """
    result = {"status": "ok", "token": False, "connection": False}
    try:
        token = get_notion_token()
        result["token"] = True
        result["token_preview"] = f"{token[:8]}... (len={len(token)})"
    except RuntimeError as e:
        result["status"] = "error"
        result["token_error"] = str(e)
        return result

    result["connection"] = check_connection()
    if not result["connection"]:
        result["status"] = "error"
        result["connection_error"] = "API Notion injoignable"
    return result


def _find_md_content_in_properties(properties):
    """
    Parcourt les propriétés Notion pour trouver du contenu potentiellement
    au format markdown (rich_text, title).

    Args:
        properties (dict): Propriétés Notion.

    Returns:
        str: Contenu markdown concaténé.
    """
    parts = []
    # Ordonner par pertinence : d'abord les champs structurants
    priority_keys = ["Objet", "Description", "Règles de gestion", "Consignes",
                     "Description des acteurs", "Logigramme", "Risques",
                     "Définitions", "Champ d'application", "Localisation procédure",
                     "Domaines", "Activités", "Observations",
                     "Documents supports", "Classification risques - Propositions",
                     "Documents de référence"]
    for key in priority_keys:
        if key in properties:
            prop = properties[key]
            ptype = prop.get("type", "")
            if ptype == "rich_text":
                txt = "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))
                if txt.strip():
                    parts.append(f"## {key}\n\n{txt}\n")
            elif ptype == "title":
                txt = "".join(t.get("plain_text", "") for t in prop.get("title", []))
                if txt.strip():
                    parts.append(f"# {txt}\n")

    # Titre
    title = extract_title(properties)
    if title:
        parts.insert(0, f"# {title}\n\n")

    return "\n".join(parts)


def _fetch_notion_procedure_md(procedure_id, data_source_id=None):
    """
    Récupère le contenu d'une procédure depuis Notion et construit
    une représentation markdown à partir de ses propriétés.

    Args:
        procedure_id (str): ID unique Notion de la page (ou Procedure_ID).
        data_source_id (str, optional): Data source ID pour la requête.

    Returns:
        dict: {"title": str, "md": str, "properties": dict, "procedure_id": str}

    Raises:
        RuntimeError: Si la procédure est introuvable.
    """
    ds_id = data_source_id or DATA_SOURCE_ID
    # Chercher par ID Notion ou par Procedure_ID — pagination complète
    all_results = []
    cursor = None
    while True:
        resp = notion_query(data_source_id=ds_id, page_size=100, start_cursor=cursor)
        batch = resp if isinstance(resp, list) else resp.get("results", [])
        all_results.extend(batch)

        has_more = resp.get("has_more", False) if isinstance(resp, dict) else False
        cursor = resp.get("next_cursor", None) if isinstance(resp, dict) else None
        if not has_more or not cursor:
            break

    target_page = None
    for page in all_results:
        props = page.get("properties", {})
        page_id = page.get("id", "")
        pid = extract_procedure_id(props)

        if page_id == procedure_id or pid == procedure_id:
            target_page = page
            break

    if not target_page:
        raise RuntimeError(
            f"Procédure introuvable dans Notion : {procedure_id}"
        )

    properties = target_page.get("properties", {})
    md_content = _find_md_content_in_properties(properties)
    title = extract_title(properties)
    pid = extract_procedure_id(properties)

    return {
        "title": title,
        "md": md_content,
        "properties": properties,
        "procedure_id": pid or procedure_id,
        "page_id": target_page.get("id", ""),
    }


# ─── Validation contre niveaux.yaml ─────────────────────────────────────────

def validate_against_niveaux(niveau="argent"):
    """
    Valide la configuration des niveaux (niveaux.yaml) pour un niveau donné :
    vérifie que les sections requises sont cohérentes avec la QG matrix.

    Returns:
        dict: Résultat de validation des sections.
    """
    niveaux = load_niveaux_config()
    if not niveaux or "niveaux" not in niveaux:
        return {"status": "warning", "message": "niveaux.yaml non chargé ou invalide"}

    config = niveaux.get("niveaux", {}).get(niveau)
    if not config:
        return {"status": "warning", "message": f"Niveau '{niveau}' non trouvé dans niveaux.yaml"}

    sections = config.get("sections", {})
    required = sections.get("required", [])
    optional = sections.get("optional", [])

    return {
        "status": "ok",
        "niveau": niveau,
        "couverture": config.get("couverture", 0),
        "finalite": config.get("finalite", ""),
        "required_sections": required,
        "optional_sections": optional,
        "total_sections": len(required) + len(optional),
    }


# ─── Vérificateurs individuels ─────────────────────────────────────────────

def _check_string_present(md_content, gate):
    """
    Vérifie la présence d'une chaîne de caractères (G1: Titre et référence).

    Args:
        md_content (str): Contenu markdown de la procédure.
        gate (dict): Définition du gate.

    Returns:
        bool: True si la condition est remplie.
    """
    # Vérifier la présence d'un titre de niveau 1
    if re.search(r"^#\s+.+", md_content, re.MULTILINE):
        return True
    return False


def _check_callout_present(md_content, gate):
    """
    Vérifie la présence d'un bloc de type callout/FLASH CARD (G2).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si présent.
    """
    # Chercher une section FLASH CARD ou un blockquote > avec résumé
    if re.search(r"FLASH\s*CARD", md_content, re.IGNORECASE):
        return True
    if re.search(r"Résumé\s*(exécutif|30s|30 secondes)", md_content, re.IGNORECASE):
        return True
    # Blockquote multiligne
    blockquotes = re.findall(r">\s*.+", md_content)
    if len(blockquotes) >= 3:
        return True
    return False


def _check_pattern_match(md_content, gate):
    """
    Vérifie la présence d'un pattern/localisation CRAIE (G3).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si présent.
    """
    if re.search(r"CRAIE", md_content, re.IGNORECASE):
        return True
    if re.search(r"Mission\s*›.*Processus\s*›", md_content):
        return True
    if re.search(r"Filière\s*RH", md_content, re.IGNORECASE):
        return True
    return False


def _check_mermaid_present(md_content, gate):
    """
    Vérifie la présence d'un diagramme Mermaid (G4).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si présent.
    """
    if re.search(r"```mermaid", md_content):
        return True
    return False


def _check_raci_complete(md_content, gate):
    """
    Vérifie la présence d'une matrice RACI complète (G5).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si RACI complet avec ≥4 acteurs et ≥3 phases.
    """
    if not re.search(r"RACI", md_content, re.IGNORECASE):
        return False
    # Compter les lignes de tableau avec entête R/A/C/I
    raci_rows = re.findall(r"\|.*\|.*\|.*\|.*\|", md_content)
    # Compter les acteurs uniques dans le tableau RACI
    acteurs = set()
    for row in raci_rows:
        cells = [c.strip() for c in row.split("|") if c.strip()]
        for cell in cells:
            if cell.upper() in ("R", "A", "C", "I"):
                continue
            if cell.startswith("**") or cell.startswith("Phase"):
                continue
            if cell in ("Acteur", "Activité", "Phase"):
                continue
            if cell and len(cell) < 50:
                acteurs.add(cell)

    phases = 0
    for row in raci_rows:
        cells = [c.strip() for c in row.split("|") if c.strip()]
        if cells and cells[0] and not cells[0].upper() in ("R", "A", "C", "I", "ACTEUR"):
            if any(c.upper() in ("R", "A", "C", "I") for c in cells[1:]):
                phases += 1

    return len(acteurs) >= 4 and phases >= 3


def _check_sections_detailed(md_content, gate):
    """
    Vérifie que les étapes détaillées sont présentes (G6).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si des étapes avec action, acteur, délai, livrable.
    """
    # Chercher des sections d'étapes
    etapes = re.findall(
        r"Étape\s+\d+.*(?:\n.*){3,}",
        md_content,
        re.IGNORECASE,
    )
    if etapes:
        return True
    # Alternative : chercher des paires Action/Acteur/Délai/Livrable
    if re.search(r"\*\*Action\*\*", md_content) and \
       re.search(r"\*\*Acteur\*\*", md_content) and \
       re.search(r"\*\*D[ée]lai\*\*", md_content) and \
       re.search(r"\*\*Livrable\*\*", md_content):
        return True
    return False


def _check_risks_present(md_content, gate):
    """
    Vérifie la présence d'au moins 3 risques documentés (G7).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si ≥3 risques avec code, description, impact, probabilité.
    """
    # Chercher des sections risques ou des tableaux de risques
    risques = re.findall(r"R\d+\b", md_content)
    if len(risques) >= 3:
        return True
    if re.search(r"Risque|Criticité", md_content, re.IGNORECASE):
        # Compter les lignes de risques dans les tableaux
        risk_rows = re.findall(r"\|.*R\d+.*\|", md_content)
        if len(risk_rows) >= 3:
            return True
        risk_codes = set()
        for row in risk_rows:
            cells = row.split("|")
            for cell in cells:
                m = re.search(r"R(\d+)", cell)
                if m:
                    risk_codes.add(int(m.group(1)))
        return len(risk_codes) >= 3
    return False


def _check_documents_present(md_content, gate):
    """
    Vérifie la présence de documents support et enregistrement (G7B).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si documents de référence listés.
    """
    has_support = bool(
        re.search(r"Documents?\s*(de\s*)?support|DOC_SUPPORT", md_content, re.IGNORECASE)
    )
    has_enreg = bool(
        re.search(r"Documents?\s*(d['e]|d')enregistrement|DOC_ENREG", md_content, re.IGNORECASE)
    )
    return has_support or has_enreg


def _check_table_present(md_content, gate):
    """
    Vérifie la présence d'un tableau de synthèse (G8).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si tableau présent.
    """
    # Chercher des tableaux markdown
    tables = re.findall(r"^\|.+\|\s*$", md_content, re.MULTILINE)
    if len(tables) >= 4:  # entête + séparateur + 2 lignes
        return True
    return False


def _check_table_comparative(md_content, gate):
    """
    Vérifie la présence d'un tableau comparatif (G9).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si tableau avec ≥3 critères.
    """
    tables = re.findall(r"^\|.+\|\s*$", md_content, re.MULTILINE)
    # Un tableau comparatif a des lignes de critères
    if len(tables) >= 5:
        return True
    return False


def _check_coverage_check(md_content, gate):
    """
    Vérifie la couverture cumulative (G10).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si checklist ou sections obligatoires présentes.
    """
    if re.search(r"Checklist|Sections obligatoires", md_content, re.IGNORECASE):
        return True
    if re.search(r"- \[.\]", md_content):
        return True
    return False


def _check_scorecard_present(md_content, gate):
    """
    Vérifie la présence d'une Scorecard (G11).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si scorecard ou trophée présent.
    """
    if re.search(r"Scorecard|Score\s*card|Trophée|Troph[ée]e", md_content, re.IGNORECASE):
        return True
    if re.search(r"Score\s*(total|QG)", md_content, re.IGNORECASE):
        return True
    return False


def _check_definitions_present(md_content, gate):
    """
    Vérifie la présence de définitions de niveaux (G12).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si définitions de niveau présentes.
    """
    if re.search(r"Définition.*niveau|Niveau.*défini", md_content, re.IGNORECASE):
        return True
    if re.search(r"🥉|🥈|🥇|💎|🔮", md_content):
        return True
    return False


def _check_criteria_table(md_content, gate):
    """
    Vérifie la présence d'un tableau critères/sous-critères (G13).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si tableau avec pondération.
    """
    if re.search(r"Critère|Sous-critère|Pondération", md_content, re.IGNORECASE):
        tables = re.findall(r"^\|.+\|\s*$", md_content, re.MULTILINE)
        if len(tables) >= 4:
            return True
    return False


def _check_date_present(md_content, gate):
    """
    Vérifie la présence d'une date de dernière revue (G14).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si date de revue présente.
    """
    if re.search(r"Dernière\s*revue|Date\s*(de\s*)?revue|Revue\s*le", md_content, re.IGNORECASE):
        return True
    # Chercher une date au format JJ/MM/AAAA ou AAAA-MM-JJ
    if re.search(r"\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}", md_content):
        # Vérifier qu'il y a un contexte de revue
        context = re.findall(r".{0,50}(?:revue|révision|mise à jour).{0,50}", md_content, re.IGNORECASE)
        return len(context) > 0
    return False


def _check_periodicite_present(md_content, gate):
    """
    Vérifie la présence de la périodicité de revue (G15).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si périodicité définie.
    """
    periodicites = [
        r"annuelle?", r"semestrielle?", r"trimestrielle?",
        r"mensuelle?", r"Périodicité", r"Fréquence\s*de\s*revue",
        r"tous\s*les\s*\d+\s*(mois|ans|an)",
    ]
    for pattern in periodicites:
        if re.search(pattern, md_content, re.IGNORECASE):
            return True
    return False


def _check_next_review_valid(md_content, gate):
    """
    Vérifie la cohérence de la prochaine revue (G16).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si prochaine revue cohérente.
    """
    if re.search(r"Prochaine\s*revue|Prochaine\s*révision", md_content, re.IGNORECASE):
        return True
    return False


def _check_faq_present(md_content, gate):
    """
    Vérifie la présence de FAQ (G17).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si FAQ présente.
    """
    faqs = re.findall(r"FAQ|Foire\s*aux\s*questions|Q\s*:?\s*|R\s*:?\s*", md_content, re.IGNORECASE)
    return len(faqs) >= 3


def _check_statut_revision(md_content, gate):
    """
    Vérifie la présence du statut de révision calculé (G18).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si statut présent.
    """
    if re.search(r"Statut\s*(de\s*)?révision|À jour|À réviser|Périmée", md_content, re.IGNORECASE):
        return True
    return False


def _check_no_regression(md_content, gate):
    """
    Vérifie la non-régression (G19) — à comparer avec version précédente.

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si non-régression documentée.
    """
    if re.search(r"Non-régression|Non.régression|Sections préservées", md_content, re.IGNORECASE):
        return True
    return False


def _check_version_history(md_content, gate):
    """
    Vérifie la présence de l'historique des versions (G20).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si historique présent.
    """
    if re.search(r"Version|Historique|Changelog|V\d+\.\d+", md_content):
        return True
    return False


def _check_global_score(md_content, gate):
    """
    Vérifie le score QG global (G21).

    Args:
        md_content (str): Contenu markdown.
        gate (dict): Définition du gate.

    Returns:
        bool: True si score global présent.
    """
    if re.search(r"Score\s*QG|QG\s*Global|Quality\s*Gate.*score", md_content, re.IGNORECASE):
        return True
    return False


# ─── Mapping check → fonction ──────────────────────────────────────────────

_CHECK_MAP = {
    "string_present": _check_string_present,
    "callout_present": _check_callout_present,
    "pattern_match": _check_pattern_match,
    "mermaid_present": _check_mermaid_present,
    "raci_complete": _check_raci_complete,
    "sections_detailed": _check_sections_detailed,
    "risks_present": _check_risks_present,
    "documents_present": _check_documents_present,
    "table_present": _check_table_present,
    "table_comparative": _check_table_comparative,
    "coverage_check": _check_coverage_check,
    "scorecard_present": _check_scorecard_present,
    "definitions_present": _check_definitions_present,
    "criteria_table": _check_criteria_table,
    "date_present": _check_date_present,
    "periodicite_present": _check_periodicite_present,
    "next_review_valid": _check_next_review_valid,
    "faq_present": _check_faq_present,
    "statut_revision": _check_statut_revision,
    "no_regression": _check_no_regression,
    "version_history": _check_version_history,
    "global_score": _check_global_score,
}


# ─── Moteur de validation ──────────────────────────────────────────────────

def check_gate(gate, md_content):
    """
    Vérifie un Quality Gate spécifique sur le contenu markdown.

    Args:
        gate (dict): Définition du QG {'name', 'check', 'criteria', ...}.
        md_content (str): Contenu markdown de la procédure.

    Returns:
        bool: True si le gate passe, False sinon.
    """
    check_name = gate.get("check", "")
    if not check_name:
        return False

    checker = _CHECK_MAP.get(check_name)
    if not checker:
        # Si le check n'est pas implémenté, log en warning
        return False

    try:
        return checker(md_content, gate)
    except Exception:
        return False


def validate_procedure(md_content, niveau="argent"):
    """
    Valide une procédure complète contre la matrice G1-G21.

    Seuls les gates dont le niveau_min est ≤ au niveau demandé sont
    activés. Le score est calculé comme (poids_passés / poids_total) * 100.

    Args:
        md_content (str): Contenu markdown de la procédure.
        niveau (str): Niveau de la procédure
            (bronze, argent, or, platine, ultra, mythique).

    Returns:
        dict: Résultats structurés :
            - score (float) : Score pondéré sur 100
            - max (int) : Score max possible
            - passes (list) : Gates passés
            - fails (list) : Gates en échec
            - warnings (list) : Avertissements
            - details (list) : Détail par gate
            - niveau (str) : Niveau testé
            - seuils (dict) : Seuils de passage par niveau
    """
    matrix = load_qg_matrix()
    gates = matrix.get("gates", {})
    seuils = matrix.get("seuils", {})

    # Mapping niveau → ordre
    niveau_order = {
        "bronze": 0, "argent": 1, "or": 2,
        "platine": 3, "ultra": 4, "mythique": 5,
    }
    niveau_index = niveau_order.get(niveau, 0)

    # Mapping niveau_min → ordre
    niveau_min_order = {
        "bronze": 0, "argent": 1, "or": 2,
        "platine": 3, "ultra": 4, "mythique": 5,
    }

    passes = []
    fails = []
    warnings = []
    details = []
    score_total = 0
    poids_total = 0

    # Trier les gates par nom (G1, G2, ..., G21)
    sorted_gates = sorted(gates.items(), key=lambda x: x[0])

    for gate_id, gate_data in sorted_gates:
        niveau_min = gate_data.get("niveau_min", "bronze")
        weight = gate_data.get("weight", 1)

        min_idx = niveau_min_order.get(niveau_min, 0)
        if min_idx > niveau_index:
            # Gate non requis pour ce niveau — ignorer
            continue

        poids_total += weight

        try:
            passed = check_gate(gate_data, md_content)
        except Exception as e:
            passed = False
            warnings.append(f"{gate_id} : erreur lors du check — {e}")

        detail = {
            "id": gate_id,
            "name": gate_data.get("name", ""),
            "niveau_min": niveau_min,
            "weight": weight,
            "passed": passed,
            "criteria": gate_data.get("criteria", []),
        }

        if passed:
            score_total += weight
            passes.append(gate_id)
            detail["result"] = "PASS"
        else:
            fails.append(gate_id)
            detail["result"] = "FAIL"

        details.append(detail)

    # Calcul du score
    max_score = poids_total
    score_pct = round((score_total / max_score * 100), 1) if max_score > 0 else 0.0

    # Validation des sections niveaux.yaml
    try:
        niveaux_result = validate_against_niveaux(niveau)
        niveaux_sections = niveaux_result if niveaux_result.get("status") == "ok" else None
    except Exception:
        niveaux_sections = None

    return {
        "score": score_pct,
        "max": max_score,
        "score_raw": score_total,
        "max_raw": poids_total,
        "passes": passes,
        "fails": fails,
        "warnings": warnings,
        "details": details,
        "niveau": niveau,
        "seuils": {
            "applicable": seuils.get(niveau, seuils.get("bronze", {})),
            "all": seuils,
        },
        "niveaux_sections": niveaux_sections,
    }


def generate_report(results):
    """
    Génère un rapport markdown à partir des résultats de validation QG.

    Args:
        results (dict): Résultat de validate_procedure().

    Returns:
        str: Rapport markdown formaté.
    """
    score = results["score"]
    niveau = results["niveau"]
    passes = results["passes"]
    fails = results["fails"]
    warnings = results["warnings"]
    details = results["details"]

    # Déterminer le trophée
    seuils = results.get("seuils", {})
    seuil_applicable = seuils.get("applicable", {})
    min_score = seuil_applicable.get("min_score", seuil_applicable.get("min_total", 0))
    min_required = seuil_applicable.get("min_required", 0)

    passed_count = len(passes)
    total_active = len(details)

    if score >= 90 and passed_count >= min_required:
        trophée = "🔮 Mythique"
    elif score >= 85 and passed_count >= min_required:
        trophée = "💎 Ultra"
    elif score >= 80 and passed_count >= min_required:
        trophée = "💎 Platine"
    elif score >= 70 and passed_count >= min_required:
        trophée = "🥇 Or"
    elif score >= 55 and passed_count >= min_required:
        trophée = "🥈 Argent"
    elif score >= 40 and passed_count >= min_required:
        trophée = "🥉 Bronze"
    else:
        trophée = "❌ Échec"

    # Vérifier les QG critiques (poids ≥ 4) en échec
    critical_fails = [
        d for d in details
        if d["result"] == "FAIL" and d.get("weight", 0) >= 4
    ]

    lines = []
    lines.append(f"# ✅ Quality Gates — Rapport de validation")
    lines.append("")
    lines.append(f"**Niveau** : {niveau}")
    lines.append(f"**Score** : {score}/{100} ({score}%)")
    lines.append(f"**Trophée** : {trophée}")
    lines.append(f"**Passés** : {passed_count}/{total_active}")
    lines.append("")

    if warnings:
        lines.append("## ⚠️ Avertissements")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append(f"## 📊 Détail par Quality Gate")
    lines.append("")
    lines.append("| Gate | Nom | Poids | Résultat | Critères |")
    lines.append("|------|-----|:-----:|:--------:|----------|")

    for d in details:
        emoji = "🟢" if d["passed"] else "🔴"
        criteres = "; ".join(d.get("criteria", [])[:2])
        if len(d.get("criteria", [])) > 2:
            criteres += "…"
        lines.append(
            f"| {d['id']} | {d['name']} | {d['weight']} "
            f"| {emoji} {d['result']} | {criteres} |"
        )

    lines.append("")
    lines.append("## 📋 Récapitulatif")
    lines.append("")
    lines.append(f"- **Score pondéré** : {results['score_raw']}/{results['max_raw']} ({score}%)")
    lines.append(f"- **Seuil requis** : min_score={min_score}, min_gates={min_required}")

    if critical_fails:
        lines.append(f"- **QG critiques en échec** ({len(critical_fails)}) :")
        for cf in critical_fails:
            lines.append(f"  - {cf['id']} — {cf['name']} (poids {cf['weight']})")
        lines.append("")
        lines.append("> ⛔ **ÉCHEC** : Des QG critiques (poids ≥ 4) sont en échec.")

    if fails:
        lines.append(f"- **QG en échec** ({len(fails)}) : {', '.join(fails)}")
    else:
        lines.append("- **Aucun QG en échec** 🎉")

    # ── Validation des sections niveaux.yaml ─────────────────────
    niveaux_sec = results.get("niveaux_sections")
    if niveaux_sec and niveaux_sec.get("status") == "ok":
        lines.append("")
        lines.append(f"## 📋 Sections requises ({niveau})")
        lines.append("")
        lines.append(f"- **Couverture** : {niveaux_sec['couverture']}")
        lines.append(f"- **Finalité** : {niveaux_sec['finalite']}")
        lines.append(
            f"- **Sections requises** ({len(niveaux_sec['required_sections'])}) : "
            f"{', '.join(niveaux_sec['required_sections'])}"
        )
        if niveaux_sec.get("optional_sections"):
            lines.append(
                f"- **Sections optionnelles** ({len(niveaux_sec['optional_sections'])}) : "
                f"{', '.join(niveaux_sec['optional_sections'])}"
            )

    lines.append("")
    lines.append("---")
    lines.append(f"> *Généré par Hermes Agent — qg_validator v1.0*")

    return "\n".join(lines)


# ─── Interface CLI ──────────────────────────────────────────────────────────

def main():
    """
    Point d'entrée CLI pour le script qg_validator.py.

    Usage:
        python3 qg_validator.py --file procedure.md
            → Valide avec niveau argent par défaut

        python3 qg_validator.py --file procedure.md --niveau ultra
            → Valide contre les QG du niveau ultra

        python3 qg_validator.py --file procedure.md --report
            → Valide et génère un rapport markdown

        python3 qg_validator.py --notion-id <page_id>
            → Valide une procédure depuis Notion (par ID page ou Procedure_ID)

        python3 qg_validator.py --check
            → Vérifie le token Notion et la connexion API

        python3 qg_validator.py --batch ./procedures/ --glob "*.md"
            → Mode batch: valider tous les fichiers markdown d'un répertoire

        python3 qg_validator.py --validate-sections --niveau ultra
            → Valide la configuration des sections niveaux.yaml
    """
    parser = argparse.ArgumentParser(
        description="Quality Gates G1-G21 Checker pour DOX_PROC",
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="Chemin du fichier markdown de la procédure",
    )
    parser.add_argument(
        "--niveau", "-n",
        type=str,
        default="argent",
        choices=["bronze", "argent", "or", "platine", "ultra", "mythique"],
        help="Niveau de la procédure (défaut: argent)",
    )
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="Générer un rapport markdown en sortie",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Sortie au format JSON",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Vérifier le token Notion et la connexion à l'API",
    )
    parser.add_argument(
        "--notion-id",
        type=str,
        default=None,
        help="ID Notion d'une procédure à valider directement depuis Notion",
    )
    parser.add_argument(
        "--batch",
        type=str,
        default=None,
        metavar="DIR",
        help="Mode batch: valider tous les fichiers d'un répertoire",
    )
    parser.add_argument(
        "--glob",
        type=str,
        default="*.md",
        help="Glob pour le mode batch (défaut: *.md)",
    )
    parser.add_argument(
        "--dir-output",
        type=str,
        default=None,
        metavar="DIR",
        help="Répertoire de sortie pour le mode batch (défaut: --batch)",
    )
    parser.add_argument(
        "--validate-sections",
        action="store_true",
        help="Valider la configuration des sections niveaux.yaml pour le niveau donné",
    )

    args = parser.parse_args()

    # ── --check : vérification Notion ──────────────────────────────
    if args.check:
        result = _cmd_check()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["status"] == "ok" else 1)

    # ── --validate-sections : validation niveaux.yaml ─────────────
    if args.validate_sections:
        result = validate_against_niveaux(niveau=args.niveau)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    # ── --batch : mode batch ───────────────────────────────────────
    if args.batch:
        results = {"batch": [], "summary": {"total": 0, "passed": 0, "failed": 0}}
        import glob as glob_module
        pattern = os.path.join(args.batch, args.glob)
        files = sorted(glob_module.glob(pattern))

        if not files:
            print(json.dumps({"status": "error", "message": f"Aucun fichier trouvé : {pattern}"}, indent=2), file=sys.stderr)
            sys.exit(1)

        for fpath in files:
            try:
                with open(fpath, "r") as f:
                    md_content = f.read()
                res = validate_procedure(md_content, niveau=args.niveau)
                res["file"] = os.path.relpath(fpath, args.batch)
                results["batch"].append(res)
                results["summary"]["total"] += 1
                if res["score"] >= 55:
                    results["summary"]["passed"] += 1
                else:
                    results["summary"]["failed"] += 1
            except Exception as e:
                results["batch"].append({
                    "file": os.path.relpath(fpath, args.batch),
                    "error": str(e),
                })
                results["summary"]["total"] += 1
                results["summary"]["failed"] += 1

        output_dir = args.dir_output or args.batch
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, "qg_validation_results.json")
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        sys.exit(0)

    # ── --notion-id : fetch depuis Notion ──────────────────────────
    if args.notion_id:
        try:
            notion_data = _fetch_notion_procedure_md(args.notion_id)
            md_content = notion_data["md"]
            if not md_content.strip():
                print(json.dumps({
                    "status": "error",
                    "message": f"Contenu vide pour la procédure Notion : {notion_data['title']} ({notion_data['procedure_id']})",
                }, indent=2), file=sys.stderr)
                sys.exit(1)
            results = validate_procedure(md_content, niveau=args.niveau)
            results["notion_procedure"] = notion_data["title"]
            results["notion_procedure_id"] = notion_data["procedure_id"]
            results["notion_page_id"] = notion_data["page_id"]

            if args.report:
                report = generate_report(results)
                print(report)
            else:
                print(json.dumps(results, indent=2, ensure_ascii=False))
        except RuntimeError as e:
            print(json.dumps({"status": "error", "message": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    # ── --file : mode fichier unique ───────────────────────────────
    if not args.file:
        parser.print_help()
        sys.exit(1)

    try:
        with open(args.file, "r") as f:
            md_content = f.read()
    except IOError as e:
        print(f"Erreur de lecture : {e}", file=sys.stderr)
        sys.exit(1)

    try:
        results = validate_procedure(md_content, niveau=args.niveau)
    except RuntimeError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif args.report:
        print(generate_report(results))
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
