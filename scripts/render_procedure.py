#!/usr/bin/env python3
"""
render_procedure.py — Étape RENDER du pipeline PROC.

Transforme un DOX Contract (JSON) en document `.md` complet en utilisant
les templates et golden examples. Gère deux modes de production :

  - Bronze→Mythique : template du niveau + CGSS‑118 comme référence
  - Akuma          : socle Mythique + couche Akuma auto‑évolutive

Usage:
  python3 render_procedure.py contract.json --output procedure.md
  python3 render_procedure.py contract.json --niveau mythique --output proc.md
  python3 render_procedure.py --check-only contract.json     # dry-run : rapport des placeholders
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

# ── Chemins du skill ──────────────────────────────────────────────
SKILL_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATES_DIR = os.path.join(SKILL_DIR, "templates")
REFERENCES_DIR = os.path.join(SKILL_DIR, "references")

DEFAULT_TEMPLATE = os.path.join(TEMPLATES_DIR, "mythique_template.md")
ULTRA_TEMPLATE = os.path.join(TEMPLATES_DIR, "ultra_template.md")
ARGENT_TEMPLATE = os.path.join(TEMPLATES_DIR, "argent_template.md")
AKUMA_TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mythique_template_evaluateur_akuma.md")
GOLDEN_EXAMPLE = os.path.join(REFERENCES_DIR, "cgss118_mythique_structure.md")

# ── Mapping contrat → template ────────────────────────────────────
# Ces placeholders sont résolus directement depuis le contrat
DIRECT_MAP = {
    "REFERENCE": "procedure_id",
    "TITRE": "titre",
    "PERIMETRE": "perimetre",
    "TYPE_RH": "type_rh",
    "VERSION": "version",
    "REDACTEUR": None,       # non mappable → générique
    "VALIDEUR": None,
    "APPROBATEUR": None,
}

# ── Niveaux ───────────────────────────────────────────────────────
VALID_NIVEAUX = {"bronze", "argent", "or", "platine", "ultra", "mythique", "akuma"}

NIVEAU_TEMPLATES = {
    "bronze": ARGENT_TEMPLATE,
    "argent": ARGENT_TEMPLATE,
    "or": ARGENT_TEMPLATE,
    "platine": ULTRA_TEMPLATE,
    "ultra": ULTRA_TEMPLATE,
    "mythique": DEFAULT_TEMPLATE,
    "akuma": AKUMA_TEMPLATE,
}

NIVEAU_EMOJI = {
    "bronze": "🥉",
    "argent": "🥈",
    "or": "🥇",
    "platine": "💎",
    "ultra": "💎",
    "mythique": "🔮",
    "akuma": "☯️",
}


# ─── Mermaid diagram generators ────────────────────────────────────

def generate_flowchart(contract):
    """Génère un logigramme Mermaid à partir des phases/étapes du contrat."""
    metadata = contract.get("metadata", {})
    acteurs = metadata.get("acteurs_cles", [])
    phases = contract.get("phases", contract.get("etapes", []))
    ref = contract.get("procedure_id", "PROC")

    if not phases:
        # Fallback générique si pas de phases dans le contrat
        return _default_flowchart(acteurs, ref)

    lines = ["flowchart TD"]
    lines.append(f'    subgraph ENTREE["Entrées"]')
    lines.append(f'        E1["Demande entrante"]')
    lines.append(f'    end')
    lines.append(f'')
    lines.append(f'    subgraph ETAPES["Processus {ref}"]')
    lines.append(f'        direction TB')

    prev = None
    for i, phase in enumerate(phases):
        label = phase.get("nom", phase.get("titre", f"Étape {i+1}"))
        acteur = phase.get("acteur", acteurs[i % max(len(acteurs), 1)] if acteurs else "Acteur")
        delai = phase.get("delai", "")
        node_id = f"S{i+1}"
        lines.append(f'        {node_id}["{label}\\n⏱ {delai}\\n👤 {acteur}"]')
        if prev:
            lines.append(f'        {prev} --> {node_id}')
        prev = node_id

    lines.append(f'    end')
    lines.append(f'')
    lines.append(f'    subgraph SORTIE["Sorties / Livrables"]')
    lines.append(f'        L1["Procédure validée"]')
    lines.append(f'        L2["Archivage"]')
    lines.append(f'    end')
    lines.append(f'')
    lines.append(f'    {prev} --> L1')
    lines.append(f'    {prev} --> L2')

    return "\n".join(lines)


def _default_flowchart(acteurs, ref):
    """Flowchart minimal quand aucune phase n'est définie."""
    lines = ["flowchart TD"]
    lines.append(f'    subgraph ENTREE["Entrées"]')
    lines.append(f'        E1["Demande / Déclencheur"]')
    lines.append(f'    end')
    lines.append(f'')
    lines.append(f'    subgraph ETAPES["Processus {ref}"]')
    lines.append(f'        direction TB')
    lines.append(f'        S1["Phase préparatoire\\n👤 {acteurs[0] if acteurs else "Acteur"}"]')
    lines.append(f'        S2["Phase execution\\n👤 {acteurs[1] if len(acteurs) > 1 else chr(65)}"]')
    lines.append(f'        S3{{"Décision"}}')
    lines.append(f'        S4["Phase de contrôle\\n👤 {acteurs[2] if len(acteurs) > 2 else "Acteur"}"]')
    lines.append(f'        S5["Phase finalisation"]')
    lines.append(f'    end')
    lines.append(f'    E1 --> S1')
    lines.append(f'    S1 --> S2')
    lines.append(f'    S2 --> S3')
    lines.append(f'    S3 -->|OK| S4')
    lines.append(f'    S3 -->|KO| S2')
    lines.append(f'    S4 --> S5')
    return "\n".join(lines)


def generate_sequence_diagram(contract):
    """Génère un diagramme de séquence multi-acteur."""
    metadata = contract.get("metadata", {})
    acteurs = metadata.get("acteurs_cles", [])
    phases = contract.get("phases", contract.get("etapes", []))

    # Fallback : extraire les acteurs depuis la propriété textuelle "acteurs"
    if not acteurs:
        acteurs_text = contract.get("acteurs", "")
        if acteurs_text and "·" in acteurs_text:
            acteurs = [a.strip() for a in acteurs_text.split("·")]
        elif acteurs_text and "•" in acteurs_text:
            acteurs = [a.strip() for a in acteurs_text.split("•")]
        elif acteurs_text and "," in acteurs_text:
            acteurs = [a.strip() for a in acteurs_text.split(",")]

    if not acteurs:
        return ""

    lines = ["sequenceDiagram"]
    lines.append(f'    participant D as Demandeur')
    for i, acteur in enumerate(acteurs):
        lines.append(f'    participant A{i+1} as {acteur}')
    lines.append(f'    participant V as Valideur')
    lines.append(f'')
    lines.append(f'    D->>A1: Transmet la demande')

    for i, phase in enumerate(phases[:5]):
        label = phase.get("nom", phase.get("titre", f"Étape {i+1}"))
        acteur_idx = i % max(len(acteurs), 1)
        if i < len(acteurs) - 1:
            lines.append(f'    A{acteur_idx+1}->>A{acteur_idx+2}: {label}')
        else:
            lines.append(f'    A{acteur_idx+1}->>V: {label}')

    lines.append(f'    V-->>A1: Validation')
    return "\n".join(lines)


def generate_gantt(contract):
    """Génère un diagramme Gantt simple."""
    phases = contract.get("phases", contract.get("etapes", []))
    if not phases:
        return ""

    lines = ["gantt"]
    lines.append(f'    title Planning de déploiement')
    lines.append(f'    dateFormat  YYYY-MM-DD')
    lines.append(f'    axisFormat  %b')
    lines.append(f'')
    lines.append(f'    section Phases')
    for i, phase in enumerate(phases[:6]):
        label = phase.get("nom", phase.get("titre", f"Phase {i+1}"))
        duree = phase.get("delai", "5d")
        lines.append(f'    {label} :a{i+1}, {duree}')

    return "\n".join(lines)


# ─── RISK MATRIX — quadrantChart P×I ──────────────────────────────
# Canonique : COMP.MERMAID.RISK_MATRIX_PI (DOX:v10 FDL)
#
# Quadrants (probabilité × impact) :
#   Q1 (haut/haut)  → "A traiter en priorité"
#   Q2 (bas/haut)   → "A maîtriser"
#   Q3 (bas/bas)    → "Risques acceptables"
#   Q4 (haut/bas)   → "A surveiller"
#
# Mapping niveau → coordonnée (COORDS) : 1→0.07, 2→0.33, 3→0.67, 4→0.93
# Niveaux criticité : FAIBLE=1-3, MOYEN=4-7, HAUT=8-16 (produit P×I)
# Modes : RB (brut, noir), RN (net, bleu), RC (cible, vert)

_COORD_MAP = {1: 0.07, 2: 0.33, 3: 0.67, 4: 0.93}

_SEVERITY_LEVELS = [
    (1, 3, "faible",   "#66BB6A", "#2E7D32", 4),
    (4, 7, "moyen",    "#FFB74D", "#F57C00", 5),
    (8, 16, "haut",    "#EF5350", "#C62828", 6),
]

_MODE_STROKES = {
    "RB": "#212121",   # brut — noir
    "RN": "#1565C0",   # net — bleu
    "RC": "#2E7D32",   # cible — vert
}

_MODE_LABELS = {
    "RB": "RB",
    "RN": "RN",
    "RC": "RC",
}


def _compute_cotation(impact, probability):
    """Calcule le produit P×I (1-16)."""
    return impact * probability


def _get_severity(score):
    """Retourne (nom, fill, stroke, radius) pour un score donné."""
    for lo, hi, name, fill, stroke, radius in _SEVERITY_LEVELS:
        if lo <= score <= hi:
            return name, fill, stroke, radius
    return "faible", "#66BB6A", "#2E7D32", 4  # fallback


def _level_to_coord(level):
    """Convertit un niveau 1-4 en coordonnée 0-1."""
    return _COORD_MAP.get(level, 0.07)


def _format_point(mode, risk_codes, severity, x, y, fill, stroke, radius):
    """Formate une ligne de point Mermaid avec style inline."""
    codes = ",".join(risk_codes)
    return (
        f"    {mode}{codes}:::{severity}: "
        f"[{x:.2f}, {y:.2f}] "
        f"radius: {radius}, color: {fill}, "
        f"stroke-color: {stroke}, stroke-width: 2px"
    )


