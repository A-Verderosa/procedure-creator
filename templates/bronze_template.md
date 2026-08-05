---
niveau: bronze
code: BZ
emoji: "🥉"
finalite: "Cadrage minimal et procédure de base"
couverture: 11
dox_version: "6.0"
---

# {{TITRE}}

> **Référence** : `{{REFERENCE}}`
> **Niveau** : 🥉 Bronze
> **Type RH** : {{TYPE_RH}}
> **Version** : {{VERSION}}
> **Date de création** : {{DATE_CREATION}}

---

## 🃏 FLASH CARD — Résumé 30s

> **Objet** : {{OBJET_FLASH}}
> **Acteurs clés** : {{ACTEURS_FLASH}}
> **Délai pivot** : {{DELAI_PIVOT}}
> **Risque majeur** : {{RISQUE_MAJEUR}}
> **Indicateur cible** : {{INDICATEUR_CIBLE}}

---

## 📍 CRAIE — Localisation

| Axe | Valeur |
|-----|--------|
| **Contexte** | {{CONTEXTE}} |
| **Référentiel** | {{REFERENTIEL}} |
| **Acteurs** | {{ACTEURS_CRAIE}} |
| **Intitulé** | {{INTITULE_PROC}} |
| **Étapes** | {{ETAPES_CRAIE}} |

### Chaîne de localisation

```
Mission › {{MISSION}} › Processus › {{PROCESSUS}} › Service › {{SERVICE}}
```

**Filière RH** : {{FILIERE_RH}}

---

## 👥 Acteurs clés

| # | Rôle | Direction/Service | Responsabilité |
|---|------|-------------------|----------------|
| 1 | {{ACTEUR_1_ROLE}} | {{ACTEUR_1_DIR}} | {{ACTEUR_1_RESP}} |
| 2 | {{ACTEUR_2_ROLE}} | {{ACTEUR_2_DIR}} | {{ACTEUR_2_RESP}} |
| 3 | {{ACTEUR_3_ROLE}} | {{ACTEUR_3_DIR}} | {{ACTEUR_3_RESP}} |
{% if ACTEUR_4 %}
| 4 | {{ACTEUR_4_ROLE}} | {{ACTEUR_4_DIR}} | {{ACTEUR_4_RESP}} |
{% endif %}

---

## 📝 Étapes simplifiées

| # | Action | Acteur | Description |
|---|--------|--------|-------------|
| 1 | {{ETAPE_1_ACTION}} | {{ETAPE_1_ACTEUR}} | {{ETAPE_1_DESC}} |
| 2 | {{ETAPE_2_ACTION}} | {{ETAPE_2_ACTEUR}} | {{ETAPE_2_DESC}} |
| 3 | {{ETAPE_3_ACTION}} | {{ETAPE_3_ACTEUR}} | {{ETAPE_3_DESC}} |
{% if ETAPE_4 %}
| 4 | {{ETAPE_4_ACTION}} | {{ETAPE_4_ACTEUR}} | {{ETAPE_4_DESC}} |
{% endif %}
{% if ETAPE_5 %}
| 5 | {{ETAPE_5_ACTION}} | {{ETAPE_5_ACTEUR}} | {{ETAPE_5_DESC}} |
{% endif %}

---

## ⚠️ Risques principaux

| Code | Risque | Description |
|------|--------|-------------|
| {{RISQUE_1_CODE}} | {{RISQUE_1_NOM}} | {{RISQUE_1_DESC}} |
| {{RISQUE_2_CODE}} | {{RISQUE_2_NOM}} | {{RISQUE_2_DESC}} |
{% if RISQUE_3_CODE %}
| {{RISQUE_3_CODE}} | {{RISQUE_3_NOM}} | {{RISQUE_3_DESC}} |
{% endif %}

---

## 📋 Informations complémentaires

| Champ | Valeur |
|-------|--------|
| **Périmètre** | {{PERIMETRE}} |
| **Directions concernées** | {{DIRECTIONS}} |
| **Services concernés** | {{SERVICES}} |
| **Date d'effet** | {{DATE_EFFET}} |
| **Validité** | {{VALIDITE}} |

---

## 🔗 Références

| Type | Référence |
|------|-----------|
| Texte fondateur | {{TEXTE_FONDATEUR}} |
| Procédure liée | {{PROCEDURE_LIEE}} |
| Note interne | {{NOTE_INTERNE}} |

---

## ✅ Checklist Bronze

- [ ] FLASH CARD présente avec résumé 30s
- [ ] Localisation CRAIE complète (Mission → Processus → Service)
- [ ] Acteurs clés (min 3) identifiés
- [ ] Étapes simplifiées (3-5) décrites
- [ ] Risques principaux (min 2) identifiés
- [ ] Périmètre et directions concernés définis

---

> **Généré par Hermes Agent — PROC v1.0**  
> **DOX v6.0 — Niveau Bronze**  
> **Prochaine évolution suggérée** : `/proc upgrade --niveau argent`
