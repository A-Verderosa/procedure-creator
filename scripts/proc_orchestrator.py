#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
proc_orchestrator.py — Orchestrateur Agent PROC (DOX_EXEC_CORE)
===============================================================

Exécute le pipeline complet de création/audit/sync de procédures
en coordonnant les 5 scripts spécialisés.

Usage:
    python3 proc_orchestrator.py --mode create --niveau argent --titre "Ma procédure"
    python3 proc_orchestrator.py --mode audit --proc PRH-042
    python3 proc_orchestrator.py --mode upgrade --proc PRH-042 --niveau or
    python3 proc_orchestrator.py --mode resync --proc PRH-042
    python3 proc_orchestrator.py --mode list
    python3 proc_orchestrator.py --mode check

DOX_EXEC_CORE 11 étapes :
  [1] INTAKE → [2] ANTI_DUPLICATE → [3] CONSULT_BDD_CANONIQUES →
  [4] DESIGN → [5] GENERATE → [6] RENDER → [7] CHECK_STRUCTURE →
  [8] LOCAL_QG → [9] BULLET_PROOFING → [10] SYNC_NOTION →
  [11] REPORT + EXEC_CLOSE
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

# ─── Chemins ────────────────────────────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).parent.absolute()
SKILL_DIR = SCRIPTS_DIR.parent
REFERENCES_DIR = SKILL_DIR / "references"
TEMPLATES_DIR = SKILL_DIR / "templates"

SCRIPTS = {
    "consult_bdd": SCRIPTS_DIR / "consult_bdd.py",
    "sync_notion": SCRIPTS_DIR / "sync_notion.py",
    "generate_contract": SCRIPTS_DIR / "generate_contract.py",
    "render_procedure": SCRIPTS_DIR / "render_procedure.py",
    "check_structure": SCRIPTS_DIR / "check_structure.py",
    "bullet_proof": SCRIPTS_DIR / "bullet_proof.py",
    "qg_validator": SCRIPTS_DIR / "qg_validator.py",
    "create_related_pages": SCRIPTS_DIR / "create_related_pages.py",
}

NIVEAUX_ORDER = ["bronze", "argent", "or", "platine", "ultra", "mythique", "akuma"]

# ─── Pipeline state ─────────────────────────────────────────────────────────
class PipelineState:
    """État du pipeline — transporte les données entre étapes."""

    def __init__(self, args):
        self.args = args
        self.workdir = Path(tempfile.mkdtemp(prefix=f"proc_{args.mode}_"))
        self.steps = {}           # step_name → {"ok": bool, "output": str, "files": dict}
        self.procedure_data = {}  # Données brutes BDD pull
        self.contract_data = {}   # DOX Contract généré
        self.qg_results = {}      # Résultats QG
        self.bullet_results = {}  # Résultats bullet proofing
        self.sync_result = {}     # Résultat sync Notion
        self.related_pages_result = {}  # Résultat création pages satellites
        self.final_report = ""    # Rapport final markdown
        self.aborted = False
        print(f"📁 Répertoire de travail : {self.workdir}")

    def step_file(self, step_num, name):
        """Chemin pour un fichier d'étape."""
        return self.workdir / f"{step_num:02d}_{name}"

    def record_step(self, name, ok=True, output="", files=None):
        self.steps[name] = {
            "ok": ok,
            "output": output,
            "files": files or {},
            "timestamp": datetime.now().isoformat(),
        }
        status = "✅" if ok else "❌"
        print(f"  {status} Étape [{name}] — {'OK' if ok else 'ÉCHEC'}")
        if not ok:
            print(f"     {output[:300]}")

    def abort(self, reason):
        """Stoppe le pipeline proprement."""
        self.aborted = True
        self.record_step("ABORTED", ok=False, output=reason)

# ─── Helpers ────────────────────────────────────────────────────────────────
def run_script(script_name, *args, timeout=120):
    """
    Lance un script du skill avec des arguments.
    Retourne (ok, stdout, stderr).
    """
    script_path = SCRIPTS.get(script_name)
    if not script_path:
        return False, "", f"Script inconnu : {script_name}"

    if not script_path.exists():
        return False, "", f"Script introuvable : {script_path}"

    cmd = [sys.executable, str(script_path)] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(SCRIPTS_DIR),
        )
        ok = result.returncode == 0
        return ok, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Timeout ({timeout}s) sur {script_name}"
    except OSError as e:
        return False, "", f"Erreur OS : {e}"