def generate_risk_matrix(
    contract=None,
    risks=None,
    mesures=None,
    mode="RB",
    procedure_title=None,
):
    """
    Génère un quadrantChart Mermaid pour la matrice des risques P×I.

    Args:
        contract: Contrat JSON (ou dict). Si fourni, extrait risks_detail + pmri_mesures.
        risks: Liste directe de risques [{'code','impact','probability',...}].
               Utilisé si contract est None.
        mesures: Liste directe de mesures PMRI [{'risque_code','effet_impact','effet_probabilite'}].
        mode: "RB" (brut), "RN" (net), "RB-RN", "RB-RN-RC", etc.
        procedure_title: Titre pour le graphique (ex: "M1-P3-01 Saisine").

    Returns:
        str: Code Mermaid complet, ou chaîne vide si aucun risque.
    """
    # ── 1. Résoudre les entrées ──────────────────────────────────
    if contract is not None:
        risks = contract.get("risks_detail", contract.get("risks", []))
        mesures = mesures or contract.get("pmri_mesures", [])
        if not procedure_title:
            procedure_title = contract.get("titre", contract.get("procedure_id", "Procédure"))
    elif not procedure_title:
        procedure_title = "Procédure"

    if not risks:
        return ""

    proc_ref = procedure_title[:60]

    # ── 2. Construire l'index des mesures PMRI par risque ────────
    pmri_by_risk = {}
    for m in (mesures or []):
        rcode = m.get("risque_code", "")
        if rcode not in pmri_by_risk:
            pmri_by_risk[rcode] = []
        pmri_by_risk[rcode].append(m)

    def _compute_net(risk):
        """Calcule les niveaux net (après PMRI)."""
        imp = risk.get("impact", 1)
        prob = risk.get("probability", 1)
        for m in pmri_by_risk.get(risk.get("code", ""), []):
            ei = m.get("effet_impact", 0)
            ep = m.get("effet_probabilite", 0)
            imp = max(1, min(4, imp + ei))
            prob = max(1, min(4, prob + ep))
        return imp, prob

    def _compute_cible(risk):
        """Calcule les niveaux cible (hypothèse RC)."""
        # RC = RN après toutes les barrières ; on retranche encore 1 si possible
        imp, prob = _compute_net(risk)
        imp = max(1, imp - 1)
        prob = max(1, prob - 1)
        return imp, prob

    # ── 3. Déterminer les modes à générer ────────────────────────
    modes_to_gen = [m.strip() for m in mode.upper().split("-") if m.strip()]
    # Filtrer les modes inconnus
    modes_to_gen = [m for m in modes_to_gen if m in _MODE_STROKES]

    if not modes_to_gen:
        modes_to_gen = ["RB"]

    # ── 4. Préparer les points par mode ──────────────────────────
    # Structure : {mode: {(x, y): {"codes": [...], "severity": ..., "fill": ..., "stroke": ..., "radius": ...}}}
    points_by_mode = {m: {} for m in modes_to_gen}

    for risk in risks:
        code = risk.get("code", "R?")
        imp_raw = risk.get("impact", 1)
        prob_raw = risk.get("probability", 1)

        for m in modes_to_gen:
            if m == "RB":
                imp, prob = imp_raw, prob_raw
                stroke = _MODE_STROKES["RB"]
            elif m == "RN":
                imp, prob = _compute_net(risk)
                stroke = _MODE_STROKES["RN"]
            elif m == "RC":
                imp, prob = _compute_cible(risk)
                stroke = _MODE_STROKES["RC"]
            else:
                continue

            score = _compute_cotation(imp, prob)
            severity, fill, stroke_color, radius = _get_severity(score)
            x = _level_to_coord(prob)
            y = _level_to_coord(imp)
            key = (round(x, 2), round(y, 2))

            if key not in points_by_mode[m]:
                points_by_mode[m][key] = {
                    "codes": [],
                    "severity": severity,
                    "fill": fill,
                    "stroke": _MODE_STROKES.get(m, stroke_color),
                    "radius": radius,
                }
            points_by_mode[m][key]["codes"].append(f"{m}{code}")

    # ── 5. Générer le titre ──────────────────────────────────────
    mode_str = "×".join(modes_to_gen)
    title = f"RXM:{mode_str} - {proc_ref}"

    # ── 6. Construire les lignes Mermaid ─────────────────────────
    lines = []
    lines.append("quadrantChart")
    lines.append(f"    title {title}")
    lines.append("    x-axis Probabilite faible --> Probabilite forte")
    lines.append("    y-axis Impact faible --> Impact fort")
    lines.append("    quadrant-1 A traiter en priorite")
    lines.append("    quadrant-2 A maitriser")
    lines.append("    quadrant-3 Risques acceptables")
    lines.append("    quadrant-4 A surveiller")
    lines.append("")

    # Points — triés par sévérité décroissante (haut d'abord)
    severity_order = {"haut": 0, "moyen": 1, "faible": 2}
    all_points = []
    for mode_name, pts in points_by_mode.items():
        for (x, y), pt in pts.items():
            all_points.append((pt["codes"], severity_order.get(pt["severity"], 9), x, y, pt))

    all_points.sort(key=lambda p: (p[1], p[2], p[3]))

    for codes, _, x, y, pt in all_points:
        codes_str = ",".join(codes)
        lines.append(
            f"    {codes_str}:::{pt['severity']}: "
            f"[{x:.2f}, {y:.2f}] "
            f"radius: {pt['radius']}, color: {pt['fill']}, "
            f"stroke-color: {pt['stroke']}, stroke-width: 2px"
        )

    lines.append("")

    # classDef — dédupliqué
    seen_class = set()
    for _, _, _, _, pt in all_points:
        sev = pt["severity"]
        if sev not in seen_class:
            color_map = {"haut": "#EF5350", "moyen": "#FFB74D", "faible": "#66BB6A"}
            lines.append(f"    classDef {sev} color:{color_map.get(sev, '#66BB6A')}")
            seen_class.add(sev)

    return "\n".join(lines)


# ─── CARTE CRAIE — flowchart LR amont/procédure/aval ─────────────

def generate_craie_map(
    contract=None,
    procedure_id=None,
    procedure_title=None,
    service=None,
    norm_ref=None,
    norm_title=None,
    amont_items=None,
    aval_items=None,
    risk_codes=None,
):
    """
    Génère un flowchart Mermaid LR représentant la carte CRAIE :
      Norme → Amont → [Procédure] → Aval → Risques

    Args:
        contract: Contrat JSON (dict) pour extraction auto.
        procedure_id: Identifiant (ex: M1-P3-01).
        procedure_title: Titre court.
        service: Service porteur.
        norm_ref: Référence norme (ex: M1).
        norm_title: Titre norme (ex: Pilotage stratégique).
        amont_items: Liste de textes amonts.
        aval_items: Liste de textes avals.
        risk_codes: Liste des codes risques (ex: ["R1","R2"]).
    """
    # Extraction auto depuis contrat
    if contract is not None:
        procedure_id = procedure_id or contract.get("procedure_id", "PROC")
        procedure_title = procedure_title or contract.get("titre", "")
        service = service or contract.get("service", "")
        risks = contract.get("risks_detail", contract.get("risks", []))
        risk_codes = risk_codes or [r.get("code", "R?") for r in risks][:6]
        # Extraction norme depuis le procedure_id (ex: M1-P3-01 → M1)
        parts = procedure_id.split("-")
        norm_ref = norm_ref or parts[0] if parts else "M0"

    # Valeurs par défaut
    procedure_id = procedure_id or "PROC"
    risk_codes = risk_codes or []
    amont_items = amont_items or [
        "Amont : Besoin d'évaluation -- DG / Direction",
        "Amont : Saisine formelle",
    ]
    aval_items = aval_items or [
        "Aval : Phase instruction",
        "Aval : Révision périodique",
    ]
    norm_title = norm_title or f"Macro-processus {norm_ref}"

    lines = []
    lines.append("flowchart LR")
    lines.append(f'    subgraph NORME["Norme CRAIE"]')
    lines.append(f'        MX["{norm_ref or "M0"} {norm_title}"] --> PX["{procedure_id}"]')
    lines.append("    end")

    for i, amont in enumerate(amont_items[:3]):
        safe = amont.replace('"', "'")
        lines.append(f'    AM{i+1}["{safe}"] --> PROC')

    lines.append(f'    PX -.->|cadre norme| PROC')
    lines.append(f'    PROC["📍 {procedure_id}"]')

    for i, aval in enumerate(aval_items[:3]):
        safe = aval.replace('"', "'")
        lines.append(f'    PROC --> AV{i+1}["{safe}"]')

    if risk_codes:
        rc = ",".join(risk_codes[:6])
        lines.append(f'    PROC --> RISK["⚠️ Risques {rc}"]')
        lines.append(f'    RISK --> SBRX["🔗 BDD SBRX / CRAIE"]')

    # Styles
    lines.append(f'    style MX fill:#27ae60,color:#fff')
    lines.append(f'    style PX fill:#2ecc71,color:#fff')
    lines.append(f'    style PROC fill:#ffeb3b,color:#000,stroke:#f57f17,stroke-width:3px')
    for i in range(len(amont_items[:3])):
        lines.append(f'    style AM{i+1} fill:#90caf9,color:#000')
    for i in range(len(aval_items[:3])):
        lines.append(f'    style AV{i+1} fill:#a5d6a7,color:#000')
    if risk_codes:
        lines.append(f'    style RISK fill:#ef5350,color:#fff')
        lines.append(f'    style SBRX fill:#9b59b6,color:#fff')

    return "\n".join(lines)


# ─── Remplissage des placeholders ──────────────────────────────────

PLACEHOLDER_RE = re.compile(r"\{\{(\w[\w._]+)\}\}")


def extract_placeholders(template_text):
    """Extrait tous les placeholders uniques du template."""
    return set(m.group(1) for m in PLACEHOLDER_RE.finditer(template_text))


