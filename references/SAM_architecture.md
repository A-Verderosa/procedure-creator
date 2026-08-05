# Système d'Analyse Mythique (SAM) — Architecture

## Vue d'ensemble

Le **Système d'Analyse Mythique (SAM)** est l'architecture qui remplace les 12 sections analytiques retirées du template Akuma par des **vues liées Notion**. Chaque procédure pointe vers les bases de données dédiées plutôt que d'incorporer l'analyse inline.

```
┌─────────────────────────────────────────────┐
│           PROCÉDURE MYTHIQUE                │
│  En-tête YAML · Étapes · Règles · Risques   │
│  Cas pratiques · Documents · Matrice        │
│  🔗 SAM → [vues liées]                      │
└─────────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐
│ MYTHIQUE │ │ MYTHIQUE │ │ MYTHIQUE     │
│ Audit    │ │ Projet   │ │ Analyse      │
│ (Contrôle)│ │(Déploiement)│ │(Bowtie...) │
└──────────┘ └──────────┘ └──────────────┘
```

## Sections retirées → Bases liées

| Section retirée | Base Notion | Type de vue |
|---|---|---|
| **14. Points de Contrôle** | MYTHIQUE Audit | Tableau des checkpoints par procédure |
| **15. Formation & Support** | MYTHIQUE Formation | Modules liés à la procédure |
| **17. Groupe de Lecture** | MYTHIQUE Revue | Comité de relecture |
| **18. Déploiement/Gantt** | MYTHIQUE Projet | Planning et jalons |
| **19. PCA / Urgence** | MYTHIQUE Continuité | Plan de reprise |
| **20. RGPD** | MYTHIQUE Données | Registre de protection |
| **21. Conformité** | MYTHIQUE Normes | Référentiels ISO/Charte |
| **23. Visualisation avancée** | MYTHIQUE Analyse | Bowtie, Ishikawa, BPMN, Radar, SIPOC, Heatmap, Timeline |
| **24. Versions** | MYTHIQUE Historique | Audit trail des versions |
| **25. Scorecard** | MYTHIQUE Pilotage | KPIs et indicateurs |
| **26. Couverture** | MYTHIQUE Cartographie | Matrice documentaire |

## Pipeline de production (verrouillage)

**Deux pipelines disponibles :**

### Legacy : `verrouiller.sh` (template Markdown → sync)
```bash
bash scripts/verrouiller.sh flux_evaluateur/procedures_prioritaires/MX-XXX_data.json --publish
```
Rendu Markdown → blocks Notion. Adapté pour Argent/Or.

### DB-Centric V2 : `publish_procedure.py` (Notion-native, Akuma/Ultra)
```bash
python3 scripts/publish_procedure.py flux_evaluateur/procedures_prioritaires/MX-XXX_data.json --publish
```
5 étapes : DOX→MYTHIQUE→SBRX→GED→Dashboard. Zéro BDD créée. Zéro rendu Markdown. La page Notion est construite directement via l'API avec propriétés + dashboard visuel.

**Workflow standard :**
1. Copier `CEV-P02_data.json` → éditer (titre, code, phases, risques, etc.)
2. Lancer `python3 scripts/publish_procedure.py <contrat> --publish`
3. Vérifier dans Notion : propriétés MYTHIQUE, relations SBRX/GED, dashboard

## Garanties

- **211 placeholders** du template Akuma → **toujours 211/211 remplis**
- **0 « À définir »** — defaults intelligents pour tous les champs non couverts par le contrat
- **Détection auto** : vues liées SAM en pied de page
- **Préfixe EVP/PRH** automatique selon `direction`
- **Page existante** détectée → update au lieu de création (V4.5)

## Architecture des fichiers

```
scripts/
├── mythique_template_evaluateur_akuma.md   # Template Akuma (14 sections)
├── render_procedure.py                     # Renderer avec defaults Akuma
├── verrouiller.sh                          # Pipeline V1→V5
├── sync_notion.py                          # Publication Notion
├── generate_contract.py                    # Validation contrat
├── generate_akuma_template.py             # Générateur du template
├── find_page_by_id.py                      # Détection page existante
└── analyse_gaps.py                         # Analyse des écarts
```

## Pour enrichir le contrat (champs disponibles)

Tous les champs du contrat CEV-P02_data.json sont compatibles. Les champs optionnels qui OVERRIDENT les defaults Akuma :

- `titre`, `procedure_id`, `direction`, `niveau`, `service`, `pole`
- `objet`, `pilote`, `champ_application`, `definitions`
- `documents_reference`, `documents_supports` (blob texte)
- `regles` (blob texte "G1 ... ; G2 ...")
- `consignes` (blob texte "C1 ... ; C2 ...")  
- `risques` (blob texte "R1: ... ; R2: ...")
- `phases` (tableau des étapes)
- `acteurs` (tableau détaillé)
