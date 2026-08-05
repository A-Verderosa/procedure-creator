# Hermes Kanban CLI — Procédure Creator

Utilisé pour le suivi du plan d'automatisation Évaluateur Public (Board: `automatisation-evaluateur`).

## Commandes

```bash
# Créer un nouveau board
hermes kanban boards create automatisation-evaluateur

# Basculer sur un board (nécessaire avant de créer/lister)
hermes kanban boards switch automatisation-evaluateur

# Lister les boards disponibles
hermes kanban boards list

# Lister les tâches du board actif
hermes kanban ls

# Créer une tâche
hermes kanban create "M1 — Gouvernance programmation (5 procédures)" \
  --body "# Contexte\n..." \
  --priority 1

# Note: --priority prend un entier (0=critique, 1=haute, 5=basse)
```

## Board actif

- `hermes kanban boards switch <slug>` ne persiste pas entre shell calls séparés.
- Toujours chaîner `switch` + `ls` dans la même commande : `hermes kanban boards switch X && hermes kanban ls`
- Exemple de la session 2026-08-02 : board `automatisation-evaluateur` avec 6 tasks (M1-M5 + QA).

## Piège

`hermes kanban list --board <slug>` échoue — la syntaxe est `boards switch` puis `ls`. Il n'y a pas de flag `--board` sur `kanban list`.