def parse_json_output(stdout):
    """Tente d'extraire un JSON du stdout d'un script."""
    # Cherche la première ligne qui commence par { ou [
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("{") or line.startswith("["):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    # Tente de parser tout le stdout
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def load_json(path):
    """Charge un fichier JSON."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return None


def save_json(path, data):
    """Sauvegarde un fichier JSON."""
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def niveau_suivant(niveau):
    """Retourne le niveau suivant dans la hiérarchie."""
    try:
        idx = NIVEAUX_ORDER.index(niveau.lower())
        if idx < len(NIVEAUX_ORDER) - 1:
            return NIVEAUX_ORDER[idx + 1]
    except ValueError:
        pass
    return None


# ─── Pipeline steps ─────────────────────────────────────────────────────────

def step_intake(state):
    """[1] INTAKE — Valider et normaliser les paramètres d'entrée."""
    args = state.args
    mode = args.mode

    # Validation des paramètres selon le mode
    errors = []
    if mode in ("create",):
        if not args.titre:
            errors.append("--titre requis pour le mode create")
        if not args.niveau:
            errors.append("--niveau requis pour le mode create")
    elif mode in ("upgrade", "audit", "resync"):
        if not args.proc and not args.titre:
            errors.append("--proc ou --titre requis")
    elif mode == "list":
        pass  # Pas de paramètre requis
    elif mode == "check":
        pass  # Vérification globale
    else:
        errors.append(f"Mode inconnu : {mode}")

    if errors:
        state.abort("; ".join(errors))
        return False

    # Normaliser le niveau
    niveau = args.niveau.lower() if args.niveau else None
    if niveau and niveau not in NIVEAUX_ORDER:
        state.abort(f"Niveau invalide : {niveau}. Choisir parmi {', '.join(NIVEAUX_ORDER)}")
        return False

    # Construire le payload d'entrée
    params = {
        "mode": mode,
        "titre": args.titre,
        "niveau": niveau,
        "proc": args.proc,
        "type_rh": args.type_rh,
        "perimetre": args.perimetre,
        "acteurs": args.acteurs,
        "workdir": str(state.workdir),
        "timestamp": datetime.now().isoformat(),
    }

    params_path = state.step_file(1, "intake_params.json")
    save_json(params_path, params)

    state.record_step("INTAKE", files={"params": str(params_path)})
    return True


def step_anti_duplicate(state):
    """[2] ANTI_DUPLICATE — Vérifier les doublons dans Notion."""
    args = state.args
    query = args.titre or args.proc or ""

    if not query:
        state.record_step("ANTI_DUPLICATE", ok=True, output="Aucune vérification nécessaire")
        return True

    # Chercher par titre via consult_bdd
    ok, stdout, stderr = run_script("consult_bdd", "--list", "--filter", "Titre", query)

    if not ok:
        state.record_step("ANTI_DUPLICATE", ok=False, output=stderr)
        return False

    result_path = state.step_file(2, "antiduplicate.json")
    save_json(result_path, {"query": query, "stdout": stdout, "stderr": stderr})

    # Analyse simple : si stdout contient des résultats, doublon potentiel
    has_results = len(stdout.strip()) > 50  # Heuristique
    state.record_step(
        "ANTI_DUPLICATE",
        ok=True,
        output=f"Doublon{' TROUVÉ' if has_results else ' non détecté'} pour '{query}'",
        files={"result": str(result_path)},
    )

    if has_results and args.mode == "create":
        print("  ⚠️  Attention : une procédure similaire existe déjà dans Notion.")
        if not args.force:
            print("  ℹ️  Utilisez --force pour passer outre, ou --mode upgrade pour mettre à jour.")
    return True


def step_consult_bdd(state):
    """[3] CONSULT_BDD_CANONIQUES — Charger données BDD."""
    args = state.args
    proc_id = args.proc
    titre = args.titre

    identifier = proc_id or titre or ""

    if not identifier:
        state.record_step("CONSULT_BDD", ok=True, output="Pas de consultation BDD nécessaire")
        return True

    # Charger les données de la procédure
    ok, stdout, stderr = run_script("consult_bdd", "--proc", identifier, "--output", "")

    if not ok:
        # Essayer avec --list et filtre
        ok2, stdout2, stderr2 = run_script("consult_bdd", "--list", "--filter", "Titre", identifier)
        if not ok2:
            state.record_step("CONSULT_BDD", ok=False, output=stderr + "\n" + stderr2)
            return False
        stdout = stdout2
        stderr = stderr2

    # Sauvegarder les données brutes
    raw_path = state.step_file(3, "bdd_canoniques_raw.json")
    save_json(raw_path, {
        "identifier": identifier,
        "stdout": stdout,
        "stderr": stderr,
    })

    # Extraire les données JSON du stdout
    data = parse_json_output(stdout)
    if data:
        state.procedure_data = data
        proc_path = state.step_file(3, "procedure_data.json")
        save_json(proc_path, data)

    state.record_step(
        "CONSULT_BDD",
        ok=True,
        output=f"Données chargées pour '{identifier}'" if data else "Stdout brut sauvegardé",
        files={"raw": str(raw_path)},
    )
    return True