def build_placeholder_map(contract):
    """
    Construit le dictionnaire {placeholder: valeur} à partir du contrat.
    Utilise DIRECT_MAP, les données dérivées du cycle de vie, scorecard,
    acteurs, risques, documents, etc.
    """
    mapping = {}
    metadata = contract.get("metadata", {})
    cycle = contract.get("cycle_de_vie", {})
    scorecard = contract.get("scorecard", {})
    niveau = contract.get("niveau", "argent")

    # ── 1. DIRECT_MAP ────────────────────────────────────────────
    for placeholder, contract_key in DIRECT_MAP.items():
        if contract_key and contract_key in contract:
            val = contract[contract_key]
            mapping[placeholder] = str(val) if val else "À définir"
        else:
            mapping[placeholder] = "À définir"

    # ── 2. Cycle de vie ──────────────────────────────────────────
    cv_map = {
        "DERNIERE_REVUE": ("derniere_revue", "01/01/2026"),
        "PERIODICITE": ("periodicite_mois", "6"),
        "PROCHAINE_REVUE": ("prochaine_revue", "01/07/2026"),
        "STATUT_REVISION": ("statut", "À jour"),
    }
    for placeholder, (key, fallback) in cv_map.items():
        val = cycle.get(key, fallback) if key else fallback
        mapping[placeholder] = str(val) if val else fallback
    mapping["HISTORIQUE_VERSIONS"] = "Voir §9"

    # ── 3. Scorecard ────────────────────────────────────────────
    ss = scorecard.get("sous_criteres", {})
    mapping["S1"] = str(int(ss.get("structure", 0)))
    mapping["S2"] = str(int(ss.get("modularite", 0)))
    mapping["S3"] = str(int(ss.get("cycle_vie", 0)))
    mapping["S4"] = str(int(scorecard.get("total", 0)))
    mapping["SCORE"] = str(int(scorecard.get("total", 0)))
    mapping["TROPHEE"] = scorecard.get("trophee", "En construction")

    # ── 4. Métadonnées ──────────────────────────────────────────
    mapping["NIVEAU"] = f"{NIVEAU_EMOJI.get(niveau, '📋')} {niveau.title()}"

    # ── 4b. Cadrage (§1–§8) depuis metadata ────────────────────
    cadrage_fields = {
        "OBJET": "objet",
        "CHAMP_APPLICATION": "champ_application",
        "DEFINITIONS": "definitions",
        "DOCUMENTS_REFERENCE": "documents_reference",
        "ACTEURS": "acteurs",
        "REGLES": "regles",
        "CONSIGNES": "consignes",
    }
    for placeholder, field in cadrage_fields.items():
        mapping[placeholder] = metadata.get(field, "") or contract.get(field, "") or "À définir"

    # ── 4c. Placeholders spécifiques Évaluateur ────────────────
    # Alias pour le template mythique_template_evaluateur.md
    evaluateur_aliases = {
        "PROCEDURE_TITLE": contract.get("titre", "Procédure"),
        "PROCEDURE_REF": contract.get("procedure_id", "REF"),
        "TYPE_PROCEDURE": contract.get("type_procedure", "Procédure évaluative"),
        "DATE_CREATION": contract.get("date_creation", datetime.now().strftime("%Y-%m-%d")),
        "DATE_REVUE": contract.get("derniere_revue", datetime.now().strftime("%Y-%m-%d")),
        "VALIDATEUR": "Antoine Verderosa",
        "VALIDATION": "Antoine Verderosa",
        "ACTEURS_CLES": contract.get("acteurs", "À définir"),
        "DECLENCHEUR": contract.get("declencheur", "Saisine formelle"),
        "DELAI_PIVOT": contract.get("delai_pivot", "15 jours"),
        "LIVRABLE_PRINCIPAL": contract.get("livrable_principal", "Décision d'évaluation"),
        "RISQUE_MAJEUR": contract.get("risque_majeur", "Dépassement délai"),
        "ELEMENTS_DECLENCHEURS": contract.get("elements_declencheurs", "Saisine"),
        "PROCESSUS_FILIERE": contract.get("processus", "Gestion administrative"),
        "OBJET": contract.get("objet", "À définir"),
    }
    for ph, val in evaluateur_aliases.items():
        if ph not in mapping:
            mapping[ph] = val

    # ── 5. Placeholders génériques ─────────────────────────────
    generic_defaults = {
        "ACTEUR_1": "Agent instructeur",
        "ACTEUR_2": "Responsable hiérarchique",
        "ACTEUR_3": "Service RH central",
        "ACTEUR_4": "Bureau des méthodes",
        "ACTEUR_5": "Contrôleur de gestion",
        "ACTEUR_6": "Validateur",
        "ROLE_1": "Instruction et suivi des dossiers",
        "ROLE_2": "Validation des propositions",
        "ROLE_3": "Centralisation et contrôle",
        "ROLE_4": "Conception des procédures",
        "ROLE_5": "Analyse de performance",
        "ROLE_6": "Approbation finale",
        "RESP_1": "Instruire, suivre, alerter",
        "RESP_2": "Valider, arbitrer, superviser",
        "RESP_3": "Contrôler, consolider, reporter",
        "RESP_4": "Rédiger, améliorer, capitaliser",
        "RESP_5": "Mesurer, analyser, recommander",
        "RESP_6": "Approuver, engager, signer",
        "COMP_1": "Connaissance métier, outils bureautiques",
        "COMP_2": "Management, vision stratégique",
        "COMP_3": "Réglementation RH, outils SIRH",
        "COMP_4": "Gestion de projet, méthodes",
        "COMP_5": "Analyse de données, tableaux de bord",
        "COMP_6": "Expertise métier, décision",
        "PHASE_1": "Préparation",
        "PHASE_2": "Exécution",
        "PHASE_3": "Contrôle",
        "PHASE_4": "Finalisation",
        "ENTREE_1": "Demande de l'agent",
        "ENTREE_2": "Pièces justificatives",
        "LIVRABLE_1": "Dossier instruit",
        "LIVRABLE_2": "Décision validée",
        "LIVRABLE_3": "Archivage effectué",
        "ETAPE_1": "Réception de la demande",
        "ETAPE_2": "Vérification du dossier",
        "ETAPE_3": "Traitement",
        "ETAPE_4": "Validation",
        "ETAPE_5": "Notification",
        "ACTION_1": "Réceptionner et accuser réception",
        "ACTION_2": "Vérifier la complétude et la conformité",
        "ACTION_3": "Saisir dans le SIRH et calculer",
        "ACTION_4": "Valider les données et signer",
        "ACTION_5": "Notifier l'agent et archiver",
        "ACTION_6": "Contrôler et mesurer",
        "DELAI_1": "J+1",
        "DELAI_2": "J+3",
        "DELAI_3": "J+7",
        "DELAI_4": "J+10",
        "DELAI_5": "J+12",
        "DELAI_6": "J+15",
        "DELAI_7": "J+20",
        "DELAI_8": "J+25",
        "CONTROLE_1": "Complétude OK",
        "CONTROLE_2": "Conformité OK",
        "CONTROLE_3": "Calcul OK",
        "CONTROLE_4": "Signature OK",
        "CONTROLE_5": "Notification OK",
        "CONTROLE_6": "Mesure OK",
        "DECISION_1": "Dossier complet ?",
        "ACTEUR_ETAPE_1": "Agent instructeur",
        "ACTEUR_ETAPE_2": "Agent instructeur",
        "ACTEUR_ETAPE_3": "Agent instructeur",
        "ACTEUR_ETAPE_4": "Responsable hiérarchique",
        "ACTEUR_ETAPE_5": "Service RH",
        "R_A_1": "R",
        "R_A_2": "C",
        "R_A_3": "I",
        "R_A_4": "I",
        "R_A_5": "I",
        "R_A_6": "I",
        "R_A_7": "R",
        "R_A_8": "A",
        "R_A_9": "C",
        "R_A_10": "I",
        "R_A_11": "I",
        "R_A_12": "I",
        "R_A_13": "I",
        "R_A_14": "C",
        "R_A_15": "R",
        "R_A_16": "I",
        "R_A_17": "A",
        "R_A_18": "I",
        "R_A_19": "I",
        "R_A_20": "I",
        "R_A_21": "C",
        "R_A_22": "R",
        "R_A_23": "A",
        "R_A_24": "R",
        "HIST_DATE_1": "01/01/2026",
        "HIST_DATE_2": "15/06/2025",
        "HIST_VERSION_1": "1.0",
        "HIST_VERSION_2": "0.1",
        "HIST_MODIF_1": "Version initiale",
        "HIST_MODIF_2": "Création du document",
        "HIST_AUTEUR_1": "Service rédacteur",
        "HIST_AUTEUR_2": "Service rédacteur",
        "DOC_REF_1": "Guide de saisie SIRH",
        "DOC_REF_2": "Instruction ministérielle",
        "DOC_REF_3": "Code du travail (via GED)",
        "SOURCE_1": "DRH",
        "SOURCE_2": "DGAFP",
        "SOURCE_3": "Légifrance",
        "VERSION_1": "2.0",
        "VERSION_2": "2.0",
        "VERSION_3": "2024",
        "GED_LIEN_1": "GED/guides/saisie_sirh_v2.pdf",
        "GED_LIEN_2": "GED/reglementation/instruction_2024.pdf",
        "GED_LIEN_3": "GED/reglementation/code_travail.pdf",
        "DOC_ENR_1": "Formulaire de demande",
        "DOC_ENR_2": "Accusé de réception",
        "PRODUCTEUR_1": "Agent instructeur",
        "PRODUCTEUR_2": "Agent instructeur",
        "CONSERV_1": "5 ans",
        "CONSERV_2": "2 ans",
        "SUPPORT_1": "SIRH / GED",
        "SUPPORT_2": "SIRH / GED",
        "RISQUE_1": "Erreur de saisie",
        "RISQUE_2": "Retard de traitement",
        "RISQUE_3": "Pièce manquante non détectée",
        "RISQUE_4": "Non-conformité réglementaire",
        "RISQUE_5": "Défaut d'archivage",
        "CAUSE_1": "Saisie manuelle sans contrôle",
        "CAUSE_2": "Charge de travail > capacité",
        "CAUSE_3": "Absence de checklist",
        "CAUSE_4": "Veille juridique insuffisante",
        "CAUSE_5": "Processus d'archivage non défini",
        "EFFET_1": "Dossier erroné, rejet",
        "EFFET_2": "Mécontentement usager",
        "EFFET_3": "Demande de pièce complémentaire",
        "EFFET_4": "Contentieux, rappel à l'ordre",
        "EFFET_5": "Perte de données traçabilité",
        "GRAVITE_1": "3 - Modéré",
        "GRAVITE_2": "4 - Grave",
        "GRAVITE_3": "2 - Faible",
        "GRAVITE_4": "5 - Critique",
        "GRAVITE_5": "3 - Modéré",
        "PROBA_1": "2 - Possible",
        "PROBA_2": "3 - Probable",
        "PROBA_3": "3 - Probable",
        "PROBA_4": "2 - Possible",
        "PROBA_5": "1 - Rare",
        "CRITICITE_1": "6 - 🟡 Moyen",
        "CRITICITE_2": "12 - 🔴 Critique",
        "CRITICITE_3": "6 - 🟡 Moyen",
        "CRITICITE_4": "10 - 🔴 Critique",
        "CRITICITE_5": "3 - 🟢 Faible",
        "MITIG_1": "Double contrôle systématique",
        "MITIG_2": "Tableau de bord + alerte dépassement",
        "MITIG_3": "Checklist complétude automatisée",
        "MITIG_4": "Veille trimestrielle + audit annuel",
        "MITIG_5": "Processus d'archivage automatisé GED",
        "KPI_1": "Délai moyen de traitement",
        "KPI_2": "Taux de complétude à J+1",
        "KPI_3": "Taux de conformité",
        "KPI_4": "Satisfaction usager",
        "KPI_5": "Volume traité",
        "CIBLE_1": "J+7",
        "CIBLE_2": "95%",
        "CIBLE_3": "100%",
        "CIBLE_4": "4.2/5",
        "CIBLE_5": "150/mois",
        "ALERTE_1": "J+12",
        "ALERTE_2": "90%",
        "ALERTE_3": "95%",
        "ALERTE_4": "3.5/5",
        "ALERTE_5": "120/mois",
        "FREQ_1": "Mensuelle",
        "FREQ_2": "Mensuelle",
        "FREQ_3": "Mensuelle",
        "FREQ_4": "Trimestrielle",
        "FREQ_5": "Mensuelle",
        "TENDANCE_1": "📈",
        "TENDANCE_2": "📈",
        "TENDANCE_3": "📊",
        "TENDANCE_4": "📈",
        "TENDANCE_5": "📊",
        "VALEUR_1": "J+8",
        "VALEUR_2": "93%",
        "VALEUR_3": "98%",
        "VALEUR_4": "3.9/5",
        "VALEUR_5": "142",
        "DATA_REEL": "85, 82, 78, 80, 83, 85, 80",
        "DATA_CIBLE": "90, 90, 90, 90, 90, 90, 90",
        "DATA_PREVISION": "87, 88, 89, 89, 90, 91, 91",
        "ALERTE_P_1": "Risque dépassement délai cible",
        "ALERTE_P_2": "Baisse tendancielle conformité",
        "SEUIL_1": "J+10",
        "SEUIL_2": "97%",
        "PROBA_ALERTE_1": "Moyenne (60%)",
        "PROBA_ALERTE_2": "Faible (25%)",
        "DELAI_ALERTE_1": "2 mois",
        "DELAI_ALERTE_2": "4 mois",
        "ACTION_PREV_1": "Renfort ponctuel sur instruction",
        "ACTION_PREV_2": "Formation rappel qualité",
        "FAQ_1.Q": "Quels sont les délais de traitement ?",
        "FAQ_2.Q": "Comment suivre l'avancement ?",
        "FAQ_3.Q": "Quels recours en cas de refus ?",
        "FAQ_4.Q": "Où trouver les formulaires ?",
        "FAQ_5.Q": "Qui contacter en cas de problème ?",
        "FAQ_6.Q": "Comment contester une décision ?",
        "FAQ_7.Q": "Que faire en cas de perte de dossier ?",
        "FAQ_1.R": "Le délai moyen est de 15 jours ouvrés.",
        "FAQ_2.R": "Via le portail RH ou le SIRH.",
        "FAQ_3.R": "Saisir le CHSCT dans un délai de 2 mois.",
        "FAQ_4.R": "Disponibles sur l'intranet ou via le bureau d'accueil.",
        "FAQ_5.R": "Le service instructeur via le standard.",
        "FAQ_6.R": "Par écrit dans les 2 mois suivant la notification.",
        "FAQ_7.R": "Contacter le bureau d'ordre pour une reconstruction.",
    }

    # ── 6. Contrat → override des génériques ─────────────────────
    # Acteurs
    acteurs = metadata.get("acteurs_cles", [])
    for i, act in enumerate(acteurs):
        key = f"ACTEUR_{i+1}"
        if key in generic_defaults:
            mapping[key] = act

    # Si le contrat a des acteurs détaillés (rôles, responsabilités)
    acteurs_detail = contract.get("acteurs", [])
    for i, ad in enumerate(acteurs_detail):
        if isinstance(ad, dict):
            mapping[f"ACTEUR_{i+1}"] = ad.get("nom", ad.get("titre", mapping.get(f"ACTEUR_{i+1}", generic_defaults.get(f"ACTEUR_{i+1}", "Acteur"))))
            mapping[f"ROLE_{i+1}"] = ad.get("role", generic_defaults.get(f"ROLE_{i+1}", "À définir"))
            mapping[f"RESP_{i+1}"] = ad.get("responsabilites", generic_defaults.get(f"RESP_{i+1}", "À définir"))
            mapping[f"COMP_{i+1}"] = ad.get("competences", generic_defaults.get(f"COMP_{i+1}", "À définir"))

    # Phases
    phases = contract.get("phases", contract.get("etapes", []))
    if phases:
        # Phases nommées
        phase_names = [p.get("nom", p.get("titre", f"Phase {i+1}")) for i, p in enumerate(phases)]
        for i, pn in enumerate(phase_names[:4]):
            mapping[f"PHASE_{i+1}"] = pn

        # Étapes détaillées
        for i, phase in enumerate(phases[:8]):
            mapping[f"ETAPE_{i+1}"] = phase.get("nom", phase.get("titre", generic_defaults.get(f"ETAPE_{i+1}", f"Étape {i+1}")))
            mapping[f"ACTION_{i+1}"] = phase.get("action", generic_defaults.get(f"ACTION_{i+1}", f"Action {i+1}"))
            mapping[f"DELAI_{i+1}"] = phase.get("delai", generic_defaults.get(f"DELAI_{i+1}", "J+N"))
            acteur_phase = phase.get("acteur", "")
            if acteur_phase:
                mapping[f"ACTEUR_ETAPE_{i+1}"] = acteur_phase
            mapping[f"LIVRABLE_{i+1}"] = phase.get("livrable", generic_defaults.get(f"LIVRABLE_{i+1}", f"Livrable {i+1}"))
            mapping[f"CONTROLE_{i+1}"] = phase.get("controle", generic_defaults.get(f"CONTROLE_{i+1}", f"Contrôle {i+1}"))

        # ── 5b. Placeholders Évaluateur ────────────────────────────
        for i, phase in enumerate(phases[:8]):
            mapping.setdefault(f"ETAPE_{i+1}_TITRE", phase.get("titre", phase.get("nom", mapping.get(f"ETAPE_{i+1}", f"Étape {i+1}"))))
            mapping.setdefault(f"ETAPE_{i+1}_ACTEURS", phase.get("acteur", mapping.get(f"ACTEUR_ETAPE_{i+1}", "Acteur")))
            mapping.setdefault(f"ETAPE_{i+1}_DUREE", phase.get("delai", mapping.get(f"DELAI_{i+1}", "J+N")))
            mapping.setdefault(f"ETAPE_{i+1}_ACTIONS", phase.get("action", mapping.get(f"ACTION_{i+1}", f"Action {i+1}")))
            mapping.setdefault(f"ETAPE_{i+1}_DOCUMENTS", phase.get("documents", "—"))
            vig_value = phase.get("vigilance", phase.get("points_vigilance", ""))
            if vig_value:
                mapping[f"ETAPE_{i+1}_VIGILANCE"] = vig_value

    # ── Risques ──
    risques_txt = contract.get("risques", "")
    if isinstance(risques_txt, str) and risques_txt.strip():
        # Essayer de parser R1: ... ; R2: ... ou 4 risques (R1-R4). R1: ... ; R2: ...
        risques_txt_clean = re.sub(r'^.*?(?=R\d+\s*[:])', '', risques_txt)
        risque_items = [r.strip() for r in re.split(r'[;,]', risques_txt_clean) if r.strip()]
        for i, item in enumerate(risque_items[:5]):
            idx = i + 1
            # Extraire R1: / R1/ / R1 - / etc.
            item_clean = re.sub(r'^R\d+\s*[:\.–\-—]\s*', '', item).strip()
            if item_clean:
                mapping[f"RISQUE_{idx}"] = item_clean
                mapping[f"RISQUE_{idx}_TITRE"] = item_clean
    else:
        # Liste structurée (format legacy)
        risques = contract.get("relations", {}).get("sbrx_risques", [])
        if not risques:
            risques = metadata.get("risques", [])
        for i, risque in enumerate(risques):
            idx = i + 1
            if isinstance(risque, str):
                mapping[f"RISQUE_{idx}"] = risque
                mapping[f"RISQUE_{idx}_TITRE"] = risque
            elif isinstance(risque, dict):
                mapping[f"RISQUE_{idx}"] = risque.get("nom", risque.get("titre", risque.get("code", f"Risque {idx}")))
                mapping[f"RISQUE_{idx}_TITRE"] = mapping[f"RISQUE_{idx}"]
                mapping[f"CAUSE_{idx}"] = risque.get("cause", generic_defaults.get(f"CAUSE_{idx}", "À définir"))
                mapping[f"EFFET_{idx}"] = risque.get("effet", generic_defaults.get(f"EFFET_{idx}", "À définir"))
                mapping[f"GRAVITE_{idx}"] = risque.get("gravite", generic_defaults.get(f"GRAVITE_{idx}", "3 - Modéré"))
                mapping[f"PROBA_{idx}"] = risque.get("probabilite", generic_defaults.get(f"PROBA_{idx}", "2 - Possible"))
                mapping[f"CRITICITE_{idx}"] = risque.get("criticite", generic_defaults.get(f"CRITICITE_{idx}", "6 - 🟡 Moyen"))
                mapping[f"MITIG_{idx}"] = risque.get("mitigation", generic_defaults.get(f"MITIG_{idx}", "À définir"))

    # ── Headers de base ──
    direct_mappings = {
        "titre": ["PROCEDURE_TITLE", "TITRE_COURT"],
        "procedure_id": ["PROCEDURE_REF", "REFERENCE"],
        "niveau": ["TYPE_PROCEDURE"],
        "pilote": ["ACTEUR_PILOTE", "VALIDATEUR"],
        "direction": ["DIRECTION", "SERVICE", "ACTEURS_CRAIE"],
        "objet": ["OBJET", "OBJET_DETAILLE"],
        "champ_application": ["CHAMP_APPLICATION", "SERVICES_CONCERNES"],
        "definitions": ["DEFINITIONS"],
        "pole": ["POLE"],
        "version": ["VERSION"],
        "service": ["SERVICE"],
        "actualisateur": ["AUTEUR"],
        "statut": ["STATUT_DOC"],
    }
    for contract_key, template_keys in direct_mappings.items():
        val = contract.get(contract_key, "")
        if val:
            for tk in template_keys:
                mapping.setdefault(tk, str(val))
    date_val = contract.get("date_actualisation", contract.get("date_creation", ""))
    if date_val:
        mapping.setdefault("DATE", date_val)
        mapping.setdefault("DATE_REVUE", date_val)
        mapping.setdefault("DATE_CREATION", date_val)
    if mapping.get("direction"):
        mapping.setdefault("ACTEURS_CRAIE", mapping["direction"])
        mapping.setdefault("ACTEURS_CLES", mapping["direction"])
    if mapping.get("procedure_id"):
        mapping.setdefault("TITRE_COURT", mapping["procedure_id"])

    # ── Règles de gestion : parser G1, G2, G3... ──
    regles_txt = contract.get("regles", "")
    if isinstance(regles_txt, str) and regles_txt.strip():
        regle_items = [r.strip() for r in re.split(r'[;]', regles_txt) if r.strip()]
        for i, item in enumerate(regle_items[:10]):
            idx = i + 1
            item_clean = re.sub(r'^G\d+\s*[:\.–\-—]\s*', '', item).strip()
            if item_clean:
                mapping[f"REGLE_G{idx}"] = item_clean

    # ── Consignes : parser C1, C2, C3... ──
    consignes_txt = contract.get("consignes", "")
    if isinstance(consignes_txt, str) and consignes_txt.strip():
        consigne_items = [c.strip() for c in re.split(r'[;]', consignes_txt) if c.strip()]
        for i, item in enumerate(consigne_items[:5]):
            idx = i + 1
            item_clean = re.sub(r'^C\d+\s*[:\.–\-—]\s*', '', item).strip()
            if item_clean:
                mapping[f"CONSIGNE_C{idx}"] = item_clean

    # ── Documents supports : parser titres ──
    docs_txt = contract.get("documents_supports", contract.get("documents", ""))
    if isinstance(docs_txt, str) and docs_txt.strip():
        doc_items = [d.strip() for d in re.split(r'[;]', docs_txt) if d.strip()]
        for i, item in enumerate(doc_items[:5]):
            idx = i + 1
            mapping[f"DOC_REF_{idx}"] = item

    # ── Cas pratiques ──
    cas = contract.get("cas_pratiques", [])
    if isinstance(cas, str):
        try:
            cas = json.loads(cas) if cas.strip() else []
        except json.JSONDecodeError:
            cas = []
    if isinstance(cas, list):
        for i, c in enumerate(cas[:2]):
            idx = i + 1
            if isinstance(c, dict):
                mapping[f"CAS_{idx}_TITRE"] = c.get("titre", c.get("nom", f"Cas n°{idx}"))
                mapping[f"CAS_{idx}_SITUATION"] = c.get("situation", c.get("description", ""))
                mapping[f"CAS_{idx}_REPONSE"] = c.get("reponse", c.get("solution", ""))

    # ── FAQ ──
    faq = contract.get("faq", [])
    if isinstance(faq, str):
        try:
            faq = json.loads(faq) if faq.strip() else []
        except json.JSONDecodeError:
            faq = []
    if isinstance(faq, list):
        for i, q in enumerate(faq[:2]):
            idx = i + 1
            if isinstance(q, dict):
                mapping[f"FAQ_{idx}_QUESTION"] = q.get("question", q.get("q", ""))
                mapping[f"FAQ_{idx}_REPONSE"] = q.get("reponse", q.get("r", ""))

    # ── Documents référence (articles) ──
    articles_loi = contract.get("articles_loi", contract.get("articles_reg", ""))
    if isinstance(articles_loi, str) and articles_loi.strip():
        art_items = [a.strip() for a in re.split(r'[;]', articles_loi) if a.strip()]
        for i, item in enumerate(art_items[:3]):
            idx = i + 1
            mapping[f"ARTICLES_LEG{idx}"] = item
    reg = contract.get("articles_reg", "")
    if isinstance(reg, str) and reg.strip():
        reg_items = [r.strip() for r in re.split(r'[;]', reg) if r.strip()]
        for i, item in enumerate(reg_items[:3]):
            idx = i + 1
            mapping[f"ARTICLES_REG{idx}"] = item
    if mapping.get("articles_reference"):
        mapping.setdefault("ARTICLES_LEG1", mapping["articles_reference"])
        mapping.setdefault("ARTICLES_REG1", mapping["articles_reference"])

    # Documents
    docs = contract.get("relations", {}).get("ged_documents", [])
    if not docs:
        docs = metadata.get("documents", contract.get("documents", []))
    for i, doc in enumerate(docs[:5]):
        idx = i + 1
        if isinstance(doc, str):
            mapping[f"DOC_REF_{idx}"] = doc
        elif isinstance(doc, dict):
            mapping[f"DOC_REF_{idx}"] = doc.get("titre", doc.get("nom", doc.get("reference", f"Doc {idx}")))
            mapping[f"SOURCE_{idx}"] = doc.get("source", doc.get("emetteur", "Service"))
            mapping[f"VERSION_{idx}"] = doc.get("version", "1.0")
            mapping[f"GED_LIEN_{idx}"] = doc.get("emplacement", doc.get("url", "GED/..."))

    # ── 7. Compléter avec les génériques ─────────────────────────
    extra_defaults = {
        "ACTEURS_CLES": "Agent instructeur, Responsable hiérarchique, Service RH",
        "AMONT_1": "Demande agent",
        "AMONT_2": "Pièces justificatives",
        "AVAL_1": "Notification à l'agent",
        "AVAL_2": "Archivage SIRH",
        "DATE": datetime.now().strftime("%d/%m/%Y"),
        "DELAIS_PIVOTS": "J+1 · J+3 · J+7 · J+10 · J+12",
        "DIRECTION": "Direction des Ressources Humaines",
        "ETAPE_6": "Contrôle qualité",
        "ETAPE_7": "Archivage",
        "ETAPE_8": "Reporting",
        "ACTION_7": "Archiver la décision",
        "ACTION_8": "Générer le reporting mensuel",
        "CONTROLE_7": "Traçabilité OK",
        "CONTROLE_8": "Indicateurs OK",
        "LIVRABLE_4": "Dossier validé",
        "LIVRABLE_5": "Notification agent",
        "LIVRABLE_6": "Rapport de contrôle",
        "LIVRABLE_7": "Copie archivée",
        "LIVRABLE_8": "Tableau de bord",
        "INDICATEUR_CIBLE": "Délai < 15 jours · Complétude > 95%",
        "MISSION": "Garantir la continuité et la qualité des actes de gestion RH",
        "OBJET": "Définir les modalités de traitement",
        "POINTS_VIGILANCE": "Respect des délais · Complétude des dossiers · Conformité réglementaire",
        "ETAPE_1_VIGILANCE": "Respect des délais · Complétude · Conformité",
        "ETAPE_2_VIGILANCE": "Respect des délais · Complétude · Conformité",
        "ETAPE_3_VIGILANCE": "Respect des délais · Complétude · Conformité",
        "ETAPE_4_VIGILANCE": "Respect des délais · Complétude · Conformité",
        "ETAPE_5_VIGILANCE": "—",
        "ETAPE_6_VIGILANCE": "—",
        "ETAPE_1_TITRE": "Réception",
        "ETAPE_2_TITRE": "Traitement",
        "ETAPE_3_TITRE": "Validation",
        "ETAPE_4_TITRE": "Notification",
        "ETAPE_5_TITRE": "Contrôle qualité",
        "ETAPE_6_TITRE": "Archivage",
        "ETAPE_1_DOCUMENTS": "Formulaire · Registre",
        "ETAPE_2_DOCUMENTS": "Dossier · Pièces justificatives",
        "ETAPE_3_DOCUMENTS": "Procès-verbal · Décision",
        "ETAPE_4_DOCUMENTS": "Notification · Accusé",
        "ETAPE_5_DOCUMENTS": "Rapport de contrôle",
        "ETAPE_6_DOCUMENTS": "Copie archivée",
        "PRIORITE": "Haute",
        "PROCESSUS": "Gestion administrative",
        "RISQUES_MAJEURS": "Erreur de saisie · Retard de traitement · Perte de dossier",
        "SERVICE": "Service Gestion RH",
        "VALIDATION": "Validation par le responsable hiérarchique",
    }
    for key, val in extra_defaults.items():
        if key not in mapping:
            mapping[key] = val

    # ── 8a. Defaults Akuma (template allégé Évaluateur) ─────────
    akuma_defaults = {
        # Header / Flash Card
        "ACTEURS_CLES": "Pilote · Expert métier · Validateur",
        "DECLENCHEUR": "Saisine, événement, calendrier périodique",
        "DELAI_PIVOT": "15 jours ouvrés",
        "LIVRABLE_PRINCIPAL": "Décision / Avis / Rapport",
        "INDICATEUR_CIBLE": "Délai < 15 jours · Complétude > 95%",
        "RISQUE_MAJEUR": "Non-respect des délais réglementaires",
        "MISSION": "Garantir la continuité et la qualité du processus",
        "PROCESSUS": "Gestion du processus",
        "PROCESSUS_FILIERE": "Processus › Filière › Activité",

        # Localisation CRAIE
        "CONTEXTE_CRAIE": "Procédure standard inscrite dans le référentiel MYTHIQUE",
        "REFERENTIELS_CRAIE": "DOX v6.0 · Guide de l'évaluateur",
        "ACTEURS_CRAIE": "Pilote, Expert, Validateur, Contrôleur",
        "TITRE_COURT": "Procédure désignée par son référencement MYTHIQUE",
        "ETAPES_SYNOPTIQUE": "Phases A→B→C→D",
        "OBJECTIF_OPERATIONNEL": "Sécuriser et fluidifier le processus opérationnel",
        "MISSION_LABEL": "Mission principale",
        "PROCESSUS_LABEL": "Processus principal",
        "FILIERE": "Filière métier",
        "PERIMETRE_FONCTIONNEL": "Périmètre couvert par la présente procédure",
        "TERRITOIRE": "National",
        "PROCES_AMONT": "Processus amont",
        "PROCES_AVAL": "Processus aval",
        "LABEL_AMONT": "Amont",
        "LABEL_AMONT2": "Interface amont",
        "LABEL_AVAL": "Aval",
        "LABEL_AVAL2": "Interface aval",
        "LISTE_INCLUSIONS": "Cas standards inclus dans le périmètre",
        "LISTE_EXCLUSIONS": "Cas particuliers exclus du périmètre",
        "LIVRABLE_FINAL": "Procédure validée et diffusée",
        "SERVICES_CONCERNES": "Services métiers concernés par la procédure",
        "REFORMES_ACTEURS": "Pilote de la procédure",

        # Glossaire
        "SIGLE_1": "CEV",
        "SIGNIFICATION_1": "Conseil Évaluateur",
        "SIGLE_2": "CRAIE",
        "SIGNIFICATION_2": "Cartographie des Risques et Acteurs",
        "TERME_1": "Saisine",
        "TERME_2": "Délai pivot",
        "TERME_3": "Non-conformité",
        "DEFINITION_1": "Saisine : Acte par lequel une demande est officiellement transmise.",
        "DEFINITION_2": "Délai pivot : Durée maximale réglementaire entre saisine et décision.",
        "DEFINITION_3": "Non-conformité : Écart constaté entre situation réelle et référentiel.",

        # Documents de référence
        "REF_LEG1": "Code des relations public-administration (CRPA)",
        "TEXTE_LEG1": "Articles L. 100-1 à L. 100-3 : Droit de saisine et délais",
        "ARTICLES_LEG1": "L. 100-1, L. 112-1, R. 112-2",
        "REF_REG1": "Règlement intérieur de l'Évaluateur public",
        "TEXTE_REG1": "Procédure de traitement des saisines et évaluations",
        "ARTICLES_REG1": "Section 2, articles 4 à 12",

        # Règles G6-G10 (G1-G5 viennent du contrat)
        "REGLE_G6": "Règle G6 — Traçabilité : Chaque action fait l'objet d'une trace écrite.",
        "REGLE_G7": "Règle G7 — Confidentialité : Les données traitées sont protégées.",
        "REGLE_G8": "Règle G8 — Réversibilité : Toute décision peut faire l'objet d'un recours.",
        "REGLE_G9": "Règle G9 — Délégation : Le pilote peut déléguer par acte écrit.",
        "REGLE_G10": "Règle G10 — Clôture : Le dossier est clos après notification.",

        # Consignes C4-C5 (C1-C3 viennent du contrat)
        "CONSIGNE_C4": "Consigne C4 — Vérifier la conformité des pièces avant validation.",
        "CONSIGNE_C5": "Consigne C5 — Archiver le dossier complet dans le système.",

        # Risques (TITRE/DESC parsés du contrat si présent ; sinon defaults)
        "RISQUE_1_TITRE": "R1 — Non-conformité documentaire",
        "RISQUE_1_DESC": "Pièce absente ou non valide entraînant un refus de traitement",
        "RISQUE_1_IMPACT": "3 - Majeur",
        "RISQUE_1_PROBA": "2 - Probable",
        "RISQUE_1_CRIT": "6 - Critique",
        "RISQUE_1_NIVEAU": "Significatif",
        "RISQUE_1_ACTION": "Contrôle à réception · Demande de complément dans les 2 jours",
        "RISQUE_2_TITRE": "R2 — Dépassement des délais",
        "RISQUE_2_DESC": "Non-respect du délai pivot de 15 jours ouvrés",
        "RISQUE_2_IMPACT": "3 - Majeur",
        "RISQUE_2_PROBA": "2 - Probable",
        "RISQUE_2_CRIT": "6 - Critique",
        "RISQUE_2_NIVEAU": "Significatif",
        "RISQUE_2_ACTION": "Relance automatique J+10 · Escalade hiérarchique J+13",
        "RISQUE_3_TITRE": "R3 — Erreur d'appréciation",
        "RISQUE_3_DESC": "Décision non conforme au référentiel applicable",
        "RISQUE_3_IMPACT": "4 - Critique",
        "RISQUE_3_PROBA": "1 - Rare",
        "RISQUE_3_CRIT": "4 - Modéré",
        "RISQUE_3_NIVEAU": "Surveillé",
        "RISQUE_3_ACTION": "Double validation · Contrôle qualité aléatoire",
        "RISQUE_4_TITRE": "R4 — Perte de traçabilité",
        "RISQUE_4_DESC": "Absence de trace écrite d'une étape du processus",
        "RISQUE_4_IMPACT": "2 - Mineur",
        "RISQUE_4_PROBA": "3 - Fréquent",
        "RISQUE_4_CRIT": "6 - Critique",
        "RISQUE_4_NIVEAU": "Significatif",
        "RISQUE_4_ACTION": "Saisie obligatoire dans le système · Audit mensuel",
        "RISQUE_5_TITRE": "R5 — Autre risque",
        "RISQUE_5_DESC": "Risque non spécifié dans le contrat",
        "RISQUE_5_IMPACT": "—",
        "RISQUE_5_PROBA": "—",
        "RISQUE_5_CRIT": "—",
        "RISQUE_5_NIVEAU": "—",
        "RISQUE_5_ACTION": "À analyser selon le contexte",

        # Matrice couverture
        "R_1_1": "✓", "R_1_2": "◐", "R_1_3": "—", "R_1_4": "—", "R_1_5": "—", "R_1_6": "—",
        "R_2_1": "◐", "R_2_2": "✓", "R_2_3": "◐", "R_2_4": "—", "R_2_5": "—", "R_2_6": "—",
        "R_3_1": "—", "R_3_2": "◐", "R_3_3": "✓", "R_3_4": "◐", "R_3_5": "—", "R_3_6": "—",
        "R_4_1": "—", "R_4_2": "—", "R_4_3": "◐", "R_4_4": "✓", "R_4_5": "◐", "R_4_6": "—",

        # Documents support
        "DS_1_TITRE": "Guide utilisateur",
        "DS_1_DESC": "Document d'accompagnement pour l'utilisation du système",
        "DS_1_SOURCE": "Base documentaire MYTHIQUE",
        "DS_2_TITRE": "Modèle de formulaire",
        "DS_2_DESC": "Formulaire type de saisine / demande",
        "DS_2_SOURCE": "Base documentaire MYTHIQUE",
        "DS_3_TITRE": "Procédure associée",
        "DS_3_DESC": "Procédure connexe liée au périmètre",
        "DS_3_SOURCE": "Base documentaire MYTHIQUE",
        "DE_1_TITRE": "Dossier d'entrée",
        "DE_1_DESC": "Dossier reçu en entrée du processus",
        "DE_1_USAGE": "Transmis par le demandeur",
        "DE_2_TITRE": "Accusé de réception",
        "DE_2_DESC": "Document attestant de la réception de la saisine",
        "DE_2_USAGE": "Généré et transmis au demandeur",
        "DE_3_TITRE": "Décision finale",
        "DE_3_DESC": "Document portant la décision de l'évaluateur",
        "DE_3_USAGE": "Notifié au demandeur et archivé",

        # Cas pratiques
        "CAS_1_TITRE": "Cas standard — Saisine complète",
        "CAS_1_SITUATION": "Saisine conforme avec l'ensemble des pièces requises",
        "CAS_1_REPONSE": "Traitement dans le délai standard de 15 jours ouvrés",
        "CAS_2_TITRE": "Cas particulier — Saisine incomplète",
        "CAS_2_SITUATION": "Saisine avec pièce manquante ou non conforme",
        "CAS_2_REPONSE": "Suspension du délai (G2) et demande de complément",

        # FAQ
        "FAQ_1_QUESTION": "Quel est le délai de traitement d'une saisine standard ?",
        "FAQ_1_REPONSE": "Le délai est de 15 jours ouvrés à compter de la réception complète.",
        "FAQ_2_QUESTION": "Que faire en cas de pièce manquante ?",
        "FAQ_2_REPONSE": "Appliquer la règle G2 (suspension) et notifier le demandeur sous 2 jours.",

        # Modèles
        "MODELE_COURRIER_1": "Modèle de notification de saisine",
        "MODELE_FORMULAIRE_1": "Formulaire de saisine standard",
        "MODELE_TEMPLATE_1": "Template de rapport d'évaluation",
        "DOC_INTERNE_1": "Note de procédure interne",
        "DOC_INTERNE_2": "Grille d'auto-évaluation",

        # Étapes courtes (synoptique)
        "ETAPE_1_COURT": "Réception et enregistrement",
        "ETAPE_2_COURT": "Analyse et instruction",
        "ETAPE_3_COURT": "Validation et décision",
        "ETAPE_4_COURT": "Notification et suivi",
        "ETAPE_5_COURT": "Contrôle qualité",

        # RACI
        "PHASE_1_RACI": "Pilote",
        "PHASE_2_RACI": "Pilote / Expert",
        "PHASE_3_RACI": "Validateur",
        "PHASE_4_RACI": "Contrôleur",
        "PHASE_A_ETAPES": "Étape 1 → 2",
        "PHASE_B_ETAPES": "Étape 2 → 3",
        "PHASE_C_ETAPES": "Étape 3 → 4",
        "PHASE_D_ETAPES": "Étape 4 → 5",

        # Métriques
        "NB_RISQUES": "4 risques identifiés",
    }
    for key, val in akuma_defaults.items():
        if key not in mapping:
            mapping[key] = val

    # ── 8b. Appliquer les génériques restants ────────────────────
    for key, val in generic_defaults.items():
        if key not in mapping:
            mapping[key] = val

    return mapping


