#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish_procedure.py — Pipeline database-centric V2 (refonte modules)
=======================================================================

Architecture DB-Centric V2 :
  - La page MYTHIQUE = dashboard (propriétés + vues liées)
  - Chaque section = propriété rich_text OU BDD satellite
  - DOX = colonne vertébrale hiérarchique
  - Zéro contenu dans le corps de page sauf le dashboard visuel
  - Modules Services : Glossaire / GED / FAQ/ Annuaire via modules_service.py
  - PAGES BUS : enregistrement automatique + liaison inverse
  - Rapport de lecture : création automatique dans RAPPORTS LECTURE DOX

Usage:
    python3 scripts/publish_procedure.py <contrat.json> [--publish]
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime

# ─── Imports du renderer (diagrammes Mermaid) ────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from scripts.render_procedure import (
    generate_risk_matrix,
    generate_flowchart,
    generate_sequence_diagram,
    generate_craie_map,
)

# ─── Imports partagés ─────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notion_shared import (
    get_notion_token, build_headers, notion_request, notion_query,
    extract_prop, extract_title,
    MYTHIQUE_DATABASE_ID, MYTHIQUE_DATA_SOURCE_ID,
    MYTHIQUE_PROP_MAP, MYTHIQUE_REL_MAP,
    SBRX_MYTHIQUE_DB, PMRI_MYTHIQUE_DB, GED_MAIN_DB, FAQ_METIER_DB,
    GLOSSAIRE_MAIN_DB, EXIGENCES_DB,
)

# ─── Modules Services (pattern COMP) ──────────────────────────
from modules_service import (
    glossary_create, glossary_find_by_procedure,
    ged_create, ged_find_by_category, ged_find_supports, ged_find_references,
    faq_create, faq_check_access,
    annuaire_get_default_author, annuaire_find_by_role,
    bus_find_by_canonical_id, bus_create_entry, bus_list_all,
    link_entities_to_bus, unlink_entities_from_bus,
)

# ─── Constantes ───────────────────────────────────────────────────────────────
DOX_DATABASE_ID = "3351d81e-4c39-827e-88a4-817c2739bbff"
PAGES_BUS_DB = "3b21d81e-4c39-81fe-b6f9-c9b661368c7a"
RAPPORT_LECTURE_DB = "bca72a91852e48dabcbbb8ab60a67cc4"
NOTION_VERSION = "2022-06-28"
BATCH_DELAY = 1.5  # secondes entre lots API

# Mapping inverse : nom Notion → nom canonique MYTHIQUE
MYTHIQUE_PROP_INV = {v: k for k, v in MYTHIQUE_PROP_MAP.items()}

# Propriétés rich_text à alimenter depuis le contrat
RICH_TEXT_PROPS = [
    "objet", "champ_application", "definitions", "acteurs",
    "documents_reference", "documents_supports", "regles",
    "consignes", "risques",
]

# Propriétés de base
BASIC_PROPS = [
    "titre", "procedure_id", "service", "statut", "version",
    "periodicite_revue", "derniere_revue",
]

# ─── Helpers API ──────────────────────────────────────────────────────────────

def notion_get(url, token=None):
    """GET request vers Notion API (shim → notion_request)."""
    return notion_request("GET", url)

def notion_post(url, data, token=None):
    """POST request vers Notion API (shim → notion_request)."""
    return notion_request("POST", url, data)

def notion_delete(url, token=None):
    """DELETE request vers Notion API (shim → notion_request)."""
    return notion_request("DELETE", url)

def notion_patch(url, data, token=None):
    """PATCH request vers Notion API (shim → notion_request)."""
    return notion_request("PATCH", url, data)


def find_dox_entry(procedure_id):
    """
    Trouve l'entrée DOX par code procédure.
    Le code dans DOX utilise des points (ex: M1.P3.01) vs tirets (M1-P3-01).
    """
    dox_code = procedure_id.replace("-", ".")

    results = notion_query(
        database_id=DOX_DATABASE_ID,
        filter_prop="Code",
        filter_value=dox_code,
        filter_type="rich_text",
    )
    if results and results.get("results"):
        entry = results["results"][0]
        print(f"  ✅ Entrée DOX trouvée : {entry['id'][:8]} ({dox_code})")
        return entry

    results2 = notion_query(
        database_id=DOX_DATABASE_ID,
        filter_prop="Code",
        filter_value=procedure_id,
        filter_type="rich_text",
    )
    if results2 and results2.get("results"):
        entry = results2["results"][0]
        print(f"  ✅ Entrée DOX trouvée : {entry['id'][:8]} ({procedure_id})")
        return entry

    print(f"  ⚠️ Entrée DOX non trouvée pour {procedure_id} (ou {dox_code})")
    return None


# ─── Étape 2 : Trouver/créer page MYTHIQUE ────────────────────────────────────

def find_mythique_page(procedure_id):
    """Trouve une page MYTHIQUE par Code procédure."""
    results = notion_query(
        database_id=MYTHIQUE_DATABASE_ID,
        filter_prop="Code procédure",
        filter_value=procedure_id,
        filter_type="rich_text",
    )
    if results and results.get("results"):
        page = results["results"][0]
        print(f"  ✅ Page MYTHIQUE existante : {page['id'][:8]}")
        return page
    return None


def create_mythique_page(procedure_id, contract, dox_entry):
    """Crée une nouvelle page MYTHIQUE avec propriétés."""
    proc = contract.get("procedure", contract)
    titre = proc.get("titre", f"Procédure {procedure_id}")
    props = build_properties(contract, dox_entry)

    payload = {
        "parent": {"database_id": MYTHIQUE_DATABASE_ID, "type": "database_id"},
        "properties": props
    }
    result = notion_request("POST", "https://api.notion.com/v1/pages", payload)
    if result:
        page_id = result.get("id", "")
        print(f"  ✅ Page MYTHIQUE créée : {page_id[:8]} ({titre})")
        return result
    print(f"  ❌ Échec création page MYTHIQUE")
    return None

