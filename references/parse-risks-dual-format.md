# parse_risks() — Format double

La fonction `parse_risks(contract)` dans `publish_procedure.py` supporte deux formats :

## Format structuré (prioritaire) — `risks_detail`

```json
{
  "procedure": {
    "risks_detail": [
      {"code": "R1", "title": "Non-respect des délais", "impact": 3, "probability": 3,
       "hyp_rc": "Aucun filet de sécurité", "hyp_nr": "Contrôle qualité systématique"},
      {"code": "R2", "title": "Risque juridique", "impact": 2, "probability": 2}
    ]
  }
}
```

Utilisé pour les contrats générés programmatiquement. Champs disponibles :
| Champ | Type | Obligatoire | Usage |
|---|---|---|---|
| `code` | string | Oui | Identifiant du risque (R1, R2...) |
| `title` | string | Oui | Description courte |
| `impact` | number | Non | Pour cotation (1-4) et matrice Mermaid |
| `probability` | number | Non | Pour cotation (1-4) et matrice Mermaid |
| `hyp_rc` | string | Non | Hypothèse Risque Courant (champ rich_text SBRX) |
| `hyp_rn` | string | Non | Hypothèse Risque Net (champ rich_text SBRX) |
| `description` | string | Non | Description longue (champ rich_text SBRX, si existe) |

## Format texte (legacy) — `risques`

```json
{
  "procedure": {
    "risques": "R1: Premier risque; R2: Second risque"
  }
}
```

Multiligne, séparé par `;`. Chaque ligne au format `R<num>: <description>`.

## Ordre de priorité

1. Si `risks_detail` existe et est non-vide → l'utiliser
2. Sinon, si `risques` existe → parser le texte
3. Sinon → retourner `[]`
