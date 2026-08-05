#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_notion.py — Synchronisation bidirectionnelle Notion
=========================================================

Assure la synchronisation des procédures DOX avec la BDD "1 Procédures RH"
sur Notion. Supporte la création, la mise à jour, l'extraction et la gestion
des relations bidirectionnelles.

Fonctions principales :
  - create_procedure_page(procedure_data) → page_id
  - update_procedure_page(page_id, procedure_data) → success
  - set_relations(page_id, relations) → success
  - sync_from_notion(procedure_id) → dict
  - build_properties(procedure_data, dox_contract) → dict

CLI :
  python3 sync_notion.py --push procedure.json
  python3 sync_notion.py --pull <procedure_id>
  python3 sync_notion.py --pull <procedure_id> --output result.json
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notion_shared import (
    get_notion_token,
    build_headers,
    notion_request,
    notion_query,
    extract_prop,
    extract_title,
    extract_procedure_id,
    PROP_MAP,
    REL_MAP,
    MYTHIQUE_PROP_MAP,
    MYTHIQUE_REL_MAP,
    DATABASE_ID,
    MYTHIQUE_DATABASE_ID,
    DATA_SOURCE_ID,
    NOTION_VERSION,
    BDD_CANONIQUES,
)


# ═══════════════════════════════════════════════════════════════════
# Construction des propriétés Notion
# ═══════════════════════════════════════════════════════════════════

def build_properties(procedure_data, prop_map=None, database="canonique"):
    """
    Construit le dictionnaire 'properties' pour l'API Notion
    à partir de données canoniques DOX.

    Le mapping utilise PROP_MAP (ou prop_map si fourni) pour convertir
    les noms canoniques en noms réels de propriétés Notion.

    Args:
        procedure_data (dict): Données avec clés canoniques (titre, niveau, etc.)
        prop_map (dict): Map optionnel (ex: MYTHIQUE_PROP_MAP). Par défaut PROP_MAP.
        database (str): "canonique" (select pour Statut) ou "mythique" (status pour Statut)

    Returns:
        dict: Propriétés formatées pour l'API Notion.
    """
    if prop_map is None:
        if database == "mythique":
            from notion_shared import MYTHIQUE_PROP_MAP
            prop_map = MYTHIQUE_PROP_MAP
        else:
            prop_map = PROP_MAP
    properties = {}

    # ── Titre (title) ──
    titre = procedure_data.get("titre", "Procédure sans titre")
    procedure_id = procedure_data.get("procedure_id", "")
    display_title = f"{titre} ({procedure_id})" if procedure_id else titre
    properties[prop_map["titre"]] = {
        "title": [{"type": "text", "text": {"content": display_title}}],
    }

    # ── Priorité / niveau (select) ──
    niveau = procedure_data.get("niveau", "")
    if niveau and "niveau" in prop_map:
        properties[prop_map["niveau"]] = {
            "select": {"name": niveau},
        }

    # ── Statut (select/status) ──
    statut = procedure_data.get("statut", "")
    if statut and "statut" in prop_map:
        if database == "mythique":
            # Statut MYTHIQUE : utiliser les noms exacts avec emoji
            statut_map = {
                "À faire": "🔲 À faire",
                "En cours": "🚧 En cours",
                "Terminé": "✅ Terminé",
                "À valider": "🚧 En cours",
                "Brouillon": "🔲 À faire",
                "Publié": "✅ Terminé",
            }
            mapped_statut = statut_map.get(statut, statut)
            properties[prop_map["statut"]] = {
                "status": {"name": mapped_statut},
            }
        else:
            properties[prop_map["statut"]] = {
                "select": {"name": statut},
            }

    # ── Validation (select) ──
    validation = procedure_data.get("validation", "")
    if validation and "validation" in prop_map:
        properties[prop_map["validation"]] = {
            "select": {"name": validation},
        }

    # ── Progression (number) ──
    progression = procedure_data.get("progression")
    if progression is not None and "progression" in prop_map:
        properties[prop_map["progression"]] = {"number": int(progression)}

    # ── ULTRA (checkbox) ──
    ultra = procedure_data.get("ultra", False)
    if "ultra" in prop_map:
        properties[prop_map["ultra"]] = {"checkbox": bool(ultra)}

    # ── Vérifiée (status) ──
    verifiee = procedure_data.get("verifiee", "")
    if verifiee and "verifiee" in prop_map:
        properties[prop_map["verifiee"]] = {
            "status": {"name": verifiee},
        }

    # ── Direction / Service / Pôle (select) ──
    for key, prop_name in [("direction", "direction"), ("service", "service"),
                            ("pole", "pole")]:
        val = procedure_data.get(key, "")
        if val and prop_name in prop_map:
            properties[prop_map[prop_name]] = {"select": {"name": val}}

    # ── Champs rich_text ──
    rich_text_keys = [
        "objet", "pilote", "regles", "consignes", "acteurs",
        "logigramme", "risques", "definitions", "champ_application",
        "localisation", "documents_reference", "documents_supports",
        "domaines", "activites", "observations", "version",
        "procedure_id",  # Code procédure dans MYTHIQUE
    ]
    for key in rich_text_keys:
        val = procedure_data.get(key, "")
        if val and key in prop_map:
            text_content = val if isinstance(val, str) else str(val)
            if text_content.strip():
                properties[prop_map[key]] = {
                    "rich_text": [
                        {"type": "text", "text": {"content": text_content}},
                    ],
                }

    # ── Date d'actualisation / Dernière revue ──
    # Pour la BDD canonique : Date_Actualisation
    # Pour MYTHIQUE : Dernière revue procédure
    date_act = procedure_data.get("date_actualisation", "")
    if date_act:
        if "date_actualisation" in prop_map:
            properties[prop_map["date_actualisation"]] = {"date": {"start": date_act}}
        if "derniere_revue" in prop_map:
            properties[prop_map["derniere_revue"]] = {"date": {"start": date_act}}

    # ── Périodicité revue (select) ──
    periodicite = procedure_data.get("periode_revue", "") or procedure_data.get("periodicite_revue", "")
    if periodicite and "periodicite_revue" in prop_map:
        properties[prop_map["periodicite_revue"]] = {
            "select": {"name": periodicite.capitalize()},
        }

    # ── Rédacteur / Validateur (relations Annuaire Global, MYTHIQUE uniquement) ──
    for rel_key, notion_prop in [("redacteur", "Rédacteur"), ("validateur", "Validateur")]:
        rel_ids = procedure_data.get(rel_key, [])
        if rel_ids and notion_prop:
            properties[notion_prop] = {
                "relation": [{"id": rid} for rid in rel_ids if rid],
            }

    # ── Contrat DOX (stocké dans Documents de référence) ──
    dox_contract = procedure_data.get("dox_contract", {})
    if dox_contract:
        contract_text = json.dumps(dox_contract, ensure_ascii=False, indent=2)
        properties["DOX Contract"] = {
            "rich_text": [
                {"type": "text", "text": {"content": contract_text}},
            ],
        }

    # ── Référence Métiers (number) ──
    ref_metiers = procedure_data.get("reference_metiers")
    if ref_metiers is not None and "reference_metiers" in prop_map:
        properties[prop_map["reference_metiers"]] = {
            "number": int(ref_metiers),
        }

    # ── Sections OR (multi_select, MYTHIQUE) ──
    sections_or = procedure_data.get("sections_or", [])
    if sections_or and "sections_or" in prop_map:
        properties[prop_map["sections_or"]] = {
            "multi_select": [{"name": s} for s in sections_or if s],
        }

    return properties


