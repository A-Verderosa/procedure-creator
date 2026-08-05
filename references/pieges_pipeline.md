# Pièges opérationnels — Pipeline DB-Centric V2

Voir `references/pieges_pipeline.md` pour le détail complet de chaque piège.

## Dashboard : ne jamais dupliquer
Le pipeline nettoie tous les blocs enfants de la page MYTHIQUE avant d'ajouter le nouveau dashboard (`fetch_children` + `delete_children`). Sans ça, chaque run ajoute un récapitulatif supplémentaire.

## Phases : toujours "Phase N — Titre"
Chaque phase dans `build_dashboard_blocks` doit s'afficher comme `Phase {num} — {nom}`. Utiliser `phase.get("titre") or phase.get("nom")` et `phase.get("numero", i)`.

## GED : parse documents supporte ; et \n
`parse_documents()` split par `;` si présent, sinon par `\n`. Supprime les tirets de liste (`-` / `*`). Les documents sans code reçoivent `D{i+1}`.

## Relations inverses
Toujours lier les entrées créées (SBRX, PMRI, etc.) au champ relation de MYTHIQUE. Étape 4b du pipeline.

## Idempotence
Toutes les `populate_*` vérifient l'existence par code/titre avant création.
