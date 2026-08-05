#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
consult_bdd.py — Consultation des BDD Notion canoniques
========================================================

Interroge la BDD "1 Procédures RH" et ses BDD satellites via l'API Notion,
avec filtrage par type de procédure, périmètre, etc.

Usage:
    python3 consult_bdd.py --check
        → Vérifie la connexion Notion

    python3 consult_bdd.py --list
        → Liste les procédures (page 1, 50 résultats)

    python3 consult_bdd.py --list --page 2 --limit 20
        → Liste avec pagination (page 2, 20 résultats/page)

    python3 consult_bdd.py --proc PRH-042
        → Extrait une procédure par son identifiant

    python3 consult_bdd.py --filter Statut "En cours" --output results.json
        → Filtre les procédures par propriété

    python3 consult_bdd.py --schema
        → Affiche le schéma complet de la BDD
"""

import argparse
import json
import os
import sys

# Module partagé
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notion_shared import (
    notion_request,
    notion_query,
    extract_prop,
    extract_title,
    extract_procedure_id,
    check_connection,
    DATA_SOURCE_ID,
    DATABASE_ID,
    BDD_CANONIQUES,
    PROP_MAP,
    REL_MAP,
)


# ─── Fonctions principales ──────────────────────────────────────────────────

def load_from_data_source(filters=None, page_size=50, page=None):
    """
    Charge les procédures depuis le data_source Notion.

    Args:
        filters (dict, optional): Filtres {propriété: valeur}.
        page_size (int): Nombre de résultats par page.
        page (int, optional): Page à retourner (1-based).
            None = tout charger (comportement historique).

    Returns:
        dict: Résultat structuré {procedures: [...], meta: {...}}.
    """
    all_results = []
    start_cursor = None
    total = 0
    api_pages_fetched = 0
    has_more_overall = False

    # En mode paginé, on s'arrête après avoir collecté assez d'items
    # pour couvrir la page demandée
    max_items = (page * page_size) if page is not None else None

    while True:
        try:
            resp = notion_query(
                data_source_id=DATA_SOURCE_ID,
                page_size=min(page_size, 100),
                start_cursor=start_cursor,
            )
        except RuntimeError as e:
            raise RuntimeError(f"Erreur data_source query : {e}")

        results = resp if isinstance(resp, list) else resp.get("results", [])
        if not results:
            break

        all_results.extend(results)
        api_pages_fetched += 1

        # En mode paginé : arrêter dès qu'on a assez d'items
        if max_items is not None and len(all_results) >= max_items:
            has_more_overall = True
            break

        # Pagination (si le format data_source supporte has_more)
        if isinstance(resp, dict):
            has_more = resp.get("has_more", False)
            start_cursor = resp.get("next_cursor") if has_more else None
            if not has_more:
                break
        else:
            break

    # En mode paginé : slicer pour ne garder que la page demandée
    if page is not None:
        start = (page - 1) * page_size
        end = page * page_size
        page_results = all_results[start:end]
    else:
        page_results = all_results

    # Appliquer les filtres post-query
    procedures = []
    for page_obj in page_results:
        props = page_obj.get("properties", {})
        pid = extract_procedure_id(props)
        titre = extract_title(props)

        # Filtrage post-query
        if filters:
            skip = False
            for prop_name, expected_val in filters.items():
                actual_val = extract_prop(props.get(prop_name, {}))
                if isinstance(actual_val, str):
                    if expected_val.lower() not in actual_val.lower():
                        skip = True
                        break
                elif isinstance(actual_val, (int, float)):
                    if str(actual_val) != expected_val:
                        skip = True
                        break
            if skip:
                continue

        procedure = {
            "page_id": page_obj.get("id", ""),
            "procedure_id": pid,
            "titre": titre,
            "url": page_obj.get("url", ""),
        }

        # Toutes les propriétés
        for prop_name, prop_value in props.items():
            procedure[prop_name] = extract_prop(prop_value)

        procedures.append(procedure)
        total += 1

    return {
        "procedures": procedures,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": has_more_overall,
        "database_id": DATABASE_ID,
        "data_source_id": DATA_SOURCE_ID,
    }


def get_procedure_by_id(pid):
    """
    Extrait une procédure spécifique par son identifiant ou titre.

    Cherche d'abord par procedure_id exact, puis par correspondance
    dans le titre (fuzzy/contains).

    Args:
        pid (str): Identifiant (ex: PRH-042, 497) ou terme de recherche.

    Returns:
        dict: Données de la procédure, ou None si introuvable.
    """
    data = load_from_data_source(page_size=100)
    pid_upper = pid.upper()

    # Passe 1 : match exact sur procedure_id
    for proc in data["procedures"]:
        if proc.get("procedure_id", "").upper() == pid_upper:
            return proc

    # Passe 2 : match sur le numéro uniquement (cas PRH-xxx → juste xxx)
    pid_numeric = "".join(c for c in pid if c.isdigit())
    if pid_numeric:
        for proc in data["procedures"]:
            pid_val = proc.get("procedure_id", "")
            if pid_val == pid_numeric:
                return proc

    # Passe 3 : recherche dans le titre (contains)
    for proc in data["procedures"]:
        titre = proc.get("titre", "").upper()
        if pid_upper in titre:
            return proc

    return None


def get_schema():
    """
    Récupère le schéma (propriétés) de la BDD Procédures.

    Returns:
        dict: Schéma de la BDD {propriété: type}.
    """
    try:
        resp = notion_request(
            "GET",
            f"https://api.notion.com/v1/databases/{DATABASE_ID}",
        )
        properties = resp.get("properties", {})
        schema = {}
        for name, prop in sorted(properties.items()):
            ptype = prop.get("type", "?")
            schema[name] = {
                "type": ptype,
                # Infos supplémentaires selon le type
                "options": _get_type_options(prop),
            }
        return schema
    except RuntimeError as e:
        raise RuntimeError(f"Erreur récupération schéma : {e}")


def _get_type_options(prop):
    """Extrait les options pour les types select/multi_select/status."""
    ptype = prop.get("type", "")
    if ptype == "select":
        return [o.get("name") for o in prop.get("select", {}).get("options", [])]
    elif ptype == "multi_select":
        return [o.get("name") for o in prop.get("multi_select", {}).get("options", [])]
    elif ptype == "status":
        return [
            g.get("name") for g in
            prop.get("status", {}).get("groups", [])
        ]
    elif ptype in ("relation", "rollup", "created_time", "last_edited_time",
                    "created_by", "last_edited_by", "formula", "unique_id"):
        return None
    return []


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Consultation des BDD Notion canoniques pour DOX_PROC",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Vérifier la connexion à l'API Notion",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="Lister les procédures (avec filtres optionnels)",
    )
    parser.add_argument(
        "--proc", type=str, default=None,
        help="ID de procédure à extraire (ex: PRH-042)",
    )
    parser.add_argument(
        "--filter", nargs=2, metavar=("PROP", "VALEUR"),
        action="append", default=[],
        help="Filtrer par propriété (ex: --filter Statut 'En cours')",
    )
    parser.add_argument(
        "--schema", action="store_true",
        help="Afficher le schéma de la BDD",
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Fichier JSON de sortie",
    )
    parser.add_argument(
        "--limit", type=int, default=50,
        help="Nombre de résultats par page (défaut: 50)",
    )
    parser.add_argument(
        "--page", type=int, default=1,
        help="Page à afficher (1-based, défaut: 1)",
    )

    args = parser.parse_args()

    try:
        # ── --check ──
        if args.check:
            connected = check_connection()
            if connected:
                result = {"status": "ok", "message": "Connexion Notion établie",
                          "database_id": DATABASE_ID}
                _output(result, args.output)
                return
            else:
                _error("Impossible de se connecter à Notion")

        # ── --schema ──
        elif args.schema:
            schema = get_schema()
            _output(schema, args.output)

        # ── --proc ──
        elif args.proc:
            proc = get_procedure_by_id(args.proc)
            if proc:
                _output(proc, args.output)
            else:
                _error(f"Procédure '{args.proc}' introuvable")

        # ── --list (défaut si aucun autre flag) ──
        else:
            filters = {}
            for prop, val in args.filter:
                filters[prop] = val

            data = load_from_data_source(
                filters=filters if filters else None,
                page_size=args.limit,
                page=args.page,
            )

            # Version résumée si pas de filtre output
            if not args.output:
                page_info = ""
                if data.get("page") is not None:
                    page_info = (
                        f" (page {data['page']}/{data['page_size']}"
                        + (f", suivante dispo" if data.get("has_more") else ", fin")
                        + ")"
                    )
                summary = {
                    "total": data["total"],
                    "page": data.get("page"),
                    "page_size": data.get("page_size"),
                    "has_more": data.get("has_more"),
                    "procedures": [
                        {
                            "id": p["procedure_id"],
                            "titre": p["titre"][:80],
                            "progression": p.get("Progression", ""),
                        }
                        for p in data["procedures"]
                    ],
                }
                print(json.dumps(summary, indent=2, ensure_ascii=False))
            else:
                _output(data, args.output)

    except RuntimeError as e:
        _error(str(e))


def _output(data, output_path=None):
    """Affiche ou sauvegarde les données JSON."""
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    if output_path:
        with open(output_path, "w") as f:
            f.write(json_str)
        print(f"Résultats sauvegardés dans {output_path}")
    else:
        print(json_str)


def _error(msg):
    """Affiche une erreur et sort."""
    print(json.dumps({"status": "error", "message": msg}, indent=2,
                     ensure_ascii=False))
    sys.exit(1)


if __name__ == "__main__":
    main()
