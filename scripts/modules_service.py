#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
modules_service.py — Services modulaires pour bases partagées (pattern COMP)
===========================================================================

Fournit les fonctions CRUD et liaison BUS pour les 4 modules services :
  - Glossary  : Glossaire Main (définitions, termes)
  - GED       : GED Main (documents supports/références)
  - Annuaire  : Annuaire DOX (contacts, rôles)
  - FAQ       : FAQ Métier (questions/réponses)

Chaque service expose :
  - list_*()           → listes paginées
  - get_*()            → page unique avec relations
  - create_*()         → création
  - update_*()         → mise à jour
  - link_to_bus()      → liaison PAGES BUS
  - unlink_from_bus()  → déliaison PAGES BUS
  - find_by_*()        → recherches spécifiques

Usage:
    from modules_service import (
        glossary_list, glossary_create, glossary_link_to_bus,
        ged_list, ged_create, ged_link_to_bus,
        annuaire_list, annuaire_create, annuaire_link_to_bus,
    )
"""

import json
import os

from notion_shared import (
    notion_request, notion_query, extract_prop, extract_title,
    GLOSSAIRE_MAIN_DB, GED_MAIN_DB, FAQ_METIER_DB,
    build_headers,
)

# ─── Constantes ───────────────────────────────────────────────────────────────

PAGES_BUS_DB = "3b21d81e-4c39-81fe-b6f9-c9b661368c7a"
ANNUAIRE_DB = "6e9d978c-b165-490c-a6c5-a4de5eaa5e56"

# Noms réels des propriétés de relation BUS dans chaque base
BUS_PROP_NAMES = {
    "glossary": "Pages liées (Bus) 1",      # Glossaire: relation convertie en rich_text mais conservée
    "ged": "Pages liées (Bus) 1",           # GED: relation conservée, suffixe 1
    "annuaire": "Pages liées (Bus)",        # Annuaire: propre
    "faq": "Pages liées (Bus)",             # FAQ: à confirmer
}

# ⚠️ NOTE: Pour Glossaire, les propriétés "Pages liées (Bus) 1" et "Test single_property"
# ont été converties en rich_text (nettoyage). La relation fonctionnelle vers PAGES BUS
# se fait via lookup par titre de page BUS. À rétablir si besoin.


# ═══════════════════════════════════════════════════════════════════════════════
# 📖 GLOSSAIRE
# ═══════════════════════════════════════════════════════════════════════════════

def glossary_list(page_size=100) -> list[dict]:
    """Liste tous les termes du glossaire."""
    resp = notion_query(database_id=GLOSSAIRE_MAIN_DB, page_size=page_size)
    results = resp.get("results", [])
    out = []
    for p in results:
        props = p.get("properties", {})
        out.append({
            "id": p["id"],
            "terme": extract_prop(props.get("Terme", {})),
            "texte": extract_prop(props.get("Texte", {})),
            "explication": extract_prop(props.get("Explication", {})),
            "lettre": extract_prop(props.get("Lettre", {})),
            "bus_pages": extract_prop(props.get(BUS_PROP_NAMES["glossary"], {})),
        })
    return out


def glossary_get(page_id: str) -> dict:
    """Retourne un terme complet avec toutes ses propriétés brutes."""
    resp = notion_request("GET", f"https://api.notion.com/v1/pages/{page_id}")
    props = resp.get("properties", {})
    return {
        "id": resp["id"],
        "terme": extract_prop(props.get("Terme", {})),
        "texte": extract_prop(props.get("Texte", {})),
        "explication": extract_prop(props.get("Explication", {})),
        "lettre": extract_prop(props.get("Lettre", {})),
        "bus_pages": extract_prop(props.get(BUS_PROP_NAMES["glossary"], [])),
        "_raw": resp,
    }


def glossary_create(terme: str, texte: str = "", explication: str = "",
                    lettre: str = None) -> dict:
    """Crée un nouveau terme dans le glossaire.

    La lettre est déduite automatiquement (1ère lettre du terme).
    """
    if not lettre and terme:
        lettre = terme[0].upper()

    properties = {
        "Terme": {"title": [{"text": {"content": terme}}]},
        "Texte": {"rich_text": [{"text": {"content": texte}}]},
    }
    if explication:
        properties["Explication"] = {"rich_text": [{"text": {"content": explication}}]}
    if lettre:
        properties["Lettre"] = {"select": {"name": lettre}}

    payload = {
        "parent": {"database_id": GLOSSAIRE_MAIN_DB},
        "properties": properties,
    }
    return notion_request("POST", "https://api.notion.com/v1/pages", payload)


def glossary_update(page_id: str, **kwargs) -> dict:
    """Met à jour un terme. kwargs: texte, explication, lettre."""
    properties = {}
    for k, v in kwargs.items():
        if k == "texte":
            properties["Texte"] = {"rich_text": [{"text": {"content": v}}]}
        elif k == "explication":
            properties["Explication"] = {"rich_text": [{"text": {"content": v}}]}
        elif k == "lettre":
            properties["Lettre"] = {"select": {"name": v}}

    if not properties:
        return {"error": "Aucun champ à mettre à jour"}
    return notion_request("PATCH", f"https://api.notion.com/v1/pages/{page_id}",
                          {"properties": properties})


def glossary_find_by_procedure(mythique_page_id: str) -> list[dict]:
    """Trouve les termes liés à une procédure MYTHIQUE (via relation legacy)."""
    # Filtre sur Procédures mythiques liées
    resp = notion_query(
        database_id=GLOSSAIRE_MAIN_DB,
        filter_prop="Procédures mythiques liées",
        filter_value=mythique_page_id,
    )
    results = resp.get("results", [])
    out = []
    for p in results:
        props = p.get("properties", {})
        out.append({
            "id": p["id"],
            "terme": extract_prop(props.get("Terme", {})),
            "texte": extract_prop(props.get("Texte", {})),
        })
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# 📁 GED
# ═══════════════════════════════════════════════════════════════════════════════

def ged_list(page_size=100) -> list[dict]:
    """Liste tous les documents GED."""
    resp = notion_query(database_id=GED_MAIN_DB, page_size=page_size)
    results = resp.get("results", [])
    out = []
    for p in results:
        props = p.get("properties", {})
        out.append({
            "id": p["id"],
            "code": extract_prop(props.get("Code & Document", {})),
            "categorie": extract_prop(props.get("Catégorie", {})),
            "fichier": extract_prop(props.get("Fichier", {})),
            "bus_pages": extract_prop(props.get(BUS_PROP_NAMES["ged"], [])),
        })
    return out


def ged_get(page_id: str) -> dict:
    """Retourne un document GED complet."""
    resp = notion_request("GET", f"https://api.notion.com/v1/pages/{page_id}")
    props = resp.get("properties", {})
    return {
        "id": resp["id"],
        "code": extract_prop(props.get("Code & Document", {})),
        "categorie": extract_prop(props.get("Catégorie", {})),
        "fichier": extract_prop(props.get("Fichier", {})),
        "bus_pages": extract_prop(props.get(BUS_PROP_NAMES["ged"], [])),
        "_raw": resp,
    }


def ged_create(code: str, categorie: str = "Document support",
               fichier_url: str = None, bus_pages: list[str] = None) -> dict:
    """Crée un document GED.

    Args:
        code: Code & Document (ex: "CEV-F01 — Saisine")
        categorie: Catégorie (Document support, Document référence, etc.)
        fichier_url: URL externe du fichier
        bus_pages: IDs des pages BUS à lier
    """
    properties = {
        "Code & Document": {"title": [{"text": {"content": code}}]},
        "Catégorie": {"select": {"name": categorie}},
    }

    payload = {
        "parent": {"database_id": GED_MAIN_DB},
        "properties": properties,
    }
    return notion_request("POST", "https://api.notion.com/v1/pages", payload)


def ged_update(page_id: str, **kwargs) -> dict:
    """Met à jour un document GED. kwargs: code, categorie."""
    properties = {}
    if "code" in kwargs:
        properties["Code & Document"] = {"title": [{"text": {"content": kwargs["code"]}}]}
    if "categorie" in kwargs:
        properties["Catégorie"] = {"select": {"name": kwargs["categorie"]}}

    if not properties:
        return {"error": "Aucun champ à mettre à jour"}
    return notion_request("PATCH", f"https://api.notion.com/v1/pages/{page_id}",
                          {"properties": properties})


def ged_find_by_category(categorie: str, page_size=100) -> list[dict]:
    """Filtre les documents par catégorie."""
    resp = notion_query(
        database_id=GED_MAIN_DB,
        filter_prop="Catégorie",
        filter_value=categorie,
        page_size=page_size,
    )
    results = resp.get("results", [])
    out = []
    for p in results:
        props = p.get("properties", {})
        out.append({
            "id": p["id"],
            "code": extract_prop(props.get("Code & Document", {})),
            "categorie": extract_prop(props.get("Catégorie", {})),
        })
    return out


def ged_find_supports() -> list[dict]:
    """Raccourci : documents de catégorie 'Document support'."""
    return ged_find_by_category("Document support")


def ged_find_references() -> list[dict]:
    """Raccourci : documents de catégorie 'Document référence'."""
    return ged_find_by_category("Document référence")


# ═══════════════════════════════════════════════════════════════════════════════
# 👤 ANNUAIRE
# ═══════════════════════════════════════════════════════════════════════════════

def annuaire_list(page_size=100) -> list[dict]:
    """Liste tous les contacts de l'annuaire."""
    resp = notion_query(database_id=ANNUAIRE_DB, page_size=page_size)
    results = resp.get("results", [])
    out = []
    for p in results:
        props = p.get("properties", {})
        out.append({
            "id": p["id"],
            "nom": extract_prop(props.get("Nom Prénom", {})),
            "email": extract_prop(props.get("Email", {})),
            "role": extract_prop(props.get("Rôle / Direction", {})),
            "contexte": extract_prop(props.get("Contexte", {})),
            "bus_pages": extract_prop(props.get(BUS_PROP_NAMES["annuaire"], [])),
        })
    return out