def build_properties(contract, dox_entry=None):
    """
    Construit les propriétés Notion pour la page MYTHIQUE.
    """
    proc = contract.get("procedure", contract)
    props = {}
    
    # Titre (obligatoire)
    titre = proc.get("titre", "Procédure sans titre")
    props["Titre"] = {"title": [{"text": {"content": titre}}]}
    
    # Code procédure
    pid = proc.get("procedure_id", "")
    props["Code procédure"] = {"rich_text": [{"text": {"content": pid}}]}
    
    # Service
    service = proc.get("service", "")
    if service:
        props["Service"] = {"select": {"name": service}}
    
    # Statut (avec émoji — type status dans Notion)
    statut = proc.get("statut", "À faire")
    statut_map = {"À faire": "🔲 À faire", "En cours": "🚧 En cours", "Terminé": "✅ Terminé",
                  "🔲 À faire": "🔲 À faire", "🚧 En cours": "🚧 En cours", "✅ Terminé": "✅ Terminé"}
    if statut:
        props["Statut"] = {"status": {"name": statut_map.get(statut, "🔲 À faire")}}
    
    # Version
    version = proc.get("version", "1.0")
    if version:
        props["Version"] = {"rich_text": [{"text": {"content": version}}]}
    
    # Niveau DOX
    niveau = proc.get("niveau", "mythique")
    niveau_map = {"mythique": "🔮 Mythique", "ultra": "💎 Ultra", "platine": "💎 Platine",
                  "or": "🥇 Or", "argent": "🥈 Argent", "bronze": "🥉 Bronze",
                  "akuma": "🔮 Mythique", "🔮 Mythique": "🔮 Mythique"}
    props["Niveau DOX"] = {"select": {"name": niveau_map.get(niveau.lower(), "🥉 Bronze")}}
    
    # Périodicité revue
    periode = proc.get("periodicite_revue", "")
    if periode:
        props["Périodicité revue"] = {"select": {"name": periode}}
    
    # Dernière revue
    dr = proc.get("date_actualisation", "")
    if dr:
        props["Dernière revue procédure"] = {"date": {"start": dr}}
    
    # Sections OR
    sections_or = proc.get("sections_or", [])
    if sections_or:
        props["Sections OR"] = {"multi_select": [{"name": s} for s in sections_or]}
    
    # Propriétés rich_text
    for prop_name in RICH_TEXT_PROPS:
        notion_name = MYTHIQUE_PROP_MAP.get(prop_name)
        if not notion_name:
            continue
        value = proc.get(prop_name, "")
        if value:
            props[notion_name] = {"rich_text": [{"text": {"content": value}}]}
    
    # Relation DOX → lien vers l'entrée hiérarchique dans la BDD DOX
    if dox_entry:
        dox_id = dox_entry.get("id", "")
        if dox_id:
            props["Hiérarchie DOX"] = {
                "relation": [{"id": dox_id}]
            }
            print(f"  🔗 Hiérarchie DOX → {dox_id[:8]}")
    
    return props


# ─── Étape 3 : Peupler SBRX (risques) ────────────────────────────────────────

def parse_risks(contract):
    """Parse les risques depuis le contrat (texte `risques` OU structuré `risks_detail`)."""
    proc = contract.get("procedure", contract)
    
    # Format structuré risks_detail (prioritaire)
    risks_detail = proc.get("risks_detail", [])
    if risks_detail:
        return [{
            "code": r.get("code", f"R{i+1}"),
            "description": r.get("title", ""),
            "impact": r.get("impact"),
            "probability": r.get("probability"),
            "hyp_rc": r.get("hyp_rc", ""),
            "hyp_rn": r.get("hyp_rn", ""),
            "index": i
        } for i, r in enumerate(risks_detail)]
    
    # Format texte legacy
    risques_text = proc.get("risques", "")
    if not risques_text:
        return []
    
    risks = []
    parts = risques_text.split(";")
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        # Extraire le code risque (R1, R2, etc.)
        import re
        match = re.match(r'R(\d+)\s*[:]\s*(.+)', part)
        if match:
            code = f"R{match.group(1)}"
            desc = match.group(2).strip()
            risks.append({"code": code, "description": desc, "index": i})
        else:
            risks.append({"code": f"R{i+1}", "description": part, "index": i})
    return risks

def populate_sbrx(risks, mythique_page_id, token):
    """Crée les entrées risques dans SBRX, liées à la procédure."""
    if not risks:
        print("  ℹ️ Aucun risque à créer")
        return []
    
    created = []
    for risk in risks:
        # Vérifier si le risque existe déjà pour cette procédure
        existing = query_database(SBRX_MYTHIQUE_DB, {
            "and": [
                {"property": "Titre", "title": {"contains": risk["code"]}},
                {"property": "Procédure Mère", "relation": {"contains": mythique_page_id}},
            ]
        }, token=token)
        
        if existing and existing.get("results"):
            page = existing["results"][0]
            print(f"  ℹ️ Risque {risk['code']} existe déjà — mise à jour des champs...")
            # Mettre à jour les champs manquants sur l'existant
            patch_fields = {}
            if risk.get("impact") is not None:
                patch_fields["Impact"] = {"number": risk["impact"]}
            if risk.get("probability") is not None:
                patch_fields["Probabilité"] = {"number": risk["probability"]}
            if risk.get("hyp_rc"):
                patch_fields["Hypothèse RC"] = {"rich_text": [{"text": {"content": risk["hyp_rc"][:2000]}}]}
            if risk.get("hyp_rn"):
                patch_fields["Hypothèse RN"] = {"rich_text": [{"text": {"content": risk["hyp_rn"][:2000]}}]}
            if patch_fields:
                notion_patch(f"https://api.notion.com/v1/pages/{page['id']}",
                    {"properties": patch_fields}, token)
                print(f"    → {len(patch_fields)} champ(s) mis à jour")
            created.append(page)
            continue
        
        # Créer le risque
        titre = f"{risk['code']} — {risk['description'][:80]}"
        props = {
            "Titre": {"title": [{"text": {"content": titre}}]},
            "Code risque": {"rich_text": [{"text": {"content": risk["code"]}}]},
            "Procédure Mère": {"relation": [{"id": mythique_page_id}]},
        }
        if risk.get("impact") is not None:
            props["Impact"] = {"number": risk["impact"]}
        if risk.get("probability") is not None:
            props["Probabilité"] = {"number": risk["probability"]}
        if risk.get("hyp_rc"):
            props["Hypothèse RC"] = {"rich_text": [{"text": {"content": risk["hyp_rc"][:2000]}}]}
        if risk.get("hyp_rn"):
            props["Hypothèse RN"] = {"rich_text": [{"text": {"content": risk["hyp_rn"][:2000]}}]}
        
        data = {
            "parent": {"database_id": SBRX_MYTHIQUE_DB, "type": "database_id"},
            "properties": props,
        }
        result = notion_post("https://api.notion.com/v1/pages", data, token)
        if result:
            print(f"  ✅ Risque {risk['code']} créé : {result['id'][:8]}")
            created.append(result)
        time.sleep(BATCH_DELAY)
    
    return created


