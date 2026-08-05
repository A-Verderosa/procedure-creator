#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_contract.py — Génération DOX Contract
===============================================

Génère et valide le DOX Contract, le document JSON structuré qui décrit
une procédure DOX et ses relations avec les BDD canoniques.

Le DOX Contract est la clé de voûte de la synchronisation bidirectionnelle
Hermes ↔ Notion.

Fonctions principales :
  - generate_dox_contract(procedure_data, niveau) → dict
  - validate_contract(contract) → liste d'erreurs
  - CLI : python3 generate_contract.py --from-file <path>
         python3 generate_contract.py --interactive
"""

import argparse
import glob as glob_module
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

# Module partagé Notion (token, PROP_MAP, requêtes API)
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


# ─── Niveaux et modules ─────────────────────────────────────────────────────

NIVEAUX_MODULES = {
    "bronze": {
        "code": "BZ",
        "emoji": "🥉",
        "modules": ["00_HUB", "01_CADRAGE"],
        "score_max": 40,
        "trophee_seuils": {"bronze": 25, "argent": None, "or": None, "platine": None, "ultra": None, "mythique": None},
    },
    "argent": {
        "code": "AR",
        "emoji": "🥈",
        "modules": ["00_HUB", "01_CADRAGE", "02_ACTEURS", "03_FLUX"],
        "score_max": 55,
        "trophee_seuils": {"argent": 40, "or": None, "platine": None, "ultra": None, "mythique": None},
    },
    "or": {
        "code": "OR",
        "emoji": "🥇",
        "modules": ["00_HUB", "01_CADRAGE", "02_ACTEURS", "03_FLUX", "04_REGLES"],
        "score_max": 70,
        "trophee_seuils": {"or": 55, "platine": None, "ultra": None, "mythique": None},
    },
    "platine": {
        "code": "PT",
        "emoji": "💎",
        "modules": ["00_HUB", "01_CADRAGE", "02_ACTEURS", "03_FLUX", "04_REGLES", "05_RISQUES", "06_DOCUMENTS", "07_QG"],
        "score_max": 80,
        "trophee_seuils": {"platine": 65, "ultra": None, "mythique": None},
    },
    "ultra": {
        "code": "UL",
        "emoji": "💎",
        "modules": ["00_HUB", "01_CADRAGE", "02_ACTEURS", "03_FLUX", "04_REGLES", "05_RISQUES", "06_DOCUMENTS", "07_QG", "08_CYCLE_VIE"],
        "score_max": 85,
        "trophee_seuils": {"ultra": 70, "mythique": None},
    },
    "mythique": {
        "code": "MY",
        "emoji": "🔮",
        "modules": [
            "00_HUB", "01_CADRAGE", "02_ACTEURS", "03_FLUX", "04_REGLES",
            "05_RISQUES", "06_DOCUMENTS", "07_QG", "08_CYCLE_VIE",
            "09_KPI", "10_TENDANCES", "11_PREDICTIF",
        ],
        "score_max": 90,
        "trophee_seuils": {"mythique": 75},
    },
    "akuma": {
        "code": "AK",
        "emoji": "👹",
        "modules": ["IA_DIAG", "IA_EVOLUTION", "IA_GARDE_FOUS"],
        "score_max": 0,
        "trophee_seuils": {},
    },
}

VALID_NIVEAUX = set(NIVEAUX_MODULES.keys())


# ─── Génération du DOX Contract ────────────────────────────────────────────

def generate_dox_contract(procedure_data, niveau="argent"):
    """
    Génère le DOX Contract pour une procédure.

    Le contrat JSON contient toutes les métadonnées nécessaires à la
    synchronisation Notion : identifiant, niveau, modules, scorecard,
    relations BDD, cycle de vie.

    Args:
        procedure_data (dict): Données de la procédure avec les clés :
            - titre (str) : Titre de la procédure
            - type_rh (str) : Type RH (rémunération, carrière, etc.)
            - perimetre (str) : Périmètre (DGAT, DGSP, etc.)
            - acteurs_cles (list) : Liste des acteurs
            - risques (list) : Liste des risques identifiés
            - documents (list) : Liste des documents liés
            - qg_score (float) : Score QG (optionnel)
            - version (str) : Version (optionnel, défaut "1.0")
        niveau (str): Niveau de la procédure
            (bronze, argent, or, platine, ultra, mythique, akuma).

    Returns:
        dict: DOX Contract JSON-serializable avec :
            - procedure_id (str) : ID généré PRH-xxx
            - niveau (str) : Niveau demandé
            - niveau_config (dict) : Configuration du niveau
            - titre (str) : Titre
            - type_rh (str) : Type RH
            - perimetre (str) : Périmètre
            - version (str) : Version
            - modules (list) : Modules activés
            - scorecard (dict) : Scorecard détaillée
            - relations (dict) : Relations BDD
            - cycle_de_vie (dict) : Cycle de vie
            - generated_at (str) : Timestamp ISO
            - metadata (dict) : Métadonnées additionnelles

    Raises:
        ValueError: Si le niveau est invalide.
    """
    niveau = niveau.lower()
    if niveau not in VALID_NIVEAUX:
        raise ValueError(
            f"Niveau invalide : '{niveau}'. "
            f"Choisir parmi : {', '.join(sorted(VALID_NIVEAUX))}"
        )

    titre = procedure_data.get("titre", "Procédure sans titre")
    type_rh = procedure_data.get("type_rh", "")
    perimetre = procedure_data.get("perimetre", "")
    version = procedure_data.get("version", "1.0")

    # Génération d'un ID unique
    procedure_id = _generate_procedure_id(titre, procedure_data)

    # Configuration du niveau
    niveau_config = NIVEAUX_MODULES[niveau]

    # Modules activés pour ce niveau
    modules = list(niveau_config["modules"])

    # Scorecard
    qg_score = procedure_data.get("qg_score", 0) or 0
    score_max = niveau_config["score_max"]
    scorecard = _generate_scorecard(qg_score, score_max, niveau, procedure_data)

    # Relations BDD
    relations = _generate_relations(procedure_data)

    # Cycle de vie
    cycle_de_vie = _generate_cycle_de_vie(procedure_data, niveau)

    # Métadonnées
    metadata = {
        "acteurs_cles": procedure_data.get("acteurs_cles", []),
        "nombre_risques": len(procedure_data.get("risques", [])),
        "nombre_documents": len(procedure_data.get("documents", [])),
        "sections_obligatoires": _get_sections_obligatoires(niveau),
        # ── Données Cadrage (§1–§8) ──
        "objet": procedure_data.get("objet", ""),
        "champ_application": procedure_data.get("champ_application", ""),
        "definitions": procedure_data.get("definitions", ""),
        "documents_reference": procedure_data.get("documents_reference", ""),
        "acteurs": procedure_data.get("acteurs", ""),
        "regles": procedure_data.get("regles", ""),
        "consignes": procedure_data.get("consignes", ""),
    }

    contract = {
        "procedure_id": procedure_id,
        "niveau": niveau,
        "niveau_config": {
            "code": niveau_config["code"],
            "emoji": niveau_config["emoji"],
            "score_max": niveau_config["score_max"],
        },
        "titre": titre,
        "type_rh": type_rh,
        "perimetre": perimetre,
        "version": version,
        "modules": modules,
        "scorecard": scorecard,
        "relations": relations,
        "cycle_de_vie": cycle_de_vie,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "metadata": metadata,
    }

    return contract


def _derive_prefix(direction):
    """
    Dérive le préfixe ID du service/pôle.

    Args:
        direction (str): Direction ou pôle de la procédure.

    Returns:
        str: Préfixe sur 3 lettres (EVP, PRH, etc.)
    """
    if not direction:
        return "EVP"
    d = direction.lower()
    if "évaluateur" in d or "evaluateur" in d:
        return "EVP"
    if "ressource" in d or "rh" in d:
        return "PRH"
    # Fallback : initiales de la direction
    words = direction.split()
    initials = "".join(w[0].upper() for w in words if w[0].isalpha())[:3]
    return initials if len(initials) == 3 else "EVP"


def _generate_procedure_id(titre, procedure_data):
    """
    Génère un identifiant unique de procédure [PRÉFIXE]-xxx.

    Le préfixe est dérivé de la direction (EVP pour Évaluateur public,
    PRH pour RH, etc.).

    Args:
        titre (str): Titre de la procédure.
        procedure_data (dict): Données de la procédure.

    Returns:
        str: Identifiant au format PREFIX-xxx.
    """
    prefix = _derive_prefix(procedure_data.get("direction", ""))

    # Si déjà fourni avec le bon format, le conserver
    existing_id = procedure_data.get("procedure_id", "")
    if existing_id and re.match(r"^[A-Z]{3}-\d{3}$", existing_id):
        return existing_id

    # Générer à partir du titre
    # Extraire les initiales du titre
    words = titre.split()
    initials = "".join(
        w[0].upper() for w in words if w[0].isalpha()
    )[:3].upper()
    if not initials:
        initials = prefix

    # Numéro basé sur timestamp (derniers 3 chiffres)
    num = int(datetime.now(timezone.utc).timestamp()) % 1000
    return f"{prefix}-{num:03d}"


def _generate_scorecard(qg_score, score_max, niveau, procedure_data):
    """
    Génère la scorecard détaillée.

    Args:
        qg_score (float): Score QG pondéré.
        score_max (int): Score maximum pour ce niveau.
        niveau (str): Niveau de la procédure.
        procedure_data (dict): Données de la procédure.

    Returns:
        dict: Scorecard avec total, max, pourcentage, trophée, sous-critères.
    """
    pct = round((qg_score / score_max * 100), 1) if score_max > 0 else 0.0

    # Détermination du trophée
    trophee = _determiner_trophee(pct, niveau)

    # Sous-critères simulés (à enrichir par qg_validator)
    sous_criteres = {
        "structure": min(100, pct * 1.1) if pct > 0 else 0,
        "modularite": min(100, pct * 0.9) if pct > 0 else 0,
        "cycle_vie": min(100, pct * 1.0) if pct > 0 else 0,
    }

    return {
        "total": round(qg_score, 1),
        "max": score_max,
        "pourcentage": pct,
        "trophee": trophee,
        "sous_criteres": sous_criteres,
    }


def _determiner_trophee(score_pct, niveau):
    """
    Détermine le trophée à partir du score et du niveau.

    Args:
        score_pct (float): Score en pourcentage.
        niveau (str): Niveau de la procédure.

    Returns:
        str: Nom du trophée.
    """
    if score_pct >= 90:
        return "Mythique"
    elif score_pct >= 85:
        return "Ultra"
    elif score_pct >= 80:
        return "Platine"
    elif score_pct >= 70:
        return "Or"
    elif score_pct >= 55:
        return "Argent"
    elif score_pct >= 40:
        return "Bronze"
    else:
        return "En construction"


def _generate_relations(procedure_data):
    """
    Génère les relations BDD à partir des données de la procédure.

    Args:
        procedure_data (dict): Données de la procédure.

    Returns:
        dict: Relations avec les BDD canoniques.
    """
    risks = procedure_data.get("risques", [])
    docs = procedure_data.get("documents", [])
    contacts = procedure_data.get("contacts", [])
    org_units = procedure_data.get("organigramme", [])

    return {
        "organigramme": [
            o if isinstance(o, str) else o.get("id", "")
            for o in org_units
        ],
        "annuaire": [
            c if isinstance(c, str) else c.get("id", "")
            for c in contacts
        ],
        "sbrx_risques": [
            r if isinstance(r, str) else r.get("code", r.get("id", ""))
            for r in risks
        ],
        "ged_documents": [
            d if isinstance(d, str) else d.get("id", "")
            for d in docs
        ],
    }


def _generate_cycle_de_vie(procedure_data, niveau):
    """
    Génère les informations de cycle de vie de la procédure.

    Args:
        procedure_data (dict): Données de la procédure.
        niveau (str): Niveau de la procédure.

    Returns:
        dict: Cycle de vie avec dates, statut, périodicité.
    """
    maintenant = datetime.now(timezone.utc)
    date_creation = procedure_data.get(
        "date_creation",
        maintenant.strftime("%Y-%m-%d"),
    )

    # Périodicité de revue selon le niveau
    periodicites = {
        "bronze": 24,   # 24 mois
        "argent": 18,
        "or": 12,
        "platine": 12,
        "ultra": 6,
        "mythique": 6,
        "akuma": 3,
    }
    periodicite_mois = periodicites.get(niveau, 12)

    # Calcul de la prochaine revue
    if isinstance(date_creation, str):
        try:
            d_creation = datetime.strptime(date_creation, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            d_creation = maintenant
    else:
        d_creation = maintenant

    prochaine_revue = d_creation + timedelta(days=periodicite_mois * 30)
    derniere_revue = procedure_data.get("derniere_revue", date_creation)

    # Statut de révision
    jours_depuis_revue = (maintenant - d_creation).days
    if jours_depuis_revue > periodicite_mois * 30:
        statut = "Périmée"
    elif jours_depuis_revue > periodicite_mois * 30 * 0.8:
        statut = "À réviser"
    else:
        statut = "À jour"

    return {
        "date_creation": date_creation if isinstance(date_creation, str) else date_creation.strftime("%Y-%m-%d"),
        "derniere_revue": derniere_revue if isinstance(derniere_revue, str) else derniere_revue.strftime("%Y-%m-%d"),
        "prochaine_revue": prochaine_revue.strftime("%Y-%m-%d"),
        "periodicite_mois": periodicite_mois,
        "statut": statut,
        "niveau": niveau,
        "version": procedure_data.get("version", "1.0"),
    }


def _get_sections_obligatoires(niveau):
    """
    Retourne la liste des sections obligatoires pour le niveau.

    Args:
        niveau (str): Niveau de la procédure.

    Returns:
        list: Noms des sections obligatoires.
    """
    sections = {
        "bronze": ["flash_card", "craie_localisation", "acteurs_cles", "etapes_simplifiees"],
        "argent": ["flash_card", "craie_localisation", "mermaid_logigramme", "raci", "etapes_detaillees", "risques_identifies"],
        "or": ["flash_card", "craie_localisation", "mermaid_logigramme", "raci_complet", "etapes_detaillees", "risques_identifies", "documents_support", "documents_enregistrement"],
        "platine": ["flash_card", "craie_localisation", "mermaid_logigramme", "raci_complet", "etapes_detaillees", "risques_identifies", "documents_support", "documents_enregistrement", "quality_gate_checklist", "cycle_vie", "scorecard"],
        "ultra": ["flash_card", "craie_localisation", "mermaid_logigramme", "raci_complet_6plus", "etapes_detaillees", "risques_sbrx_ries", "documents_support", "documents_enregistrement", "quality_gate_checklist", "cycle_vie_verrouille", "scorecard_complet", "modularite_tableau", "points_vigilance", "indicateurs_performance"],
        "mythique": ["flash_card", "craie_localisation", "mermaid_logigramme", "raci_complet_6plus", "etapes_detaillees", "risques_sbrx_ries", "documents_support", "documents_enregistrement", "quality_gate_checklist", "cycle_vie_verrouille", "scorecard_complet", "modularite_tableau", "points_vigilance", "indicateurs_performance", "kpi_cockpit", "analyse_tendances", "predictive_alerts", "visualization_avancee", "audit_trail"],
        "akuma": ["diagnostic_ia", "indicateurs_dynamiques", "boucle_retour_auto", "garde_fous_securite", "simulation_evolution"],
    }
    return sections.get(niveau, [])


# ─── Validation du contrat ──────────────────────────────────────────────────

def validate_contract(contract):
    """
    Valide un DOX Contract et retourne la liste des erreurs.

    Vérifie :
      - Présence et format des champs obligatoires
      - Validité du niveau
      - Cohérence des modules
      - Format de l'ID
      - Intégrité des relations
      - Scorecard cohérente

    Args:
        contract (dict): Contrat DOX à valider.

    Returns:
        list: Liste des erreurs (str). Vide si le contrat est valide.
    """
    errors = []

    # Champs obligatoires
    required_fields = [
        "procedure_id", "niveau", "titre", "modules",
        "scorecard", "relations", "cycle_de_vie",
    ]
    for field in required_fields:
        if field not in contract:
            errors.append(f"Champ obligatoire manquant : '{field}'")

    if errors:
        return errors

    # ID
    pid = contract.get("procedure_id", "")
    if not re.match(r"^[A-Z]{3}-\d{3}$", pid):
        errors.append(
            f"Format ID invalide : '{pid}'. "
            "Attendu : PREFIX-xxx (PREFIX = 3 lettres, xxx = 3 chiffres)"
        )

    # Niveau
    niveau = contract.get("niveau", "").lower()
    if niveau not in VALID_NIVEAUX:
        errors.append(
            f"Niveau invalide : '{niveau}'. "
            f"Valides : {', '.join(sorted(VALID_NIVEAUX))}"
        )

    # Modules
    modules = contract.get("modules", [])
    if not modules:
        errors.append("La liste des modules est vide")
    else:
        # Vérifier que les modules sont cohérents avec le niveau
        expected_modules = NIVEAUX_MODULES.get(niveau, {}).get("modules", [])
        missing_modules = [m for m in expected_modules if m not in modules]
        if missing_modules:
            errors.append(
                f"Modules obligatoires manquants pour {niveau} : "
                f"{', '.join(missing_modules)}"
            )

    # Scorecard
    scorecard = contract.get("scorecard", {})
    if not isinstance(scorecard, dict):
        errors.append("La scorecard doit être un dictionnaire")
    else:
        if "total" not in scorecard:
            errors.append("Scorecard : champ 'total' manquant")
        if "max" not in scorecard:
            errors.append("Scorecard : champ 'max' manquant")
        if "trophee" not in scorecard:
            errors.append("Scorecard : champ 'trophee' manquant")

    # Relations
    relations = contract.get("relations", {})
    if not isinstance(relations, dict):
        errors.append("Les relations doivent être un dictionnaire")
    else:
        valid_relation_keys = {"organigramme", "annuaire", "sbrx_risques", "ged_documents"}
        unknown_keys = set(relations.keys()) - valid_relation_keys
        if unknown_keys:
            errors.append(
                f"Clés de relations inconnues : {', '.join(unknown_keys)}. "
                f"Valides : {', '.join(sorted(valid_relation_keys))}"
            )

    # Cycle de vie
    cycle = contract.get("cycle_de_vie", {})
    if not isinstance(cycle, dict):
        errors.append("Le cycle de vie doit être un dictionnaire")
    else:
        cycle_fields = ["date_creation", "derniere_revue", "prochaine_revue", "statut"]
        for field in cycle_fields:
            if field not in cycle:
                errors.append(f"Cycle de vie : champ '{field}' manquant")

        # Vérifier le statut
        statut = cycle.get("statut", "")
        if statut and statut not in ("À jour", "À réviser", "Périmée"):
            errors.append(
                f"Statut invalide : '{statut}'. "
                "Attendu : 'À jour', 'À réviser', ou 'Périmée'"
            )

    return errors


# ─── Helpers CLI : vérification, batch, notion ────────────────────────────

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


def _cmd_validate(path):
    """
    Valide un fichier JSON de contrat DOX existant.

    Args:
        path (str): Chemin vers le fichier contrat JSON.
    """
    if not os.path.isfile(path):
        print(json.dumps({
            "status": "error", "message": f"Fichier introuvable : {path}",
        }, indent=2))
        sys.exit(1)

    with open(path, "r") as f:
        contract = json.load(f)

    # Déwrapper : supporte {"procedure": {...}} et {...}
    if "procedure" in contract and isinstance(contract["procedure"], dict):
        contract = contract["procedure"]
    elif "data" in contract and isinstance(contract["data"], dict):
        contract = contract["data"]

    errors = validate_contract(contract)
    if errors:
        print(json.dumps({
            "valid": False, "errors": errors,
        }, indent=2, ensure_ascii=False))
        sys.exit(1)
    else:
        print(json.dumps({
            "valid": True,
            "contract_id": contract.get("procedure_id", ""),
        }, indent=2))
        sys.exit(0)


def _cmd_from_file(path, niveau=None, output=None,
                   notion_format=False, verify_unique=False):
    """
    Génère un contrat DOX à partir d'un fichier JSON de données.

    Args:
        path (str): Chemin du fichier JSON d'entrée.
        niveau (str, optional): Niveau de procédure.
        output (str, optional): Fichier de sortie.
        notion_format (bool): Ajouter les champs PROP_MAP au contrat.
        verify_unique (bool): Vérifier l'unicité du procedure_id.
    """
    if not os.path.isfile(path):
        print(json.dumps({
            "status": "error", "message": f"Fichier introuvable : {path}",
        }, indent=2))
        sys.exit(1)

    with open(path, "r") as f:
        data = json.load(f)

    # Support du format wrap: {"procedure": {...}}
    proc_data = data.get("procedure", data)

    niveau = niveau or proc_data.get("niveau", "argent")
    contract = generate_dox_contract(proc_data, niveau)

    if notion_format:
        _add_notion_fields(contract)

    if verify_unique and contract.get("procedure_id"):
        existing = _verify_unique_in_notion(contract["procedure_id"])
        contract["notion_uniqueness"] = existing

    if output:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w") as f:
            json.dump(contract, f, indent=2, ensure_ascii=False)
        print(f"Contrat généré dans {output}")
    else:
        print(json.dumps(contract, indent=2, ensure_ascii=False))


def _cmd_batch(input_dir, glob_pattern="*.json", output_dir=None,
               niveau=None, notion_format=False, verify_unique=False):
    """
    Traite en batch tous les fichiers JSON d'un répertoire.

    Args:
        input_dir (str): Répertoire contenant les fichiers JSON.
        glob_pattern (str): Glob pattern pour filtrer les fichiers.
        output_dir (str): Répertoire de sortie pour les contrats.
        niveau (str, optional): Niveau forcé pour tous.
        notion_format (bool): Ajouter les champs PROP_MAP.
        verify_unique (bool): Vérifier l'unicité des procedure_id.

    Returns:
        dict: Résumé du batch {total, success, errors, contracts}.
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
            "contracts": [],
            "message": f"Aucun fichier trouvé avec {pattern}",
        }

    results = []
    success_count = 0
    error_count = 0

    for filepath in files:
        basename = os.path.splitext(os.path.basename(filepath))[0]
        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            # Support du format wrap: {"procedure": {...}}
            proc_data = data.get("procedure", data)

            niveau_eff = niveau or proc_data.get("niveau", "argent")
            contract = generate_dox_contract(proc_data, niveau_eff)

            if notion_format:
                _add_notion_fields(contract)

            if verify_unique and contract.get("procedure_id"):
                existing = _verify_unique_in_notion(contract["procedure_id"])
                contract["notion_uniqueness"] = existing

            # Sauvegarder le contrat
            out_path = os.path.join(output_dir, f"{basename}_contract.json")
            with open(out_path, "w") as f:
                json.dump(contract, f, indent=2, ensure_ascii=False)

            results.append({
                "file": basename,
                "status": "success",
                "contract_id": contract.get("procedure_id", ""),
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
        "contracts": results,
    }


def _add_notion_fields(contract):
    """
    Ajoute les noms de propriétés Notion (PROP_MAP) dans le contrat
    sous la clé 'notion_properties' pour faciliter le push vers Notion.

    Args:
        contract (dict): Contrat DOX (modifié sur place).
    """
    mapping = {}
    for dox_key, notion_key in PROP_MAP.items():
        # Chercher la valeur correspondante dans le contrat
        if dox_key in contract:
            mapping[dox_key] = {
                "notion_name": notion_key,
                "valeur": contract[dox_key],
            }
    contract["notion_properties"] = mapping


def _verify_unique_in_notion(procedure_id):
    """
    Vérifie si un procedure_id existe déjà dans la BDD Notion.

    Args:
        procedure_id (str): ID de procédure à vérifier.

    Returns:
        dict: Résultat {exists, existing_page_id, existing_url} ou
              {error: str} si la vérification échoue.
    """
    try:
        resp = notion_query(data_source_id=DATA_SOURCE_ID, page_size=50)
        results = resp if isinstance(resp, list) else resp.get("results", [])

        for page in results:
            props = page.get("properties", {})
            pid = extract_procedure_id(props)
            if pid and pid.split("-")[-1] == procedure_id:
                return {
                    "exists": True,
                    "existing_page_id": page.get("id", ""),
                    "existing_url": page.get("url", ""),
                }

        return {"exists": False}

    except RuntimeError as e:
        return {"error": str(e)}


# ─── Interface CLI (suite) ────────────────────────────────────────────────

def main():
    """
    Point d'entrée CLI pour le script generate_contract.py.

    Usage:
        python3 generate_contract.py --from-file procedure.json
            → Génère le contrat à partir d'un fichier JSON de données

        python3 generate_contract.py --from-file procedure.json --niveau ultra
            → Génère le contrat pour un niveau spécifique

        python3 generate_contract.py --interactive
            → Mode interactif (saisie des données pas à pas)

        python3 generate_contract.py --validate contract.json
            → Valide un contrat existant
    """
    parser = argparse.ArgumentParser(
        description="Génération et validation du DOX Contract",
    )
    parser.add_argument(
        "--from-file",
        type=str,
        default=None,
        help="Fichier JSON contenant les données de la procédure",
    )
    parser.add_argument(
        "--niveau",
        type=str,
        default=None,
        choices=sorted(VALID_NIVEAUX),
        help="Niveau de la procédure (défaut: depuis les données)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Mode interactif avec saisie pas à pas",
    )
    parser.add_argument(
        "--validate",
        type=str,
        default=None,
        help="Valide un fichier JSON de contrat DOX existant",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Fichier de sortie pour le contrat généré",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Vérifier le token Notion et la connexion à l'API",
    )
    parser.add_argument(
        "--notion-format",
        action="store_true",
        help="Ajouter les noms de propriétés Notion (PROP_MAP) dans le contrat",
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
    parser.add_argument(
        "--verify-unique",
        action="store_true",
        help="Vérifier l'unicité du procedure_id dans Notion avant génération",
    )

    args = parser.parse_args()

    try:
        # ── --check : vérification Notion ──────────────────────────────
        if args.check:
            _cmd_check()

        # ── --batch : mode batch ───────────────────────────────────────
        elif args.batch:
            results = _cmd_batch(
                input_dir=args.batch,
                glob_pattern=args.glob,
                output_dir=args.dir_output or args.batch,
                niveau=args.niveau,
                notion_format=args.notion_format,
                verify_unique=args.verify_unique,
            )
            print(json.dumps(results, indent=2, ensure_ascii=False))

        # ── --validate ────────────────────────────────────────────────
        elif args.validate:
            _cmd_validate(args.validate)

        # ── --from-file ────────────────────────────────────────────────
        elif args.from_file:
            _cmd_from_file(args.from_file, args.niveau, args.output,
                           args.notion_format, args.verify_unique)

        # ── --interactive ──────────────────────────────────────────────
        elif args.interactive:
            contract = _interactive_mode()
            if args.notion_format:
                _add_notion_fields(contract)
            if args.output:
                with open(args.output, "w") as f:
                    json.dump(contract, f, indent=2, ensure_ascii=False)
                print(f"Contrat généré dans {args.output}")
            else:
                print(json.dumps(contract, indent=2, ensure_ascii=False))

        else:
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e),
        }, indent=2), file=sys.stderr)
        sys.exit(1)