# ═══════════════════════════════════════════════════════════════════
# Création d'une page procédure
# ═══════════════════════════════════════════════════════════════════

def create_procedure_page(procedure_data, database="canonique"):
    """
    Crée une nouvelle page procédure dans la BDD Notion.

    Args:
        procedure_data (dict): Données de la procédure (clés canoniques DOX).
        database (str): "canonique" (1 Procédures RH) ou "mythique" (MYTHIQUE).

    Returns:
        dict: Info de la page créée {page_id, url}.
    """
    is_mythique = database == "mythique"
    prop_map = MYTHIQUE_PROP_MAP if is_mythique else PROP_MAP
    db_id = MYTHIQUE_DATABASE_ID if is_mythique else DATABASE_ID

    properties = build_properties(procedure_data, prop_map=prop_map, database=database)

    # Étape 1 : Créer la page avec les propriétés SEULEMENT
    # (Option B : éviter la limite 100 blocks de POST /v1/pages)
    payload = {
        "parent": {"database_id": db_id},
        "properties": properties,
    }

    url = "https://api.notion.com/v1/pages"
    response = notion_request("POST", url, payload)

    page_id = response.get("id", "")
    if not page_id:
        raise RuntimeError("Création de page échouée : ID non reçu")

    # Étape 2 : Ajouter le contenu markdown en lots de 50 blocks
    contenu = procedure_data.get("contenu_markdown", "")
    if contenu:
        new_blocks = _markdown_to_notion_blocks(contenu)
        if new_blocks:
            _append_blocks_batch(page_id, new_blocks, chunk_size=50)

    return {
        "page_id": page_id,
        "url": response.get("url", f"https://app.notion.com/{page_id.replace('-', '')}"),
    }


# ═══════════════════════════════════════════════════════════════════
# Mise à jour d'une page existante
# ═══════════════════════════════════════════════════════════════════

