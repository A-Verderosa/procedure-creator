#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup_duplicates.py — Supprime les pages en doublon dans la BDD MYTHIQUE

Usage:
    python3 cleanup_duplicates.py <procedure_id> [--keep PAGE_ID] [--dry-run]

Exemple:
    python3 cleanup_duplicates.py M1-P3-01 --dry-run
    python3 cleanup_duplicates.py M1-P3-01 --keep 3b11d81e-4c39-81ed-900a-e3c974a530d1
"""

import json
import sys
import os

# Ajouter le répertoire scripts au path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from notion_shared import (
    notion_request,
    notion_query,
    extract_title,
    extract_procedure_id,
    MYTHIQUE_DATABASE_ID,
)


def find_all_pages_by_procedure_id(procedure_id):
    """Trouve TOUTES les pages dans MYTHIQUE avec ce procedure_id."""
    pages = []
    cursor = None
    
    while True:
        try:
            results = notion_query(
                database_id=MYTHIQUE_DATABASE_ID,
                page_size=100,
                start_cursor=cursor,
            )
        except RuntimeError:
            break
        
        for page in results.get("results", []):
            props = page.get("properties", {})
            pid = extract_procedure_id(props)
            title = extract_title(props)
            
            if pid == procedure_id or procedure_id in title:
                pages.append({
                    "id": page["id"],
                    "title": title,
                    "url": page.get("url", ""),
                    "created_time": page.get("created_time", ""),
                    "last_edited_time": page.get("last_edited_time", ""),
                })
        
        cursor = results.get("next_cursor")
        if not cursor:
            break
    
    return pages


def delete_page(page_id):
    """Supprime une page Notion en l'archivant."""
    try:
        resp = notion_request(
            "PATCH",
            f"https://api.notion.com/v1/pages/{page_id}",
            {"archived": True},
        )
        return resp.get("archived", False)
    except RuntimeError as e:
        print(f"[ERREUR] Suppression {page_id}: {e}", file=sys.stderr)
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Nettoie les pages en doublon MYTHIQUE")
    parser.add_argument("procedure_id", help="ID de la procédure (ex: M1-P3-01)")
    parser.add_argument("--keep", default="", help="Page_id à conserver (la plus récente)")
    parser.add_argument("--dry-run", action="store_true", help="Simulation sans supprimer")
    
    args = parser.parse_args()
    
    print(f"🔍 Recherche des pages pour : {args.procedure_id}")
    pages = find_all_pages_by_procedure_id(args.procedure_id)
    
    if not pages:
        print("Aucune page trouvée.")
        return
    
    print(f"\n📄 {len(pages)} page(s) trouvée(s) :")
    for i, p in enumerate(pages, 1):
        keep_mark = " ✅ CONSERVÉE" if p["id"] == args.keep else ""
        print(f"  {i}. {p['title']}")
        print(f"     ID: {p['id']}{keep_mark}")
        print(f"     Créée: {p['created_time'][:19]}")
        print(f"     URL: {p['url']}")
        print()
    
    # Si keep non spécifié, garder la plus récente
    if not args.keep:
        pages_sorted = sorted(pages, key=lambda p: p.get("created_time", ""), reverse=True)
        args.keep = pages_sorted[0]["id"]
        print(f"  → Page la plus récente conservée : {args.keep}")
    
    to_delete = [p for p in pages if p["id"] != args.keep]
    
    if not to_delete:
        print("✅ Aucun doublon à supprimer.")
        return
    
    if args.dry_run:
        print(f"\n🔷 DRY RUN — {len(to_delete)} page(s) seraient supprimées :")
        for p in to_delete:
            print(f"  - {p['id']} ({p['title']})")
        print("\nPassez sans --dry-run pour exécuter la suppression.")
        return
    
    # Suppression
    print(f"\n🗑️ Suppression de {len(to_delete)} page(s) en doublon...")
    success = 0
    for p in to_delete:
        if delete_page(p["id"]):
            print(f"  ✅ {p['id']} supprimée")
            success += 1
        else:
            print(f"  ❌ {p['id']} échec")
    
    print(f"\n✅ {success}/{len(to_delete)} page(s) archivée(s)")


if __name__ == "__main__":
    main()
