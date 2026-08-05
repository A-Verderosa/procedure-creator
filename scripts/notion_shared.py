#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
notion_shared.py — Module partagé pour l'API Notion
====================================================

Fournit les fonctions communes à tous les scripts du skill procedure-creator :
  - Détection du token (NOTION_TOKEN, NOTION_API_KEY, fichiers)
  - Requêtes HTTP vers l'API Notion v2025-09-03
  - Extraction/formatage des propriétés Notion
  - Constantes BDD

Usage:
    from notion_shared import (
        get_notion_token, build_headers,
        notion_request, notion_query,
        extract_prop, extract_title,
        DATABASE_ID, DATA_SOURCE_ID,
    )
"""

import json
import os
import sys
import urllib.error
import urllib.request

# ─── Constantes BDD Procédures ───────────────────────────────────────────────

# Data Source de la BDD "1 Procédures RH" (permet le query filtré)
DATA_SOURCE_ID = "b6c395ef-19fc-42d4-95ef-2ca586872139"

# Database ID parente (extrait des pages retournées par le data_source)
DATABASE_ID = "7155819e-29d8-4ba6-be2e-4aaa6b6fee38"

NOTION_VERSION = "2022-06-28"

# Noms réels des propriétés Notion (BDD "1 Procédures RH")
# Découverts via API le 2026-08-01 sur la page CGSS 118 ULTRA

# Mapping : nom canonique DOX → nom réel Notion
PROP_MAP = {
    "titre": "Titre",                              # title
    "procedure_id": "Procedure_ID",                # unique_id (format: None-xxx)
    "statut": "Statut",                            # select (Terminé, En cours, etc.)
    "validation": "Validation",                    # select (1-Brouillon, 2-Production, etc.)
    "niveau": "Priorité",                          # select (0 - Ultra, etc.)
    "objet": "Objet",                              # rich_text
    "pilote": "Pilote procédure",                  # rich_text
    "progression": "Progression",                  # number (0-100)
    "regles": "Règles de gestion",                 # rich_text
    "consignes": "Consignes",                      # rich_text
    "acteurs": "Description des acteurs",          # rich_text
    "logigramme": "Logigramme",                    # rich_text
    "risques": "Risques",                          # rich_text
    "definitions": "Définitions",                  # rich_text
    "champ_application": "Champ d\u2019application",    # rich_text
    "localisation": "Localisation procédure",      # rich_text
    "date_actualisation": "Date_Actualisation",    # date
    "ultra": "ULTRA",                              # checkbox
    "verifiee": "Vérifiée",                        # status (Oui/Non)
    "direction": "Direction",                      # select
    "service": "Service",                          # select
    "pole": "Pole",                                # select
    "domaines": "Domaines",                        # rich_text
    "activites": "Activités",                      # rich_text
    "observations": "Observations",                # rich_text
    "documents_supports": "Documents supports",    # rich_text
    "classification_risques": "Classification risques - Propositions",  # rich_text
    "documents_reference": "Documents de référence",  # rich_text
    "reference_metiers": "Référence_Métiers",      # number
    "sprint": "Sprint",                            # select
    "priorite_revue": "Priorité de revue",         # select
    "url": "URL",                                  # url
    "expertises": "Expertises requises",           # multi_select
    "nocodb_id": "Nocodb_id",                      # rich_text
    "notion_id": "Notion_id",                      # rich_text
    "bprod_uid": "BPROD_UID",                      # rich_text
    "bdia_uid": "BDIA_UID",                        # rich_text
    "bia_uid": "BIA_UID",                          # rich_text
}

# Relations bidirectionnelles
REL_MAP = {
    "organigramme": "Organigramme Structure",
    "annuaire": "Lié à BDD - 7 Annuaire Procedure (BDD - 1 PROCÉDURES RH)",
    "sbrx_risques": "Risques Spécifiques SBRX",
    "mppc": "MPPC (mesures)",
    "ged_documents": "Documents liés",
    "sous_element": "Sous-élément",
    "element_parent": "élément parent",
    "glossaire": "Glossaire RH",
    "exigences": "Exigences (G/C)",
    "actions": "Actions liées",
    "etapes_proc": "Etapes_Proc",
    "notations": "Notations ULTRA",
    "workflows": "Workflows dérivés",
    "faq": "FAQ liées",
    "guides": "Guides agents (MVP)",
    "experts": "Experts associés",
    "intervenant": "Intervenant",
}

# ─── MYTHIQUE / ULTRA — PROP_MAP pour la BDD "DOX BDD — PROCÉDURES MYTHIQUES" ──
# Noms de propriétés réels dans la BDD MYTHIQUE
MYTHIQUE_PROP_MAP = {
    "titre": "Titre",
    "procedure_id": "Code procédure",
    "niveau": "Niveau DOX",
    "statut": "Statut",
    "objet": "Objet",
    "champ_application": "Champ d'application",
    "acteurs": "Acteurs responsables",
    "service": "Service",
    "consignes": "Consignes opérationnelles",
    "regles": "Règles de gestion",
    "documents_reference": "Documents de référence",
    "documents_supports": "Documents support",
    "definitions": "Définitions & glossaire",
    "risques": "Analyse des risques",
    "version": "Version",
    "periodicite_revue": "Périodicité revue",
    "derniere_revue": "Dernière revue procédure",
    "sections_or": "Sections OR",
}

# Relations pour la BDD MYTHIQUE
MYTHIQUE_REL_MAP = {
    "sbrx_risques": "Risques liés",
    "mppc": "Mesures PMRI",
    "ged_documents": "Document GED",
    "faq": "FAQ liée",
}

# ─── MYTHIQUE / ULTRA — base de procédures hub ──────────────────────────────
MYTHIQUE_DATA_SOURCE_ID = "0a1689d5-ec35-4422-95cb-188a1dd35113"
MYTHIQUE_DATABASE_ID = "0a1689d5-ec35-4422-95cb-188a1dd35113"

# BDD satellites MYTHIQUE — IDs résolus
SBRX_MYTHIQUE_DB = "8e0efb57-8ac1-4a5d-9a6e-8a59431f9603"
PMRI_MYTHIQUE_DB = "6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9"
GED_MAIN_DB = "3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e"
FAQ_METIER_DB = "3c44d2d1-ee87-44ed-b991-bab4d1e94442"
GLOSSAIRE_MAIN_DB = "1481d81e-4c39-808a-b304-fd1857c29329"
EXIGENCES_DB = "8e25465d-57b6-42cc-b082-879db77c8493"

# BDD canoniques avec leurs IDs réels
BDD_CANONIQUES = {
    "procedures": {
        "name": "BDD - 1 Procédures RH",
        "type": "data_source",
        "id": DATA_SOURCE_ID,
        "database_id": DATABASE_ID,
    },
    "procedures_mythique": {
        "name": "DOX BDD — PROCÉDURES MYTHIQUES",
        "type": "database",
        "id": MYTHIQUE_DATABASE_ID,
        "database_id": MYTHIQUE_DATABASE_ID,
    },
    "risques_sbrx": {
        "name": "DOX BDD — SBRX MYTHIQUE",
        "type": "database",
        "id": SBRX_MYTHIQUE_DB,
        "database_id": SBRX_MYTHIQUE_DB,
    },
    "annuaire": {
        "name": "DOX BDD — Annuaire",
        "type": "recherche",
        "note": "Data source: 12a1d81e-4c39-801d-af43-edbec3a22b88",
    },
    "organigramme": {
        "name": "DOX BDD - ORGANIGRAMME GLOBAL",
        "type": "recherche",
    },
    "ged": {
        "name": "GED MAIN",
        "type": "database",
        "id": GED_MAIN_DB,
        "database_id": GED_MAIN_DB,
    },
    "mesures_pmri": {
        "name": "DOX BDD — PMRI MYTHIQUE",
        "type": "database",
        "id": PMRI_MYTHIQUE_DB,
        "database_id": PMRI_MYTHIQUE_DB,
    },
    "glossaire": {
        "name": "DOX BDD - GLOSSAIRE MAIN",
        "type": "database",
        "id": GLOSSAIRE_MAIN_DB,
        "database_id": GLOSSAIRE_MAIN_DB,
    },
    "faq": {
        "name": "FAQ METIER",
        "type": "database",
        "id": FAQ_METIER_DB,
        "database_id": FAQ_METIER_DB,
    },
    "exigences_gc": {
        "name": "📏 BDD — Exigences (G/C)",
        "type": "database",
        "id": "2ef82f38-8f6c-4498-8716-4db6cd9247e5",
    },
    "actions": {
        "name": "Suivi des Actions",
        "type": "recherche",
    },
    "agents_ia": {
        "name": "DOX BDD - REGISTRE DES AGENTS IA",
        "type": "recherche",
    },
}


# ─── Token ───────────────────────────────────────────────────────────────────

def get_notion_token():
    """
    Récupère le token API Notion depuis (par ordre de priorité) :
      1. Variable d'environnement NOTION_TOKEN
      2. Variable d'environnement NOTION_API_KEY
      3. Fichier /tmp/notion_token.txt
      4. Fichier ~/.notion_token

    Returns:
        str: Token API Notion.

    Raises:
        RuntimeError: Si aucun token n'est trouvé.
    """
    # 1. NOTION_TOKEN
    token = os.environ.get("NOTION_TOKEN", "")
    if token.strip():
        return token.strip()

    # 2. NOTION_API_KEY
    token = os.environ.get("NOTION_API_KEY", "")
    if token.strip():
        return token.strip()

    # 3. /tmp/notion_token.txt
    for path in ("/tmp/notion_token.txt",
                 os.path.expanduser("~/.notion_token")):
        try:
            with open(path, "r") as f:
                token = f.read().strip()
            if token:
                return token
        except (FileNotFoundError, IOError):
            pass

    raise RuntimeError(
        "Token Notion introuvable. Définissez NOTION_TOKEN ou NOTION_API_KEY "
        "dans l'environnement, ou créez /tmp/notion_token.txt"
    )


def build_headers():
    """Construit les en-têtes HTTP pour l'API Notion."""
    token = get_notion_token()
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


