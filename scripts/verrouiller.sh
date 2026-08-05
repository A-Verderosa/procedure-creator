#!/usr/bin/env bash
# ============================================================================
# 🔒 verrouiller.sh — Pipeline de verrouillage procédure Mythique
#
# Usage:
#   verrouiller.sh <contract.json> [options]
#
# Options:
#   --golden PATH      Chemin du Golden Example (défaut: auto-détection)
#   --publish          Pousser vers Notion après vérification
#   --update PAGE_ID   Mettre à jour une page Notion existante (nécessite --publish)
#   --output PATH      Forcer le chemin de sortie .md (défaut: auto-dérivé)
#   --template NAME    Forcer un template (evaluateur|générique)
#   --check-only       Vérifier les placeholders sans produire le fichier
#   --skip-structure   Sauter le check structure (21 portes)
#   --skip-diff        Sauter le diff structurel contre Golden
#   --skip-satellites  Sauter la création des pages satellites (V6)
#   -v, --verbose      Mode verbeux
#   -h, --help         Affiche cette aide
#
# Retour:
#   0 = succès (tous les verrous passés)
#   1 = erreur à une étape (le pipeline s'arrête)
# ============================================================================
set -euo pipefail

# ── Couleurs ──────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Utilitaires ───────────────────────────────────────────────────────────
info()  { echo -e "${BLUE}🔍${NC} $*"; }
ok()    { echo -e "${GREEN}✅${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠️${NC} $*"; }
err()   { echo -e "${RED}❌${NC} $*" >&2; }
header(){ echo -e "\n${BOLD}${CYAN}═══════════════════════════════════════════════════════${NC}"; echo -e "${BOLD} $*${NC}"; echo -e "${CYAN}───────────────────────────────────────────────────────────${NC}"; }

# ── Chemins ───────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROCEDURES_DIR="$PROJECT_DIR/flux_evaluateur/procedures_prioritaires"
GOLDEN_DEFAULT="$PROCEDURES_DIR/CEV-P02_MYTHIQUE.md"

# ── Parse arguments ──────────────────────────────────────────────────────
CONTRACT=""
OUTPUT=""
GOLDEN="$GOLDEN_DEFAULT"
TEMPLATE=""
PUBLISH=false
UPDATE=""
CHECK_ONLY=false
SKIP_STRUCTURE=false
SKIP_DIFF=false
SKIP_SATELLITES=false
VERBOSE=false
NO_COLOR=false

usage() { sed -n 's/^# //p; s/^#$//p' "$0"; exit 0; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --golden)       GOLDEN="$2";       shift 2 ;;
        --output)       OUTPUT="$2";        shift 2 ;;
        --template)     TEMPLATE="$2";      shift 2 ;;
        --update)       UPDATE="$2";        shift 2 ;;
        --publish)      PUBLISH=true;       shift ;;
        --check-only)   CHECK_ONLY=true;    shift ;;
        --skip-structure) SKIP_STRUCTURE=true; shift ;;
        --skip-diff)    SKIP_DIFF=true;     shift ;;
        --skip-satellites) SKIP_SATELLITES=true; shift ;;
        -v|--verbose)   VERBOSE=true;       shift ;;
        --no-color)     NO_COLOR=true;      shift ;;
        -h|--help)      usage ;;
        -*)
            err "Option inconnue : $1"
            usage
            ;;
        *)
            if [[ -z "$CONTRACT" ]]; then
                CONTRACT="$1"
            else
                err "Argument superflu : $1"
                exit 1
            fi
            shift
            ;;
    esac
done

# ── Vérifications ─────────────────────────────────────────────────────────
if [[ -z "$CONTRACT" ]]; then
    err "Usage : verrouiller.sh <contract.json> [options]"
    err "       verrouiller.sh --help pour l'aide"
    exit 1
fi
if [[ ! -f "$CONTRACT" ]]; then
    err "Fichier contrat introuvable : $CONTRACT"
    exit 1
fi

# Dériver le nom de sortie
CONTRACT_NAME="$(basename "$CONTRACT" .json)"
if [[ -z "$OUTPUT" ]]; then
    OUTPUT_DIR="$(dirname "$CONTRACT")"
    OUTPUT="$OUTPUT_DIR/${CONTRACT_NAME%_data}_MYTHIQUE.md"
fi

# Déduire le template si non forcé
TEMPLATE_FLAG=""
if [[ -n "$TEMPLATE" ]]; then
    TEMPLATE_FLAG="--template $TEMPLATE"
fi

# Détection du niveau depuis le contrat (défaut: mythique)
NIVEAU="mythique"