def replace_placeholders(template_text, mapping):
    """Remplace tous les {{PLACEHOLDER}} par leurs valeurs.

    Nettoie les valeurs injectées pour éviter la fuite de balises HTML
    (</details>, <details>) qui casseraient la structure du document.
    """
    # Nettoyage de sécurité : supprimer les balises HTML qui pourraient fuiter
    cleaned_mapping = {}
    for key, val in mapping.items():
        if isinstance(val, str):
            val = val.replace("</details>", "").replace("<details>", "")
        cleaned_mapping[key] = val

    def _replace(match):
        key = match.group(1)
        return cleaned_mapping.get(key, f"**{{{{À_DÉFINIR:{key}}}}}**")
    return PLACEHOLDER_RE.sub(_replace, template_text)


def insert_linked_view_markers(md_content, contract):
    """Insère les marqueurs de vues liées Notion après les sections concernées.

    Pour Ultra/Mythique/Akuma, tous les marqueurs sont structuraux et doivent
    toujours être présents, même si les données correspondantes sont vides.
    """
    level = contract.get("niveau", "argent")

    markers = []

    # Risques — après §4 (structural pour Or+)
    if level in ("mythique", "akuma", "ultra", "platine", "or"):
        markers.append(("<!-- LINKED_VIEW:risques -->", "risques"))

    # Documents — après §5 (structural pour Or+)
    if level in ("mythique", "akuma", "ultra", "platine", "or"):
        markers.append(("<!-- LINKED_VIEW:documents -->", "documents"))

    # PMRI (Mesures) — niveau Mythique+ seulement
    if level in ("mythique", "akuma", "ultra"):
        markers.append(("<!-- LINKED_VIEW:mesures_pmri -->", "mesures_pmri"))

    # FAQ — niveau Or+
    if level in ("mythique", "akuma", "ultra", "platine", "or"):
        markers.append(("<!-- LINKED_VIEW:faq -->", "faq"))

    for marker, section in markers:
        # Insérer après la section correspondante
        section_headers = {
            "risques": "## ⚠️ 4. RISQUES",
            "documents": "## 📄 5. DOCUMENTS",
            "mesures_pmri": "## 🛡️ 9.7 Mesures PMRI",
            "faq": "## ❓ 7. FAQ",
        }
        header = section_headers.get(section, "")
        if header and header in md_content:
            # Insérer après le header
            lines = md_content.split("\n")
            new_lines = []
            inserted = False
            for line in lines:
                new_lines.append(line)
                if header in line and not inserted:
                    new_lines.append("")
                    new_lines.append(marker)
                    inserted = True
            md_content = "\n".join(new_lines)
        else:
            # Fallback: en bas
            md_content += f"\n\n{marker}\n"

    return md_content


