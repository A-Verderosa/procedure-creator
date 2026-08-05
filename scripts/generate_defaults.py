#!/usr/bin/env python3
"""Analyse les 142 placeholders non résolus et génère des defaults intelligents."""
import re, os, ast

with open('../scripts/render_procedure.py') as f:
    code = f.read()

# Trouver generic_defaults dans le code
tree = ast.parse(code)
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'generic_defaults':
                # C'est un dict literal
                defaults = {}
                if isinstance(node.value, ast.Dict):
                    for k, v in zip(node.value.keys, node.value.values):
                        if isinstance(k, ast.Constant) and isinstance(v, (ast.Constant, ast.List)):
                            defaults[k.value] = v
                print(f"generic_defaults: {len(defaults)} keys existantes")
                break

# Lire tous les placeholders du template
with open('../scripts/mythique_template_akuma.md') as f:
    template = f.read()
template_keys = set(re.findall(r'\{\{([A-Z_0-9]+)\}\}', template))
print(f"Template Akuma: {len(template_keys)} placeholders")

# Clés déjà dans generic_defaults
def_keys = set(defaults.keys())

# Clés manquantes génériques
uncovered = template_keys - def_keys
print(f"Placeholders non couverts par generic_defaults: {len(uncovered)}")

# Catégoriser
cats = {}
for k in sorted(uncovered):
    if k.startswith('RISQUE_'):
        cats.setdefault('RISQUE_*', []).append(k)
    elif k.startswith('REGLE_'):
        cats.setdefault('REGLE_*', []).append(k)
    elif k.startswith('CONSIGNE_'):
        cats.setdefault('CONSIGNE_*', []).append(k)
    elif k.startswith('ETAPE_'):
        cats.setdefault('ETAPE_*', []).append(k)
    elif k.startswith('PHASE_'):
        cats.setdefault('PHASE_*', []).append(k)
    elif k.startswith('CAS_'):
        cats.setdefault('CAS_*', []).append(k)
    elif k.startswith('FAQ_'):
        cats.setdefault('FAQ_*', []).append(k)
    elif re.match(r'^R_\d_\d$', k):
        cats.setdefault('R_MATRICE', []).append(k)
    elif k.startswith('DS_') or k.startswith('DE_'):
        cats.setdefault('DS/DE', []).append(k)
    elif k.startswith('DOC_') or k.startswith('MODELE_'):
        cats.setdefault('DOC', []).append(k)
    elif k.startswith('SIGLE_') or k.startswith('SIGNIFICATION_') or k.startswith('TERME_') or k.startswith('DEFINITION_'):
        cats.setdefault('GLOSSAIRE', []).append(k)
    elif k.startswith('REF_') or k.startswith('TEXTE_') or k.startswith('ARTICLES_'):
        cats.setdefault('REF_LEGALE', []).append(k)
    else:
        cats.setdefault('DIVERS', []).append(k)

# Générer un dict de defaults pour chaque catégorie
smart_defaults = {}

# Header divers
divers_defaults = {
    'CONTEXTE_CRAIE': 'Procédure standard',
    'REFERENTIELS_CRAIE': 'DOX v6.0 · Guide de l\'évaluateur',
    'OBJECTIF_OPERATIONNEL': 'Sécuriser et fluidifier le processus',
    'MISSION_LABEL': 'Mission principale',
    'PROCESSUS_LABEL': 'Processus principal',
    'FILIERE': 'Filière métier',
    'PERIMETRE_FONCTIONNEL': 'Périmètre défini par le contrat',
    'TERRITOIRE': 'National',
    'PROCES_AMONT': 'Processus amont',
    'PROCES_AVAL': 'Processus aval',
    'LABEL_AMONT': 'Amont',
    'LABEL_AMONT2': 'Interface amont',
    'LABEL_AVAL': 'Aval',
    'LABEL_AVAL2': 'Interface aval',
    'LISTE_INCLUSIONS': 'Cas standards inclus dans le périmètre',
    'LISTE_EXCLUSIONS': 'Cas particuliers exclus du périmètre',
    'LIVRABLE_FINAL': 'Procédure validée et diffusée',
    'NB_RISQUES': '4 risques identifiés',
    'REFORMES_ACTEURS': 'Pilote de la procédure',
}