# ── Log d'entrée ──────────────────────────────────────────────────────────
header "🔒 VERROUILLER — Pipeline production"
echo -e "  ${BOLD}Contrat :${NC}   $CONTRACT"
echo -e "  ${BOLD}Sortie :${NC}    $OUTPUT"
echo -e "  ${BOLD}Golden :${NC}    $GOLDEN"
echo -e "  ${BOLD}Template :${NC}  ${TEMPLATE:-auto}"
echo -e "  ${BOLD}Publish :${NC}   $PUBLISH"
echo

# ── V1 : Validation du contrat ────────────────────────────────────────────
header "🔓 V1 — Validation du contrat"
# Vérifier que le JSON est valide et contient les champs essentiels
V1_OK=false
if python3 -c "
import json, sys
with open('$CONTRACT') as f:
    data = json.load(f)
proc = data.get('procedure', data)
required = ['procedure_id', 'niveau', 'titre']
missing = [f for f in required if f not in proc]
if missing:
    print(json.dumps({'valid': False, 'errors': [f'Champ manquant: {m}' for m in missing]}, indent=2))
    sys.exit(1)
print(json.dumps({'valid': True, 'id': proc['procedure_id'], 'titre': proc['titre'], 'niveau': proc['niveau']}, indent=2))
" 2>&1; then
    ok "Contrat valide : $CONTRACT"
else
    err "ÉCHEC V1 — Contrat invalide"
    exit 1
fi

# ── V2 : Rendu du template → .md ──────────────────────────────────────────
header "🔓 V2 — Rendu du template"
RENDER_ARGS=("$CONTRACT" "-o" "$OUTPUT")
[[ -n "$TEMPLATE" ]] && RENDER_ARGS+=("--template" "$TEMPLATE")
if $CHECK_ONLY; then RENDER_ARGS+=("--check-only"); fi

if python3 "$SCRIPT_DIR/render_procedure.py" "${RENDER_ARGS[@]}" 2>&1; then
    ok "Rendu produit : $OUTPUT"
    if $CHECK_ONLY; then
        ok "Mode check-only — arrêt après V2"
        exit 0
    fi
else
    err "ÉCHEC V2 — Erreur de rendu"
    exit 1
fi

# Vérifier que le fichier a bien été créé
if [[ ! -f "$OUTPUT" ]]; then
    err "Fichier de sortie manquant après rendu : $OUTPUT"
    exit 1
fi

# ── V3 : 21 quality gates ────────────────────────────────────────────────
if ! $SKIP_STRUCTURE; then
    header "🔓 V3 — 21 Quality Gates"
    # Détecter si c'est un template Évaluateur (structure différente)
    EVAL_TEMPLATE=false
    if python3 -c "
import json
with open('$CONTRACT') as f:
    data = json.load(f)
proc = data.get('procedure', data)
direction = proc.get('direction', '')
print('evaluateur' if 'évaluateur' in direction.lower() else 'generic')
" 2>/dev/null | grep -q "evaluateur"; then
        EVAL_TEMPLATE=true
    fi

    if $EVAL_TEMPLATE && [[ -z "${TEMPLATE:-}" || "$TEMPLATE" == "auto" ]]; then
        warn "Template Évaluateur détecté — le check structure générique ne s'applique pas"
        warn "Passe --skip-structure ou ajoute un check Évaluateur dédié"
        warn "(les sections du template Évaluateur sont différentes du format Mythique générique)"
    else
        if python3 "$SCRIPT_DIR/check_structure.py" "$OUTPUT" --niveau "$NIVEAU" 2>&1; then
            ok "Structure validée — 21 portes passées"
        else
            err "ÉCHEC V3 — Structure invalide (voir détails ci-dessus)"
            err "Conseil : pour les procédures Évaluateur, utilise --skip-structure"
            exit 1
        fi
    fi
else
    header "🔓 V3 — 21 Quality Gates"
    warn "Structure check skipped (--skip-structure)"
fi

# ── V4 : Diff structurel contre Golden Example ───────────────────────────
if ! $SKIP_DIFF; then
    header "🔓 V4 — Diff structurel vs Golden"
    if [[ ! -f "$GOLDEN" ]]; then
        warn "Golden introuvable : $GOLDEN — diff ignoré"
    else
        # Comparer les titres de sections (## et ###)
        GOLDEN_SECTIONS=$(mktemp)
        OUTPUT_SECTIONS=$(mktemp)
        trap 'rm -f "$GOLDEN_SECTIONS" "$OUTPUT_SECTIONS"' EXIT

        grep '^## ' "$GOLDEN" > "$GOLDEN_SECTIONS" || true
        grep '^## ' "$OUTPUT" > "$OUTPUT_SECTIONS" || true

        if diff -q "$GOLDEN_SECTIONS" "$OUTPUT_SECTIONS" &>/dev/null; then
            ok "Structure identique au Golden Example"
        else
            warn "Structure DIFFÉRENTE du Golden Example — sections manquantes ou en trop :"
            diff --color=auto "$GOLDEN_SECTIONS" "$OUTPUT_SECTIONS" 2>/dev/null || \
            diff "$GOLDEN_SECTIONS" "$OUTPUT_SECTIONS" || true
            warn "⚠ Ce n'est pas bloquant — vérifie manuellement si c'est intentionnel"
        fi
    fi