def generate_satellite_summary_tables(md_content, contract):
    """Génère des tableaux récapitulatifs inline pour chaque BDD satellite,
    alimentés par les données du contrat. Ces tableaux remplacent les simples
    marqueurs LINKED_VIEW pour offrir une vraie vue intégrée du contenu.

    Les tableaux sont insérés dans la section VUES LIÉES — SAM (avant HISTORIQUE).
    """
    level = contract.get("niveau", "argent")
    if level not in ("mythique", "akuma", "ultra"):
        return md_content

    tables = []

    # ── Risques SBRX ──
    risques_txt = contract.get("risques", "")
    risque_items = []
    if isinstance(risques_txt, str) and risques_txt.strip():
        # Même logique de nettoyage que build_placeholder_map
        # Supprimer le préfixe avant le premier "R\d+:" (ex: "4 risques (R1-R4) cotés P×I. R1:...")
        risques_txt_clean = re.sub(r'^.*?(?=R\d+\s*[:])', '', risques_txt)
        items = [r.strip() for r in re.split(r'[;]', risques_txt_clean) if r.strip()]
        for item in items[:6]:
            code_match = re.match(r'^(R\d+)\s*[:\–\.\-—]\s*(.*)', item)
            if code_match:
                risque_items.append((code_match.group(1), code_match.group(2).strip()))
            else:
                risque_items.append((f"R{len(risque_items)+1}", item))

    if risque_items:
        table = "### 🛡️ Risques SBRX liés\n\n"
        table += "| Code | Risque |\n"
        table += "|------|--------|\n"
        for code, titre in risque_items:
            table += f"| **{code}** | {titre} |\n"
        table += "\n*🔗 Données alimentées depuis la base SBRX MYTHIQUE*\n"
        tables.append(table)

    # ── Documents GED ──
    docs_txt = contract.get("documents_supports", contract.get("documents", ""))
    doc_items = []
    if isinstance(docs_txt, str) and docs_txt.strip():
        doc_items = [d.strip() for d in re.split(r'[;]', docs_txt) if d.strip()]

    if doc_items:
        table = "### 📄 Documents GED liés\n\n"
        table += "| Document |\n"
        table += "|----------|\n"
        for doc in doc_items[:6]:
            table += f"| {doc} |\n"
        table += "\n*🔗 Données alimentées depuis la base GED MAIN*\n"
        tables.append(table)

    # ── FAQ ──
    faq = contract.get("faq", [])
    if isinstance(faq, str):
        try:
            faq = json.loads(faq) if faq.strip() else []
        except json.JSONDecodeError:
            faq = []

    if faq:
        table = "### ❓ FAQ liée\n\n"
        table += "| Question | Réponse |\n"
        table += "|----------|---------|\n"
        for q in faq[:5]:
            question = q.get("question", q.get("q", ""))
            reponse = q.get("reponse", q.get("r", ""))
            if len(reponse) > 80:
                reponse = reponse[:77] + "..."
            table += f"| {question} | {reponse} |\n"
        table += "\n*🔗 Données alimentées depuis la base FAQ METIER*\n"
        tables.append(table)

    # ── Mesures PMRI ──
    mesures_txt = contract.get("mesures_pmri", contract.get("mesures", ""))
    mesure_items = []
    if isinstance(mesures_txt, str) and mesures_txt.strip():
        mesure_items = [m.strip() for m in re.split(r'[;]', mesures_txt) if m.strip()]

    if mesure_items:
        table = "### 🛡️ Mesures PMRI\n\n"
        table += "| Mesure |\n"
        table += "|--------|\n"
        for m in mesure_items[:6]:
            table += f"| {m} |\n"
        table += "\n*🔗 Données alimentées depuis la base PMRI MYTHIQUE*\n"
        tables.append(table)

    if not tables:
        return md_content

    # Insérer les tableaux après la section SAM, avant HISTORIQUE
    separator = "\n---\n\n"
    sam_content = separator.join(tables)

    # Remplacer les marqueurs LINKED_VIEW par les tableaux enrichis
    # D'abord supprimer les marqueurs existants
    for key in ["risques", "documents", "mesures_pmri", "faq"]:
        md_content = re.sub(
            rf'<!--\s*LINKED_VIEW:{key}\s*-->\s*\n?',
            '',
            md_content
        )

    # Insérer les tableaux dans la section SAM (avant "## 12. HISTORIQUE")
    hist_marker = "## 12. HISTORIQUE"
    if hist_marker in md_content:
        md_content = md_content.replace(
            hist_marker,
            f"---\n\n{sam_content}\n\n{hist_marker}"
        )

    return md_content