smart_defaults.update(divers_defaults)

# Glossaire (SIGLE, TERME, DEFINITION)
glossary_prefix = {
    'SIGLE_1': 'CEV', 'SIGNIFICATION_1': 'Conseil Évaluateur',
    'SIGLE_2': 'CRAIE', 'SIGNIFICATION_2': 'Cartographie des Risques et Acteurs Intervenant dans l\'Évaluation',
    'TERME_1': 'Saisine', 'TERME_2': 'Délai pivot', 'TERME_3': 'Non-conformité',
    'DEFINITION_1': 'Saisine : Acte par lequel une demande d\'évaluation est officiellement transmise au service compétent.',
    'DEFINITION_2': 'Délai pivot : Durée maximale réglementaire entre la saisine et la décision finale.',
    'DEFINITION_3': 'Non-conformité : Écart constaté entre une situation réelle et le référentiel applicable.',
}
smart_defaults.update(glossary_prefix)

# Références légales
ref_legale = {
    'REF_LEG1': 'Code des relations entre le public et l\'administration (CRPA)',
    'TEXTE_LEG1': 'Articles L. 100-1 à L. 100-3 : Droit de saisine et délais',
    'ARTICLES_LEG1': 'L. 100-1, L. 112-1, R. 112-2',
    'REF_REG1': 'Règlement intérieur de l\'Évaluateur public',
    'TEXTE_REG1': 'Procédure de traitement des saisines et évaluations',
    'ARTICLES_REG1': 'Section 2, articles 4 à 12',
}
smart_defaults.update(ref_legale)

# Règles G6-G10 (les 5 premières sont parsées du contrat)
for i in range(6, 11):
    smart_defaults[f'REGLE_G{i}'] = f'Règle G{i} — À préciser selon le contexte de la procédure'

# Consignes C4-C5 (C1-C3 parsées)
smart_defaults['CONSIGNE_C4'] = 'Consigne C4 — À adapter'
smart_defaults['CONSIGNE_C5'] = 'Consigne C5 — À adapter'

# Risques (le parseur remplit TITRE/DESC pour R1-R4, tout le reste a besoin de defaults)
for i in range(1, 6):
    if i <= 4:
        smart_defaults[f'RISQUE_{i}_IMPACT'] = '3 - Majeur'
        smart_defaults[f'RISQUE_{i}_PROBA'] = '2 - Probable'
        smart_defaults[f'RISQUE_{i}_CRIT'] = '6 - Critique'
        smart_defaults[f'RISQUE_{i}_ACTION'] = 'Surveillance continue et plan d\'action correctif'
        smart_defaults[f'RISQUE_{i}_NIVEAU'] = 'Significatif'
    else:
        # R5 n'existe pas dans le contrat
        smart_defaults[f'RISQUE_{i}_TITRE'] = 'Risque non identifié dans le contrat'
        smart_defaults[f'RISQUE_{i}_DESC'] = 'À compléter selon l\'analyse de risque'
        smart_defaults[f'RISQUE_{i}_IMPACT'] = '—'
        smart_defaults[f'RISQUE_{i}_PROBA'] = '—'
        smart_defaults[f'RISQUE_{i}_CRIT'] = '—'
        smart_defaults[f'RISQUE_{i}_ACTION'] = 'À définir'
        smart_defaults[f'RISQUE_{i}_NIVEAU'] = '—'

# Étapes courtes (pour synoptique)
for i in range(1, 6):
    smart_defaults[f'ETAPE_{i}_COURT'] = f'Étape {i} : action principale'

# RACI (PHASE_N_RACI)
smart_defaults['PHASE_1_RACI'] = 'Pilote'
smart_defaults['PHASE_2_RACI'] = 'Pilote / Expert'
smart_defaults['PHASE_3_RACI'] = 'Validateur'
smart_defaults['PHASE_4_RACI'] = 'Contrôleur'

