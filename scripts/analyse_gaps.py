#!/usr/bin/env python3
"""Analyse what template placeholders are actually filled vs unfilled."""
import re
import json
import sys
import os
import importlib.util

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../scripts'))

# Import the renderer
sys.path.insert(0, '../scripts')
# Parse the renderer file to extract generic_defaults
with open('../scripts/render_procedure.py') as f:
    renderer_code = f.read()

# Extract generic_defaults dict as Python code
exec_globals = {}
exec(re.sub(r'^.*?(generic_defaults\s*=\s*\{)', r'\1', renderer_code[:renderer_code.find('\n#')], flags=re.DOTALL), exec_globals)
# Actually let me just use exec properly

with open('../scripts/render_procedure.py') as f:
    code = f.read()

# Better approach: just grab the dict via ast
import ast
tree = ast.parse(code)
gen_defaults = {}
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'generic_defaults':
                gen_defaults = {k.value: v.value for k, v in zip(node.value.keys, node.value.values)
                                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant)}
print(f"generic_defaults keys extracted: {len(gen_defaults)}")

# Template placeholders
with open('../scripts/mythique_template_evaluateur.md') as f:
    template = f.read()
template_keys = set(re.findall(r'\{\{([A-Z_0-9]+)\}\}', template))
print(f"Template placeholder keys: {len(template_keys)}")

# Direct mapping coverage (what my parser fills)
# Now load and RUN build_placeholder_map
from importlib import import_module
spec = importlib.util.spec_from_file_location("render_procedure", "../scripts/render_procedure.py")
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)

with open('../flux_evaluateur/procedures_prioritaires/M1-P3-01_data.json') as f:
    contract = json.load(f)
if 'procedure' in contract:
    contract = contract['procedure']

mapping = rp.build_placeholder_map(contract, {}, template, gen_defaults, "mythique")

filled = {k: v for k, v in mapping.items() if v and str(v).strip()}
covered = template_keys & set(filled.keys())
uncovered = template_keys - set(filled.keys())

print(f"Remplis par mapping: {len(covered)}")
print(f"Non couverts: {len(uncovered)}")