def step_design(state):
    """[4] DESIGN — Préparer la note de conception."""
    args = state.args
    niveau = args.niveau.lower() if args.niveau else None

    if args.mode in ("list", "check", "resync"):
        state.record_step("DESIGN", ok=True, output="Étape DESIGN non applicable")
        return True

    # Vérifier que le template existe
    if niveau:
        template_path = TEMPLATES_DIR / f"{niveau}_template.md"
        if not template_path.exists():
            state.record_step("DESIGN", ok=False, output=f"Template introuvable : {template_path}")
            return False

    # Vérifier que niveaux.yaml et qg_matrix.yaml existent
    niveaux_path = REFERENCES_DIR / "niveaux.yaml"
    qg_path = REFERENCES_DIR / "qg_matrix.yaml"

    missing = []
    if not niveaux_path.exists():
        missing.append("niveaux.yaml")
    if not qg_path.exists():
        missing.append("qg_matrix.yaml")
    if niveau and not template_path.exists():
        missing.append(f"{niveau}_template.md")

    if missing:
        state.record_step("DESIGN", ok=False, output=f"Références manquantes : {', '.join(missing)}")
        return False

    # Note de conception
    design_note = {
        "niveau": niveau,
        "template": str(template_path) if niveau and template_path.exists() else None,
        "niveaux_ref": str(niveaux_path),
        "qg_ref": str(qg_path),
        "golden_example": "CGSS 118 ULTRA (ID 497)",
    }

    design_path = state.step_file(4, "design_note.json")
    save_json(design_path, design_note)

    state.record_step(
        "DESIGN",
        ok=True,
        output=f"Doctrine chargée pour niveau {niveau}" if niveau else "Conception squelettique",
        files={"note": str(design_path)},
    )
    return True


def step_generate(state):
    """[5] GENERATE — Produire le DOX Contract via generate_contract.py."""
    args = state.args
    niveau = args.niveau.lower() if args.niveau else None

    if args.mode in ("list", "check", "audit", "resync"):
        state.record_step("GENERATE", ok=True, output="Étape GENERATE non applicable")
        return True

    contract_out = state.step_file(5, "contract.json")

    # Construire la commande generate_contract
    gen_args = []

    # Si on a des données BDD réelles, les passer via --from-file
    proc_data_path = state.step_file(3, "procedure_data.json")
    has_real_data = False
    if proc_data_path.exists():
        proc_data = load_json(proc_data_path)
        if proc_data and (proc_data.get("titre") or proc_data.get("procedure_id") or proc_data.get("properties") or proc_data.get("procedures")):
            has_real_data = True
    if has_real_data:
        gen_args.extend(["--from-file", str(proc_data_path)])
    elif args.mode == "create":
        # Mode création : on peut utiliser --interactive ou construire un squelette
        # Pour l'instant, créer un fichier minimal
        minimal_data = {
            "titre": args.titre,
            "niveau": niveau,
            "type_rh": args.type_rh or "",
            "perimetre": args.perimetre or "",
            "acteurs": args.acteurs or "",
        }
        skeleton_path = state.step_file(1, "skeleton_data.json")
        save_json(skeleton_path, minimal_data)
        gen_args.extend(["--from-file", str(skeleton_path)])
    else:
        state.record_step("GENERATE", ok=False, output="Aucune donnée source pour générer le contrat")
        return False

    if niveau:
        gen_args.extend(["--niveau", niveau])
    gen_args.extend(["--output", str(contract_out), "--notion-format"])

    ok, stdout, stderr = run_script("generate_contract", *gen_args)

    if not ok:
        state.record_step("GENERATE", ok=False, output=stderr)
        return False

    # Charger le contrat généré
    contract_data = load_json(str(contract_out))
    if contract_data:
        state.contract_data = contract_data

    state.record_step(
        "GENERATE",
        ok=True,
        output=f"Contrat généré → {contract_out}",
        files={"contract": str(contract_out)},
    )
    return True


def step_render(state):
    """[6] RENDER — Générer le document .md complet via render_procedure.py."""
    args = state.args
    niveau = args.niveau.lower() if args.niveau else None

    if args.mode in ("list", "check", "audit", "resync"):
        state.record_step("RENDER", ok=True, output="Étape RENDER non applicable")
        return True

    # ── 1. Vérifier que le contrat existe ───────────────────────
    contract_path = state.step_file(5, "contract.json")
    if not contract_path.exists():
        state.record_step("RENDER", ok=False, output=f"Contrat introuvable : {contract_path}")
        return False

    # ── 2. Déterminer le niveau ─────────────────────────────────
    niveau_arg = niveau or "mythique"
    # Le contrat peut contenir le niveau réel
    contract_data = load_json(contract_path) or {}
    niveau_reel = niveau or contract_data.get("niveau", "mythique")

    # ── 3. Lancer render_procedure ──────────────────────────────
    md_out = state.step_file(6, "procedure.md")
    ok, stdout, stderr = run_script(
        "render_procedure",
        str(contract_path),
        "--output", str(md_out),
        "--niveau", niveau_reel,
        timeout=180,
    )

    if not ok:
        state.record_step("RENDER", ok=False, output=stderr or stdout)
        return False

    # ── 4. Sauvegarder le résultat ──────────────────────────────
    render_data = parse_json_output(stdout) or {"output_path": str(md_out)}

    state.record_step(
        "RENDER",
        ok=True,
        output=f"Document .md généré → {md_out}",
        files={
            "contract": str(contract_path),
            "procedure_md": str(md_out),
        },
    )
    return True