# ─── Requêtes API ───────────────────────────────────────────────────────────

def notion_request(method, url, payload=None, timeout=30):
    """
    Exécute une requête HTTP vers l'API Notion.

    Args:
        method (str): Méthode HTTP (GET, POST, PATCH, DELETE).
        url (str): URL complète de l'API.
        payload (dict, optional): Corps de la requête (sérialisé en JSON).
        timeout (int): Timeout en secondes (défaut: 30).

    Returns:
        dict: Réponse JSON de l'API.

    Raises:
        RuntimeError: En cas d'échec de la requête.
    """
    headers = build_headers()
    data = json.dumps(payload).encode("utf-8") if payload else None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"API Notion [{e.code}] {e.reason} : {error_body[:500]}"
        )
    except urllib.error.URLError as e:
        raise RuntimeError(f"Erreur réseau Notion : {e.reason}")
    except OSError as e:
        raise RuntimeError(f"Erreur de connexion : {e}")


def notion_query(data_source_id=None, database_id=None, filter_prop=None,
                 filter_value=None, page_size=50, start_cursor=None):
    """
    Requête une BDD Notion avec filtre optionnel.

    Supporte deux modes :
      - data_source_id : POST /v1/data_sources/{id}/query
      - database_id    : POST /v1/databases/{id}/query

    Args:
        data_source_id (str, optional): ID du data_source Notion.
        database_id (str, optional): ID de la database Notion.
        filter_prop (str, optional): Nom de la propriété pour le filtre.
        filter_value (str, optional): Valeur du filtre.
        page_size (int): Nombre de résultats (max 100).
        start_cursor (str, optional): Pagination.

    Returns:
        dict: Résultats de la requête.

    Raises:
        RuntimeError: Si aucun ID ou erreur API.
    """
    if data_source_id:
        url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
    elif database_id:
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
    else:
        raise RuntimeError(
            "Spécifiez data_source_id ou database_id pour la requête"
        )

    payload = {"page_size": min(page_size, 100)}
    if start_cursor:
        payload["start_cursor"] = start_cursor

    if filter_prop and filter_value:
        payload["filter"] = {
            "property": filter_prop,
            "rich_text": {"equals": filter_value},
        }

    return notion_request("POST", url, payload)