# ─── Étape 3b : Peupler PMRI (mesures) ─────────────────────────────────────

def parse_pmri(contract):
    """Parse les mesures PMRI depuis le contrat (structure `pmri_mesures`)."""
    proc = contract.get("procedure", contract)
    mesures = proc.get("pmri_mesures", [])
    return mesures

def populate_pmri(mesures, mythique_page_id, sbrx_pages_map, token):
    """Crée les entrées PMRI liées à la procédure et au risque traité.
    Écrit Famille, Fréquence, Type contrôle, Responsable (si trouvé).
    """
    # Mapping valeurs contrat → options Notion
    FREQ_MAP = {
        "Quotidien": "Quotidienne", "Mensuel": "Mensuelle",
        "Annuel": "Annuelle", "Trimestriel": "Trimestrielle",
        "Hebdomadaire": "Hebdomadaire", "Semestriel": "Semestrielle",
        "Continue": "Continue",
    }
    CTL_TYPE_MAP = {
        "Automatique": "Préventif", "Manuel": "Détectif",
        "Semi-automatique": "Détectif", "Correctif": "Correctif",
    }
    # Base Responsable (créer un cache de recherche)
    RESP_DB_ID = "6e9d978c-b165-490c-a6c5-a4de5eaa5e56"
    responsible_cache = {}
    try:
        resp_result = query_database(RESP_DB_ID, {}, token=token)
        for p in resp_result.get("results", []):
            for name, prop in p.get("properties", {}).items():
                if prop.get("type") == "title":
                    val = prop.get("title", [{}])[0].get("text", {}).get("content", "")
                    if val:
                        responsible_cache[val.lower()] = p["id"]
    except Exception:
        pass  # DB inaccessible, on skip

    if not mesures:
        print("  ℹ️ Aucune mesure PMRI à créer")
        return []

    created = []
    for m in mesures:
        risque_code = m.get("risque_code", "")
        titre = m.get("titre", f"Mesure sans titre")
        sbrx_id = sbrx_pages_map.get(risque_code, "")

        existing = query_database(PMRI_MYTHIQUE_DB, {
            "and": [
                {"property": "Titre", "title": {"contains": titre[:30]}},
                {"property": "Procédure Source", "relation": {"contains": mythique_page_id}},
            ]
        }, token=token)

        def _build_pmri_props(m, sbrx_id, mythique_id):
            props = {
                "Titre": {"title": [{"text": {"content": titre[:80]}}]},
                "Procédure Source": {"relation": [{"id": mythique_id}]},
            }
            if sbrx_id:
                props["Risque Traité"] = {"relation": [{"id": sbrx_id}]}
            ei = m.get("effet_impact")
            if ei:
                props["Effet attendu sur impact"] = {"number": ei}
            ep = m.get("effet_probabilite")
            if ep:
                props["Effet attendu sur probabilité"] = {"number": ep}
            # Famille de mesure
            famille = m.get("famille")
            if famille:
                props["Famille de mesure"] = {"multi_select": [{"name": famille}]}
            # Fréquence contrôle
            freq = m.get("frequence_controle")
            if freq and freq in FREQ_MAP:
                props["Fréquence contrôle"] = {"select": {"name": FREQ_MAP[freq]}}
            # Type contrôle
            tc = m.get("type_controle")
            if tc and tc in CTL_TYPE_MAP:
                props["Type de contrôle"] = {"select": {"name": CTL_TYPE_MAP[tc]}}
            # Responsable
            responsable = m.get("responsable")
            if responsable and responsable.lower() in responsible_cache:
                props["Responsable"] = {"relation": [{"id": responsible_cache[responsable.lower()]}]}
            elif responsable:
                print(f"    ⚠️ Responsable '{responsable}' introuvable dans la base")
            return props

        if existing and existing.get("results"):
            page = existing["results"][0]
            print(f"  ℹ️ Mesure '{titre}' existe déjà — mise à jour des champs...")
            patch_fields = _build_pmri_props(m, sbrx_id, mythique_page_id)
            patch_fields.pop("Titre", None)
            patch_fields.pop("Procédure Source", None)
            patch_fields.pop("Risque Traité", None)
            if patch_fields:
                notion_patch(f"https://api.notion.com/v1/pages/{page['id']}",
                    {"properties": patch_fields}, token)
                print(f"    → {len(patch_fields)} champ(s) mis à jour")
            created.append(page)
            continue

        props = _build_pmri_props(m, sbrx_id, mythique_page_id)
        data = {"parent": {"database_id": PMRI_MYTHIQUE_DB, "type": "database_id"}, "properties": props}
        result = notion_post("https://api.notion.com/v1/pages", data, token)
        if result:
            print(f"  ✅ Mesure PMRI '{titre}' créée : {result['id'][:8]}")
            created.append(result)
        time.sleep(BATCH_DELAY)
    return created