else
    header "🔓 V4 — Diff structurel vs Golden"
    warn "Diff skipped (--skip-diff)"
fi

# ── V5 : Sync Notion (optionnelle) ────────────────────────────────────────
if $PUBLISH; then
    header "🔓 V5 — Publication Notion"

    # 🔍 V4.5 : Recherche auto d'une page existante par procedure_id
    # Évite les doublons : enrichit la page existante si trouvée
    if [[ -z "${UPDATE:-}" ]]; then
        pid=$(python3 -c "
import json
with open('$CONTRACT') as f:
    data = json.load(f)
d = data.get('procedure', data)
print(d.get('procedure_id', '') or '')
")
        if [[ -n "$pid" ]]; then
            info "Recherche page existante : $pid..."
            FOUND_PAGE=$(cd "$PROJECT_DIR" && python3 "$SCRIPT_DIR/find_page_by_id.py" "$pid" 2>/dev/null || true)
            if [[ -n "$FOUND_PAGE" ]]; then
                warn "Page existante trouvée : $FOUND_PAGE → mise à jour"
                UPDATE="$FOUND_PAGE"
            else
                info "Aucune page existante → création nouvelle page"
            fi
        fi
    fi

    SYNC_ARGS=()
    SYNC_ARGS+=("--push" "$CONTRACT")
    SYNC_ARGS+=("--markdown" "$OUTPUT")
    SYNC_ARGS+=("--database" "mythique")
    if [[ -n "$UPDATE" ]]; then
        SYNC_ARGS+=("--update" "$UPDATE")
    fi

    # Capturer la sortie JSON de sync_notion.py pour récupérer le page_id
    SYNC_OUTPUT=$(mktemp)
    if python3 "$SCRIPT_DIR/sync_notion.py" "${SYNC_ARGS[@]}" 2>&1 | tee "$SYNC_OUTPUT"; then
        ok "Publication Notion réussie"
        # Extraire le page_id du JSON de sortie
        SYNC_PAGE_ID=$(python3 -c "
import json, sys
with open('$SYNC_OUTPUT') as f:
    for line in f:
        line = line.strip()
        if line.startswith('{'):
            try:
                data = json.loads(line)
                pid = data.get('page_id', '')
                if pid:
                    print(pid)
                    sys.exit(0)
            except json.JSONDecodeError:
                pass
" 2>/dev/null || true)
        rm -f "$SYNC_OUTPUT"
        if [[ -z "$SYNC_PAGE_ID" ]]; then
            SYNC_PAGE_ID="${UPDATE:-}"
        fi
    else
        err "ÉCHEC V5 — Publication Notion échouée"
        rm -f "$SYNC_OUTPUT"
        exit 1
    fi

    # ── V6 : Création des pages satellites (Risques, PMRI, GED, FAQ) ────
    if $SKIP_SATELLITES; then
        header "🔓 V6 — Pages satellites (relations Notion)"
        warn "Satellites skipped (--skip-satellites)"
    else
        header "🔓 V6 — Pages satellites (relations Notion)"
    fi
    if ! $SKIP_SATELLITES && [[ -n "$SYNC_PAGE_ID" ]]; then
        info "Création des pages satellites pour : $SYNC_PAGE_ID"
        if python3 "$SCRIPT_DIR/create_satellite_pages.py" "$CONTRACT" "$SYNC_PAGE_ID" 2>&1; then
            ok "Pages satellites créées et liées"
        else
            warn "ÉCHEC V6 — Erreur lors de la création des pages satellites"
            warn "Le pipeline continue (les relations peuvent être ajoutées manuellement)"
        fi
    else
        warn "Aucun page_id disponible — V6 ignoré"
    fi
fi

# ── Final ─────────────────────────────────────────────────────────────────
echo
header "✅ VERROUILLÉ — Procédure prête"
echo -e "  ${BOLD}Fichier :${NC}  $OUTPUT"
echo -e "  ${BOLD}Taille :${NC}   $(wc -c < "$OUTPUT") octets"
echo -e "  ${BOLD}Lignes :${NC}   $(wc -l < "$OUTPUT")"
echo