# ─── Extraction de propriétés ───────────────────────────────────────────────

def extract_prop(prop):
    """
    Extrait la valeur simplifiée d'une propriété Notion.

    Args:
        prop (dict): Propriété Notion (objet JSON de l'API).

    Returns:
        Valeur extraite (str, list, int, bool, etc.).
    """
    if not isinstance(prop, dict):
        return str(prop)

    ptype = prop.get("type", "")

    if ptype == "title":
        parts = prop.get("title", [])
        return "".join(t.get("plain_text", "") for t in parts)

    elif ptype == "rich_text":
        parts = prop.get("rich_text", [])
        return "".join(t.get("plain_text", "") for t in parts)

    elif ptype == "select":
        s = prop.get("select")
        return s.get("name", "") if s else ""

    elif ptype == "multi_select":
        return [s.get("name", "") for s in prop.get("multi_select", [])]

    elif ptype == "number":
        return prop.get("number")

    elif ptype == "date":
        d = prop.get("date")
        return {"start": d.get("start"), "end": d.get("end")} if d else None

    elif ptype == "checkbox":
        return prop.get("checkbox", False)

    elif ptype == "url":
        return prop.get("url", "")

    elif ptype == "email":
        return prop.get("email", "")

    elif ptype == "phone_number":
        return prop.get("phone_number", "")

    elif ptype == "status":
        s = prop.get("status")
        return s.get("name", "") if s else ""

    elif ptype == "relation":
        return [r.get("id", "") for r in prop.get("relation", [])]

    elif ptype == "rollup":
        r = prop.get("rollup", {})
        rtype = r.get("type", "")
        return r.get(rtype, "")

    elif ptype == "unique_id":
        uid = prop.get("unique_id", {})
        prefix = uid.get("prefix", "")
        number = uid.get("number")
        return f"{prefix}-{number}" if prefix and number else str(number) if number else ""

    elif ptype == "created_time":
        return prop.get("created_time", "")

    elif ptype == "last_edited_time":
        return prop.get("last_edited_time", "")

    elif ptype == "created_by":
        user = prop.get("created_by", {})
        return user.get("id", "")

    elif ptype == "last_edited_by":
        user = prop.get("last_edited_by", {})
        return user.get("id", "")

    return str(prop)