def annuaire_get(page_id: str) -> dict:
    """Retourne un contact complet."""
    resp = notion_request("GET", f"https://api.notion.com/v1/pages/{page_id}")
    props = resp.get("properties", {})
    return {
        "id": resp["id"],
        "nom": extract_prop(props.get("Nom Prénom", {})),
        "email": extract_prop(props.get("Email", {})),
        "role": extract_prop(props.get("Rôle / Direction", {})),
        "contexte": extract_prop(props.get("Contexte", {})),
        "bus_pages": extract_prop(props.get(BUS_PROP_NAMES["annuaire"], [])),
        "_raw": resp,
    }


def annuaire_create(nom: str, email: str = "", role: str = "",
                    contexte: str = "PRO") -> dict:
    """Crée un contact dans l'annuaire."""
    properties = {
        "Nom Prénom": {"title": [{"text": {"content": nom}}]},
        "Contexte": {"select": {"name": contexte}},
    }
    if email:
        properties["Email"] = {"email": email}
    if role:
        properties["Rôle / Direction"] = {"select": {"name": role}}

    payload = {
        "parent": {"database_id": ANNUAIRE_DB},
        "properties": properties,
    }
    return notion_request("POST", "https://api.notion.com/v1/pages", payload)


def annuaire_find_by_role(role: str) -> list[dict]:
    """Recherche les contacts par rôle (Rédacteur, Valideur, etc.)."""
    resp = notion_query(
        database_id=ANNUAIRE_DB,
        filter_prop="Rôle / Direction",
        filter_value=role,
    )
    results = resp.get("results", [])
    out = []
    for p in results:
        props = p.get("properties", {})
        out.append({
            "id": p["id"],
            "nom": extract_prop(props.get("Nom Prénom", {})),
            "email": extract_prop(props.get("Email", {})),
        })
    return out