def _get_all_block_ids(page_id):
    """
    Récupère TOUS les IDs de blocks d'une page Notion (gère la pagination).

    Args:
        page_id (str): ID Notion de la page.

    Returns:
        list: Liste de tous les IDs de blocks.
    """
    block_ids = []
    cursor = None
    while True:
        url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
        if cursor:
            url += f"&start_cursor={cursor}"
        try:
            resp = notion_request("GET", url)
            block_ids.extend(b["id"] for b in resp.get("results", []))
            if resp.get("has_more") and resp.get("next_cursor"):
                cursor = resp["next_cursor"]
            else:
                break
        except RuntimeError:
            break
    return block_ids


def _append_blocks_batch(page_id, blocks, chunk_size=50):
    """
    Ajoute des blocs Notion à une page par lots.

    Args:
        page_id (str): ID Notion de la page.
        blocks (list): Liste d'objets block Notion.
        chunk_size (int): Taille max par requête PATCH (API Notion limite à 50).

    Returns:
        bool: True si tous les lots ont été envoyés avec succès.
    """
    for i in range(0, len(blocks), chunk_size):
        chunk = blocks[i:i + chunk_size]
        try:
            append_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
            notion_request("PATCH", append_url, {"children": chunk})
        except RuntimeError:
            return False
        # Délai anti-rate-limit (Notion: 3 req/s max)
        time.sleep(1.5)
    return True


def _update_page_blocks(page_id, md_content):
    """
    Remplace le contenu (blocks) d'une page Notion existante.

    Supprime TOUS les blocks existants (avec pagination), puis ajoute
    les nouveaux blocks convertis depuis le markdown.

    Args:
        page_id (str): ID Notion de la page.
        md_content (str): Contenu markdown à convertir en blocks.

    Returns:
        bool: True si la mise à jour a réussi.
    """
    if not md_content:
        return True

    # 1. Récupérer TOUS les blocks existants (pagination gérée)
    block_ids = _get_all_block_ids(page_id)

    # 2. Supprimer les blocks existants (un par un)
    for bid in block_ids:
        try:
            notion_request("DELETE", f"https://api.notion.com/v1/blocks/{bid}")
        except RuntimeError:
            pass  # Si un block ne peut pas être supprimé, on continue

    # 3. Ajouter les nouveaux blocks par lots (via helper partagé)
    new_blocks = _markdown_to_notion_blocks(md_content)
    if new_blocks:
        if not _append_blocks_batch(page_id, new_blocks, chunk_size=50):
            return False

    return True


def update_procedure_page(page_id, procedure_data, database="canonique"):
    """
    Met à jour une page procédure existante dans Notion.

    Met à jour les propriétés ET le contenu (blocks) si
    ``contenu_markdown`` est fourni.

    Args:
        page_id (str): ID Notion de la page.
        procedure_data (dict): Données à mettre à jour.
        database (str): "canonique" ou "mythique".

    Returns:
        bool: True si la mise à jour a réussi.
    """
    prop_map = MYTHIQUE_PROP_MAP if database == "mythique" else PROP_MAP
    properties = build_properties(procedure_data, prop_map=prop_map, database=database)

    if properties:
        payload = {"properties": properties}
        url = f"https://api.notion.com/v1/pages/{page_id}"
        notion_request("PATCH", url, payload)

    # Mise à jour du contenu (blocks)
    contenu = procedure_data.get("contenu_markdown", "")
    if contenu:
        return _update_page_blocks(page_id, contenu)

    return True


# ═══════════════════════════════════════════════════════════════════
# Relations bidirectionnelles
# ═══════════════════════════════════════════════════════════════════

def set_relations(page_id, relations):
    """
    Définit les relations bidirectionnelles d'une page procédure.

    Lie la procédure aux entrées des BDD satellites :
    Organigramme, Annuaire, SBRX Risques, MPPC, GED Documents, etc.

    Args:
        page_id (str): ID de la page procédure Notion.
        relations (dict): Relations à établir avec les clés REL_MAP :
            - organigramme (list) : IDs Organigramme Structure
            - annuaire (list) : IDs Annuaire
            - sbrx_risques (list) : IDs Risques Spécifiques SBRX
            - mppc (list) : IDs MPPC mesures
            - ged_documents (list) : IDs Documents liés
            - glossaire (list) : IDs Glossaire RH
            - exigences (list) : IDs Exigences (G/C)
            - actions (list) : IDs Actions liées
            - experts (list) : IDs Experts associés
            - etc.

    Returns:
        bool: True si les relations ont été définies.
    """
    properties = {}

    for rel_canon, rel_ids in relations.items():
        if not rel_ids:
            continue

        # Nom réel de la propriété relation dans Notion
        notion_prop_name = REL_MAP.get(rel_canon, rel_canon)
        properties[notion_prop_name] = {
            "relation": [{"id": rid} for rid in rel_ids if rid],
        }

    if not properties:
        return True

    payload = {"properties": properties}
    url = f"https://api.notion.com/v1/pages/{page_id}"
    notion_request("PATCH", url, payload)
    return True


# ═══════════════════════════════════════════════════════════════════
# Extraction (pull) depuis Notion
# ═══════════════════════════════════════════════════════════════════

