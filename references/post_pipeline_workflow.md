# Post-pipeline workflow

Après `publish_procedure.py --publish`, 4 étapes manuelles (API Notion directe) sont nécessaires pour compléter une procédure.

## Ordre d'exécution

```
Pipeline → A (SBRX enrich) → B (PMRI create) → C (FAQ create) → D (Rapport lecture)
```

## A. Enrichir les risques SBRX

Le pipeline crée les pages SBRX mais **sans** Impact, Probabilité ni Hypothèses.

**Actions :** PATCH chaque page SBRX avec :
- `Impact` (number, 1-4)
- `Probabilité` (number, 1-4)
- `Hypothèse RC` (rich_text)
- `Hypothèse RN` (rich_text)
- `Statut` → `🔲 À faire`

Récupérer les IDs SBRX depuis `Risques liés` (relation) sur la page MYTHIQUE.

## B. Créer les mesures PMRI

**BDD :** `6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9`

Créer 1+ mesure par risque. Chaque mesure doit être liée à :
- `Procédure Source` → MYTHIQUE (relation)
- `Risque Traité` → SBRX (relation)

Propriétés : Titre, Famille de mesure (multi_select), Fréquence contrôle (select), Contribution risque (select), Effet attendu impact/probabilité (number, -1 à -4), Statut.

Puis mettre à jour `Mesures PMRI` sur MYTHIQUE avec les IDs créés.

## C. Créer les FAQ

**BDD :** `3c44d2d1-ee87-44ed-b991-bab4d1e94442`

Simples : Question (title) + Réponse (rich_text). Lier via `FAQ liée` sur MYTHIQUE.

## D. Créer le Rapport de lecture

**BDD :** `bca72a91852e48dabcbbb8ab60a67cc4`

**Propriétés clés :** Rapport (title), Procédure (relation → DOX), Procédure mythique (relation → MYTHIQUE), Niveau DOX évalué (select), Score lecture (number 0-100), Verdict global (Favorable/Favorable avec réserves/Défavorable), Synthèse (rich_text), Statut (Préliminaire/En cours/Finalisé/Validé).

Mettre à jour les 2 champs MYTHIQUE après création :
- `Rapport de lecture` (multi) — historique
- `Dernier rapport de lecture` (unique) — le plus récent

---

**Voir `references/db_centric_v2_relations.md`** pour la liste exhaustive des propriétés de chaque BDD satellite.
