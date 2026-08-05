#!/usr/bin/env python3
"""Génère le template MYTHIQUE Akuma (épuré) depuis le template complet."""
import re

with open('../scripts/mythique_template_evaluateur.md') as f:
    content = f.read()

lines = content.split('\n')

# Définir les sections à GARDER (numéro de ligne, 1-indexed)
# Format: (line_start, line_end)  où line_end est EXCLUSIVE (dernière ligne AVANT le --- suivant)
KEEP_SECTIONS = {
    # Flash Card (31-42, le --- à 43 est exclus)
    (31, 43): "Flash Card",
    # Localisation (45-97, --- à 98)
    (45, 98): "Localisation",
    # Objet (100-105, --- à 106)
    (100, 106): "Objet",
    # Champ d'application (108-123, --- à 124)
    (108, 124): "Champ Application",
    # Définitions (126-142, --- à 143)
    (126, 143): "Définitions",
    # Documents de référence (145-165, --- à 166)
    (145, 166): "Docs référence",
    # Acteurs responsables (168-245, --- à 246)
    (168, 246): "Acteurs",
    # Procédure étapes (248-407, --- à 408)
    (248, 408): "Procédure",
    # Règles de gestion (410-424, --- à 425)
    (410, 425): "Règles",
    # Consignes (427-436, --- à 437)
    (427, 437): "Consignes",
    # Analyse des risques (439-472, --- à 473)
    (439, 473): "Risques",
    # Documents support (475-500, --- à 501)
    (475, 501): "Documents",
    # Cas pratiques & FAQ (503-538, --- à 539)
    (503, 539): "Cas & FAQ",
}

# Construire le template Akuma
akuma_lines = []
# YAML header (lines 1-17)
akuma_lines.extend(lines[0:17])  # L'index 17 est le --- de fin du YAML

# YAML footer
akuma_lines.append('')

# Ajouter une section dédiée dans le YAML pour marquer le template
# Remplacer la ligne "niveau: mythique" par "niveau: akuma"
# Et ajouter un champ systeme_analytique
for i, line in enumerate(akuma_lines):
    if line.startswith('niveau:'):
        akuma_lines[i] = 'niveau: akuma'
    if line.startswith('dox_version:'):
        akuma_lines[i] = 'dox_version: "6.0-akuma"'

# Ajouter la note système analytique juste après le YAML
akuma_lines.append('')
akuma_lines.append('> **🔗 Système d\'Analyse Mythique (SAM)** : Consulter la base de données analytique liée pour les sections retirées :')
akuma_lines.append('> [Gantt Déploiement] · [Bowtie Risques] · [Ishikawa Causes] · [BPMN Swimlanes] · [PCA Reprise] · [RGPD] · [Scorecard]')
akuma_lines.append('> *Ces sections sont générées automatiquement par le pipeline SAM.*')
akuma_lines.append('')

# Flash Card ligne
akuma_lines.append('# 🔮 {{PROCEDURE_TITLE}}')
akuma_lines.append('')

# Insérer les sections gardées
for (start, end), name in sorted(KEEP_SECTIONS.items()):
    # Ajouter les lignes de la section (sans le --- de fin)
    section = lines[start-1:end-1]  # -1 pour conversion 1→0-indexed, end-1 pour exclure le ---
    akuma_lines.extend(section)
    # Ajouter le séparateur ---
    akuma_lines.append('---')
    akuma_lines.append('')

# Ajouter la section vue analytique à la fin
akuma_lines.append('## 🔗 SYSTÈME D\'ANALYSE MYTHIQUE (SAM)')
akuma_lines.append('')
akuma_lines.append('Les sections analytiques suivantes sont disponibles en vues liées dans la base MYTHIQUE :')
akuma_lines.append('')
akuma_lines.append('| Section | Base liée | Description |')
akuma_lines.append('|---------|-----------|-------------|')
akuma_lines.append('| **14. Points de Contrôle** | MYTHIQUE Audit | Checkpoints et jalons de vérification |')
akuma_lines.append('| **15. Formation** | MYTHIQUE Formation | Modules de formation et supports pédagogiques |')
akuma_lines.append('| **17. Groupe de Lecture** | MYTHIQUE Revue | Comité de relecture et validation |')
akuma_lines.append('| **18. Déploiement** | MYTHIQUE Projet | Planning Gantt, jalons et ressources |')
akuma_lines.append('| **19. PCA / Urgence** | MYTHIQUE Continuité | Plan de continuité et reprise d\'activité |')
akuma_lines.append('| **20. RGPD** | MYTHIQUE Données | Protection des données et registre RGPD |')
akuma_lines.append('| **21. Conformité** | MYTHIQUE Normes | Référentiels normatifs (ISO, Charte) |')
akuma_lines.append('| **23. Visualisation** | MYTHIQUE Analyse | Bowtie, Ishikawa, BPMN, Radar, SIPOC, Heatmap, Timeline |')
akuma_lines.append('| **24. Versions** | MYTHIQUE Historique | Historique des versions et audit trail |')
akuma_lines.append('| **25. Scorecard** | MYTHIQUE Pilotage | Tableau de bord complet et indicateurs |')
akuma_lines.append('| **26. Couverture** | MYTHIQUE Cartographie | Matrice de couverture documentaire |')
akuma_lines.append('')
akuma_lines.append('---')
akuma_lines.append('')
akuma_lines.append('## 24. HISTORIQUE DES VERSIONS')
akuma_lines.append('')
akuma_lines.append('| Version | Date | Auteur | Modifications |')
akuma_lines.append('|---------|------|--------|---------------|')
akuma_lines.append(f'| 1.0 | {{DATE_REVUE}} | Pipeline Akuma | Génération automatique via contrat MYTHIQUE |')
akuma_lines.append('')
akuma_lines.append('---')
akuma_lines.append('')
akuma_lines.append('*Document généré par le pipeline Mythique — Template Akuma v6.0*')

output = '\n'.join(akuma_lines)

with open('../scripts/mythique_template_akuma.md', 'w') as f:
    f.write(output)

# Stats
total_placeholders = len(re.findall(r'\{\{[A-Z_0-9]+\}\}', output))
print(f"Template Akuma créé : {len(akuma_lines)} lignes, {total_placeholders} placeholders")
print(f"Sections gardées : {len(KEEP_SECTIONS)}")
print(f"Sections remplacées par vues liées : 12")
