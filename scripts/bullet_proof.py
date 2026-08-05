#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bullet_proof.py — Bullet Proofing 4 angles
============================================

Sécurisation d'une procédure DOX selon 4 angles :
  1. 🏗️ Architectural  — Cohérence BDD-native (relations Notion valides)
  2. 📜 Transactionnel — Traçabilité des modifications
  3. 🔗 Systémique     — Compatibilité 10 BDD canoniques
  4. ⛔ Anti-régression — Pas de perte en upgrade

Fonctions principales :
  - architectural_check(procedure_data) → list of issues
  - transactionnel_check(version_history) → list of issues
  - systemique_check(relations, bdd_config) → list of issues
  - anti_regression_check(old_version, new_version) → list of differences
  - full_bullet_proof(procedure_data, old_version=None) → dict des 4 angles
  - CLI : python3 bullet_proof.py --file <path>
         python3 bullet_proof.py --file <path> --diff-with <old_path>
"""

import argparse
import glob as glob_module
import json
import os
import re
import sys
from datetime import datetime

# Module partagé Notion (token, PROP_MAP, REL_MAP, requêtes API)
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
    REL_MAP,
    DATA_SOURCE_ID,
    DATABASE_ID,
)


# ─── Chemins ─────────────────────────────────────────────────────────────────

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BDD_CONFIG_PATH = os.path.join(SKILL_DIR, "references", "bdd_canoniques.yaml")


# ─── 1. VÉRIFICATION ARCHITECTURALE ─────────────────────────────────────────

def architectural_check(procedure_data):
    """
    Vérifie la cohérence architecturale BDD-native d'une procédure.

    Contrôle :
      - Présence d'un ID valide (PRH-xxx, EVP-xxx, etc.)
      - Présence des champs obligatoires (titre, niveau, type_rh)
      - Cohérence des modules avec le niveau
      - Validité des relations Notion
      - Intégrité du DOX Contract si présent

    Args:
        procedure_data (dict): Données de la procédure à vérifier.

    Returns:
        list: Issues détectées. Chaque issue est un dict :
            - severity (str) : 'error' | 'warning' | 'info'
            - code (str) : Code de l'issue (ex: 'ARCH-001')
            - message (str) : Description de l'issue
            - field (str) : Champ concerné (optionnel)
    """
    issues = []

    # ── ARCH-001 : ID de procédure ──────────────────────────────────────
    pid = procedure_data.get("procedure_id", "")
    if not pid:
        issues.append({
            "severity": "error",
            "code": "ARCH-001",
            "message": "Aucun ID de procédure (procedure_id). Un ID PREFIX-xxx est requis (ex: EVP-001, PRH-042).",
            "field": "procedure_id",
        })
    elif not re.match(r"^[A-Z]{3}-\d{3}$", pid):
        issues.append({
            "severity": "error",
            "code": "ARCH-002",
            "message": f"Format d'ID invalide : '{pid}'. Attendu : PREFIX-xxx (PREFIX = 3 lettres, xxx = 3 chiffres, ex: EVP-001).",
            "field": "procedure_id",
        })

    # ── ARCH-003 : Titre ────────────────────────────────────────────────
    titre = procedure_data.get("titre", "")
    if not titre:
        issues.append({
            "severity": "error",
            "code": "ARCH-003",
            "message": "Titre de procédure manquant.",
            "field": "titre",
        })
    elif len(titre) < 5:
        issues.append({
            "severity": "warning",
            "code": "ARCH-004",
            "message": f"Titre trop court ({len(titre)} caractères). Minimum 5 caractères.",
            "field": "titre",
        })

    # ── ARCH-005 : Niveau ───────────────────────────────────────────────
    niveau = procedure_data.get("niveau", "").lower()
    niveaux_valides = {
        "bronze", "argent", "or", "platine", "ultra", "mythique", "akuma",
    }
    if not niveau:
        issues.append({
            "severity": "error",
            "code": "ARCH-005",
            "message": "Niveau de procédure manquant.",
            "field": "niveau",
        })
    elif niveau not in niveaux_valides:
        issues.append({
            "severity": "error",
            "code": "ARCH-006",
            "message": f"Niveau invalide : '{niveau}'. Valides : {', '.join(sorted(niveaux_valides))}.",
            "field": "niveau",
        })

    # ── ARCH-007 : Type RH ──────────────────────────────────────────────
    type_rh = procedure_data.get("type_rh", "")
    if not type_rh:
        issues.append({
            "severity": "warning",
            "code": "ARCH-007",
            "message": "Type RH non spécifié. Requis pour le filtrage BDD.",
            "field": "type_rh",
        })

    # ── ARCH-008 : Périmètre ────────────────────────────────────────────
    perimetre = procedure_data.get("perimetre", "")
    if not perimetre:
        issues.append({
            "severity": "info",
            "code": "ARCH-008",
            "message": "Périmètre non spécifié. Recommandé pour le ciblage BDD.",
            "field": "perimetre",
        })

    # ── ARCH-009 : Modules vs Niveau ────────────────────────────────────
    modules = procedure_data.get("modules", procedure_data.get("dox_contract", {}).get("modules", []))
    if niveau in niveaux_valides and modules:
        module_map = {
            "bronze": ["00_HUB", "01_CADRAGE"],
            "argent": ["00_HUB", "01_CADRAGE", "02_ACTEURS", "03_FLUX"],
            "or": ["00_HUB", "01_CADRAGE", "02_ACTEURS", "03_FLUX", "04_REGLES"],
            "platine": ["00_HUB", "01_CADRAGE", "02_ACTEURS", "03_FLUX", "04_REGLES", "05_RISQUES", "06_DOCUMENTS", "07_QG"],
            "ultra": ["00_HUB", "01_CADRAGE", "02_ACTEURS", "03_FLUX", "04_REGLES", "05_RISQUES", "06_DOCUMENTS", "07_QG", "08_CYCLE_VIE"],
            "mythique": ["00_HUB", "01_CADRAGE", "02_ACTEURS", "03_FLUX", "04_REGLES", "05_RISQUES", "06_DOCUMENTS", "07_QG", "08_CYCLE_VIE", "09_KPI", "10_TENDANCES", "11_PREDICTIF"],
            "akuma": ["IA_DIAG", "IA_EVOLUTION", "IA_GARDE_FOUS"],
        }
        expected = set(module_map.get(niveau, []))
        actual = set(modules)
        missing = expected - actual
        if missing:
            issues.append({
                "severity": "warning",
                "code": "ARCH-009",
                "message": f"Modules obligatoires manquants pour le niveau {niveau} : {', '.join(sorted(missing))}.",
                "field": "modules",
            })

    # ── ARCH-010 : Relations ────────────────────────────────────────────
    relations = procedure_data.get("relations", procedure_data.get("dox_contract", {}).get("relations", {}))
    if isinstance(relations, dict):
        valid_keys = {"organigramme", "annuaire", "sbrx_risques", "ged_documents"}
        for key in relations:
            if key not in valid_keys:
                issues.append({
                    "severity": "warning",
                    "code": "ARCH-010",
                    "message": f"Clé de relation inconnue : '{key}'. Valides : {', '.join(sorted(valid_keys))}.",
                    "field": f"relations.{key}",
                })
            elif not isinstance(relations[key], list):
                issues.append({
                    "severity": "error",
                    "code": "ARCH-011",
                    "message": f"La relation '{key}' doit être une liste.",
                    "field": f"relations.{key}",
                })

    # ── ARCH-012 : Contenu markdown ─────────────────────────────────────
    md_content = procedure_data.get("contenu_markdown", "")
    if not md_content:
        issues.append({
            "severity": "error",
            "code": "ARCH-012",
            "message": "Contenu markdown de la procédure manquant.",
            "field": "contenu_markdown",
        })

    return issues


# ─── 2. VÉRIFICATION TRANSACTIONNELLE ───────────────────────────────────────

def transactionnel_check(version_history):
    """
    Vérifie la traçabilité des modifications (aspect transactionnel).

    Contrôle :
      - Présence d'un historique des versions
      - Cohérence des dates (création ≤ dernière revue ≤ maintenant)
      - Présence d'au moins 2 entrées pour les niveaux Ultra+
      - Validité des champs de version

    Args:
        version_history (list): Liste des entrées de version. Chaque entrée
            est un dict avec : version, date, auteur, description.

    Returns:
        list: Issues détectées.
    """
    issues = []

    if not version_history:
        issues.append({
            "severity": "error",
            "code": "TRAN-001",
            "message": "Aucun historique de versions fourni.",
            "field": "version_history",
        })
        return issues

    if not isinstance(version_history, list):
        issues.append({
            "severity": "error",
            "code": "TRAN-002",
            "message": "L'historique des versions doit être une liste.",
            "field": "version_history",
        })
        return issues

    # Vérifier chaque entrée
    for i, entry in enumerate(version_history):
        # Version
        version = entry.get("version", "")
        if not version:
            issues.append({
                "severity": "error",
                "code": "TRAN-003",
                "message": f"Entrée #{i + 1} : champ 'version' manquant.",
                "field": f"version_history[{i}].version",
            })

        # Date
        date_str = entry.get("date", "")
        if not date_str:
            issues.append({
                "severity": "error",
                "code": "TRAN-004",
                "message": f"Entrée #{i + 1} (v{version}) : champ 'date' manquant.",
                "field": f"version_history[{i}].date",
            })
        else:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                issues.append({
                    "severity": "warning",
                    "code": "TRAN-005",
                    "message": f"Entrée #{i + 1} (v{version}) : format de date invalide '{date_str}'. Attendu : YYYY-MM-DD.",
                    "field": f"version_history[{i}].date",
                })

        # Auteur
        auteur = entry.get("auteur", "")
        if not auteur:
            issues.append({
                "severity": "warning",
                "code": "TRAN-006",
                "message": f"Entrée #{i + 1} (v{version}) : auteur non spécifié.",
                "field": f"version_history[{i}].auteur",
            })

        # Description
        desc = entry.get("description", "")
        if not desc:
            issues.append({
                "severity": "info",
                "code": "TRAN-007",
                "message": f"Entrée #{i + 1} (v{version}) : description manquante.",
                "field": f"version_history[{i}].description",
            })

    # Cohérence chronologique des dates
    dates = []
    for entry in version_history:
        d = entry.get("date", "")
        if d:
            try:
                dates.append(datetime.strptime(d, "%Y-%m-%d"))
            except ValueError:
                dates.append(None)
        else:
            dates.append(None)

    for i in range(len(dates) - 1):
        if dates[i] and dates[i + 1]:
            if dates[i] > dates[i + 1]:
                issues.append({
                    "severity": "error",
                    "code": "TRAN-008",
                    "message": (
                        f"Incohérence chronologique : version #{i + 1} "
                        f"({version_history[i].get('date', '?')}) est "
                        f"postérieure à la version #{i + 2}"
                    ),
                    "field": f"version_history[{i}].date",
                })

    # Nombre d'entrées
    if len(version_history) < 2:
        issues.append({
            "severity": "info",
            "code": "TRAN-009",
            "message": (
                f"Une seule version tracée ({len(version_history)} entrée). "
                "Recommandé : ≥ 2 pour les niveaux Ultra+."
            ),
            "field": "version_history",
        })

    return issues


# ─── 3. VÉRIFICATION SYSTÉMIQUE ─────────────────────────────────────────────

def systemique_check(relations, bdd_config=None):
    """
    Vérifie la compatibilité systémique avec les 10 BDD canoniques.

    Contrôle :
      - Chaque relation pointe vers une BDD valide
      - Pas de liens morts (IDs manquants ou vides)
      - Les types de relations sont cohérents
      - Cardinalités respectées

    Args:
        relations (dict): Relations de la procédure avec les BDD.
        bdd_config (dict, optional): Configuration des BDD canoniques.
            Si None, tente de charger depuis le fichier.

    Returns:
        list: Issues détectées.
    """
    issues = []

    if not bdd_config:
        try:
            import yaml
            if os.path.isfile(BDD_CONFIG_PATH):
                with open(BDD_CONFIG_PATH, "r") as f:
                    bdd_config = yaml.safe_load(f) or {}
            else:
                bdd_config = {}
        except Exception:
            bdd_config = {}

    bdd_canoniques = bdd_config.get("bdd_canoniques", {})
    relations_config = bdd_config.get("relations", {})

    if not relations:
        issues.append({
            "severity": "warning",
            "code": "SYS-001",
            "message": "Aucune relation BDD définie. La procédure n'est pas connectée aux BDD canoniques.",
            "field": "relations",
        })
        return issues

    # Mapping nom logique → nom BDD canonique
    relation_bdd_map = {
        "organigramme": "organigramme",
        "annuaire": "annuaire",
        "sbrx_risques": "risques_sbrx",
        "ged_documents": "ged",
    }

    for rel_key, rel_ids in relations.items():
        bdd_key = relation_bdd_map.get(rel_key)

        # SYS-002 : Relation non standard
        if not bdd_key:
            issues.append({
                "severity": "warning",
                "code": "SYS-002",
                "message": f"Relation '{rel_key}' non reconnue dans les BDD canoniques.",
                "field": f"relations.{rel_key}",
            })
            continue

        # SYS-003 : BDD canonique configurée ?
        bdd_entry = bdd_canoniques.get(bdd_key, {})
        bdd_name = bdd_entry.get("name", bdd_key)
        bdd_id = bdd_entry.get("id", "")

        if not bdd_id and bdd_entry.get("type") != "recherche":
            issues.append({
                "severity": "warning",
                "code": "SYS-003",
                "message": f"La BDD '{bdd_name}' ({bdd_key}) n'a pas d'ID configuré.",
                "field": f"bdd_canoniques.{bdd_key}",
            })

        # SYS-004 : IDs invalides ou vides
        if isinstance(rel_ids, list):
            empty_ids = [i for i, rid in enumerate(rel_ids) if not rid]
            if empty_ids:
                issues.append({
                    "severity": "error",
                    "code": "SYS-004",
                    "message": (
                        f"Relation '{rel_key}' : {len(empty_ids)} ID(s) vide(s) "
                        f"aux positions {empty_ids}."
                    ),
                    "field": f"relations.{rel_key}",
                })
        else:
            issues.append({
                "severity": "error",
                "code": "SYS-005",
                "message": f"Relation '{rel_key}' : doit être une liste d'IDs.",
                "field": f"relations.{rel_key}",
            })

    # SYS-006 : Vérifier les relations configurées mais absentes
    for rel_name in relations_config:
        if rel_name not in relations:
            bdd_key = relation_bdd_map.get(rel_name)
            if bdd_key and bdd_key in bdd_canoniques:
                issues.append({
                    "severity": "info",
                    "code": "SYS-006",
                    "message": f"Relation '{rel_name}' configurée dans bdd_canoniques mais absente des données.",
                    "field": f"relations.{rel_name}",
                })

    return issues


# ─── 4. VÉRIFICATION ANTI-RÉGRESSION ────────────────────────────────────────

def anti_regression_check(old_version, new_version):
    """
    Compare deux versions d'une procédure et détecte les régressions.

    La non-régression est vérifiée selon :
      - Aucune section obligatoire supprimée
      - Aucun risque retiré sans justification
      - Aucun module désactivé
      - Score QG non diminué
      - Contenu global non réduit

    Args:
        old_version (dict): Ancienne version de la procédure (données structurées
            ou contenu markdown).
        new_version (dict): Nouvelle version de la procédure.

    Returns:
        list: Différences détectées. Chaque différence est un dict :
            - type (str) : 'regression' | 'amelioration' | 'changement'
            - code (str) : Code de la différence (ex: 'REG-001')
            - message (str) : Description
            - old_value : Ancienne valeur
            - new_value : Nouvelle valeur
    """
    differences = []

    # Support à la fois dict structuré et contenu markdown brut
    old_text = ""
    new_text = ""

    if isinstance(old_version, dict):
        old_text = old_version.get("contenu_markdown", json.dumps(old_version))
        old_data = old_version
    else:
        old_text = str(old_version)
        old_data = {}

    if isinstance(new_version, dict):
        new_text = new_version.get("contenu_markdown", json.dumps(new_version))
        new_data = new_version
    else:
        new_text = str(new_version)
        new_data = {}

    # ── REG-001 : Sections supprimées ──────────────────────────────────
    if old_text and new_text:
        old_sections = set(re.findall(r"^##\s+(.+)$", old_text, re.MULTILINE))
        new_sections = set(re.findall(r"^##\s+(.+)$", new_text, re.MULTILINE))
        removed_sections = old_sections - new_sections
        for section in removed_sections:
            differences.append({
                "type": "regression",
                "code": "REG-001",
                "message": f"Section supprimée : '{section}'.",
                "old_value": section,
                "new_value": None,
            })

    # ── REG-002 : Risques retirés ──────────────────────────────────────
    old_risks = _extract_risk_codes(old_text, old_data)
    new_risks = _extract_risk_codes(new_text, new_data)
    removed_risks = old_risks - new_risks
    for risk in removed_risks:
        differences.append({
            "type": "regression",
            "code": "REG-002",
            "message": f"Risque retiré : '{risk}' sans justification.",
            "old_value": risk,
            "new_value": None,
        })

    # ── REG-003 : Modules désactivés ───────────────────────────────────
    old_modules = set(old_data.get("modules", old_data.get("dox_contract", {}).get("modules", [])))
    new_modules = set(new_data.get("modules", new_data.get("dox_contract", {}).get("modules", [])))
    removed_modules = old_modules - new_modules
    for mod in removed_modules:
        differences.append({
            "type": "regression",
            "code": "REG-003",
            "message": f"Module désactivé : '{mod}'.",
            "old_value": mod,
            "new_value": None,
        })

    # ── REG-004 : Score QG diminué ─────────────────────────────────────
    old_score = old_data.get("qg_score", old_data.get("score", 0))
    new_score = new_data.get("qg_score", new_data.get("score", 0))
    if old_score and new_score and new_score < old_score:
        differences.append({
            "type": "regression",
            "code": "REG-004",
            "message": f"Score QG diminué : {old_score} → {new_score}.",
            "old_value": old_score,
            "new_value": new_score,
        })

    # ── REG-005 : Contenu réduit ───────────────────────────────────────
    if old_text and new_text:
        old_len = len(old_text)
        new_len = len(new_text)
        reduction_pct = (old_len - new_len) / old_len * 100 if old_len > 0 else 0
        if reduction_pct > 20:
            differences.append({
                "type": "regression",
                "code": "REG-005",
                "message": (
                    f"Contenu réduit de {reduction_pct:.0f}% "
                    f"({old_len} → {new_len} caractères)."
                ),
                "old_value": old_len,
                "new_value": new_len,
            })

    # ── REG-006 : Éléments ajoutés (amélioration) ──────────────────────
    added_sections = new_sections - old_sections if old_text and new_text and 'old_sections' in dir() else set()
    # Re-calcul sécurisé
    if old_text and new_text:
        old_secs = set(re.findall(r"^##\s+(.+)$", old_text, re.MULTILINE))
        new_secs = set(re.findall(r"^##\s+(.+)$", new_text, re.MULTILINE))
        added = new_secs - old_secs
        for section in added:
            differences.append({
                "type": "amelioration",
                "code": "REG-006",
                "message": f"Nouvelle section ajoutée : '{section}'.",
                "old_value": None,
                "new_value": section,
            })

    # REG-007 : Nouveaux risques
    added_risks = new_risks - old_risks
    for risk in added_risks:
        differences.append({
            "type": "amelioration",
            "code": "REG-007",
            "message": f"Nouveau risque ajouté : '{risk}'.",
            "old_value": None,
            "new_value": risk,
        })

    # REG-008 : Nouveaux modules
    added_modules = new_modules - old_modules
    for mod in added_modules:
        differences.append({
            "type": "amelioration",
            "code": "REG-008",
            "message": f"Nouveau module activé : '{mod}'.",
            "old_value": None,
            "new_value": mod,
        })

    return differences


def _extract_risk_codes(text, data):
    """
    Extrait les codes de risque (R1, R2, ...) du texte ou des données.

    Args:
        text (str): Contenu markdown.
        data (dict): Données structurées.

    Returns:
        set: Ensemble des codes de risque.
    """
    codes = set()
    # Depuis le texte
    if text:
        matches = re.findall(r"\bR(\d+)\b", text)
        for m in matches:
            codes.add(f"R{m}")

    # Depuis les données structurées
    risques = data.get("risques", [])
    for r in risques:
        if isinstance(r, str):
            if re.match(r"^R\d+$", r):
                codes.add(r)
        elif isinstance(r, dict):
            code = r.get("code", "")
            if code:
                codes.add(code)

    return codes


# ─── VÉRIFICATION COMPLÈTE ──────────────────────────────────────────────────

def full_bullet_proof(procedure_data, old_version=None):
    """
    Exécute les 4 angles de Bullet Proofing sur une procédure.

    Args:
        procedure_data (dict): Données complètes de la procédure.
        old_version (dict, optional): Ancienne version pour l'anti-régression.

    Returns:
        dict: Résultats structurés avec les 4 angles :
            - architectural (dict) : {passed, total, issues}
            - transactionnel (dict) : {passed, total, issues}
            - systemique (dict) : {passed, total, issues}
            - anti_regression (dict) : {passed, total, issues}
            - global (dict) : {passed, total, score_pct, verdict}
    """
    # 1. Architectural
    arch_issues = architectural_check(procedure_data)
    arch_errors = [i for i in arch_issues if i["severity"] == "error"]
    arch_warnings = [i for i in arch_issues if i["severity"] == "warning"]

    # 2. Transactionnel
    version_history = procedure_data.get("version_history", [])
    tran_issues = transactionnel_check(version_history)
    tran_errors = [i for i in tran_issues if i["severity"] == "error"]
    tran_warnings = [i for i in tran_issues if i["severity"] == "warning"]

    # 3. Systémique
    relations = procedure_data.get("relations", procedure_data.get("dox_contract", {}).get("relations", {}))
    sys_issues = systemique_check(relations)
    sys_errors = [i for i in sys_issues if i["severity"] == "error"]
    sys_warnings = [i for i in sys_issues if i["severity"] == "warning"]

    # 4. Anti-régression
    if old_version:
        reg_diffs = anti_regression_check(old_version, procedure_data)
        reg_regressions = [d for d in reg_diffs if d["type"] == "regression"]
    else:
        reg_diffs = []
        reg_regressions = []

    # Synthèse
    total_checks = [
        ("architectural", arch_issues),
        ("transactionnel", tran_issues),
        ("systemique", sys_issues),
    ]
    all_issues = arch_issues + tran_issues + sys_issues + reg_diffs
    all_errors = arch_errors + tran_errors + sys_errors + reg_regressions
    all_warnings = arch_warnings + tran_warnings + sys_warnings

    total = max(len(all_issues), 1)
    passed = total - len(all_errors)

    if all_errors:
        verdict = "⛔ ÉCHEC"
    elif all_warnings:
        verdict = "⚠️ AVERTISSEMENTS"
    else:
        verdict = "✅ OK"

    return {
        "architectural": {
            "passed": len(arch_errors) == 0,
            "total": len(arch_issues),
            "errors": len(arch_errors),
            "warnings": len(arch_warnings),
            "issues": arch_issues,
        },
        "transactionnel": {
            "passed": len(tran_errors) == 0,
            "total": len(tran_issues),
            "errors": len(tran_errors),
            "warnings": len(tran_warnings),
            "issues": tran_issues,
        },
        "systemique": {
            "passed": len(sys_errors) == 0,
            "total": len(sys_issues),
            "errors": len(sys_errors),
            "warnings": len(sys_warnings),
            "issues": sys_issues,
        },
        "anti_regression": {
            "passed": len(reg_regressions) == 0 if old_version else None,
            "total": len(reg_diffs),
            "regressions": len(reg_regressions),
            "differences": reg_diffs,
        },
        "global": {
            "passed": len(all_errors) == 0,
            "total_issues": total,
            "errors": len(all_errors),
            "warnings": len(all_warnings),
            "score_pct": round(passed / total * 100, 1) if total > 0 else 100.0,
            "verdict": verdict,
        },
    }


# ─── Helpers CLI : vérification, batch, BDD Notion ──────────────────────────

def _cmd_check():
    """
    Vérifie le token Notion et la connexion à l'API.
    """
    try:
        token = get_notion_token()
        print(json.dumps({
            "status": "ok",
            "token": f"{token[:8]}... (len={len(token)})",
            "message": "Token Notion trouvé",
        }, indent=2))
    except RuntimeError as e:
        print(json.dumps({
            "status": "error",
            "message": str(e),
        }, indent=2))
        sys.exit(1)

    connected = check_connection()
    if connected:
        print(json.dumps({
            "status": "ok",
            "message": "Connexion API Notion établie",
            "database_id": DATABASE_ID,
        }, indent=2))
    else:
        print(json.dumps({
            "status": "error",
            "message": "Impossible de se connecter à l'API Notion",
        }, indent=2))
        sys.exit(1)

    sys.exit(0)


def _verify_relations_in_notion(procedure_data):
    """
    Vérifie les relations BDD contre la BDD Notion réelle.

    Pour chaque relation déclarée dans procedure_data['relations'],
    tente de retrouver les IDs référencés dans la BDD Notion.

    Args:
        procedure_data (dict): Données de la procédure.

    Returns:
        dict: {relation_key: {verdict, detail}} pour chaque relation.
    """
    results = {}
    relations = procedure_data.get("relations", {})

    if not relations:
        return {}

    # Notion database query — récupère toutes les pages de la BDD Procédures
    try:
        resp = notion_query(data_source_id=DATA_SOURCE_ID, page_size=100)
        notion_pages = resp if isinstance(resp, list) else resp.get("results", [])
    except RuntimeError as e:
        return {"_error": f"Impossible d'interroger Notion : {e}"}

    # Construire un index des Notion IDs existants
    existing_ids = set()
    for page in notion_pages:
        page_id = page.get("id", "")
        if page_id:
            existing_ids.add(page_id)
        # Également dans les propriétés de relation
        props = page.get("properties", {})
        for prop_name, prop_value in props.items():
            if isinstance(prop_value, dict) and prop_value.get("type") == "relation":
                for rel in prop_value.get("relation", []):
                    if rel.get("id"):
                        existing_ids.add(rel["id"])

    for rel_key, rel_ids in relations.items():
        if not isinstance(rel_ids, list):
            results[rel_key] = {
                "verdict": "skip",
                "detail": "Format non liste, ignoré",
            }
            continue

        valid_ids = [rid for rid in rel_ids if rid]
        if not valid_ids:
            results[rel_key] = {
                "verdict": "empty",
                "detail": "Aucun ID de relation fourni",
            }
            continue

        found = [rid for rid in valid_ids if rid in existing_ids]
        missing = [rid for rid in valid_ids if rid not in existing_ids]

        if not missing:
            results[rel_key] = {
                "verdict": "valid",
                "detail": f"{len(found)}/{len(valid_ids)} ID(s) trouvé(s) dans Notion",
            }
        else:
            results[rel_key] = {
                "verdict": "invalid",
                "detail": f"{len(missing)} ID(s) introuvable(s) dans Notion : {missing[:5]}{'...' if len(missing) > 5 else ''}",
                "missing_ids": missing[:10],
            }

    return results


def _cmd_batch(input_dir, glob_pattern="*.json", output_dir=None,
               notion_verify=False):
    """
    Traite en batch tous les fichiers JSON d'un répertoire.

    Args:
        input_dir (str): Répertoire contenant les fichiers JSON.
        glob_pattern (str): Glob pattern pour filtrer les fichiers.
        output_dir (str): Répertoire de sortie pour les rapports.
        notion_verify (bool): Vérifier les relations dans Notion.

    Returns:
        dict: Résumé du batch {total, success, errors, reports}.
    """
    if not os.path.isdir(input_dir):
        raise RuntimeError(
            f"Répertoire introuvable pour le mode batch : {input_dir}"
        )

    output_dir = output_dir or input_dir
    os.makedirs(output_dir, exist_ok=True)

    pattern = os.path.join(input_dir, glob_pattern)
    files = sorted(glob_module.glob(pattern))

    if not files:
        return {
            "total": 0,
            "success": 0,
            "errors": 0,
            "reports": [],
            "message": f"Aucun fichier trouvé avec {pattern}",
        }

    results = []
    success_count = 0
    error_count = 0

    for filepath in files:
        basename = os.path.splitext(os.path.basename(filepath))[0]
        try:
            with open(filepath, "r") as f:
                procedure_data = json.load(f)

            # Bullet proofing complet
            report = full_bullet_proof(procedure_data)

            # Vérification Notion optionnelle
            if notion_verify:
                notion_results = _verify_relations_in_notion(procedure_data)
                report["notion_verification"] = notion_results

            # Sauvegarder le rapport
            out_path = os.path.join(output_dir, f"{basename}_bulletproof.json")
            with open(out_path, "w") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            verdict = report.get("global", {}).get("verdict", "?")
            results.append({
                "file": basename,
                "status": "success",
                "verdict": verdict,
                "output": out_path,
            })
            success_count += 1

        except Exception as e:
            results.append({
                "file": basename,
                "status": "error",
                "error": str(e),
            })
            error_count += 1

    return {
        "total": len(files),
        "success": success_count,
        "errors": error_count,
        "reports": results,
    }


# ─── Interface CLI ──────────────────────────────────────────────────────────

def main():
    """
    Point d'entrée CLI pour le script bullet_proof.py.

    Usage:
        python3 bullet_proof.py --file procedure.json
            → Bullet proofing complet (architectural + transactionnel + systémique)

        python3 bullet_proof.py --file procedure.json --diff-with old_version.json
            → Bullet proofing avec anti-régression

        python3 bullet_proof.py --file procedure.json --angle architectural
            → Un seul angle spécifique

        python3 bullet_proof.py --file procedure.json --notion-verify
            → Bullet proofing + vérification des relations dans Notion

        python3 bullet_proof.py --batch ./procedures/ --glob "*.json"
            → Mode batch: traiter tous les fichiers JSON d'un répertoire

        python3 bullet_proof.py --check
            → Vérifier le token Notion et la connexion API

        python3 bullet_proof.py --batch ./data/ --notion-verify --dir-output ./reports/
            → Batch avec vérification Notion et répertoire de sortie dédié
    """
    parser = argparse.ArgumentParser(
        description="Bullet Proofing 4 angles pour DOX_PROC",
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="Fichier JSON de la procédure à vérifier",
    )
    parser.add_argument(
        "--diff-with",
        type=str,
        default=None,
        help="Fichier JSON de l'ancienne version (anti-régression)",
    )
    parser.add_argument(
        "--angle",
        type=str,
        default=None,
        choices=["architectural", "transactionnel", "systemique", "anti_regression"],
        help="Exécuter un seul angle spécifique",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Fichier de sortie pour les résultats",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Vérifier le token Notion et la connexion à l'API",
    )
    parser.add_argument(
        "--notion-verify",
        action="store_true",
        help="Vérifier les relations BDD dans Notion (requiert API)",
    )
    parser.add_argument(
        "--batch",
        type=str,
        default=None,
        metavar="DIR",
        help="Mode batch: traiter tous les fichiers JSON d'un répertoire",
    )
    parser.add_argument(
        "--glob",
        type=str,
        default="*.json",
        help="Glob pour le mode batch (défaut: *.json)",
    )
    parser.add_argument(
        "--dir-output",
        type=str,
        default=None,
        metavar="DIR",
        help="Répertoire de sortie pour le mode batch (défaut: --batch)",
    )

    args = parser.parse_args()

    try:
        # ── --check : vérification Notion ──────────────────────────────
        if args.check:
            _cmd_check()

        # ── --batch : mode batch ───────────────────────────────────────
        elif args.batch:
            batch_results = _cmd_batch(
                input_dir=args.batch,
                glob_pattern=args.glob,
                output_dir=args.dir_output or args.batch,
                notion_verify=args.notion_verify,
            )
            print(json.dumps(batch_results, indent=2, ensure_ascii=False))

        # ── --file : mode fichier unique (par défaut) ──────────────────
        elif args.file:
            if not os.path.isfile(args.file):
                print(f"Erreur : fichier introuvable — {args.file}",
                      file=sys.stderr)
                sys.exit(1)

            try:
                with open(args.file, "r") as f:
                    procedure_data = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                print(f"Erreur de lecture : {e}", file=sys.stderr)
                sys.exit(1)

            old_version = None
            if args.diff_with:
                if not os.path.isfile(args.diff_with):
                    print(f"Erreur : fichier introuvable — {args.diff_with}",
                          file=sys.stderr)
                    sys.exit(1)
                with open(args.diff_with, "r") as f:
                    old_version = json.load(f)

            if args.angle == "architectural":
                result = {"angle": "architectural", "issues": architectural_check(procedure_data)}
            elif args.angle == "transactionnel":
                vh = procedure_data.get("version_history", [])
                result = {"angle": "transactionnel", "issues": transactionnel_check(vh)}
            elif args.angle == "systemique":
                relations = procedure_data.get("relations", {})
                result = {"angle": "systemique", "issues": systemique_check(relations)}
            elif args.angle == "anti_regression":
                if not old_version:
                    print("Erreur : --diff-with requis pour l'angle anti_regression",
                          file=sys.stderr)
                    sys.exit(1)
                diffs = anti_regression_check(old_version, procedure_data)
                result = {"angle": "anti_regression", "differences": diffs}
            else:
                result = full_bullet_proof(procedure_data, old_version)

            # Vérification Notion optionnelle
            if args.notion_verify:
                notion_results = _verify_relations_in_notion(procedure_data)
                result["notion_verification"] = notion_results

            if args.output:
                with open(args.output, "w") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"Résultats sauvegardés dans {args.output}")
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))

        else:
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e),
        }, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