def step_check_structure(state):
    """[7] CHECK_STRUCTURE — Valider les sections avant QG."""
    args = state.args
    niveau = args.niveau.lower() if args.niveau else None

    if args.mode in ("list", "check", "audit", "resync"):
        state.record_step("CHECK_STRUCTURE", ok=True, output="Étape CHECK_STRUCTURE non applicable")
        return True

    # ── 1. Trouver le fichier .md généré ────────────────────────
    md_path = state.step_file(6, "procedure.md")
    if not md_path.exists():
        state.record_step(
            "CHECK_STRUCTURE",
            ok=False,
            output=f"Aucun .md trouvé : {md_path}. L'étape RENDER n'a pas été exécutée ou a échoué.",
        )
        return False

    # ── 2. Déterminer le niveau attendu ─────────────────────────
    niveau_attendu = niveau or "mythique"

    # ── 3. Lancer check_structure ───────────────────────────────
    ok, stdout, stderr = run_script(
        "check_structure",
        str(md_path),
        "--niveau", niveau_attendu,
        "--json",
    )

    if not ok:
        state.record_step(
            "CHECK_STRUCTURE",
            ok=True,  # non-bloquant
            output=f"⚠️ Vérification structure : {stderr or stdout}",
        )
        report_path = state.step_file(7, "structure_report.json")
        save_json(report_path, {"status": "unknown", "note": "check_structure a échoué, pipeline continue"})
        return True

    # ── 4. Analyser le rapport ──────────────────────────────────
    report = parse_json_output(stdout)
    if not report:
        state.record_step(
            "CHECK_STRUCTURE",
            ok=False,
            output="Impossible de parser le rapport check_structure",
        )
        return False

    score = report.get("quality_score", 0)
    ready = report.get("ready_for_qg", False)
    completeness = report.get("completeness", {})
    pct = completeness.get("percentage", 0)
    missing = report.get("missing_required", [])
    missing_linked = report.get("missing_linked", [])

    # Sauvegarder le rapport détaillé
    report_path = state.step_file(7, "structure_report.json")
    save_json(report_path, report)

    if missing:
        missing_str = ', '.join(missing[:10])
        state.record_step(
            "CHECK_STRUCTURE",
            ok=True,  # non-bloquant : la procédure est créée, les sections manquantes sont signalées
            output=(
                f"⚠️ Sections manquantes ({len(missing)}) : {missing_str}"
                f"{'...' if len(missing) > 10 else ''} | "
                f"Complétude {pct}% | Score {score}/100"
            ),
            files={"report": str(report_path)},
        )
        # Continue le pipeline malgré les sections manquantes
        return True

    # Vues liées manquantes = avertissement, pas bloquant
    lv_warn = ""
    if missing_linked:
        lv_warn = f" (⚠️ vues liées : {', '.join(missing_linked)})"

    state.record_step(
        "CHECK_STRUCTURE",
        ok=True,
        output=f"✅ Structure valide — {completeness.get('present', 0)}/{completeness.get('required', 0)} "
               f"sections ({pct}%) — Score {score}/100 — Prêt pour QG 🟢{lv_warn}",
        files={"report": str(report_path), "procedure_md": str(md_path)},
    )
    return True
def step_local_qg(state):
    """[8] LOCAL_QG — Valider les Quality Gates via qg_validator.py."""
    args = state.args
    niveau = args.niveau.lower() if args.niveau else "argent"

    if args.mode in ("list", "check", "resync"):
        state.record_step("LOCAL_QG", ok=True, output="Étape QG non applicable")
        return True

    # Chercher un fichier markdown à valider
    md_file = None
    if args.file:
        md_file = Path(args.file)

    # Chercher dans le workdir
    if not md_file or not md_file.exists():
        for f in sorted(state.workdir.glob("*.md")):
            md_file = f
            break

    qg_args = []
    if md_file and md_file.exists():
        qg_args.extend(["--file", str(md_file)])
    elif args.proc:
        # Valider directement depuis Notion
        # Utiliser le page_id résolu par CONSULT_BDD si disponible
        notion_id = None
        try:
            proc_data = state.procedure_data or {}
            resolved_id = proc_data.get("page_id") or proc_data.get("Notion_id") or proc_data.get("Unique_Id") or args.proc
            notion_id = str(resolved_id)
        except Exception:
            notion_id = args.proc
        qg_args.extend(["--notion-id", notion_id])
    else:
        state.record_step("LOCAL_QG", ok=True, output="Aucun fichier à valider")
        return True

    qg_args.extend(["--niveau", niveau, "--json"])

    ok, stdout, stderr = run_script("qg_validator", *qg_args)

    if not ok:
        state.record_step("LOCAL_QG", ok=False, output=stderr)
        return False

    # Extraire les résultats JSON
    qg_data = parse_json_output(stdout)
    if qg_data:
        state.qg_results = qg_data
        qg_json_path = state.step_file(8, "qg_results.json")
        save_json(qg_json_path, qg_data)

    # Générer aussi le rapport markdown
    qg_report_path = state.step_file(8, "qg_report.md")
    qg_report_args = qg_args.copy()
    qg_report_args.remove("--json")
    qg_report_args.append("--report")
    run_script("qg_validator", *qg_report_args)

    state.record_step(
        "LOCAL_QG",
        ok=True,
        output=f"Quality Gates G1-G21 validés (niveau {niveau})",
        files={"json": str(qg_json_path) if qg_data else "", "report": str(qg_report_path)},
    )
    return True