def extract_title(properties):
    """
    Extrait le titre (propriété de type 'title') d'un dict de propriétés.

    Args:
        properties (dict): Propriétés Notion (clé → valeur).

    Returns:
        str: Titre extrait, ou chaîne vide.
    """
    for name, prop in properties.items():
        if prop.get("type") == "title":
            parts = prop.get("title", [])
            return "".join(t.get("plain_text", "") for t in parts)
    return ""


def extract_procedure_id(properties):
    """
    Extrait le Procedure_ID (unique_id) d'un dict de propriétés.

    Args:
        properties (dict): Propriétés Notion.

    Returns:
        str: ID de procédure (ex: PRH-042), ou chaîne vide.
    """
    for name, prop in properties.items():
        if prop.get("type") == "unique_id":
            uid = prop.get("unique_id", {})
            prefix = uid.get("prefix", "")
            number = uid.get("number")
            if prefix and number:
                return f"{prefix}-{number}"
            return str(number) if number else ""
    return ""


# ─── Vérification de connexion ──────────────────────────────────────────────

def check_connection():
    """
    Vérifie la connexion à l'API Notion.

    Returns:
        bool: True si la connexion est OK.
    """
    try:
        resp = notion_request("GET", "https://api.notion.com/v1/users/me")
        return resp.get("object") == "user"
    except RuntimeError:
        return False


# ─── Test direct ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test rapide
    try:
        token = get_notion_token()
        print(f"✓ Token trouvé : {token[:8]}... (len={len(token)})")
    except RuntimeError as e:
        print(f"✗ Token : {e}")
        sys.exit(1)

    ok = check_connection()
    print(f"{'✓' if ok else '✗'} Connexion API : {'OK' if ok else 'ÉCHEC'}")

    if not ok:
        sys.exit(1)

    # Test data_source query
    try:
        resp = notion_query(data_source_id=DATA_SOURCE_ID, page_size=2)
        results = resp if isinstance(resp, list) else resp.get("results", [])
        print(f"✓ Data source query : {len(results)} résultat(s)")
        if results:
            title = extract_title(results[0].get("properties", {}))
            pid = extract_procedure_id(results[0].get("properties", {}))
            print(f"  Ex: {pid} — {title[:60]}")
            # Afficher database_id
            parent = results[0].get("parent", {})
            print(f"  Database ID: {parent.get('database_id', '?')}")
    except RuntimeError as e:
        print(f"✗ Data source query : {e}")