# ─── Étape 3c : Peupler FAQ ────────────────────────────────────────────────

def parse_faq(contract):
    """Parse les FAQ depuis le contrat (structure `faq`)."""
    proc = contract.get("procedure", contract)
    faqs = proc.get("faq", [])
    return faqs

def populate_faq(faqs, token):
    """Crée les entrées FAQ (pool global) via modules_service."""
    if not faqs:
        print("  ℹ️ Aucune FAQ à créer")
        return []

    created = []
    for f in faqs:
        question = f.get("question", "")
        if not question:
            continue

        try:
            result = faq_create(
                question=question,
                reponse=f.get("reponse", ""),
            )
            if result:
                print(f"  ✅ FAQ créée : '{question[:40]}...' ({result['id'][:8]})")
                created.append(result)
        except RuntimeError as e:
            if "dupl" in str(e).lower() or "409" in str(e):
                print(f"  ℹ️ FAQ '{question[:40]}...' existe déjà")
            else:
                print(f"  ❌ Erreur FAQ '{question[:40]}...': {e}")
        time.sleep(BATCH_DELAY)
    return created



# ─── Étape 3d : Peupler Glossaire (définitions) ────────────────────────────

def parse_glossary(contract):
    """Parse les définitions depuis le contrat (texte `definitions`)."""
    proc = contract.get("procedure", contract)
    text = proc.get("definitions", "")
    if not text:
        return []
    entries = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or not line.startswith("*") and not line.startswith("-"):
            continue
        line = line.lstrip("*- ")
        if ":" in line:
            term, definition = line.split(":", 1)
            entries.append({"terme": term.strip().strip("**"), "texte": definition.strip()})
    return entries

def populate_glossary(entries, mythique_page_id, token):
    """Crée des entrées dans Glossaire Main via modules_service et les lie à MYTHIQUE."""
    if not entries:
        print("  ℹ️ Aucune définition à créer")
        return []
    created = []
    for entry in entries:
        # Chercher si le terme existe déjà via modules_service
        existing_terms = glossary_find_by_procedure(mythique_page_id)
        found = any(e["terme"].lower() == entry["terme"].lower() for e in existing_terms)
        if found:
            print(f"  ℹ️ Terme déjà existant: {entry['terme']}")
            continue

        try:
            result = glossary_create(
                terme=entry["terme"][:100],
                texte=entry["texte"][:1000],
            )
            if result:
                print(f"  ✅ Terme créé: {entry['terme']}")
                # Lier à MYTHIQUE via Procédures mythiques liées
                time.sleep(BATCH_DELAY)
                notion_request("PATCH", f"https://api.notion.com/v1/pages/{result['id']}",
                    {"properties": {
                        "Procédures mythiques liées": {"relation": [{"id": mythique_page_id}]}
                    }})
                created.append(result)
        except Exception as e:
            print(f"  ❌ Erreur création terme '{entry['terme']}': {e}")
        time.sleep(BATCH_DELAY)

    # Lier les entrées sur MYTHIQUE (relation inverse)
    term_ids = [p["id"] for p in created if p.get("id")]
    if term_ids:
        notion_request("PATCH", f"https://api.notion.com/v1/pages/{mythique_page_id}",
            {"properties": {"Glossaire lié": {"relation": [{"id": tid} for tid in term_ids]}}})
        print(f"  ✅ Glossaire lié: {len(term_ids)} termes")
    return created

# ─── Étape 3e-3f : Peupler Exigences (règles + consignes) ─────────────────────

def parse_exigences(contract, exigence_type="regles"):
    """Parse les règles (Type=Règle) ou consignes (Type=Consigne) depuis le contrat."""
    proc = contract.get("procedure", contract)
    text = proc.get(exigence_type, "")
    if not text:
        return []
    entries = []
    if exigence_type == "regles":
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Enlever la numérotation: "1. Texte" ou "1. **Titre:** Texte"
            import re
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            if not line:
                continue
            entries.append({"intitule": line[:80], "texte": line})
    else:
        # Pour les consignes avec en-têtes en gras
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Supprimer le gras markdown
            clean = line.replace("**", "").strip()
            if not clean:
                continue
            entries.append({"intitule": clean[:80], "texte": clean})
    return entries

def populate_exigences(entries, mythique_page_id, token, type_label="Regle"):
    """Crée des entrées dans Exigences et les lie à MYTHIQUE.
    type_label: 'Regle' pour regles, 'Consigne' pour consignes.
    """
    if not entries:
        print(f"  i Aucune exigence ({type_label}) à créer")
        return []
    # Sélecteur Notion pour le type
    select_val = "Regle (G)" if type_label == "Regle" else "Consigne (C)"
    # Champ relation MYTHIQUE selon le type
    if type_label == "Regle":
        rel_field = "Procédures mythiques — règles"
    else:
        rel_field = "Procédures mythiques — consignes"
    created = []
    for entry in entries:
        existing = query_database(EXIGENCES_DB, {
            "property": "Intitulé", "title": {"contains": entry["intitule"][:60]}
        }, token=token)
        if existing and existing.get("results"):
            p = existing["results"][0]
            print(f"  i Exigence déjà existante: {entry['intitule'][:40]}...")
            created.append(p)
            continue
        data = {
            "parent": {"database_id": EXIGENCES_DB, "type": "database_id"},
            "properties": {
                "Intitulé": {"title": [{"text": {"content": entry["intitule"][:100]}}]},
                "Texte canonique": {"rich_text": [{"text": {"content": entry["texte"][:1000]}}]},
                "Type": {"select": {"name": select_val}},
                rel_field: {"relation": [{"id": mythique_page_id}]},
            }
        }
        result = notion_post("https://api.notion.com/v1/pages", data, token)
        if result:
            print(f"  ✓ Exigence créée ({type_label}): {entry['intitule'][:40]}...")
            created.append(result)
        time.sleep(BATCH_DELAY)
    # Lier les entrées sur MYTHIQUE
    if created:
        ids = [p["id"] for p in created if p.get("id")]
        if ids:
            field_name = "Règles de gestion liées" if type_label == "Regle" else "Consignes de sécurité liées"
            notion_patch(f"https://api.notion.com/v1/pages/{mythique_page_id}",
                {"properties": {field_name: {"relation": [{"id": iid} for iid in ids]}}}, token)
            print(f"  ✓ {field_name}: {len(ids)} exigences liees")
    return created


