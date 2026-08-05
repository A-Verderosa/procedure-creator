#!/usr/bin/env python3
"""
check_structure.py — Validation structurelle des procédures .md générées.

Vérifie qu'un document procédure contient toutes les sections obligatoires
pour son niveau, que les diagrammes Mermaid sont bien formés, et que les
marqueurs LINKED_VIEW sont présents.

Usage:
  python3 check_structure.py procedure.md [--niveau mythique] [--verbose]
  python3 check_structure.py procedure.md --contract contract.json  # plus précis
"""

import argparse
import json
import os
import re
import sys
import yaml  # PyYAML

SKILL_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
NIVEAUX_PATH = os.path.join(SKILL_DIR, "references", "niveaux.yaml")

# ── Niveaux valides ────────────────────────────────────────────────
VALID_NIVEAUX = {"bronze", "argent", "or", "platine", "ultra", "mythique", "akuma"}

# ── Headers de section à chercher dans le document ─────────────────
# Mappe : nom_canonique → pattern regex pour détecter la section
SECTION_HEADERS = {
    "flash_card": r"##\s+🃏\s*FLASH\s+CARD(?:\s*[—–-]\s*Résumé\s+30s)?",
    "craie_localisation": r"##\s+📍\s*CRAIE\s*[—–-]\s*Localisation",
    "acteurs_raci": r"##\s+👥\s*RACI\s*[—–-]\s*Matrice\s+des\s+responsabilités",
    "raci_matrix": r"###\s+Matrice\s+RACI",
    "logigramme": r"##\s+🔄\s*Logigramme\s+Mermaid",
    "etapes_detaillees": r"##\s+📝\s*Étapes\s+détaillées",
    "risques": r"##\s+⚠️\s*Risques\s+identifiés",
    "documents": r"##\s+📄\s*Documents\s+de\s+référence",
    "kpi_cockpit": r"##\s+📊\s*6\.?\s*COCKPIT\s+KPI",
    "faq": r"##\s+❓\s*7\.?\s*FAQ",
    "modularite": r"##\s+🎚️\s*8\.?\s*SYNTHÈSE\s+DE\s+LA\s+MODULARITÉ",
    "scorecard": r"###\s+8\.\d\s*Scorecard",
    "cycle_vie": r"##\s+🔐\s*9\.?\s*CYCLE\s+DE\s+VIE",
    "quality_gate": r"##\s+✅\s*10\.?\s*QUALITY\s+GATE",
    "audit_trail": r"###\s+Audit\s+trail",
    "analyse_tendances": r"###\s+6\.\d\s*Analyse\s+des\s+tendances",
    "predictive_alerts": r"###\s+6\.\d\s*Alertes\s+prédictives",
    "points_vigilance": r"Points?\s+de\s+vigilance",
    "linked_risques": r"<!--\s*LINKED_VIEW:risques\s*-->",
    "linked_documents": r"<!--\s*LINKED_VIEW:documents\s*-->",
    "linked_mesures": r"<!--\s*LINKED_VIEW:mesures_pmri\s*-->",
    "linked_faq": r"<!--\s*LINKED_VIEW:faq\s*-->",
    "couche_akuma": r"##\s+☯️\s*11\.?\s*COUCHE\s+AKUMA",
}

