# BDD Notion canoniques

## Identifiants

| BDD | ID | Notes |
|-----|----|-------|
| DOX | `3351d81e-4c39-827e-88a4-817c2739bbff` | Hiérarchie Mission→Processus→Procédure |
| MYTHIQUE | `0a1689d5-ec35-4422-95cb-188a1dd35113` | Page hub avec 32 propriétés |
| SBRX | `4f51d81e-4c39-8192-9b38-ed3fb5a890cd` | Risques |
| PMRI | `6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9` | Mesures |
| FAQ | `3c44d2d1-ee87-44ed-b991-bab4d1e94442` | Questions |
| Glossaire Main | `1481d81e-4c39-808a-b304-fd1857c29329` | Définitions |
| Exigences | `8e25465d-681b-4e4c-a3e6-063724790843` | Règles (Règle/Consigne) |
| GED MAIN | `3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e` | Documents, champ Catégorie (select) |
| RAPPORTS LECTURE DOX | `bca72a91-852e-48da-bcbb-b8ab60a67cc4` | Rapports lecture |
| ANNUAIRE DOX (contacts) | `6e9d978c-b165-490c-a6c5-a4de5eaa5e56` | Responsables PMRI, contacts — **pré-populer avant de lier Responsable** |

## MYTHIQUE — Propriétés clés

- Rédacteur / Validateur → relation Personnes (défaut AVR: `12f1d81e-4c39-81af-b875-e5c5364a397c`)
- Dernière revue → date (initialisée à la création)
- Rapport de lecture → relation RAPPORTS LECTURE DOX (état zéro à la création)
- Analyse des risques → rich text (peuplé depuis SBRX)
- Risques liés → relation SBRX (inverse)
- Mesures PMRI → relation PMRI (inverse, champ conservé pour lisibilité)
- FAQ liée → relation FAQ
- Glossaire lié → relation Glossaire Main
- Règles de gestion liées / Consignes de sécurité liées → relation Exigences
- Document GED → relation GED MAIN
- Phases opérationnelles → rich text (généré depuis le contrat)

## GED MAIN — Propriétés

| Propriété | Type | Usage |
|-----------|------|-------|
| Code & Document | title | Code + titre |
| Procédures liées | relation → MYTHIQUE | Lien inverse |
| Catégorie | select | "Document support" pour supports, aucun pour références |
| Fichier | files | Pièce jointe (optionnel) |

## RAPPORTS LECTURE DOX — Propriétés

Inspecter via Notion API pour la liste complète (~24 propriétés). 
Relation vers MYTHIQUE, date de création, état (initial), dernière revue.

## Glossaire Main — Propriétés

Définitions avec relation `Procédures mythiques liées` vers MYTHIQUE.

## Exigences — Propriétés

Champ `Type` (select) : "Règle" ou "Consigne". Relations séparées vers MYTHIQUE :
- `Procédures mythiques liées (règles)` → pour les Règles de gestion
- `Procédures mythiques liées (consignes)` → pour les Consignes de sécurité

## ANNUAIRE DOX (contacts) — Propriétés

| Propriété | Type | Usage |
|-----------|------|-------|
| Nom Prénom | title | Nom du contact |
| Email | email | Adresse professionnelle |
| Rôle / Direction | select | (options à définir) |
| Procédures Rédigées | relation → MYTHIQUE | Procédures rédigées par cet acteur |
| Contexte | select | PRO / PERSO |
| Service/Direction | relation | Direction de rattachement |

Cette base doit être pré-populée avec les acteurs (Évaluateur public, Contrôle qualité, Directeur de l'évaluation, etc.) avant que le champ `Responsable` des mesures PMRI puisse être lié automatiquement par le pipeline.