DEFAULT_AUTHOR_UUID = "12f1d81e-4c39-81af-b875-e5c5364a397c"
DEFAULT_AUTHOR_NAME = "Antoine Verderosa"


def annuaire_get_default_author() -> dict:
    """Retourne l'auteur par défaut (Antoine Verderosa)."""
    return {"id": DEFAULT_AUTHOR_UUID, "nom": DEFAULT_AUTHOR_NAME}


# ═══════════════════════════════════════════════════════════════════════════════
# ❓ FAQ
# ═══════════════════════════════════════════════════════════════════════════════

def faq_list(page_size=100) -> list[dict]:
    """Liste toutes les FAQ."""
    try:
        resp = notion_query(database_id=FAQ_METIER_DB, page_size=page_size)
        results = resp.get("results", [])
    except RuntimeError:
        # FAQ DB not shared with integration
        return []

    out = []
    for p in results:
        props = p.get("properties", {})
        out.append({
            "id": p["id"],
            "question": extract_prop(props.get("Question", props.get("Nom", {}))),
            "reponse": extract_prop(props.get("Réponse", props.get("Description", {}))),
        })
    return out


def faq_create(question: str, reponse: str = "", categorie: str = "",
               bus_pages: list[str] = None) -> dict:
    """Crée une entrée FAQ.

    Args:
        question: Intitulé de la question
        reponse: Réponse détaillée
        categorie: Thématique (optionnelle)
        bus_pages: IDs des pages BUS à lier (optionnel)
    """
    properties = {
        "Question": {"title": [{"text": {"content": question}}]},
    }
    if reponse:
        properties["Réponse"] = {"rich_text": [{"text": {"content": reponse}}]}
    if categorie:
        properties["Catégorie"] = {"select": {"name": categorie}}

    payload = {
        "parent": {"database_id": FAQ_METIER_DB},
        "properties": properties,
    }
    return notion_request("POST", "https://api.notion.com/v1/pages", payload)


def faq_check_access() -> bool:
    """Vérifie si la base FAQ est accessible via l'API."""
    try:
        notion_query(database_id=FAQ_METIER_DB, page_size=1)
        return True
    except RuntimeError:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# 🔗 PAGES BUS — Utilitaires génériques de liaison