# ── Sections requises par niveau (basé sur niveaux.yaml + template réel) ──
NIVEAU_SECTIONS = {
    "bronze": {
        "required": ["flash_card", "craie_localisation", "acteurs_raci"],
        "optional": ["logigramme"],
        "linked_views": [],
    },
    "argent": {
        "required": ["flash_card", "craie_localisation", "logigramme",
                      "acteurs_raci", "etapes_detaillees", "risques"],
        "optional": ["documents"],
        "linked_views": [],
    },
    "or": {
        "required": ["flash_card", "craie_localisation", "logigramme",
                      "acteurs_raci", "etapes_detaillees", "risques",
                      "documents", "faq"],
        "optional": ["kpi_cockpit"],
        "linked_views": [],
    },
    "platine": {
        "required": ["flash_card", "craie_localisation", "logigramme",
                      "acteurs_raci", "etapes_detaillees", "risques",
                      "documents", "quality_gate", "cycle_vie", "scorecard"],
        "optional": ["kpi_cockpit", "faq"],
        "linked_views": [],
    },
    "ultra": {
        "required": ["flash_card", "craie_localisation", "logigramme",
                      "acteurs_raci", "etapes_detaillees", "risques",
                      "documents", "quality_gate", "cycle_vie", "scorecard",
                      "modularite", "points_vigilance", "kpi_cockpit"],
        "optional": ["faq", "analyse_tendances"],
        "linked_views": [],
    },
    "mythique": {
        "required": ["flash_card", "craie_localisation", "logigramme",
                      "acteurs_raci", "etapes_detaillees", "risques",
                      "documents", "kpi_cockpit", "faq", "modularite",
                      "scorecard", "cycle_vie", "quality_gate",
                      "analyse_tendances", "predictive_alerts", "audit_trail",
                      "points_vigilance"],
        "optional": [],
        "linked_views": ["linked_risques", "linked_documents", "linked_mesures", "linked_faq"],
    },
    "akuma": {
        "required": ["flash_card", "craie_localisation", "logigramme",
                      "acteurs_raci", "etapes_detaillees", "risques",
                      "documents", "kpi_cockpit", "faq", "modularite",
                      "scorecard", "cycle_vie", "quality_gate",
                      "audit_trail", "couche_akuma"],
        "optional": [],
        "linked_views": ["linked_risques", "linked_documents", "linked_mesures", "linked_faq"],
    },
}

MERMAID_TYPES = {
    "flowchart": "Logigramme de processus",
    "sequenceDiagram": "Diagramme de séquence",
    "gantt": "Diagramme de Gantt",
    "xychart-beta": "Graphique XY (tendance)",
    "quadrantChart": "Quadrant Chart (risques)",
}


def detect_level_from_content(md_content):
    """Détecte le niveau à partir du contenu du document."""
    # Cherche le niveau dans le front matter YAML
    fm_match = re.search(r"niveau:\s*([🥉🥈🥇💎🔮☯️]+\s*)?(\w+)", md_content)
    if fm_match:
        level = fm_match.group(2).lower()
        if level in VALID_NIVEAUX:
            return level

    # Cherche dans la Flash Card
    fc_match = re.search(r"NIVEAU\s*(MYTHIQUE|ULTRA|PLATINE|OR|ARGENT|BRONZE|AKUMA)", md_content, re.IGNORECASE)
    if fc_match:
        return fc_match.group(1).lower()

    # Par défaut, mythique
    return "mythique"


def check_mermaid_blocks(md_content):
    """Vérifie et catégorise les blocs Mermaid."""
    blocks = []
    pattern = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
    for i, match in enumerate(pattern.finditer(md_content)):
        block_content = match.group(1).strip()
        first_line = block_content.split("\n")[0].strip()

        # Déterminer le type
        block_type = "unknown"
        for mtype, mlabel in MERMAID_TYPES.items():
            if first_line.startswith(mtype):
                block_type = mtype
                break

        blocks.append({
            "index": i,
            "type": block_type,
            "label": MERMAID_TYPES.get(block_type, "Type inconnu"),
            "lines": len(block_content.split("\n")),
            "valid_syntax": bool(block_content.strip()),
            "first_line": first_line,
        })

    return blocks


def check_scorecard_values(md_content):
    """Vérifie que la scorecard a des valeurs numériques cohérentes."""
    results = {}

    # Chercher le tableau Scorecard
    # Pattern: | Critère | Poids | Score | Max |
    table_match = re.search(
        r"\|\s*Critère\s*\|\s*Poids\s*\|\s*Score\s*\|\s*Max\s*\|\n"
        r"(?:\|[^\n]*\n)*?"
        r"\|\s*\*\*Total\*\*\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|",
        md_content, re.MULTILINE
    )

    if table_match:
        results["total"] = int(table_match.group(2))
        results["max"] = int(table_match.group(3))
        results["valid"] = results["total"] <= results["max"]
    else:
        results["error"] = "Tableau Scorecard introuvable"

    # Chercher le trophée
    trophee = re.search(r"\*\*Trophée\*\*\s*\|\s*\|\s*\*{0,2}([^*|]+)\*{0,2}\s*\|", md_content)
    results["trophee"] = trophee.group(1).strip() if trophee else "Non trouvé"

    return results


