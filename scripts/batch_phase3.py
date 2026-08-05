#!/usr/bin/env python3
"""Script batch pour lancer les 6 procédures Phase 3 — Évaluateur public."""

import subprocess, sys, time, json
from pathlib import Path

SCRIPTS_DIR = Path("/data/skills/software-development/procedure-creator/scripts")
ORCHESTRATOR = SCRIPTS_DIR / "proc_orchestrator.py"

PROCEDURES = [
    ("Charte de l'évaluation", "argent"),
    ("Procédure de saisine", "argent"),
    ("Note de cadrage", "or"),
    ("Collecte des données", "or"),
    ("Phase contradictoire", "platine"),
    ("Suivi des recommandations", "platine"),
]

results = []
for i, (titre, niveau) in enumerate(PROCEDURES, 1):
    print(f"\n{'='*70}")
    print(f"[{i}/6] Création : {titre} (niveau {niveau.upper()})")
    print(f"{'='*70}")
    
    cmd = [
        sys.executable, str(ORCHESTRATOR),
        "--mode", "create",
        "--titre", titre,
        "--niveau", niveau,
    ]
    
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    elapsed = time.time() - start
    
    ok = result.returncode == 0
    status = "✅" if ok else "❌"
    print(f"  {status} Returncode={result.returncode}, {elapsed:.0f}s")
    
    # Extract page_id from sync result if possible
    page_id = None
    for line in result.stdout.split('\n'):
        if 'page_id' in line and '3b01' in line:
            page_id = line.split('"')[-2] if '"' in line else None
    
    results.append({
        "titre": titre,
        "niveau": niveau,
        "ok": ok,
        "returncode": result.returncode,
        "elapsed": round(elapsed, 1),
        "page_id": page_id,
    })
    
    # Stderr
    if result.stderr:
        print(f"  STDERR: {result.stderr[:500]}")
    
    # Brief output
    stdout_lines = [l for l in result.stdout.split('\n') if l.strip() and not l.startswith('\\n')]
    for line in stdout_lines[-5:]:
        print(f"  {line}")

print(f"\n{'='*70}")
print("RÉSULTATS PHASE 3")
print(f"{'='*70}")
for r in results:
    icon = "✅" if r["ok"] else "❌"
    print(f"  {icon} {r['titre']} ({r['niveau']}) — {r['elapsed']}s")
print(f"\n✅ Succès: {sum(1 for r in results if r['ok'])}/6")
if any(not r['ok'] for r in results):
    print(f"❌ Échecs: {sum(1 for r in results if not r['ok'])}/6")