def sync_from_notion(procedure_id):
    """
    Extrait (pull) les données d'une procédure depuis Notion.

    Args:
        procedure_id (str): ID Notion (page_id) ou ID de procédure
                           (ex: 497 pour CGSS 118 ULTRA).

    Returns:
        dict: Données structurées de la procédure.
    """
    # Essayer d'abord par requête directe de page (si c'est un page_id)
    if procedure_id.startswith("http"):
        # C'est une URL Notion
        page_id = procedure_id.split("/")[-1].split("-")[-1]
        if len(page_id) == 32:
            procedure_id = page_id

    if len(procedure_id) == 36 and "-" in procedure_id:
        # C'est probablement un page_id UUID
        try:
            url = f"https://api.notion.com/v1/pages/{procedure_id}"
            response = notion_request("GET", url)
            return _parse_page_response(response)
        except RuntimeError:
            pass

    # Recherche dans la BDD par titre ou par ID numérique
    try:
        resp = notion_query(data_source_id=DATA_SOURCE_ID, page_size=100)
        results = resp if isinstance(resp, list) else resp.get("results", [])
    except RuntimeError as e:
        raise RuntimeError(f"Erreur lors de la recherche : {e}")

    for page in results:
        props = page.get("properties", {})
        pid = extract_procedure_id(props)
        titre = extract_title(props)

        # Match par ID de procédure (numéro)
        if pid and pid.split("-")[-1] == procedure_id:
            url = f"https://api.notion.com/v1/pages/{page['id']}"
            response = notion_request("GET", url)
            return _parse_page_response(response)

        # Match par titre
        if procedure_id.lower() in titre.lower():
            url = f"https://api.notion.com/v1/pages/{page['id']}"
            response = notion_request("GET", url)
            return _parse_page_response(response)

    raise RuntimeError(
        f"Aucune procédure trouvée avec l'ID : {procedure_id}"
    )


def _parse_page_response(response):
    """
    Parse la réponse d'une page Notion en données structurées.

    Args:
        response (dict): Réponse JSON de l'API Notion.

    Returns:
        dict: Données parsées avec toutes les propriétés.
    """
    props = response.get("properties", {})
    page_id = response.get("id", "")

    result = {
        "page_id": page_id,
        "url": response.get("url", ""),
        "proprietes": {},
        "relations": {},
    }

    for prop_name, prop_value in props.items():
        value = extract_prop(prop_value)
        result["proprietes"][prop_name] = value

        # Extraire les relations séparément
        if prop_value.get("type") == "relation" and isinstance(value, list):
            result["relations"][prop_name] = value

        # Extraire le titre
        if prop_value.get("type") == "title":
            result["titre"] = value

        # Extraire le Procedure_ID (format PRH-xxx)
        # Note: data_source query retourne prefix=null, number=N
        if prop_value.get("type") == "unique_id":
            uid = prop_value.get("unique_id", {})
            prefix = uid.get("prefix") or ""
            number = uid.get("number")
            if prefix and number is not None:
                result["procedure_id"] = f"{prefix}-{number}"
            elif number is not None:
                # data_source ne retourne pas le prefix → utiliser juste le numéro
                result["procedure_id"] = str(number)
            else:
                result["procedure_id"] = ""

    return result


# ═══════════════════════════════════════════════════════════════════
# Convertisseur Markdown → Blocks Notion
# ═══════════════════════════════════════════════════════════════════

import re

def _parse_inline_formatting(text):
    """
    Parse le formatage inline markdown en rich_text Notion.
    
    Gère : **gras**, *italique*, `code`, ~~barré~~, [liens](url)
    Retourne une liste de dicts rich_text Notion.
    """
    if not text:
        return [{"type": "text", "text": {"content": ""}}]
    
    # Protection contre les textes trop longs (Notion limite à 2000)
    MAX_TEXT = 2000
    
    # Pattern combiné : **gras** | *italique* | ~~barré~~ | `code` | [texte](url)
    pattern = r'(\*\*(.+?)\*\*|\*(.+?)\*|~~(.+?)~~|`(.+?)`|\[([^\]]+)\]\(([^)]+)\))'
    
    segments = []
    last_end = 0
    
    for m in re.finditer(pattern, text):
        # Texte avant ce match
        if m.start() > last_end:
            before = text[last_end:m.start()]
            if before:
                for chunk in _split_long_text(before, MAX_TEXT):
                    segments.append({
                        "type": "text",
                        "text": {"content": chunk},
                    })
        
        matched = m.group(1)
        
        if matched.startswith('**') and matched.endswith('**'):
            content = m.group(2)
            for chunk in _split_long_text(content, MAX_TEXT):
                segments.append({
                    "type": "text",
                    "text": {"content": chunk},
                    "annotations": {"bold": True},
                })
        elif matched.startswith('*') and not matched.startswith('**'):
            content = m.group(3)
            for chunk in _split_long_text(content, MAX_TEXT):
                segments.append({
                    "type": "text",
                    "text": {"content": chunk},
                    "annotations": {"italic": True},
                })
        elif matched.startswith('~~'):
            content = m.group(4)
            for chunk in _split_long_text(content, MAX_TEXT):
                segments.append({
                    "type": "text",
                    "text": {"content": chunk},
                    "annotations": {"strikethrough": True},
                })
        elif matched.startswith('`'):
            content = m.group(5)
            for chunk in _split_long_text(content, MAX_TEXT):
                segments.append({
                    "type": "text",
                    "text": {"content": chunk},
                    "annotations": {"code": True},
                })
        elif matched.startswith('['):
            link_text = m.group(6)
            link_url = m.group(7)
            for chunk in _split_long_text(link_text, MAX_TEXT):
                segments.append({
                    "type": "text",
                    "text": {"content": chunk, "link": {"url": link_url}},
                })
        
        last_end = m.end()
    
    # Reste du texte après le dernier match
    if last_end < len(text):
        rest = text[last_end:]
        if rest:
            for chunk in _split_long_text(rest, MAX_TEXT):
                segments.append({
                    "type": "text",
                    "text": {"content": chunk},
                })
    
    return segments if segments else [{"type": "text", "text": {"content": text[:MAX_TEXT]}}]