def check_mermaid_renderability(mermaid_blocks):
    """Vérifie si les blocs Mermaid sont potentiellement rendables."""
    issues = []
    for block in mermaid_blocks:
        if block["type"] == "unknown":
            issues.append(f"Bloc Mermaid #{block['index']} : type inconnu (« {block['first_line'][:30]} »)")
    return issues


def check_structure(md_path, niveau=None, verbose=False):
    """
    Fonction principale : valide la structure d'un document de procédure.

    Args:
        md_path (str): Chemin vers le fichier .md
        niveau (str, optional): Niveau attendu (détection auto si omis)
        verbose (bool): Plus de détails

    Returns:
        dict: Rapport structuré
    """
    if not os.path.isfile(md_path):
        return {"status": "error", "message": f"Fichier introuvable : {md_path}"}

    with open(md_path, "r") as f:
        md_content = f.read()

    # ── 1. Détection du niveau ───────────────────────────────────
    detected_level = detect_level_from_content(md_content)
    target_level = (niveau or detected_level).lower()

    if target_level not in VALID_NIVEAUX:
        return {"status": "error", "message": f"Niveau invalide : {target_level}"}

    # ── 2. Sections ──────────────────────────────────────────────
    section_config = NIVEAU_SECTIONS.get(target_level, NIVEAU_SECTIONS["mythique"])
    required_sections = section_config["required"]
    optional_sections = section_config["optional"]
    required_linked_views = section_config["linked_views"]

    section_results = {}
    for sec_name, sec_pattern in SECTION_HEADERS.items():
        found = bool(re.search(sec_pattern, md_content, re.IGNORECASE | re.MULTILINE))
        is_required = sec_name in required_sections
        is_linked_view = sec_name in required_linked_views
        section_results[sec_name] = {
            "present": found,
            "required": is_required or is_linked_view,
            "linked_view": is_linked_view,
        }

    # ── 3. Mermaid blocks ────────────────────────────────────────
    mermaid_blocks = check_mermaid_blocks(md_content)
    mermaid_issues = check_mermaid_renderability(mermaid_blocks)

    # ── 4. Scorecard ─────────────────────────────────────────────
    scorecard = check_scorecard_values(md_content)

    # ── 5. Synthèse ──────────────────────────────────────────────
    missing_required = [
        s for s, d in section_results.items()
        if d["required"] and not d["present"] and not d.get("linked_view")
    ]
    missing_linked = [
        s for s, d in section_results.items()
        if d.get("linked_view") and not d["present"]
    ]
    present_optional = [
        s for s, d in section_results.items()
        if s in optional_sections and d["present"]
    ]
    present_linked = [
        s for s, d in section_results.items()
        if d.get("linked_view") and d["present"]
    ]

    scorecard_valid = scorecard.get("valid", False)
    scorecard_score = scorecard.get("total", 0)
    scorecard_max = scorecard.get("max", 0)

    # Score de complétude (hors linked views)
    total_required = len(required_sections)
    total_present = total_required - len(missing_required)
    completeness_pct = round((total_present / total_required * 100), 1) if total_required > 0 else 100.0

    report = {
        "status": "ok" if not missing_required else "incomplete",
        "file": md_path,
        "niveau": target_level,
        "detected_niveau": detected_level,
        "completeness": {
            "present": total_present,
            "required": total_required,
            "percentage": completeness_pct,
        },
        "sections": section_results,
        "missing_required": missing_required,
        "missing_linked": missing_linked,
        "present_optional": present_optional,
        "linked_views": {
            "required": required_linked_views,
            "present": present_linked,
            "missing": [v for v in required_linked_views if v not in present_linked],
        },
        "mermaid": {
            "total_blocks": len(mermaid_blocks),
            "blocks": mermaid_blocks,
            "issues": mermaid_issues,
        },
        "scorecard": scorecard,
        "file_size": len(md_content),
    }

    # Score qualité (0-100)
    quality_score = 100.0

    # Pénalité sections manquantes
    missing_penalty = len(missing_required) * 15
    quality_score -= missing_penalty

    # Pénalité linked views manquantes (légère — structural mais pas critique)
    missing_lv = len(report.get("missing_linked", []))
    quality_score -= missing_lv * 5

    # Pénalité scorecard
    if not scorecard_valid:
        quality_score -= 10

    # Pénalité Mermaid issues
    quality_score -= len(mermaid_issues) * 5

    report["quality_score"] = max(0, min(100, round(quality_score, 1)))
    report["ready_for_qg"] = report["quality_score"] >= 70 and not missing_required

    return report


