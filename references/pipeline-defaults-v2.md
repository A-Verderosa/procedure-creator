# Pipeline DB-Centric V2 — Défauts & Champs obligatoires

Mis à jour : 2026-08-04
Corrigé le 2026-08-04 : ajout PMRI, FAQ, Rapport zéro dans le pipeline, Rédacteur/Validateur = AVR par défaut.

## Pipeline complet `publish_procedure.py`

```
Étape 1  🔍 DOX           → find_dox_entry(pid)
Étape 2  📄 MYTHIQUE      → find_or_create_mythique() + 32 propriétés
                            → Défauts : Rédacteur/Validateur = Antoine Verderosa
                            → Défauts : Dernière revue procédure = date du jour
Étape 3  ⚠️ SBRX          → populate_sbrx(risks, page_id)
Étape 3b 📏 PMRI          → populate_pmri(mesures, page_id, sbrx_map)
Étape 3c ❓ FAQ           → populate_faq(faqs)  — pool global (pas de lien entrant)
Étape 4  📁 GED           → populate_ged(documents, page_id)
Étape 4b 🔗 Relations     → Risques liés + Mesures PMRI ← patch MYTHIQUE
Étape 4c 📖 Rapport zéro  → Crée rapport de lecture état zéro (BDD bca72a91)
                            Statut=Finalisé, Score=0, Niveau=Mythique
Étape 5  🎨 Dashboard      → 30+ blocs (4 diagrammes Mermaid)
```

⚠️ **Format des textes structurés** :

## RICH_TEXT_PROPS (propriétés alimentées depuis le contrat)

Ces propriétés sont en rich_text et alimentées automatiquement via `build_properties()` :

```python
RICH_TEXT_PROPS = [
    "objet",              # → Objet
    "champ_application",  # → Champ d'application
    "definitions",        # → Définitions & glossaire
    "acteurs",            # → Acteurs responsables
    "documents_reference",# → Documents de référence
    "documents_supports", # → Documents support
    "regles",             # → Règles de gestion
    "consignes",          # → Consignes opérationnelles
    "risques",            # → Analyse des risques (texte legacy)
]
```

## Champs obligatoires du contrat JSON

```json
{
  "procedure": {
    "procedure_id": "M1-P?",
    "titre": "...",
    "direction": "Évaluateur Public",
    "version": "1.0",
    "statut": "À faire",
    "objet": "Texte libre — finalité de la procédure",
    "champ_application": "Périmètre et bénéficiaires",
    "definitions": "Glossaire des termes clés",
    "acteurs": "Liste des rôles et responsables",
    "regles": "Règles de gestion applicables",
    "consignes": "Consignes opérationnelles (sécurité, RGPD, traçabilité)",
    "documents_reference": "Documents de référence (liste)",
    "documents_supports": "Documents supports / modèles",
    "periodicite_revue": "Mensuelle|Trimestrielle|Semestrielle|Annuelle|À événement",
    "craie_context": "Contexte pour la carte CRAIE",
    "phases": [ ... ],
    "risques" ou "risks_detail": "Risques en texte ou structuré",
    "pmri_mesures": [ ... ],
    "faq": [ ... ],
    "redacteur": "(optionnel — défaut Antoine Verderosa)",
    "validateur": "(optionnel — défaut Antoine Verderosa)"
  }
}
```

## Défauts automatiques

| Champ | Valeur par défaut | Source |
|:--|:--|:--|
| Rédacteur | Antoine Verderosa (id `12f1d81e-4c39-81af-b875-e5c5364a397c`) | pipeline étape 2 |
| Validateur | Antoine Verderosa (même id) | pipeline étape 2 |
| Dernière revue procédure | Date du jour (datetime.now()) | pipeline étape 2 |
| Rapport de lecture | État zéro créé si absent | pipeline étape 4c |

## Rédacteur/Validateur — ID Annuaire

Antoine Verderosa (AVR) est le rédacteur/validateur par défaut :
```
id: 12f1d81e-4c39-81af-b875-e5c5364a397c
Nom: Antoine VERDEROSA
BDD: Annuaire Global (12f1d81e-4c39-8122-bffe-d61e547e9ea9)
```

## Contrat exemple M1-P3-02

Voir `templates/contrat_M1-P3-02.json` ou `/data/contrat_M1-P3-02.json` pour un contrat complet avec tous les champs.