def _split_long_text(text, max_len):
    """Découpe un texte long en chunks pour l'API Notion."""
    if not isinstance(text, str) or not text:
        return [""]
    if len(text) <= max_len:
        return [text]
    chunks = []
    for i in range(0, len(text), max_len):
        chunks.append(text[i:i + max_len])
    return chunks


def _build_rich_text(text):
    """Construit rich_text avec parsing inline. Retourne liste de dicts."""
    return _parse_inline_formatting(text)


def _heading_block(level, text):
    """Block titre Notion avec formatage inline."""
    rich_text = _build_rich_text(text)
    return {
        "object": "block",
        "type": level,
        level: {"rich_text": rich_text},
    }


def _callout_block(text, icon="💡", color="gray_background"):
    """Block callout Notion avec formatage inline, icône et couleur.

    Args:
        text (str): Texte du callout (multi-lignes séparées par \\n).
        icon (str): Emoji de l'icône.
        color (str): Couleur d'arrière-plan (gray_background, yellow_background,
                     red_background, blue_background, green_background,
                     purple_background, orange_background).
    """
    rich_text = _build_rich_text(text)
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": rich_text,
            "icon": {"type": "emoji", "emoji": icon},
            "color": color,
        },
    }


def _toggle_block_with_children(title, children_blocks):
    """Block toggle Notion avec enfants (contenu repliable).

    Args:
        title (str): Texte du titre du toggle.
        children_blocks (list): Liste de blocks Notion enfants.
    """
    rich_text = _build_rich_text(title)
    block = {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": rich_text,
        },
    }
    if children_blocks:
        block["toggle"]["children"] = children_blocks
    return block


def _detect_callout_config(text):
    """Détecte l'icône et la couleur d'un callout en fonction du contenu.

    Args:
        text (str): Texte complet du callout (plusieurs lignes).

    Returns:
        tuple: (icon, color)
    """
    t = text.lower()
    if "flash card" in t or "🃏" in text or "résumé exécutif" in t:
        return "⚡", "yellow_background"
    if "⚠️" in text or "vigilance" in t or "risque" in t or "attention" in t:
        return "⚠️", "red_background"
    if "localisation craie" in t or "📍" in text:
        return "🧭", "purple_background"
    if "⚖️" in text or "juridique" in t or "réglementaire" in t:
        return "⚖️", "blue_background"
    if "💡" in text or "conseil" in t or "astuce" in t:
        return "💡", "blue_background"
    if "✅" in text or "validation" in t:
        return "✅", "green_background"
    if "📊" in text or "indicateur" in t or "kpi" in t:
        return "📊", "purple_background"
    if "🔮" in text or "mythique" in t:
        return "🔮", "purple_background"
    if "📋" in text or "référence" in t or "reférence" in t:
        return "📋", "gray_background"
    if "📌" in text or "source" in t:
        return "📌", "green_background"
    if "🔐" in text or "rgpd" in t or "confidentiel" in t:
        return "🔐", "blue_background"
    if "🔄" in text or "version" in t or "tracabilité" in t:
        return "🔄", "orange_background"
    if "🎯" in text or "objectif" in t or "cible" in t:
        return "🎯", "blue_background"
    return "💡", "gray_background"


def _bulleted_item_block(text):
    """Block liste à puces Notion avec formatage inline."""
    rich_text = _build_rich_text(text)
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": rich_text},
    }


def _numbered_item_block(text):
    """Block liste numérotée Notion avec formatage inline."""
    rich_text = _build_rich_text(text)
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": rich_text},
    }


