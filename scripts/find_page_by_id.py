#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
find_page_by_id.py — Recherche une page Notion par identifiant de procédure

Recherche une page existante dans la BDD MYTHIQUE par :
  1. Filtre rich_text sur "Code procédure" (si property_type=rich_text)
  2. Fallback : recherche par titre avec le pattern "{titre} ({id})"
  3. Fallback ultime : scan complet et extraction unique_id

Usage:
    python3 find_page_by_id.py <procedure_id>
    python3 find_page_by_id.py M1-P3-01

Retourne :
    page_id si trouvé, sinon code 1 (rien sur stdout)
"""

import json
import os
import re
import sys

# Ajouter le répertoire scripts au path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from notion_shared import (
    notion_request,
    notion_query,
    extract_prop,
    extract_title,
    extract_procedure_id,
    PROP_MAP,
    MYTHIQUE_PROP_MAP,
    MYTHIQUE_DATABASE_ID,
    MYTHIQUE_DATA_SOURCE_ID,
)


def find_page_by_id(procedure_id):
    """Recherche une page par procedure_id dans la BDD MYTHIQUE."""
    if not procedure_id:
        return None

    # ── Stratégie 1 : Filtre rich_text sur "Code procédure" ─────────
    try:
        code_proc_name = MYTHIQUE_PROP_MAP.get("procedure_id", "Code procédure")
        results = notion_query(
            database_id=MYTHIQUE_DATABASE_ID,
            filter_prop=code_proc_name,
            filter_value=procedure_id,
        )
        pages = results.get("results", [])
        if pages:
            page_id = pages[0].get("id", "")
            if page_id:
                print(page_id)
                return page_id
    except Exception as e:
        debug(f"Stratégie 1 échouée : {e}")

    # ── Stratégie 2 : Recherche par titre (pattern "{nom} ({id})") ──
    try:
        # Sans connaître le titre exact, on cherche par sous-chaîne
        results = notion_query(
            database_id=MYTHIQUE_DATABASE_ID,
            page_size=100,
        )
        pages = results.get("results", [])
        for page in pages:
            props = page.get("properties", {})
            pid = extract_procedure_id(props)
            title = extract_title(props)

            if pid == procedure_id:
                page_id = page.get("id", "")
                if page_id:
                    print(page_id)
                    return page_id

            # Fallback sur le titre
            if procedure_id in title:
                page_id = page.get("id", "")
                if page_id:
                    print(page_id)
                    return page_id

        # Pagination si plus de 100 pages
        cursor = results.get("next_cursor")
        while cursor:
            results = notion_query(
                database_id=MYTHIQUE_DATABASE_ID,
                page_size=100,
                start_cursor=cursor,
            )
            pages = results.get("results", [])
            for page in pages:
                props = page.get("properties", {})
                pid = extract_procedure_id(props)
                title = extract_title(props)

                if pid == procedure_id:
                    page_id = page.get("id", "")
                    if page_id:
                        print(page_id)
                        return page_id

                if procedure_id in title:
                    page_id = page.get("id", "")
                    if page_id:
                        print(page_id)
                        return page_id

            cursor = results.get("next_cursor")
    except Exception as e:
        debug(f"Stratégie 2 échouée : {e}")

    return None


def debug(msg):
    """Écrit un message de debug sur stderr."""
    print(f"[DEBUG] {msg}", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print("Usage: find_page_by_id.py <procedure_id>", file=sys.stderr)
        sys.exit(1)

    procedure_id = sys.argv[1].strip()
    if not procedure_id:
        print("Erreur : procedure_id vide", file=sys.stderr)
        sys.exit(1)

    result = find_page_by_id(procedure_id)
    if result:
        sys.exit(0)
    else:
        debug(f"Aucune page trouvée pour {procedure_id}")
        sys.exit(1)


if __name__ == "__main__":
    main()
