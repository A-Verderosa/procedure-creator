#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_satellite_pages.py — Crée les pages dans les BDD satellites Notion

Ce script :
  1. Parse les champs du contrat (risques, mesures_pmri, documents, faq, etc.)
  2. Crée les pages correspondantes dans les BDD satellites (SBRX, PMRI, GED, FAQ)
  3. Établit les relations bidirectionnelles sur la page procédure MYTHIQUE

Usage:
    python3 create_satellite_pages.py <contrat.json> <procedure_page_id>

Contrat attendu : fichier JSON produit par generate_contract.py
"""

import json
import os
import re
import sys
import uuid
from datetime import date

# Ajouter le répertoire scripts au path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from notion_shared import (
    notion_request,
    notion_query,
    get_notion_token,
    build_headers,
    extract_title,
    SBRX_MYTHIQUE_DB,
    PMRI_MYTHIQUE_DB,
    GED_MAIN_DB,
    FAQ_METIER_DB,
    MYTHIQUE_DATABASE_ID,
)

# ─── Mapping relation MYTHIQUE → BDD satellite ───────────────────────────────
RELATION_MAP = {
    "risques":              ("Risques liés",  SBRX_MYTHIQUE_DB),
    "mesures_pmri":         ("Mesures PMRI",  PMRI_MYTHIQUE_DB),
    "documents_supports":   ("Document GED",  GED_MAIN_DB),
    "faq":                  ("FAQ liée",      FAQ_METIER_DB),
}

# ─── Noms des champs relation inverse (BDD satellite → MYTHIQUE) ────────────
REVERSE_RELATION_MAP = {
    SBRX_MYTHIQUE_DB: "Procédure Mère",
    GED_MAIN_DB:      "Procédures liées",
    PMRI_MYTHIQUE_DB: "Procédure Source",
    FAQ_METIER_DB:    None,  # Pas de champ relation dans FAQ
}

# ─── Propriétés minimales pour chaque BDD satellite ──────────────────────────

SBRX_PROPERTIES = lambda titre, code_risque="", impact=0, probabilite=0: {
    "Titre":               {"title": [{"text": {"content": titre}}]},
    "Code risque":         {"rich_text": [{"text": {"content": code_risque}}]},
    "Impact":              {"number": impact},
    "Probabilité":         {"number": probabilite},
}

PMRI_PROPERTIES = lambda titre, type_mesure="", frequence="": {
    "Titre":               {"title": [{"text": {"content": titre}}]},
    "Type de mesure":      {"rich_text": [{"text": {"content": type_mesure}}]},
}

GED_PROPERTIES = lambda titre, categorie="Document support": {
    "Code & Document":     {"title": [{"text": {"content": titre}}]},
    "Catégorie":           {"select": {"name": categorie}},
}

FAQ_PROPERTIES = lambda question, reponse="": {
    "Question":            {"title": [{"text": {"content": question}}]},
    "Réponse":             {"rich_text": [{"text": {"content": reponse}}]},
}


# ─── Parsing des champs texte ────────────────────────────────────────────────

def parse_risques(text):
    """Parse un champ risques en items (titre, code, impact, probabilité).
    
    Formats supportés :
    - "R1 : Saisine non traitée ; R2 : ..."
    - "4 risques (R1-R4) cotés P×I. R1 : ..."
    - "Risque 1: description ; Risque 2: ..."
    """
    if not text or text.strip() in ("", "-", "—", "Non défini", "À déterminer"):
        return []
    
    items = []
    
    # Pattern: R{N} : description (ou RN: desc)
    pattern = r'(R\d+)\s*[:：]\s*([^;]+?)(?:\s*;\s*|$)'
    matches = re.findall(pattern, text)
    
    if matches:
        for code, desc in matches:
            desc = desc.strip().rstrip('.')
            items.append({
                "titre": desc,
                "code_risque": code,
                "impact": 0,
                "probabilite": 0,
            })
    
    # Fallback: split on numbered items
    if not items:
        parts = re.split(r'[;•]\s*', text)
        for i, part in enumerate(parts):
            part = part.strip()
            if part and len(part) > 3:
                items.append({
                    "titre": re.sub(r'^Risque\s+\d+\s*[:：]\s*', '', part).strip(),
                    "code_risque": f"R{i+1}",
                    "impact": 0,
                    "probabilite": 0,
                })
    
    return items


def parse_mesures_pmri(text):
    """Parse un champ mesures_pmri en items."""
    if not text or text.strip() in ("", "-", "—", "Non défini", "À déterminer"):
        return []
    
    items = []
    
    # Pattern: PMRI-{N} : description ; ou mesures listées
    pattern = r'(PMRI-\d+|M\d+)\s*[:：]\s*([^;]+?)(?:\s*;\s*|$)'
    matches = re.findall(pattern, text)
    
    if matches:
        for code, desc in matches:
            desc = desc.strip().rstrip('.')
            items.append({
                "titre": desc,
                "code_mesure": code,
            })
    
    if not items:
        parts = re.split(r'[;•]\s*', text)
        for i, part in enumerate(parts):
            part = part.strip()
            if part and len(part) > 3:
                items.append({
                    "titre": part,
                    "code_mesure": f"PMRI-{i+1}",
                })
    
    return items


def parse_documents(text):
    """Parse un champ documents_supports ou documents_reference."""
    if not text or text.strip() in ("", "-", "—", "Non défini", "À déterminer"):
        return []
    
    items = []
    parts = re.split(r'[;•]\s*', text)
    for part in parts:
        part = part.strip().rstrip('.')
        if part and len(part) > 3:
            items.append({"titre": part})
    
    return items


def parse_faq(text):
    """Parse un champ faq en paires Q/R."""
    if not text or text.strip() in ("", "-", "—", "Non défini", "À déterminer"):
        return []
    
    items = []
    
    # Pattern: Q{N} : question ; R{N} : réponse
    q_pattern = r'Q\d+\s*[:：]\s*([^;]+?)\s*;\s*R\d+\s*[:：]\s*([^;]+?)(?:\s*;\s*|$)'
    matches = re.findall(q_pattern, text, re.IGNORECASE)
    
    if matches:
        for question, reponse in matches:
            items.append({
                "question": question.strip(),
                "reponse": reponse.strip().rstrip('.'),
            })
    
    if not items:
        # Fallback: Q: ... R: ...
        q_pattern2 = r'(?:^|;\s*)Q\d*\s*[:：]\s*([^;]+?)(?:\s*;\s*R\d*\s*[:：]\s*([^;]+?))?(?=\s*;|$)'
        matches = re.findall(q_pattern2, text, re.IGNORECASE)
        for q, r in matches:
            if q.strip():
                items.append({
                    "question": q.strip(),
                    "reponse": r.strip() if r else "",
                })
    
    if not items:
        parts = re.split(r'[;]\s*', text)
        for i, part in enumerate(parts):
            part = part.strip()
            if part and len(part) > 3:
                items.append({
                    "question": part,
                    "reponse": "",
                })
    
    return items


# ─── Création de page dans BDD satellite ─────────────────────────────────────

def create_satellite_page(database_id, properties):
    """Crée une page dans une BDD satellite Notion."""
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }
    try:
        resp = notion_request("POST", "https://api.notion.com/v1/pages", payload, timeout=30)
        return resp.get("id", "")
    except RuntimeError as e:
        print(f"[ERREUR] Création page satellite: {e}", file=sys.stderr)
        return ""


def get_existing_satellite_pages(database_id, title_field, title_value):
    """Recherche une page existante dans une BDD satellite par titre."""
    try:
        results = notion_query(
            database_id=database_id,
            filter_prop=title_field,
            filter_value=title_value,
        )
        pages = results.get("results", [])
        if pages:
            return [p.get("id", "") for p in pages]
    except RuntimeError:
        pass
    return []


# ─── Mise à jour des relations sur la page procédure ────────────────────────

def set_relations_on_page(page_id, relation_name, satellite_ids):
    """Ajoute des relations sur une page procédure.
    
    Args:
        page_id: ID de la page procédure MYTHIQUE
        relation_name: Nom de la propriété relation Notion
        satellite_ids: Liste des IDs des pages satellites
    """
    if not satellite_ids:
        return True
    
    # Construire le payload de relation
    relation_data = [{"id": sid} for sid in satellite_ids if sid]
    
    payload = {
        "properties": {
            relation_name: {
                "relation": relation_data,
            }
        }
    }
    
    try:
        notion_request(
            "PATCH",
            f"https://api.notion.com/v1/pages/{page_id}",
            payload,
            timeout=30,
        )
        return True
    except RuntimeError as e:
        print(f"[ERREUR] Mise à jour relation {relation_name}: {e}", file=sys.stderr)
        return False


# ─── Traitement principal ───────────────────────────────────────────────────

def process_contract_field(contract_data, field_name, procedure_page_id):
    """Traite un champ du contrat et crée les pages satellites associées.
    
    Returns:
        dict: {field_name: [satellite_page_ids]}
    """
    field_relation = RELATION_MAP.get(field_name)
    if not field_relation:
        return {field_name: []}
    
    relation_name, db_id = field_relation
    
    # Déterminer le parseur selon le champ
    if field_name == "risques":
        items = parse_risques(contract_data.get(field_name, ""))
    elif field_name == "mesures_pmri":
        items = parse_mesures_pmri(contract_data.get(field_name, ""))
    elif field_name in ("documents_supports", "documents_reference"):
        items = parse_documents(contract_data.get(field_name, ""))
    elif field_name == "faq":
        items = parse_faq(contract_data.get(field_name, ""))
    else:
        return {field_name: []}
    
    if not items:
        return {field_name: []}
    
    satellite_ids = []
    
    for item in items:
        # Construire les propriétés selon la BDD
        if field_name == "risques":
            props = SBRX_PROPERTIES(
                titre=item["titre"],
                code_risque=item.get("code_risque", ""),
                impact=item.get("impact", 0),
                probabilite=item.get("probabilite", 0),
            )
            title_field = "Titre"
        elif field_name == "mesures_pmri":
            props = PMRI_PROPERTIES(
                titre=item["titre"],
                type_mesure=item.get("code_mesure", ""),
            )
            title_field = "Titre"
        elif field_name in ("documents_supports", "documents_reference"):
            props = GED_PROPERTIES(titre=item["titre"])
            title_field = "Code & Document"
        elif field_name == "faq":
            props = FAQ_PROPERTIES(
                question=item.get("question", item.get("titre", "")),
                reponse=item.get("reponse", ""),
            )
            title_field = "Question"
        else:
            continue
        
        # ── Ajouter la relation inverse (BDD satellite → MYTHIQUE) ──
        rev_field = REVERSE_RELATION_MAP.get(db_id)
        if rev_field:
            props[rev_field] = {
                "relation": [{"id": procedure_page_id}]
            }
        
        # Vérifier si la page existe déjà
        existing = get_existing_satellite_pages(db_id, title_field, item.get("titre", "") or item.get("question", ""))
        if existing:
            satellite_ids.extend(existing)
            # Mettre à jour la relation inverse sur les pages existantes
            for existing_id in existing:
                if rev_field:
                    notion_request("PATCH", f"https://api.notion.com/v1/pages/{existing_id}", {
                        "properties": {
                            rev_field: {"relation": [{"id": procedure_page_id}]}
                        }
                    }, timeout=30)
            continue
        
        # Créer la page
        page_id = create_satellite_page(db_id, props)
        if page_id:
            satellite_ids.append(page_id)
    
    # Mettre à jour la relation sur la page procédure
    if satellite_ids:
        set_relations_on_page(procedure_page_id, relation_name, satellite_ids)
    
    return {field_name: satellite_ids}


def main():
    if len(sys.argv) < 3:
        print("Usage: create_satellite_pages.py <contrat.json> <procedure_page_id>", file=sys.stderr)
        print("  contrat.json    : Fichier contrat produit par generate_contract.py", file=sys.stderr)
        print("  procedure_page_id : ID Notion de la page procédure MYTHIQUE", file=sys.stderr)
        sys.exit(1)
    
    contrat_path = sys.argv[1]
    procedure_page_id = sys.argv[2].strip()
    
    # Charger le contrat (wrapper "procedure" optionnel)
    try:
        with open(contrat_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        # Déwrapper {"procedure": ...} si présent
        contract_data = raw.get("procedure", raw)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ERREUR] Chargement contrat {contrat_path}: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"📋 Contrat chargé : {contrat_path}", flush=True)
    print(f"📄 Page procédure : {procedure_page_id}", flush=True)
    
    # Champs à traiter
    fields = ["risques", "mesures_pmri", "documents_supports", "faq"]
    all_relations = {}
    
    for field in fields:
        result = process_contract_field(contract_data, field, procedure_page_id)
        all_relations.update(result)
        count = len(result.get(field, []))
        field_label = {
            "risques": "Risques SBRX",
            "mesures_pmri": "Mesures PMRI",
            "documents_supports": "Documents GED",
            "faq": "FAQ",
        }.get(field, field)
        print(f"  {field_label}: {count} page(s) liée(s)", flush=True)
    
    total = sum(len(v) for v in all_relations.values())
    print(f"\n✅ {total} page(s) satellite créées/liées sur {len(fields)} champ(s)", flush=True)
    
    # Sortie JSON pour chaînage avec verrouiller.sh
    output = {"procedure_page_id": procedure_page_id, "relations": all_relations}
    print(json.dumps(output))


if __name__ == "__main__":
    main()