# PHASE_A/B/C/D_ETAPES
smart_defaults['PHASE_A_ETAPES'] = 'Étape 1→2'
smart_defaults['PHASE_B_ETAPES'] = 'Étape 2→3'
smart_defaults['PHASE_C_ETAPES'] = 'Étape 3→4'
smart_defaults['PHASE_D_ETAPES'] = 'Étape 4→5'

# Cas pratiques (CAS_1/2)
smart_defaults['CAS_1_TITRE'] = 'Cas standard — Saisine complète'
smart_defaults['CAS_1_SITUATION'] = 'Saisine conforme avec l\'ensemble des pièces requises'
smart_defaults['CAS_1_REPONSE'] = 'Traitement dans le délai standard de 15 jours ouvrés'
smart_defaults['CAS_2_TITRE'] = 'Cas particulier — Saisine incomplète'
smart_defaults['CAS_2_SITUATION'] = 'Saisine avec pièce manquante ou non conforme'
smart_defaults['CAS_2_REPONSE'] = 'Suspension du délai (G2) et demande de complément'

# FAQ
smart_defaults['FAQ_1_QUESTION'] = 'Quel est le délai de traitement d\'une saisine standard ?'
smart_defaults['FAQ_1_REPONSE'] = 'Le délai est de 15 jours ouvrés à compter de la réception de la saisine complète.'
smart_defaults['FAQ_2_QUESTION'] = 'Que faire en cas de pièce manquante ?'
smart_defaults['FAQ_2_REPONSE'] = 'Appliquer la règle G2 (suspension du délai) et notifier le demandeur dans les 2 jours.'

# DS (Documents Support)
for i in range(1, 4):
    smart_defaults[f'DS_{i}_TITRE'] = f'Document support {i}'
    smart_defaults[f'DS_{i}_DESC'] = f'Document de référence associé à la procédure'
    smart_defaults[f'DS_{i}_SOURCE'] = 'Base documentaire MYTHIQUE'

# DE (Documents Entrée/Sortie)
for i in range(1, 4):
    smart_defaults[f'DE_{i}_TITRE'] = f'Document entrée/sortie {i}'
    smart_defaults[f'DE_{i}_DESC'] = f'Document associé au circuit de traitement'
    smart_defaults[f'DE_{i}_USAGE'] = 'Usage standard'

# Modèles (courrier, formulaire, template)
smart_defaults['MODELE_COURRIER_1'] = 'Modèle de notification de saisine'
smart_defaults['MODELE_FORMULAIRE_1'] = 'Formulaire de saisine standard'
smart_defaults['MODELE_TEMPLATE_1'] = 'Template de rapport d\'évaluation'

# Autres documents
smart_defaults['DOC_INTERNE_1'] = 'Note de procédure interne'
smart_defaults['DOC_INTERNE_2'] = 'Grille d\'auto-évaluation'

# Matrice de couverture (R_1_1 à R_4_6)
# 4 risques × 6 règles
risk_names = ['Non-conformité documentaire', 'Dépassement délai', 'Pièce non conforme', 'Erreur d\'appréciation']
rule_names = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6']
for r in range(1, 5):
    for c in range(1, 7):
        # Value simple basée sur la couverture
        val = '✓' if r == c else ('◐' if abs(r-c) <= 1 else '—')
        smart_defaults[f'R_{r}_{c}'] = val

# Synoptique
smart_defaults['ETAPES_SYNOPTIQUE'] = 'Phases A→B→C→D'

print(f"\n=== Defaults générés ===")
print(f"Total defaults: {len(smart_defaults)}")
print(f"Catégories couvertes:")

# Montrer combien sont maintenant couverts
remaining = uncovered - set(smart_defaults.keys())
print(f"Encore non couverts après génération: {len(remaining)}")
if remaining:
    for r in sorted(remaining):
        print(f"  MANQUE: {r}")

# Écrire le fichier de defaults
with open('smart_defaults.txt', 'w') as f:
    for k, v in sorted(smart_defaults.items()):
        f.write(f"    \"{k}\": \"{v}\",\n")
print(f"\nFichier généré: smart_defaults.txt ({len(smart_defaults)} entrées)")