def _interactive_mode():
    """
    Mode interactif pour saisir les données de la procédure pas à pas.

    Returns:
        dict: Contrat DOX généré.
    """
    print("=== Génération interactive du DOX Contract ===")
    print()

    titre = input("Titre de la procédure : ").strip()
    while not titre:
        titre = input("Titre (obligatoire) : ").strip()

    niveau = input(
        f"Niveau ({', '.join(sorted(VALID_NIVEAUX))}) [argent] : "
    ).strip().lower() or "argent"
    while niveau not in VALID_NIVEAUX:
        niveau = input(
            f"Niveau invalide. Choisir parmi {', '.join(sorted(VALID_NIVEAUX))} : "
        ).strip().lower() or "argent"

    type_rh = input("Type RH (rémunération, carrière, formation, etc.) : ").strip()
    perimetre = input("Périmètre (DGAT, DGSP, DGA, etc.) : ").strip()

    # Acteurs
    acteurs_input = input("Acteurs clés (séparés par des virgules) : ").strip()
    acteurs = [a.strip() for a in acteurs_input.split(",") if a.strip()] if acteurs_input else []

    # Score QG
    score_str = input("Score QG (optionnel) : ").strip()
    qg_score = float(score_str) if score_str else 0

    data = {
        "titre": titre,
        "niveau": niveau,
        "type_rh": type_rh,
        "perimetre": perimetre,
        "acteurs_cles": acteurs,
        "qg_score": qg_score,
        "risques": [],
        "documents": [],
    }

    print("\nGénération du contrat...")
    return generate_dox_contract(data, niveau)


if __name__ == "__main__":
    main()