# ─── Étape 4 : Peupler GED (documents) ───────────────────────────────────────

def parse_documents(contract):
    """Parse les documents support et référence depuis le contrat.
    Retourne une liste de dicts avec code, title, category.
    Supporte séparateurs ; ou \\n, et tirets de listes.
    """
    import re
    
    def _parse_text(docs_text, prefix, category):
        """Parse un champ textuel en liste de documents."""
        if not docs_text:
            return []
        if ";" in docs_text:
            parts = docs_text.split(";")
        else:
            parts = docs_text.split("\n")
        docs = []
        for i, part in enumerate(parts):
            part = part.strip().strip("-").strip("*").strip()
            if not part:
                continue
            # Code explicite : "CEV-F01 Texte" ou "D1 Texte" — laisse passer CEV-F01, REF1, R5...
            match = re.match(r'([A-Z][A-Z0-9-]*\d+)\s+(.+)', part)
            if match:
                docs.append({"code": match.group(1), "title": match.group(2).strip(), "category": category})
            else:
                docs.append({"code": f"{prefix}{i+1}", "title": part, "category": category})
        return docs
    
    proc = contract.get("procedure", contract)
    docs = []
    docs += _parse_text(proc.get("documents_supports", ""), "D", "Document support")
    docs += _parse_text(proc.get("documents_reference", ""), "REF", "Document référence")
    return docs

def populate_ged(documents, mythique_page_id, token):
    """Crée les entrées documents dans GED MAIN via modules_service."""
    if not documents:
        print("  ℹ️ Aucun document à créer")
        return []

    created = []
    for doc in documents:
        code = doc.get("code", "")
        title = doc.get("title", "")
        category = doc.get("category", "Document support")
        titre_ged = f"{code} — {title[:80]}"

        # Vérifier via ged_find_by_category si le doc existe
        existing_docs = ged_find_by_category(category) if category else []
        found = any(code in (d.get("code", "")) for d in existing_docs)
        if found:
            print(f"  ℹ️ Document {code} existe déjà")
            continue

        try:
            result = ged_create(
                code=titre_ged,
                categorie=category,
            )
            if result:
                print(f"  ✅ Document {code} créé [{category}]")
                # Lier à MYTHIQUE via Procédures liées
                time.sleep(BATCH_DELAY)
                notion_request("PATCH", f"https://api.notion.com/v1/pages/{result['id']}",
                    {"properties": {
                        "Procédures liées": {"relation": [{"id": mythique_page_id}]}
                    }})
                created.append(result)
        except Exception as e:
            print(f"  ❌ Erreur création document {code}: {e}")
        time.sleep(BATCH_DELAY)

    return created



# ─── Helpers : blocs enfants page ──────────────────────────────────────────

def fetch_children(page_id):
    """Récupère tous les blocs enfants d'une page Notion."""
    children = []
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    while url:
        result = notion_request("GET", url)
        if not result:
            break
        results = result.get("results", [])
        children.extend(results)
        if result.get("has_more"):
            cursor = result["next_cursor"]
            url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100&start_cursor={cursor}"
        else:
            url = None
    return children


def delete_children(block_ids):
    """Supprime une liste de blocs enfants par leurs IDs.
    Notion impose un délai entre les suppressions.
    """
    for bid in block_ids:
        result = notion_request("DELETE", f"https://api.notion.com/v1/blocks/{bid}")
        if result:
            time.sleep(0.35)


# ─── Étape 5 : Dashboard visuel (callouts + tableaux) ───────────────────────