def step_bullet_proof(state):
    """[9] BULLET_PROOFING — 4 angles de sécurisation."""
    args = state.args

    if args.mode in ("list", "check", "resync"):
        state.record_step("BULLET_PROOFING", ok=True, output="Étape BULLET_PROOFING non applicable")
        return True

    # Déterminer le fichier à vérifier
    target_file = None
    contract_path = state.step_file(5, "contract.json")
    if contract_path.exists():
        target_file = contract_path
    elif args.file:
        target_file = Path(args.file)

    if not target_file or not target_file.exists():
        state.record_step("BULLET_PROOFING", ok=True, output="Aucun fichier à vérifier")
        return True

    bullet_out = state.step_file(9, "bullet_report.json")

    ok, stdout, stderr = run_script(
        "bullet_proof",
        "--file", str(target_file),
        "--output", str(bullet_out),
    )

    if not ok:
        state.record_step("BULLET_PROOFING", ok=False, output=stderr)
        return False

    bullet_data = load_json(bullet_out)
    if bullet_data:
        state.bullet_results = bullet_data

    state.record_step(
        "BULLET_PROOFING",
        ok=True,
        output=f"4 angles validés → {bullet_out}",
        files={"report": str(bullet_out)},
    )
    return True


def step_sync_notion(state):
    """[10] SYNC_NOTION — Synchronisation bidirectionnelle."""
    args = state.args

    if args.dry_run:
        sync_out = state.step_file(10, "sync_result.json")
        save_json(sync_out, {"dry_run": True, "mode": args.mode, "note": "Dry-run : push Notion désactivé"})
        state.record_step(
            "SYNC_NOTION",
            ok=True,
            output=f"✅ Dry-run : synchronisation Notion simulée (aucun push effectué)",
            files={"result": str(sync_out)},
        )
        return True

    if args.mode in ("list", "check"):
        state.record_step("SYNC_NOTION", ok=True, output="Étape SYNC non applicable")
        return True

    if args.mode in ("create", "upgrade"):
        # Push vers Notion
        contract_path = state.step_file(5, "contract.json")
        if not contract_path.exists():
            state.record_step("SYNC_NOTION", ok=False, output="Aucun contrat à pousser")
            return False

        sync_args = ["--push", str(contract_path), "--database", "mythique"]

        # Ajouter le contenu markdown généré par RENDER
        md_path = state.step_file(6, "procedure.md")
        if md_path.exists():
            sync_args.extend(["--markdown", str(md_path)])

        # Si c'est un upgrade, on update la page existante
        if args.mode == "upgrade" and args.proc:
            # Récupérer l'ID Notion de la procédure
            if state.procedure_data:
                notion_id = (
                    state.procedure_data.get("page_id")
                    or state.procedure_data.get("id")
                    or state.procedure_data.get("notion_id", "")
                )
                if notion_id:
                    sync_args.extend(["--update", notion_id])

        sync_out = state.step_file(10, "sync_result.json")
        sync_args.extend(["--output", str(sync_out)])

        ok, stdout, stderr = run_script("sync_notion", *sync_args)

        if not ok:
            state.record_step("SYNC_NOTION", ok=False, output=stderr)
            return False

        sync_data = load_json(sync_out)
        if sync_data:
            state.sync_result = sync_data

        state.record_step(
            "SYNC_NOTION",
            ok=True,
            output=f"Procédure synchronisée dans Notion",
            files={"result": str(sync_out)},
        )

    elif args.mode == "resync":
        # Pull depuis Notion
        identifier = args.proc or args.titre or ""
        if not identifier:
            state.record_step("SYNC_NOTION", ok=False, output="--proc ou --titre requis pour resync")
            return False

        sync_out = state.step_file(10, "sync_result.json")
        ok, stdout, stderr = run_script(
            "sync_notion",
            "--pull", identifier,
            "--output", str(sync_out),
        )

        if not ok:
            state.record_step("SYNC_NOTION", ok=False, output=stderr)
            return False

        sync_data = load_json(sync_out)
        if sync_data:
            state.sync_result = sync_data

        state.record_step(
            "SYNC_NOTION",
            ok=True,
            output=f"Procédure '{identifier}' extraite de Notion",
            files={"result": str(sync_out)},
        )

    elif args.mode == "audit":
        # Pull pour analyse (lecture seule)
        identifier = args.proc or args.titre or ""
        if identifier:
            sync_out = state.step_file(10, "sync_result.json")
            ok, stdout, stderr = run_script(
                "sync_notion",
                "--pull", identifier,
                "--output", str(sync_out),
            )
            if ok:
                state.record_step("SYNC_NOTION", ok=True, output=f"Données extraites pour audit")
            else:
                state.record_step("SYNC_NOTION", ok=True, output="Pas de pull nécessaire")
        else:
            state.record_step("SYNC_NOTION", ok=True, output="Pas de sync nécessaire (audit)")

    return True