# Grouper les non couverts
categories = {}
for k in uncovered:
    prefix = k.split('_')[0] if '_' in k else k
    if k.startswith('ETAPE_'): cat = 'ETAPE_*'
    elif k.startswith('PHASE_'): cat = 'PHASE_*'
    elif k.startswith('REGLE_G'): cat = 'REGLE_G*'
    elif k.startswith('CONSIGNE_'): cat = 'CONSIGNE_*'
    elif k.startswith('RISQUE_'): cat = 'RISQUE_*'
    elif k.startswith('BOWTIE_'): cat = 'BOWTIE_*'
    elif k.startswith('ISHIKAWA_'): cat = 'ISHIKAWA_*'
    elif k.startswith('GANTT_'): cat = 'GANTT_*'
    elif k.startswith('SWIMLANE_'): cat = 'SWIMLANE_*'
    elif re.match(r'^R_\d+_\d+$', k): cat = 'R_MATRICE'
    elif k.startswith('HEATMAP_'): cat = 'HEATMAP_*'
    elif k.startswith('KPI_'): cat = 'KPI_*'
    elif k.startswith(('DS_', 'DE_', 'DOC_')): cat = 'DS/DE/DOC'
    elif k.startswith(('CAS_', 'FAQ_')): cat = 'CAS/FAQ'
    elif k.startswith('CHECKPOINT_'): cat = 'CHECKPOINT_*'
    elif k.startswith(('RB_', 'RN_', 'RC_')): cat = 'RB/RN/RC_RADAR'
    elif k.startswith(('OKR_', 'COCKPIT_')): cat = 'OKR/COCKPIT'
    elif k.startswith('GL_'): cat = 'GL_GROUPE_LECTURE'
    elif k.startswith('PCA_'): cat = 'PCA_REPRISE'
    elif k.startswith('PDCA_'): cat = 'PDCA_*'
    elif k.startswith('RGPD_'): cat = 'RGPD_*'
    elif k.startswith(('COMM_',)): cat = 'COMMUNICATION'
    elif k.startswith(('MODULE_', 'FORMATION_')): cat = 'FORMATION'
    elif k.startswith('DEPLOIEMENT_'): cat = 'DEPLOIEMENT'
    elif k.startswith(('NORME_', 'INDIC_CONF_')): cat = 'NORME_CONFORMITE'
    elif k.startswith('VERSION_CHECK_'): cat = 'VERSION_CHECK'
    elif k.startswith('TIMELINE_'): cat = 'TIMELINE'
    elif k.startswith(('SIPOC_')): cat = 'SIPOC'
    elif k.startswith(('AMELIO_')): cat = 'AMELIORATION'
    elif k.startswith(('GL_',)): cat = 'GROUPE_LECTURE'
    elif k.startswith(('TRACE_',)): cat = 'TRACABILITE'
    elif k.startswith(('SIGLE_', 'TERME_', 'DEFINITION_')): cat = 'GLOSSAIRE'
    elif k in ('CONTEXTE_CRAIE', 'REFERENTIELS_CRAIE', 'OBJECTIF_OPERATIONNEL', 'MISSION',
               'MISSION_LABEL', 'FILIERE','PERIMETRE_FONCTIONNEL', 'TERRITOIRE',
               'PROCEDURE_TITLE', 'PROCEDURE_REF', 'TYPE_PROCEDURE', 'DATE_CREATION',
               'DATE_REVUE', 'TITRE_COURT', 'OBJET', 'OBJET_DETAILLE', 'ACTEUR_PILOTE',
               'VALIDATEUR', 'SERVICES_CONCERNES', 'AUTEUR', 'PROCESSUS', 'PROCESSUS_FILIERE',
               'PROCESSUS_LABEL', 'PROCES_AMONT', 'PROCES_AVAL', 'LABEL_AMONT', 'LABEL_AMONT2',
               'LABEL_AVAL', 'LABEL_AVAL2', 'LISTE_INCLUSIONS', 'LISTE_EXCLUSIONS',
               'LIVRABLE_FINAL', 'LIVRABLE_PRINCIPAL', 'RISQUE_MAJEUR', 'DECLENCHEUR',
               'DELAI_PIVOT', 'NB_RISQUES', 'RESSOURCES_HUMAINES', 'RESSOURCES_MATERIELLES',
               'MODELE_COURRIER_1', 'MODELE_FORMULAIRE_1', 'MODELE_TEMPLATE_1',
               'DOC_INTERNE_1', 'DOC_INTERNE_2', 'ECART_1', 'ECART_2',
               'ECHEANCE_1', 'ECHEANCE_2', 'REF_LEG1', 'REF_REG1',
               'TEXTE_LEG1', 'TEXTE_REG1', 'ARTICLES_LEG1', 'ARTICLES_REG1',
               'INDICATEUR_CIBLE', 'REFORMES_ACTEURS', 'SANKEY_DATA',
               'CONTACT_METHODO', 'CONTACT_PILOTE', 'CONTACT_SI',
               'ALERTE_CRITIQUE', 'ALERTE_CRITIQUE_2', 'ALERTE_INFO', 'ALERTE_MODEREE',
               'REGLE_G10', 'ETAPES_SYNOPTIQUE', 'N'):
        cat = 'DIVERS'
    else:
        cat = 'AUTRES'
    categories.setdefault(cat, []).append(k)

print("\n=== Gaps par catégorie ===")
total = 0
for cat, keys in sorted(categories.items()):
    print(f"  {cat:<30s}: {len(keys):>3}  ex: {', '.join(sorted(keys)[:3])}")
    total += len(keys)
print(f"\nTotal gaps: {total}")