def _paragraph_block(text, wrap_table_row=False):
    """Block paragraphe Notion avec formatage inline."""
    rich_text = _build_rich_text(text)
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": rich_text},
    }


def _code_block(text, language=""):
    """Block code Notion."""
    rich_text = _build_rich_text(text)
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": rich_text,
            "language": language or "plain text",
        },
    }


def _table_row_as_paragraph(line):
    """Convertit une ligne de tableau markdown en paragraphe."""
    cells = [c.strip() for c in line.strip().split("|")[1:-1]]
    return _paragraph_block(" | ".join(cells))


def _markdown_to_notion_blocks(md_text):
    """
    Convertit du texte markdown en blocks Notion (version complète).

    Gère : h1/h2/h3, callout blocks (> ), toggles HTML (details/summary),
           listes (à puces et numérotées), tableaux Markdown, séparateurs,
           blocs de code, formatage inline (gras, italique, code, barré, liens).

    Args:
        md_text (str): Texte markdown.

    Returns:
        list: Liste de blocks Notion.
    """
    blocks = []
    lines = md_text.split("\n")
    i = 0
    in_table = False
    in_code_block = False
    code_buffer = []
    code_lang = ""

    # ── État pour les callouts (> ) ──
    in_callout = False
    callout_buffer = []

    # ── État pour les toggles (<summary> / </details>) ──
    in_toggle = False
    toggle_title = ""
    toggle_buffer = []

    max_blocks = 500  # Limite haute pour éviter les timeouts API

    while i < len(lines) and len(blocks) < max_blocks:
        line = lines[i]
        stripped = line.strip()

        # ════════════════════════════════════════════════════════════
        # Étape 1 : Nettoyer les balises HTML résiduelles
        # ════════════════════════════════════════════════════════════
        cleaned_stripped = stripped
        had_details_close = False
        had_details_open = False
        had_summary = "<summary>" in cleaned_stripped

        # Détection intelligente de </details> :
        #   - Si la ligne se réduit à "</details>" (ou avec whitespace) → vrai close
        #   - Si </details> est noyé dans du texte → simple nettoyage, pas un close
        stripped_of_details = stripped.replace(" ", "").rstrip()
        if stripped_of_details == "</details>":
            had_details_close = True
            cleaned_stripped = ""  # ligne entièrement consommée par le tag
        elif "</details>" in cleaned_stripped:
            # </details> noyé dans du contenu → nettoyer sans fermer le toggle
            cleaned_stripped = cleaned_stripped.replace("</details>", "").strip()

        # Extraire <summary>Title</summary> → Title
        summary_title = None
        if had_summary:
            m = re.search(r'<summary>(.*?)</summary>', cleaned_stripped)
            if m:
                summary_title = m.group(1).strip()
                # Nettoyer la ligne du tag HTML
                cleaned_stripped = cleaned_stripped.replace(m.group(0), "").strip()

        # Nettoyer <details> si présent
        if "<details>" in cleaned_stripped:
            cleaned_stripped = cleaned_stripped.replace("<details>", "").strip()

        # ════════════════════════════════════════════════════════════
        # Étape 2 : Gestion des blocs de code (```)
        # ════════════════════════════════════════════════════════════
        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = stripped[3:].strip()
                code_buffer = []
            else:
                in_code_block = False
                if code_buffer:
                    code_text = "\n".join(code_buffer)
                    blocks.append(_code_block(code_text, code_lang))
                code_buffer = []
                code_lang = ""
            i += 1
            continue

        # ════════════════════════════════════════════════════════════
        # Étape 2bis : LINKED_VIEW — vues liées aux BDD satellites
        # ════════════════════════════════════════════════════════════
        LINKED_VIEW_MAP = {
            "risques":      "8e0efb57-8ac1-4a5d-9a6e-8a59431f9603",
            "documents":    "3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e",
            "mesures_pmri": "6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9",
            "faq":          "3c44d2d1-ee87-44ed-b991-bab4d1e94442",
        }
        linked_view_match = re.match(r'<!--\s*LINKED_VIEW:(\w+)\s*-->', cleaned_stripped)
        if linked_view_match:
            view_key = linked_view_match.group(1)
            db_id = LINKED_VIEW_MAP.get(view_key)
            if db_id:
                blocks.append({
                    "object": "block",
                    "type": "link_to_page",
                    "link_to_page": {
                        "type": "database_id",
                        "database_id": db_id,
                    }
                })
            i += 1
            continue

        if in_code_block:
            code_buffer.append(line)
            i += 1
            continue

        # ════════════════════════════════════════════════════════════
        # Étape 3 : Gestion des toggles HTML (details/summary)
        # ════════════════════════════════════════════════════════════
        # ── Fermeture de toggle : </details> ──
        if had_details_close and in_toggle:
            # Le buffer est passé tel quel au convertisseur récursif
            # qui gère nativement les tableaux, callouts, headings, etc.
            toggle_text = "\n".join(toggle_buffer)
            children = _markdown_to_notion_blocks(toggle_text.strip())
            blocks.append(_toggle_block_with_children(toggle_title, children))
            toggle_buffer = []
            toggle_title = ""
            in_toggle = False

        # ── Ouverture d'un nouveau toggle : <summary> ──
        if summary_title is not None:
            # Si un toggle était déjà ouvert, le fermer d'abord
            if in_toggle:
                children = _markdown_to_notion_blocks("\n".join(toggle_buffer))
                blocks.append(_toggle_block_with_children(toggle_title, children))
                toggle_buffer = []
            toggle_title = summary_title
            in_toggle = True
            toggle_buffer = []

        # ── Si on est dans un toggle, bufferiser la ligne ──
        if in_toggle:
            if had_details_close and not summary_title:
                # C'est juste un </details> de fermeture, ne pas bufferiser
                pass
            elif cleaned_stripped and not had_summary:
                toggle_buffer.append(line)
            i += 1
            continue

        # ════════════════════════════════════════════════════════════
        # Étape 4 : Callout >  (buffered) – doit être AVANT table
        # ════════════════════════════════════════════════════════════
        if cleaned_stripped.startswith("> "):
            in_callout = True
            callout_buffer.append(cleaned_stripped[2:])
            i += 1
            continue

        if in_callout:
            # Flush le callout buffer
            callout_text = "\n".join(callout_buffer)
            icon, color = _detect_callout_config(callout_text)
            blocks.append(_callout_block(callout_text, icon, color))
            in_callout = False
            callout_buffer = []
            # Ne pas continue — traiter cette ligne normalement ci-dessous

        # ════════════════════════════════════════════════════════════
        # Étape 5 : Tableaux Markdown → blocks Notion table
        # ════════════════════════════════════════════════════════════
        if cleaned_stripped.startswith("|") and "|" in cleaned_stripped[1:] and not in_toggle:
            if not in_table:
                in_table = True
                
                # Ligne 1 : header | Col1 | Col2 | Col3 | ...
                header_cells = [c.strip() for c in cleaned_stripped.split("|")[1:-1]]
                n_cols = len(header_cells)
                table_rows = []
                
                # Ligne 1 = header row
                header_row_rich = []
                for cell in header_cells:
                    rich = _parse_inline_formatting(cell.strip())
                    header_row_rich.append(rich)
                table_rows.append(header_row_rich)
                
                # Sauter la ligne de séparation |---|---|
                i += 1
                if i < len(lines):
                    next_line = lines[i].strip().replace("<details>", "").replace("</details>", "").strip()
                    sep_chars = set(next_line.replace("|", "").replace("-", "").replace(":", "").strip())
                    if sep_chars == set() or sep_chars == {''}:
                        i += 1  # skip separator line
                
                # Lire les lignes de données tant qu'elles commencent par |
                has_column_header = True
                while i < len(lines):
                    data_line = lines[i].strip().replace("<details>", "").replace("</details>", "").strip()
                    if data_line.startswith("|") and "|" in data_line[1:]:
                        data_cells = [c.strip() for c in data_line.split("|")[1:-1]]
                        row_rich = []
                        for cell in data_cells:
                            rich = _parse_inline_formatting(cell.strip())
                            row_rich.append(rich)
                        table_rows.append(row_rich)
                        i += 1
                    else:
                        break
                
                # Vider les lignes vides après le tableau
                while i < len(lines) and not lines[i].strip():
                    i += 1
                
                # Construire les blocks table_row
                row_blocks = []
                for row in table_rows:
                    cells = []
                    for cell_rich in row:
                        cells.append(cell_rich)
                    row_blocks.append({
                        "object": "block",
                        "type": "table_row",
                        "table_row": {"cells": cells}
                    })
                
                # Ajouter l'en-tête comme première ligne si identifié
                blocks.append({
                    "object": "block",
                    "type": "table",
                    "table": {
                        "table_width": n_cols,
                        "has_column_header": has_column_header,
                        "has_row_header": False,
                        "children": row_blocks
                    }
                })
                in_table = False
            else:
                in_table = False
                i += 1
            continue

        # ════════════════════════════════════════════════════════════
        # Étape 6 : Titres
        # ════════════════════════════════════════════════════════════
        if cleaned_stripped.startswith("# ") and not cleaned_stripped.startswith("##"):
            blocks.append(_heading_block("heading_1", cleaned_stripped[2:]))
        elif cleaned_stripped.startswith("## ") and not cleaned_stripped.startswith("###"):
            blocks.append(_heading_block("heading_2", cleaned_stripped[3:]))
        elif cleaned_stripped.startswith("### ") and not cleaned_stripped.startswith("####"):
            blocks.append(_heading_block("heading_3", cleaned_stripped[4:]))
        elif cleaned_stripped.startswith("####"):
            blocks.append(_heading_block("heading_4", cleaned_stripped[5:]))
        elif cleaned_stripped.startswith("#####"):
            blocks.append(_heading_block("heading_5", cleaned_stripped[6:]))
        elif cleaned_stripped.startswith("######"):
            blocks.append(_heading_block("heading_6", cleaned_stripped[7:]))

        # ════════════════════════════════════════════════════════════
        # Étape 7 : Séparateur
        # ════════════════════════════════════════════════════════════
        elif cleaned_stripped == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})

        # ════════════════════════════════════════════════════════════
        # Étape 8 : Listes à puces
        # ════════════════════════════════════════════════════════════
        elif cleaned_stripped.startswith("- ") or cleaned_stripped.startswith("* "):
            text = cleaned_stripped[2:].strip()
            if text:
                blocks.append(_bulleted_item_block(text))

        # ════════════════════════════════════════════════════════════
        # Étape 9 : Listes numérotées
        # ════════════════════════════════════════════════════════════
        elif re.match(r'^\d+[\\.\\)]\s', cleaned_stripped):
            text = re.sub(r'^\d+[\\.\\)]\s*', '', cleaned_stripped, count=1)
            if text:
                blocks.append(_numbered_item_block(text))

        # ════════════════════════════════════════════════════════════
        # Étape 10 : Paragraphe (contenu normal)
        # ════════════════════════════════════════════════════════════
        elif cleaned_stripped:
            blocks.append(_paragraph_block(cleaned_stripped))

        # Lignes vides ignorées

        i += 1

    # ── Flush final : callout ou toggle en attente ──
    if in_callout and callout_buffer:
        callout_text = "\n".join(callout_buffer)
        icon, color = _detect_callout_config(callout_text)
        blocks.append(_callout_block(callout_text, icon, color))

    if in_toggle and toggle_title:
        children = _markdown_to_notion_blocks("\n".join(toggle_buffer))
        blocks.append(_toggle_block_with_children(toggle_title, children))

    return blocks


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Synchronisation bidirectionnelle Notion pour DOX_PROC",
    )
    parser.add_argument(
        "--push", type=str, default=None,
        help="Chemin du fichier JSON de la procédure à pousser",
    )
    parser.add_argument(
        "--pull", type=str, default=None,
        help="ID ou titre de la procédure à extraire de Notion",
    )
    parser.add_argument(
        "--update", type=str, default=None,
        help="ID Notion de la page à mettre à jour (avec --push)",
    )
    parser.add_argument(
        "--set-relations", type=str, default=None,
        help="Fichier JSON des relations à établir",
    )
    parser.add_argument(
        "--markdown", "-m", type=str, default=None,
        help="Chemin du fichier markdown (.md) contenant le corps de la procédure à pousser",
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Fichier de sortie",
    )
    parser.add_argument(
        "--database", "-d", type=str, default="canonique",
        choices=["canonique", "mythique"],
        help="Base de données cible : canonique (1 Procédures RH) ou mythique (MYTHIQUE)",
    )

    args = parser.parse_args()

    try:
        if args.push:
            if not os.path.isfile(args.push):
                print(f"Erreur : fichier introuvable — {args.push}",
                      file=sys.stderr)
                sys.exit(1)

            with open(args.push, "r") as f:
                data = json.load(f)

            procedure_data = data.get("procedure", data)

            # Injecter le contenu markdown si fourni
            if args.markdown and os.path.isfile(args.markdown):
                with open(args.markdown, "r") as f:
                    md_content = f.read()
                if md_content.strip():
                    procedure_data["contenu_markdown"] = md_content

            if args.update:
                success = update_procedure_page(args.update, procedure_data, database=args.database)
                if not success:
                    print(json.dumps({"status": "error", "action": "update", "message": "Échec mise à jour des blocks"}, indent=2, ensure_ascii=False))
                    sys.exit(1)
                result = {
                    "status": "ok",
                    "action": "update",
                    "page_id": args.update,
                }
            else:
                created = create_procedure_page(procedure_data, database=args.database)
                result = {
                    "status": "ok",
                    "action": "create",
                    "page_id": created["page_id"],
                    "url": created["url"],
                }

            if args.set_relations:
                if os.path.isfile(args.set_relations):
                    with open(args.set_relations, "r") as f:
                        relations = json.load(f)
                    set_relations(result["page_id"], relations)
                    result["relations_set"] = True

            print(json.dumps(result, indent=2, ensure_ascii=False))

            if args.output:
                with open(args.output, "w") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

        elif args.pull:
            data = sync_from_notion(args.pull)
            if args.output:
                with open(args.output, "w") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"Données extraites dans {args.output}")
            else:
                print(json.dumps(data, indent=2, ensure_ascii=False))

        else:
            parser.print_help()
            sys.exit(1)

    except RuntimeError as e:
        print(json.dumps({
            "status": "error",
            "message": str(e),
        }, indent=2, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