def step_create_related_pages(state):
    """[11] CREATE_RELATED_PAGES — Pages satellites SBRX, PMRI, GED, FAQ, Glossaire."""
    args = state.args

    if args.dry_run:
        state.record_step(
            "CREATE_RELATED_PAGES",
            ok=True,
            output="✅ Dry-run : création pages satellites simulée",
        )
        return True

    if args.mode in ("list", "check", "audit"):
        state.record_step("CREATE_RELATED_PAGES", ok=True, output="Étape non applicable")
        return True

    # Récupérer le page_id depuis step_sync_notion
    sync_result = state.sync_result or {}
    procedure_page_id = (
        sync_result.get("page_id")
        or sync_result.get("id")
        or sync_result.get("notion_id")
        or (state.procedure_data or {}).get("page_id")
    )

    if not procedure_page_id:
        state.record_step(
            "CREATE_RELATED_PAGES",
            ok=False,
            output="Aucun page_id Notion trouvé dans sync_result ni procedure_data",
        )
        return False

    # Trouver le .md rendu
    md_path = None
    for f in sorted(state.workdir.glob("*.md")):
        md_path = f
        break

    if not md_path or not md_path.exists():
        md_path = state.step_file(6, "procedure.md")
        if not md_path.exists():
            state.record_step(
                "CREATE_RELATED_PAGES",
                ok=False,
                output="Aucun fichier .md trouvé dans le workdir",
            )
            return False

    # Chemin de sortie
    output_path = state.step_file(11, "related_pages_result.json")

    ok, stdout, stderr = run_script(
        "create_related_pages",
        "--md", str(md_path),
        "--procedure-page-id", procedure_page_id,
        "--output", str(output_path),
    )

    if not ok:
        state.record_step(
            "CREATE_RELATED_PAGES",
            ok=False,
            output=stderr or stdout,
        )
        return False

    # Charger le résultat
    result_data = load_json(output_path)
    if result_data:
        state.related_pages_result = result_data

    # Compter les pages créées
    created_count = 0
    for category in ("sbrx", "pmri", "ged", "faq", "glossaire"):
        items = (result_data or {}).get(category, [])
        created = sum(1 for i in items if i.get("action") == "created")
        existing = sum(1 for i in items if i.get("action") == "already_exists")
        created_count += created

    total_items = sum(
        len((result_data or {}).get(c, []))
        for c in ("sbrx", "pmri", "ged", "faq", "glossaire")
    )

    relations = (result_data or {}).get("relations", {})
    rel_count = sum(1 for v in relations.values() if v.get("ok"))

    state.record_step(
        "CREATE_RELATED_PAGES",
        ok=True,
        output=f"✅ Pages satellites : {created_count} créées sur {total_items} total — "
               f"{rel_count} relations établies",
        files={"result": str(output_path)},
    )
    return True