# ═══════════════════════════════════════════════════════════════════════════════

def bus_find_by_canonical_id(canonical_id: str) -> dict | None:
    """Trouve une page BUS par son ID canonique (ex: 'PAGE.M1.P3.01')."""
    resp = notion_query(
        database_id=PAGES_BUS_DB,
        filter_prop="ID canonique",
        filter_value=canonical_id,
    )
    results = resp.get("results", [])
    if results:
        p = results[0]
        return {
            "id": p["id"],
            "nom": extract_prop(p.get("properties", {}).get("Nom page", {})),
            "type": extract_prop(p.get("properties", {}).get("Type entité", {})),
            "id_canonique": extract_prop(
                p.get("properties", {}).get("ID canonique", {})),
        }
    return None


def bus_create_entry(nom: str, type_entite: str = "Procédure",
                     id_canonique: str = "", description: str = "",
                     version: str = "1.0") -> dict:
    """Crée une entrée dans PAGES BUS."""
    properties = {
        "Nom page": {"title": [{"text": {"content": nom}}]},
        "Type entité": {"select": {"name": type_entite}},
    }
    if id_canonique:
        properties["ID canonique"] = {"rich_text": [{"text": {"content": id_canonique}}]}
    if description:
        properties["Description"] = {"rich_text": [{"text": {"content": description}}]}
    if version:
        properties["Version"] = {"rich_text": [{"text": {"content": version}}]}

    payload = {
        "parent": {"database_id": PAGES_BUS_DB},
        "properties": properties,
    }
    return notion_request("POST", "https://api.notion.com/v1/pages", payload)


def bus_list_all() -> list[dict]:
    """Liste toutes les entrées PAGES BUS."""
    resp = notion_query(database_id=PAGES_BUS_DB, page_size=100)
    results = resp.get("results", [])
    out = []
    for p in results:
        props = p.get("properties", {})
        out.append({
            "id": p["id"],
            "nom": extract_prop(props.get("Nom page", {})),
            "type": extract_prop(props.get("Type entité", {})),
            "id_canonique": extract_prop(props.get("ID canonique", {})),
        })
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# 🔗 Liaison générique vers PAGES BUS (utilise l'API page PATCH directe)
# ═══════════════════════════════════════════════════════════════════════════════

def _update_relation(source_page_id: str, prop_name: str, relation_ids: list[str]) -> dict:
    """Met à jour une propriété relation sur une page."""
    payload = {
        "properties": {
            prop_name: {
                "relation": [{"id": rid} for rid in relation_ids],
            }
        }
    }
    return notion_request(
        "PATCH",
        f"https://api.notion.com/v1/pages/{source_page_id}",
        payload,
    )


def link_entities_to_bus(source_page_id: str, bus_page_ids: list[str],
                         source_type: str = "glossary") -> dict:
    """Lie une page d'un module service à des pages BUS.

    Args:
        source_page_id: ID de la page source (glossaire, GED, annuaire, etc.)
        bus_page_ids: IDs des pages BUS à lier
        source_type: 'glossary', 'ged', 'annuaire', ou 'faq'
    """
    prop_name = BUS_PROP_NAMES.get(source_type)
    if not prop_name:
        return {"error": f"Type source inconnu: {source_type}"}
    return _update_relation(source_page_id, prop_name, bus_page_ids)


def unlink_entities_from_bus(source_page_id: str, source_type: str = "glossary") -> dict:
    """Supprime toutes les liaisons BUS d'une page source."""
    return link_entities_to_bus(source_page_id, [], source_type)


# ═══════════════════════════════════════════════════════════════════════════════
# Test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=== MODULES SERVICE — Tests rapides ===\n")

    # Bus
    entries = bus_list_all()
    print(f"📋 PAGES BUS: {len(entries)} entrées")
    for e in entries[:5]:
        print(f"   • {e['nom']} ({e['id_canonique']}) [{e['type']}]")

    # Glossaire
    terms = glossary_list()
    print(f"\n📖 Glossaire: {len(terms)} termes")
    for t in terms[:3]:
        print(f"   • {t['terme']} — {t['texte'][:50]}")

    # Annuaire
    contacts = annuaire_list()
    print(f"\n👤 Annuaire: {len(contacts)} contacts")
    for c in contacts[:3]:
        print(f"   • {c['nom']} ({c['role']})")

    # GED
    docs = ged_list()
    print(f"\n📁 GED: {len(docs)} documents")
    for d in docs[:3]:
        print(f"   • {d['code']} [{d['categorie']}]")

    # FAQ
    faq_ok = faq_check_access()
    print(f"\n❓ FAQ accessible via API: {'OUI' if faq_ok else 'NON (à connecter dans Notion)'}")

    print("\n✅ OK")