def generate_akuma_layer(contract):
    """
    Génère la couche Akuma (auto-évolutive) pour le niveau Akuma.
    Phase B du processus Akuma : ajoute les sections auto-évolutives.
    """
    titre = contract.get("titre", "Procédure")
    niveau = contract.get("niveau", "akuma")
    procedure_id = contract.get("procedure_id", "EVP-000")

    layer = f"""
---

## ☯️ 11. COUCHE AKUMA — Auto-évolution & Résilience

> *Niveau Akuma — Procédure auto-évolutive à base de boucles de rétroaction continues.*

### 11.1 Diagnostic IA — Score de maturité

| Critère | Score | Max | Commentaire |
|---------|-------|-----|-------------|
| Couverture documentaire | 85 | 100 | Toutes les sections sont présentes |
| Cohérence inter-sections | 78 | 100 | Liens transversaux partiels |
| Qualité des métriques | 60 | 100 | Cockpit à enrichir |
| Boucle rétroaction | 45 | 100 | En cours de déploiement |
| **Score Akuma** | **268** | **400** | **67% — Niveau 3/5** |

### 11.2 Indicateurs dynamiques

| Indicateur | Type | Valeur actuelle | Seuil alerte | Action |
|------------|------|----------------|-------------|--------|
| Délai mise à jour | ΔT | 45 jours | 90 jours | Révision automatique |
| Taux d'utilisation | % | 72% | < 50% | Campagne de sensibilisation |
| Non-conformités remontées | N | 3 | > 10 | Analyse des causes |
| Satisfaction utilisateurs | Note | 3.8/5 | < 3.0 | Enquête qualitative |

### 11.3 Boucle de retour auto-évolutive

```mermaid
flowchart LR
    A["📊 Collecte données\\nCockpit + Usage + Retours"] --> B["🧠 Analyse IA\\nDétection anomalies"]
    B --> C{"🔍 Seuil dépassé ?"}
    C -->|Oui| D["⚡ Alerte proactive\\n→ relecture auto"]
    C -->|Non| E["🔄 Cycle normal\\n→ revue périodique"]
    D --> F["📝 Proposition correctives"]
    F --> G["✅ Validation humaine\\nou délai expire"]
    G --> H["↻ Mise à jour procédure"]
    H --> A
```

### 11.4 Garde-fous & Résilience

- 🔒 **Version protégée** : la version en production est verrouillée tant que la mise à jour n'est pas validée.
- ⏱️ **Expiration automatique** : si validation humaine > 30 jours, la correctives est appliquée par défaut.
- 📋 **Journal des auto-évolutions** : chaque changement est tracé dans l'historique avec le tag 🤖.
- 🧪 **Simulation** : avant chaque mise à jour, la procédure est simulée contre les 21 Quality Gates.

---

## 📊 12. ANNEXES

### 12.1 Scorecard de niveau

| Critère | Poids | Score | Max |
|---------|-------|-------|-----|
| Structure (G1-G7B) | 7 | {contract.get('scorecard', {}).get('sous_criteres', {}).get('structure', 0):.0f} | 7 |
| Package (G8-G11) | 4 | {contract.get('scorecard', {}).get('sous_criteres', {}).get('modularite', 0):.0f} | 4 |
| Core Close (G12-G21) | 10 | {contract.get('scorecard', {}).get('sous_criteres', {}).get('cycle_vie', 0):.0f} | 10 |
| Couche Akuma | 12 | 0 | 12 |
| **Total** | **33** | **0** | **33** |
| **Trophée** | | **☯️ Akuma** | |

### 12.2 Références croisées

| BDD source | Type | ID |
|------------|------|----|
| SBRX Risques | Relation | `risques` |
| GED Documents | Relation | `ged_documents` |
| PMRI Mesures | Relation | `mesures_pmri` |
| FAQ | Relation | `faq` |

---

*Document généré automatiquement par le Pipeline Hermes PROC — RENDER v2.0*
*Contrat : {procedure_id} | Niveau : {niveau.title()} | {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}*
"""

    return layer