def print_report(report, verbose=False):
    """Affiche un rapport structuré et lisible."""
    status_emoji = "✅" if report["status"] == "ok" else "⚠️" if report["status"] == "incomplete" else "❌"
    qg_emoji = "🟢" if report.get("ready_for_qg") else "🔴"

    print(f"{status_emoji} **CHECK STRUCTURE** — {os.path.basename(report['file'])}")
    print(f"   Niveau : {report['niveau'].title()} (détecté : {report['detected_niveau'].title()})")
    print(f"   Complétude : {report['completeness']['present']}/{report['completeness']['required']} "
          f"({report['completeness']['percentage']}%)")
    print(f"   Score qualité : {report['quality_score']}/100")
    print(f"   Prêt pour QG : {qg_emoji}")
    print()

    if report["missing_required"]:
        print(f"❌ **Sections obligatoires manquantes :**")
        for sec in report["missing_required"]:
            label = SECTION_HEADERS.get(sec, sec)
            print(f"   • {label}")
        print()

    if report["present_optional"]:
        print(f"➕ **Sections optionnelles présentes :**")
        for sec in report["present_optional"]:
            label = SECTION_HEADERS.get(sec, sec)
            print(f"   • {label}")
        print()

    lv = report['linked_views']
    missing_lv = report.get('missing_linked', [])
    if missing_lv:
        print(f'⚠️ **Vues liées manquantes ({len(missing_lv)}) :**')
        for v in missing_lv:
            print(f"   • {v}")
        print()

    mermaid = report["mermaid"]
    print(f"📊 **Diagrammes Mermaid :** {mermaid['total_blocks']} trouvé(s)")
    for block in mermaid["blocks"]:
        flag = "✅" if block["type"] != "unknown" else "⚠️"
        print(f"   {flag} #{block['index']} — {block['label']} ({block['lines']} lignes)")
    if mermaid["issues"]:
        for issue in mermaid["issues"]:
            print(f"   ⚠️ {issue}")
    print()

    sc = report["scorecard"]
    if "error" in sc:
        print(f"⚠️ Scorecard : {sc['error']}")
    else:
        sc_flag = "✅" if sc.get("valid") else "⚠️"
        print(f"{sc_flag} Scorecard : {sc.get('total', 'N/A')}/{sc.get('max', 'N/A')} — Trophée : {sc.get('trophee', 'N/A')}")
    print()

    if verbose:
        print("--- Sections détaillées ---")
        for sec, data in report["sections"].items():
            if data["required"] or data["present"]:
                icon = "✅" if data["present"] else "❌"
                label = SECTION_HEADERS.get(sec, sec)
                lv_tag = " [LV]" if data.get("linked_view") else ""
                print(f"   {icon} {label}{lv_tag}")

    return report["status"] == "ok"


# ─── CLI ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CHECK STRUCTURE — Valide la structure d'une procédure .md",
    )
    parser.add_argument("md_file", type=str, help="Fichier .md de la procédure")
    parser.add_argument("--niveau", type=str, default=None,
                        choices=sorted(VALID_NIVEAUX), help="Niveau attendu")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Afficher toutes les sections")
    parser.add_argument("--json", action="store_true",
                        help="Sortie JSON brute")

    args = parser.parse_args()

    report = check_structure(
        args.md_file,
        niveau=args.niveau,
        verbose=args.verbose,
    )

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        ok = print_report(report, verbose=args.verbose)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