def build_dashboard_blocks(contract, sbrx_pages, ged_pages):
    """Construit les blocs du dashboard visuel dans le corps de la page."""
    proc = contract.get("procedure", contract)
    phases = proc.get("phases", [])
    blocks = []
    
    # 1. Callout récapitulatif
    n_risks = len(sbrx_pages)
    n_docs = len(ged_pages)
    n_phases = len(phases)
    
    blocks.append({
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": f"📊 Récapitulatif : {n_risks} risque(s) · {n_docs} document(s) · {n_phases} phase(s)"}}],
            "icon": {"emoji": "📊"},
            "color": "blue_background"
        }
    })
    
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    
    # 2. Sections dynamiques
    # 2a. Risques
    if sbrx_pages:
        toggle_blocks = [
            {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "📋 Risques identifiés"}}]}},
        ]
        # Tableau summary
        table_rows = []
        table_rows.append({
            "type": "table_row",
            "table_row": {"cells": [
                [{"type": "text", "text": {"content": "Code"}}],
                [{"type": "text", "text": {"content": "Description"}}],
            ]}
        })
        for r in sbrx_pages:
            p = r.get("properties", {})
            code = extract_prop(p.get("Titre", {}))[:20]
            desc = extract_prop(p.get("Code risque", {}))[:60]
            table_rows.append({
                "type": "table_row",
                "table_row": {"cells": [
                    [{"type": "text", "text": {"content": code}}],
                    [{"type": "text", "text": {"content": desc}}],
                ]}
            })
        toggle_blocks.append({
            "object": "block", "type": "table",
            "table": {"table_width": 2, "has_column_header": True, "children": table_rows}
        })
        blocks.append({
            "object": "block", "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": f"📋 Risques ({len(sbrx_pages)})"}}],
                "children": toggle_blocks
            }
        })
    
    # 2b. Phases
    if phases:
        phases_blocks = [
            {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "📋 Phases opérationnelles"}}]}},
        ]
        for i, phase in enumerate(phases, 1):
            nom = phase.get("titre") or phase.get("nom", "Phase sans nom")
            num = phase.get("numero", i)
            titre_phase = f"Phase {num} — {nom}"
            acteur = phase.get("acteurs", phase.get("acteur", ""))
            delai = phase.get("delai", "")
            phases_blocks.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": titre_phase}}]}
            })
            if acteur or delai:
                meta = f"👤 {acteur}  ⏱ {delai}"
                phases_blocks.append({
                    "object": "block", "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": meta}}]}
                })
        
        blocks.append({
            "object": "block", "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": f"📋 Phases ({len(phases)})"}}],
                "children": phases_blocks
            }
        })
    
    # 2c. Documents
    if ged_pages:
        doc_blocks = [
            {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "📄 Documents support"}}]}},
        ]
        table_rows = []
        table_rows.append({
            "type": "table_row",
            "table_row": {"cells": [
                [{"type": "text", "text": {"content": "Code"}}],
                [{"type": "text", "text": {"content": "Titre"}}],
            ]}
        })
        for g in ged_pages:
            p = g.get("properties", {})
            code = extract_prop(p.get("Code & Document", {}))[:20]
            title = extract_prop(p.get("Code & Document", {}))[20:80]  # suite du titre
            table_rows.append({
                "type": "table_row",
                "table_row": {"cells": [
                    [{"type": "text", "text": {"content": code}}],
                    [{"type": "text", "text": {"content": title}}],
                ]}
            })
        doc_blocks.append({
            "object": "block", "type": "table",
            "table": {"table_width": 2, "has_column_header": True, "children": table_rows}
        })
        blocks.append({
            "object": "block", "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": f"📄 Documents ({len(ged_pages)})"}}],
                "children": doc_blocks
            }
        })

    # 2d. Carte CRAIE (flowchart LR — vue macro)
    try:
        pid = proc.get('procedure_id', 'PROC')
        craie_code = generate_craie_map(contract=proc)
        if craie_code:
            craie_blocks = [
                {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"🗺️ Carte CRAIE — Vue macro"}}]}},
                {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Amont → Procédure → Aval, inscrit dans la norme CRAIE"}}]}},
                {"object":"block","type":"code","code":{"rich_text":[{"type":"text","text":{"content":craie_code}}],"language":"mermaid"}},
            ]
            blocks.append({
                "object":"block","type":"toggle",
                "toggle":{"rich_text":[{"type":"text","text":{"content":"🗺️ Carte CRAIE"}}],"children":craie_blocks}
            })
    except Exception as e:
        print(f"  ⚠️ Erreur génération CRAIE: {e}")

    # 2e. Logigramme (flowchart TB — arbre décisionnel phases)
    try:
        logigramme_code = generate_flowchart(proc)
        if logigramme_code:
            logi_blocks = [
                {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"📋 Logigramme opérationnel"}}]}},
                {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Déroulement phase par phase avec acteurs et décisions"}}]}},
                {"object":"block","type":"code","code":{"rich_text":[{"type":"text","text":{"content":logigramme_code}}],"language":"mermaid"}},
            ]
            blocks.append({
                "object":"block","type":"toggle",
                "toggle":{"rich_text":[{"type":"text","text":{"content":"📋 Logigramme"}}],"children":logi_blocks}
            })
    except Exception as e:
        print(f"  ⚠️ Erreur génération logigramme: {e}")

    # 2f. Diagramme de séquence (vue acteurs)
    try:
        seq_code = generate_sequence_diagram(proc)
        if seq_code:
            seq_blocks = [
                {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"👥 Diagramme de séquence — Vue acteurs"}}]}},
                {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Interactions entre acteurs par phase"}}]}},
                {"object":"block","type":"code","code":{"rich_text":[{"type":"text","text":{"content":seq_code}}],"language":"mermaid"}},
            ]
            blocks.append({
                "object":"block","type":"toggle",
                "toggle":{"rich_text":[{"type":"text","text":{"content":"👥 Diagramme séquence"}}],"children":seq_blocks}
            })
    except Exception as e:
        print(f"  ⚠️ Erreur génération séquence: {e}")

    # 2g. Matrice des risques (Mermaid quadrantChart)
    risks_detail = proc.get("risks_detail", proc.get("risks", []))
    if risks_detail:
        try:
            mermaid_code = generate_risk_matrix(
                contract=proc,
                mode="RB-RN",
                procedure_title=f"{proc.get('procedure_id','')} - {proc.get('titre','')}"
            )
            if mermaid_code:
                matrix_blocks = [
                    {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"📊 Matrice des risques P×I"}}]}},
                    {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Superposition RB (brut, noir) + RN (net, bleu)"}}]}},
                    {"object":"block","type":"code","code":{"rich_text":[{"type":"text","text":{"content":mermaid_code}}],"language":"mermaid"}},
                ]
                blocks.append({
                    "object":"block","type":"toggle",
                    "toggle":{
                        "rich_text":[{"type":"text","text":{"content":f"📊 Matrice risques ({len(risks_detail)})"}}],
                        "children":matrix_blocks
                    }
                })
        except Exception as e:
            print(f"  ⚠️ Erreur génération matrice risques: {e}")

    # 3. Liens vers les BDD satellites
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    blocks.append({
        "object": "block", "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": "🔗 Bases liées : SBRX (risques) · GED (documents) · PMRI (mesures) · FAQ (questions)"}}],
            "icon": {"emoji": "🔗"},
            "color": "gray_background"
        }
    })
    
    return blocks