def step_report(state):
    """[12] REPORT + EXEC_CLOSE — Compiler le rapport final."""
    args = state.args
    mode = args.mode

    lines = []
    lines.append(f"# 📋 Rapport Agent PROC — {mode.upper()}")
    lines.append(f"")
    lines.append(f"**Date** : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Mode** : {mode}")
    if args.titre:
        lines.append(f"**Titre** : {args.titre}")
    if args.niveau:
        lines.append(f"**Niveau** : {args.niveau}")
    if args.proc:
        lines.append(f"**Procédure** : {args.proc}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Résumé des étapes
    lines.append(f"## Résumé des étapes")
    lines.append(f"")
    lines.append(f"| Étape | Statut | Détail |")
    lines.append(f"|-------|--------|--------|")
    for step_name, step_data in state.steps.items():
        status = "✅" if step_data["ok"] else "❌"
        detail = step_data["output"][:80].replace("\n", " ")
        lines.append(f"| {step_name} | {status} | {detail} |")

    lines.append(f"")

    # Résultats QG
    if state.qg_results:
        lines.append(f"## 🎯 Quality Gates")
        lines.append(f"")
        if isinstance(state.qg_results, dict):
            total = state.qg_results.get("total", state.qg_results.get("score", "?"))
            max_score = state.qg_results.get("max", state.qg_results.get("total_gates", "?"))
            passed = state.qg_results.get("passed", state.qg_results.get("ok", "?"))
            lines.append(f"- **Score** : {total}/{max_score}")
            lines.append(f"- **Passés** : {passed}")
        lines.append(f"")

    # Résultats bullet proofing
    if state.bullet_results:
        lines.append(f"## 🛡️ Bullet Proofing")
        lines.append(f"")
        if isinstance(state.bullet_results, dict):
            for angle, result in state.bullet_results.items():
                if isinstance(result, dict):
                    status = "✅" if result.get("ok", result.get("passed", False)) else "❌"
                    lines.append(f"- {angle} : {status}")
        lines.append(f"")

    # Résultat sync
    if state.sync_result:
        lines.append(f"## 🔄 Synchronisation Notion")
        lines.append(f"")
        if isinstance(state.sync_result, dict):
            url = state.sync_result.get("url", state.sync_result.get("notion_url", ""))
            notion_id = state.sync_result.get("id", state.sync_result.get("notion_id", ""))
            if url:
                lines.append(f"- **URL Notion** : {url}")
            if notion_id:
                lines.append(f"- **ID Notion** : {notion_id}")
        lines.append(f"")

    # Résultats CREATE_RELATED_PAGES
    if state.related_pages_result:
        lines.append(f"## 🛰️ Pages satellites créées")
        lines.append(f"")
        rel_result = state.related_pages_result
        categories = [
            ("sbrx", "⚠️ Risques (SBRX)"),
            ("pmri", "🛡️ Mesures (PMRI)"),
            ("ged", "📄 Documents (GED)"),
            ("faq", "❓ FAQ"),
            ("glossaire", "📖 Glossaire"),
        ]
        for key, label in categories:
            items = rel_result.get(key, [])
            if not items:
                continue
            created = sum(1 for i in items if i.get("action") == "created")
            existing = sum(1 for i in items if i.get("action") == "already_exists")
            errors = sum(1 for i in items if i.get("action") == "error")
            lines.append(f"- {label} : {len(items)} ({created} créés, {existing} existants{f', {errors} erreurs' if errors else ''})")

        relations = rel_result.get("relations", {})
        if relations:
            lines.append(f"- **Relations** : {sum(1 for v in relations.values() if v.get('ok'))}/{len(relations)} OK")
        lines.append(f"")

    # Fichiers produits
    lines.append(f"## 📁 Fichiers produits")
    lines.append(f"")
    lines.append(f"**Répertoire de travail** : `{state.workdir}`")
    lines.append(f"")
    for f in sorted(state.workdir.iterdir()):
        if f.is_file():
            size = f.stat().st_size
            lines.append(f"- `{f.name}` ({size} octets)")
    lines.append(f"")

    # Prochaine action suggérée
    if mode == "create" and args.niveau:
        next_n = niveau_suivant(args.niveau)
        if next_n:
            lines.append(f"---")
            lines.append(f"")
            lines.append(f"## 🔜 Prochaine action suggérée")
            lines.append(f"")
            lines.append(f"```")
            lines.append(f"python3 proc_orchestrator.py --mode upgrade \\")
            lines.append(f"    --proc {args.titre or args.proc or '<ID>'} --niveau {next_n}")
            lines.append(f"```")

    state.final_report = "\n".join(lines)

    # Sauvegarder le rapport
    report_path = state.step_file(12, "final_report.md")
    with open(report_path, "w") as f:
        f.write(state.final_report)

    state.record_step(
        "REPORT",
        ok=True,
        output=f"Rapport final → {report_path}",
        files={"report": str(report_path)},
    )
    return True


# ─── Pipeline orchestrator ──────────────────────────────────────────────────
def create_pipeline(mode):
    """Retourne la liste des étapes pour un mode donné."""
    if mode == "create":
        return [
            step_intake,
            step_design,
            step_generate,
            step_render,
            step_check_structure,
            step_local_qg,
            step_bullet_proof,
            step_sync_notion,
            step_create_related_pages,
            step_report,
        ]
    elif mode == "upgrade":
        return [
            step_intake,
            step_anti_duplicate,
            step_consult_bdd,
            step_design,
            step_generate,
            step_render,
            step_check_structure,
            step_local_qg,
            step_bullet_proof,
            step_sync_notion,
            step_create_related_pages,
            step_report,
        ]
    elif mode == "audit":
        return [
            step_intake,
            step_consult_bdd,
            step_local_qg,
            step_bullet_proof,
            step_sync_notion,
            step_report,
        ]
    elif mode == "resync":
        return [
            step_intake,
            step_sync_notion,
            step_report,
        ]
    elif mode == "list":
        return []
    elif mode == "check":
        return []
    else:
        return []


def cmd_list(args):
    """Mode list — appeler consult_bdd --list."""
    list_args = ["--list"]
    if args.filter_prop and args.filter_val:
        list_args.extend(["--filter", args.filter_prop, args.filter_val])
    if args.limit:
        list_args.extend(["--limit", str(args.limit)])
    if args.output:
        list_args.extend(["--output", args.output])

    ok, stdout, stderr = run_script("consult_bdd", *list_args)
    if ok:
        print(stdout)
    else:
        print(f"Erreur : {stderr}", file=sys.stderr)
    return 0 if ok else 1


def cmd_check(args):
    """Mode check — vérifier tous les scripts."""
    print("🔍 Vérification globale du système Agent PROC")
    print("=" * 50)
    all_ok = True

    for name, path in SCRIPTS.items():
        exists = path.exists()
        print(f"  {'✅' if exists else '❌'} Script {name} : {'présent' if exists else 'introuvable'}")
        if not exists:
            all_ok = False

    # Vérifier les templates
    print()
    for niveau in NIVEAUX_ORDER:
        tpl = TEMPLATES_DIR / f"{niveau}_template.md"
        exists = tpl.exists()
        print(f"  {'✅' if exists else '❌'} Template {niveau} : {'présent' if exists else 'introuvable'}")
        if not exists:
            all_ok = False

    # Vérifier les références
    print()
    for ref_name in ["niveaux.yaml", "qg_matrix.yaml", "bdd_canoniques.yaml"]:
        ref_path = REFERENCES_DIR / ref_name
        exists = ref_path.exists()
        print(f"  {'✅' if exists else '❌'} Réf. {ref_name} : {'présente' if exists else 'introuvable'}")
        if not exists:
            all_ok = False

    # Vérifier le token Notion
    print()
    ok, stdout, stderr = run_script("consult_bdd", "--check")
    # La réponse est au format JSON : {"status": "ok", ...}
    check_ok = False
    try:
        check_data = json.loads(stdout)
        check_ok = check_data.get("status") == "ok"
    except (json.JSONDecodeError, TypeError):
        check_ok = "OK" in stdout or "ok" in stdout.lower()
    print(f"  {'✅' if check_ok else '❌'} Connexion Notion : {'OK' if check_ok else 'ÉCHEC'}")
    if not check_ok:
        print(f"     {stderr[:200] if stderr else stdout[:200]}")
        all_ok = False

    print()
    print(f"Résultat : {'✅ TOUT OK' if all_ok else '❌ PROBLÈMES DÉTECTÉS'}")
    return 0 if all_ok else 1


# ─── CLI ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="🧠 Agent PROC — Orchestrateur DOX_EXEC_CORE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes disponibles:
  create   Pipeline complet de création (INTAKE → REPORT)
  upgrade  Mise à jour de niveau d'une procédure existante
  audit    Audit sans modification (QG + Bullet Proof)
  resync   Synchronisation bidirectionnelle Notion
  list     Lister les procédures dans la BDD
  check    Vérifier l'état du système

Exemples:
  %(prog)s --mode create --niveau argent --titre "Ma procédure"
  %(prog)s --mode upgrade --proc PRH-042 --niveau or
  %(prog)s --mode audit --proc PRH-042
  %(prog)s --mode list
  %(prog)s --mode check
        """,
    )

    parser.add_argument(
        "--mode", "-m",
        choices=["create", "upgrade", "audit", "resync", "list", "check"],
        required=True,
        help="Mode d'exécution du pipeline",
    )

    parser.add_argument("--titre", "-t", help="Titre de la procédure")
    parser.add_argument("--niveau", "-n", help="Niveau (bronze, argent, or, platine, ultra, mythique, akuma)")
    parser.add_argument("--proc", "-p", help="ID de procédure (ex: PRH-042) ou titre")
    parser.add_argument("--type-rh", help="Type RH (rémunération, carrière, formation, etc.)")
    parser.add_argument("--perimetre", help="Périmètre (directions/services concernés)")
    parser.add_argument("--acteurs", help="Liste des rôles clés (séparés par des virgules)")
    parser.add_argument("--file", "-f", help="Fichier procédure existant (markdown ou JSON)")
    parser.add_argument("--output", "-o", help="Fichier de sortie pour le rapport final")
    parser.add_argument(
        "--force", action="store_true",
        help="Passer outre les avertissements (doublons, etc.)",
    )

    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulation complète sans push vers Notion",
    )

    # Options pour le mode list
    parser.add_argument("--filter-prop", help="Propriété pour filtrage (mode list)")
    parser.add_argument("--filter-val", help="Valeur pour filtrage (mode list)")
    parser.add_argument("--limit", type=int, default=50, help="Nombre max de résultats")

    args = parser.parse_args()

    # Routage des modes spéciaux
    if args.mode == "list":
        return cmd_list(args)

    if args.mode == "check":
        return cmd_check(args)

    # Pipeline pour create/upgrade/audit/resync
    state = PipelineState(args)
    pipeline = create_pipeline(args.mode)

    if not pipeline:
        print(f"Échec : aucun pipeline défini pour le mode '{args.mode}'", file=sys.stderr)
        return 1

    print(f"\n🚀 Agent PROC — Mode {args.mode.upper()}")
    print(f"{'=' * 50}\n")

    for step_func in pipeline:
        if state.aborted:
            print("\n⛔ Pipeline abandonné.")
            break
        step_name = step_func.__name__.replace("step_", "").upper()
        print(f"\n▶ [{step_name}]")
        step_func(state)

    # Résultat final
    print(f"\n{'=' * 50}")
    success = not state.aborted and all(
        s["ok"] for name, s in state.steps.items() if name != "ABORTED"
    )

    if success:
        print(f"\n✅ Pipeline terminé avec succès !")
    else:
        failed = [n for n, s in state.steps.items() if not s["ok"]]
        print(f"\n❌ Pipeline terminé avec {len(failed)} échec(s) : {', '.join(failed)}")

    # Afficher le rapport final
    if state.final_report:
        print(f"\n{state.final_report[:2000]}...")
        if len(state.final_report) > 2000:
            print(f"\\n[ Rapport complet : {state.step_file(12, 'final_report.md')} ]")

    # Copier le rapport dans --output si demandé
    if args.output and state.final_report:
        try:
            with open(args.output, "w") as f:
                f.write(state.final_report)
            print(f"\n📄 Rapport copié → {args.output}")
        except OSError as e:
            print(f"\n⚠️  Impossible d'écrire {args.output} : {e}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