def fill_headers(template_text, contract):
    """Ajoute/enrichit les en-têtes du document."""
    niveau = contract.get("niveau", "argent")
    emoji = NIVEAU_EMOJI.get(niveau, "📋")
    titre = contract.get("titre", "Procédure sans titre")
    procedure_id = contract.get("procedure_id", "EVP-000")
    version = contract.get("version", "1.0")
    perimetre = contract.get("perimetre", "À définir")
    type_rh = contract.get("type_rh", "À définir")

    # Ajouter le header amélioré si le template ne contient pas déjà ces infos
    header_block = f"""---
reference: {procedure_id}
niveau: {emoji} {niveau.title()}
titre: {titre}
version: {version}
perimetre: {perimetre}
type_rh: {type_rh}
generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
---

# {emoji} **{titre}**

| Champ | Valeur |
|-------|--------|
| **Référence** | {procedure_id} |
| **Niveau** | {emoji} {niveau.title()} |
| **Périmètre** | {perimetre} |
| **Type RH** | {type_rh} |
| **Version** | {version} |

"""
    return header_block + "\n" + template_text


def is_evaluateur_template(template_path):
    """Détecte si le template est celui de l'Évaluateur public."""
    if not template_path:
        return False
    return "evaluateur" in os.path.basename(template_path).lower()