# ─── Pipeline principal ──────────────────────────────────────────────────────

def publish_procedure(contract_path, publish=False):
    """Exécute le pipeline complet pour une procédure."""
    token = os.environ.get("NOTION_API_KEY", "")
    if not token:
        print("❌ NOTION_API_KEY non défini")
        return False
    
    # Étape 0 : Charger contrat
    print(f"\n{'='*60}")
    print(f"📋 Pipeline DB-Centric V2")
    print(f"{'='*60}")
    
    with open(contract_path) as f:
        raw = json.load(f)
    contract = raw.get("procedure", raw)
    
    pid = contract.get("procedure_id", "???")
    titre = contract.get("titre", "Sans titre")
    print(f"\n📄 {pid} — {titre}")
    
    # Étape 1 : Trouver DOX
    print(f"\n🔍 Étape 1 — Entrée DOX...")
    dox_entry = find_dox_entry(pid)
    
    # Étape 2 : Trouver/créer MYTHIQUE
    print(f"\n📄 Étape 2 — Page MYTHIQUE...")
    existing_page = find_mythique_page(pid)
    
    if existing_page:
        page_id = existing_page["id"]
        props = build_properties(contract, dox_entry)
        result = notion_patch(f"https://api.notion.com/v1/pages/{page_id}", {"properties": props}, token)
        if result:
            print(f"  ✅ Propriétés mises à jour")
    else:
        print(f"  🆕 Aucune page MYTHIQUE existante pour {pid}")
        if not publish:
            print(f"  ℹ️ Utilisez --publish pour créer la page")
            return True
        new_page = create_mythique_page(pid, contract, dox_entry)
        if not new_page:
            print(f"  ❌ Échec création — abandon")
            return False
        page_id = new_page["id"]
    
    # Défauts : Rédacteur, Validateur, Dernière revue (via Annuaire Service)
    if publish:
        try:
            auteur = annuaire_get_default_author()
            auteur_id = auteur["id"]
            print(f"  👤 Rédacteur/Validateur : {auteur.get('email', auteur_id[:8])}")
        except Exception:
            auteur_id = "12f1d81e-4c39-81af-b875-e5c5364a397c"  # fallback AVR2
            print(f"  ⚠️ Annuaire indisponible, fallback AVR2")
        today = datetime.now().strftime("%Y-%m-%d")
        notion_request("PATCH", f"https://api.notion.com/v1/pages/{page_id}",
            {"properties": {
                "Rédacteur": {"relation": [{"id": auteur_id}]},
                "Validateur": {"relation": [{"id": auteur_id}]},
                "Dernière revue procédure": {"date": {"start": today}}
            }})
        print(f"  ✅ Défauts appliqués : Rédacteur/Validateur, Dernière revue ({today})")

    # Étape 2b : Enregistrement dans PAGES BUS
    if publish:
        print(f"\n🗄️ Étape 2b — PAGES BUS...")
        bus_entry = bus_find_by_canonical_id(pid)
        if bus_entry:
            print(f"  ℹ️ Page BUS existe déjà : {bus_entry['nom']} ({bus_entry['id'][:8]})")
        else:
            canonique_id = pid
            result = bus_create_entry(
                nom=f"{pid} — {titre}",
                type_entite="Procédure",
                id_canonique=canonique_id,
                description=titre,
                version=contract.get("version", "1.0"),
            )
            if result:
                print(f"  ✅ Page BUS créée : {result['id'][:8]}")
            time.sleep(BATCH_DELAY)

    # Étape 2c : Rapport de lecture initial
    if publish:
        print(f"\n📋 Étape 2c — Rapport de lecture...")
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            rapport_payload = {
                "parent": {"database_id": RAPPORT_LECTURE_DB, "type": "database_id"},
                "properties": {
                    "Titre": {"title": [{"text": {"content": f"RL — {pid} — {today}"}}]},
                    "Date": {"date": {"start": today}},
                    "MYTHIQUE": {"relation": [{"id": page_id}]},
                    "Statut": {"status": {"name": "Initial"}},
                    "Date dernière revue": {"date": {"start": today}},
                }
            }
            rapport = notion_request("POST", "https://api.notion.com/v1/pages", rapport_payload)
            if rapport:
                print(f"  ✅ Rapport de lecture créé ({rapport['id'][:8]})")
        except Exception as e:
            print(f"  ⚠️ Rapport de lecture non créé: {e}")
        time.sleep(BATCH_DELAY)
    else:
        print(f"\n📋 Étape 2c — Rapport de lecture... ignoré (--publish requis)")

    # ──── DEBUT ETAPES 3-4 : satellites SBRX / PMRI / FAQ / Glossaire / Règles / Consignes / GED ────

    # Étape 3 : Peupler SBRX
    print(f"\n⚠️ Étape 3 — Risques SBRX...")
    risks = parse_risks(contract)
    print(f"  {len(risks)} risque(s) détecté(s)")
    sbrx_pages = populate_sbrx(risks, page_id, token)

    # Étape 3b : Peupler PMRI
    print(f"\n📏 Étape 3b — Mesures PMRI...")
    mesures = parse_pmri(contract)
    print(f"  {len(mesures)} mesure(s) détectée(s)")
    sbrx_map = {}
    for p in (sbrx_pages or []):
        props = p.get("properties", {})
        code = extract_prop(props.get("Titre", {}))[:10]
        sbrx_map[code] = p["id"]
    pmri_pages = populate_pmri(mesures, page_id, sbrx_map, token) if mesures else []

    # Étape 3c : Peupler FAQ
    print(f"\n❓ Étape 3c — FAQ...")
    faqs = parse_faq(contract)
    print(f"  {len(faqs)} FAQ(s) détectée(s)")
    faq_pages = populate_faq(faqs, token) if faqs else []

    # Étape 3d : Peupler Glossaire (définitions)
    if publish:
        print(f"\n📖 Étape 3d — Glossaire...")
        gloss_entries = parse_glossary(contract)
        print(f"  {len(gloss_entries)} définition(s) détectée(s)")
        if gloss_entries:
            populate_glossary(gloss_entries, page_id, token)

    # Étape 3e : Peupler Règles de gestion
    if publish:
        print(f"\n⚖️ Étape 3e — Règles de gestion...")
        regle_entries = parse_exigences(contract, "regles")
        print(f"  {len(regle_entries)} règle(s) détectée(s)")
        if regle_entries:
            populate_exigences(regle_entries, page_id, token, "Regle")

    # Étape 3f : Peupler Consignes de sécurité
    if publish:
        print(f"\n🔒 Étape 3f — Consignes de sécurité...")
        consigne_entries = parse_exigences(contract, "consignes")
        print(f"  {len(consigne_entries)} consigne(s) détectée(s)")
        if consigne_entries:
            populate_exigences(consigne_entries, page_id, token, "Consigne")

    # Étape 4 : Peupler GED
    print(f"\n📄 Étape 4 — Documents GED...")
    documents = parse_documents(contract)
    print(f"  {len(documents)} document(s) détecté(s)")
    ged_pages = populate_ged(documents, page_id, token)

    # Lier FAQ liée sur MYTHIQUE
    if publish and faq_pages:
        faq_ids = [p["id"] for p in faq_pages if p.get("id")]
        if faq_ids:
            notion_request("PATCH", f"https://api.notion.com/v1/pages/{page_id}",
                {"properties": {"FAQ liée": {"relation": [{"id": fid} for fid in faq_ids]}}})
            print(f"  ✅ FAQ liée mise à jour ({len(faq_ids)} FAQ)")
        time.sleep(BATCH_DELAY)

    # Lier Document GED sur MYTHIQUE
    if publish and ged_pages:
        ged_ids = [p["id"] for p in ged_pages if p.get("id")]
        if ged_ids:
            notion_request("PATCH", f"https://api.notion.com/v1/pages/{page_id}",
                {"properties": {"Document GED": {"relation": [{"id": gid} for gid in ged_ids]}}})
            print(f"  ✅ Document GED mis à jour ({len(ged_ids)} documents)")
        time.sleep(BATCH_DELAY)

    # Étape 4b : Relations inverses (bidirectionnelles)
    if publish and sbrx_pages:
        print(f"\n🔗 Étape 4b — Relations inverses...")
        # Risques liés (SBRX → MYTHIQUE)
        sbrx_ids = [p["id"] for p in sbrx_pages if p.get("id")]
        if sbrx_ids:
            notion_request("PATCH", f"https://api.notion.com/v1/pages/{page_id}",
                {"properties": {"Risques liés": {"relation": [{"id": sid} for sid in sbrx_ids]}}})
            print(f"  ✅ Risques liés mis à jour ({len(sbrx_ids)} risques)")
        # Mesures PMRI (PMRI → MYTHIQUE)
        pmri_ids = [p["id"] for p in pmri_pages if p.get("id")]
        if pmri_ids:
            notion_request("PATCH", f"https://api.notion.com/v1/pages/{page_id}",
                {"properties": {"Mesures PMRI": {"relation": [{"id": mid} for mid in pmri_ids]}}})
            print(f"  ✅ Mesures PMRI mises à jour ({len(pmri_ids)} mesures)")
        time.sleep(BATCH_DELAY)

    # Étape 4c : BUS linking — lier MYTHIQUE ↔ PAGES BUS
    if publish:
        print(f"\n🔁 Étape 4c — Liaison BUS inverse...")
        bus_entry = bus_find_by_canonical_id(pid)
        if bus_entry:
            # Lier MYTHIQUE vers PAGES BUS
            notion_request("PATCH", f"https://api.notion.com/v1/pages/{page_id}",
                {"properties": {"Pages liées (Bus)": {"relation": [{"id": bus_entry["id"]}]}}})
            print(f"  ✅ MYTHIQUE ← PAGES BUS lié")
        else:
            print(f"  ⚠️ Aucune entrée BUS trouvée pour {pid}")
        time.sleep(BATCH_DELAY)

    # Étape 5 : Dashboard visuel
    print(f"\n🎨 Étape 5 — Dashboard visuel...")
    dashboard_blocks = build_dashboard_blocks(contract, sbrx_pages if sbrx_pages else [], ged_pages if ged_pages else [])

    if dashboard_blocks:
        # Nettoyer les anciens blocs dashboard avant d'ajouter les nouveaux
        existing_children = fetch_children(page_id)
        if existing_children:
            child_ids = [c["id"] for c in existing_children]
            print(f"  🧹 Suppression de {len(child_ids)} ancien(s) bloc(s) dashboard...")
            delete_children(child_ids)
            time.sleep(BATCH_DELAY)

        # Envoyer par lots de 50
        for i in range(0, len(dashboard_blocks), 50):
            chunk = dashboard_blocks[i:i+50]
            result = notion_request(
                "PATCH",
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                {"children": chunk},
            )
            if result:
                print(f"  ✅ Lot {i//50+1}/{(len(dashboard_blocks)-1)//50+1} ajouté ({len(chunk)} blocs)")
            time.sleep(BATCH_DELAY)

    print(f"\n{'='*60}")
    print(f"✅ Pipeline terminé pour {pid}")
    print(f"{'='*60}")
    return True


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline DB-Centric V2")
    parser.add_argument("contract", help="Chemin vers le contrat JSON")
    parser.add_argument("--publish", action="store_true", help="Publier sur Notion")
    args = parser.parse_args()
    
    publish_procedure(args.contract, publish=args.publish)