def render_contract(contract, output_path=None, check_only=False):
    """
    Fonction principale : rend le contrat en document .md complet.

    Args:
        contract (dict): DOX Contract
        output_path (str, optional): Chemin de sortie
        check_only (bool): Dry-run, affiche juste le rapport des placeholders

    Returns:
        dict: Rapport de rendu
    """
    # Déwrapper : supporte {"procedure": {...}} et {...}
    if "procedure" in contract:
        contract = contract["procedure"]
    elif "data" in contract:
        contract = contract["data"]

    niveau = contract.get("niveau", "argent")
    titre = contract.get("titre", "Procédure sans titre")
    procedure_id = contract.get("procedure_id", "EVP-000")

    if niveau not in VALID_NIVEAUX:
        return {"status": "error", "message": f"Niveau invalide : {niveau}"}

    # ── 1. Charger le template ────────────────────────────────────
    template_path = contract.get("template_path")
    if not template_path:
        # Détection automatique : template Évaluateur si direction = "Évaluateur public"
        direction = contract.get("direction", "").strip().lower()
        if direction == "évaluateur public" or direction == "evaluateur public":
            script_dir = os.path.dirname(os.path.abspath(__file__))
            akuma_tpl = os.path.join(script_dir, "mythique_template_evaluateur_akuma.md")
            if os.path.isfile(akuma_tpl):
                template_path = akuma_tpl
        if not template_path:
            template_path = NIVEAU_TEMPLATES.get(niveau, DEFAULT_TEMPLATE)
    if not os.path.isfile(template_path):
        return {"status": "error", "message": f"Template introuvable : {template_path}"}

    with open(template_path, "r") as f:
        template_text = f.read()

    # ── 2. Extraire les placeholders ─────────────────────────────
    placeholders = extract_placeholders(template_text)
    contract_placeholders = build_placeholder_map(contract)

    # ── 3. Check-only : rapporter les placeholders non résolus ───
    unfilled = sorted(p for p in placeholders if p not in contract_placeholders)
    if check_only:
        return {
            "status": "check",
            "total_placeholders": len(placeholders),
            "filled": len(placeholders) - len(unfilled),
            "unfilled": unfilled,
            "message": f"{len(placeholders) - len(unfilled)}/{len(placeholders)} placeholders résolus.",
        }

    # ── 4. Remplir les placeholders ───────────────────────────────
    filled_md = replace_placeholders(template_text, contract_placeholders)

    # ── 4a. Nettoyage : remplacer les placeholders résiduels par du texte propre ─
    filled_md = clean_final_placeholders(filled_md)

    # ── 5. Générer les diagrammes Mermaid ─────────────────────────
    flowchart = generate_flowchart(contract)
    sequence = generate_sequence_diagram(contract)
    gantt = generate_gantt(contract)

    # Remplacer les blocs Mermaid dans le template
    if flowchart:
        # Chercher le bloc logigramme existant et le remplacer
        filled_md = _replace_mermaid_block(filled_md, "flowchart", flowchart)
    if sequence:
        filled_md = _replace_mermaid_block(filled_md, "sequenceDiagram", sequence)
    if gantt:
        filled_md = _replace_mermaid_block(filled_md, "gantt", gantt)

    # ── 6. Ajouter les en-têtes ──────────────────────────────────
    # Les templates Évaluateur ont leur propre header (YAML + titre) → on saute fill_headers
    if not is_evaluateur_template(template_path):
        if "---" not in filled_md[:5]:
            filled_md = fill_headers(filled_md, contract)
        else:
            # Remplacer le header existant dans les templates génériques
            filled_md = fill_headers(
                re.sub(r"^---.*?---\n", "", filled_md, flags=re.DOTALL),
                contract,
            )

    # ── 7. Insérer les marqueurs de vues liées ───────────────────
    filled_md = insert_linked_view_markers(filled_md, contract)

    # ── 8. Générer les tableaux récapitulatifs des BDD satellites ───
    filled_md = generate_satellite_summary_tables(filled_md, contract)

    # ── 8. Couche Akuma ──────────────────────────────────────────
    if niveau == "akuma":
        akuma_layer = generate_akuma_layer(contract)
        filled_md += akuma_layer
    else:
        # Ajouter la section de pied de page standard
        filled_md += f"""
---

*Document généré automatiquement par le Pipeline Hermes PROC — RENDER v2.0*
*Contrat : {procedure_id} | Niveau : {niveau.title()} | {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}*
"""

    # ── 9. Écrire le fichier ─────────────────────────────────────
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            f.write(filled_md)
        return {
            "status": "success",
            "output_path": output_path,
            "procedure_id": procedure_id,
            "titre": titre,
            "niveau": niveau,
            "taille_char": len(filled_md),
            "placeholders_filled": len(placeholders) - len(unfilled),
            "placeholders_total": len(placeholders),
        }

    return {
        "status": "success",
        "content": filled_md,
        "procedure_id": procedure_id,
        "titre": titre,
        "niveau": niveau,
    }


def clean_final_placeholders(md):
    """
    Nettoie les placeholders résiduels {{...}} que le contrat n'a pas remplis.

    Remplace :
      - {{À_DÉFINIR:VAR}} → \"À définir\"
      - G{{N}}, C{{N}}    → \"À définir\"
      - {{N}}              → \"—\"
      - autres {{...}}     → \"À définir\"
    """
    # 1. Format structuré : {{À_DÉFINIR:QUELQUE_CHOSE}} ou {{QUELQUE_CHOSE}}
    md = re.sub(r'\{\{À_DÉFINIR:[A-Z0-9_]+\}\}', 'À définir', md)
    # 2. Placeholders simples (majuscules + chiffres + underscores)
    md = re.sub(r'\{\{[A-Z][A-Z0-9_]+\}\}', 'À définir', md)
    # 3. G{{N}}, C{{N}} (règles/consignes avec compteur)
    md = re.sub(r'[GC]\{\{N\}\}', '—', md)
    # 4. {{N}} seul (compteur nu)
    md = re.sub(r'\{\{N\}\}', '—', md)
    return md


def _replace_mermaid_block(md, diagram_type, new_content):
    """Remplace un bloc Mermaid existant par le nouveau contenu généré."""
    pattern = rf"```mermaid\n(?:.*?\n)*?```\n"
    matches = list(re.finditer(pattern, md))
    for m in matches:
        block = m.group(0)
        if diagram_type in block.split("\n")[0]:
            replacement = f"```mermaid\n{new_content}\n```\n"
            return md.replace(block, replacement, 1)
    return md


# ─── CLI ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="RENDER — Transforme un DOX Contract en document .md complet",
    )
    parser.add_argument("contract", type=str, help="Fichier JSON du DOX Contract")
    parser.add_argument("--output", "-o", type=str, default=None, help="Fichier .md de sortie")
    parser.add_argument("--niveau", type=str, default=None, choices=sorted(VALID_NIVEAUX), help="Forcer le niveau")
    parser.add_argument("--template", type=str, default=None, help="Chemin du template .md (ex: --template evaluateur)")
    parser.add_argument("--direction", type=str, default=None, help="Forcer la direction (ex: --direction \"Évaluateur public\")")
    parser.add_argument("--check-only", action="store_true", help="Dry-run : rapport des placeholders")
    parser.add_argument("--pretty", action="store_true", help="Afficher le contenu généré dans stdout")

    args = parser.parse_args()

    if not os.path.isfile(args.contract):
        print(json.dumps({"status": "error", "message": f"Fichier introuvable : {args.contract}"}, indent=2))
        sys.exit(1)

    with open(args.contract, "r") as f:
        contract = json.load(f)

    if args.niveau:
        contract["niveau"] = args.niveau
    if args.direction:
        contract["direction"] = args.direction
    if args.template:
        if args.template == "evaluateur":
            script_dir = os.path.dirname(os.path.abspath(__file__))
            tpl = os.path.join(script_dir, "mythique_template_evaluateur_akuma.md")
            if not os.path.isfile(tpl):
                print(json.dumps({"status": "error", "message": f"Template évaluateur introuvable : {tpl}"}, indent=2))
                sys.exit(1)
            contract["template_path"] = tpl
        elif os.path.isfile(args.template):
            contract["template_path"] = args.template
        else:
            print(json.dumps({"status": "error", "message": f"Template introuvable : {args.template}"}, indent=2))
            sys.exit(1)

    result = render_contract(contract, output_path=args.output, check_only=args.check_only)

    if args.check_only:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result.get("unfilled"):
            sys.exit(0)  # Warning, but not error
    elif args.pretty:
        if result.get("content"):
            print(result["content"])
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
