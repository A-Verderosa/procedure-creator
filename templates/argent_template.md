---
niveau: argent
code: AR
emoji: "🥈"
finalite: "Procédure interne complète et exploitable"
couverture: 14
dox_version: "6.0"
---

# {{TITRE}}

> **Référence** : `{{REFERENCE}}`
> **Niveau** : 🥈 Argent
> **Type RH** : {{TYPE_RH}}
> **Version** : {{VERSION}}
> **Date de création** : {{DATE_CREATION}}
> **Dernière mise à jour** : {{DERNIERE_MAJ}}

---

## **§1. Objet**

{{OBJET}}

## **§2. Champ d'application**

{{CHAMP_APPLICATION}}

## **§3. Définitions**

{{DEFINITIONS}}

## **§4. Documents de référence**

{{DOCUMENTS_REFERENCE}}

## **§5. Acteurs**

{{ACTEURS}}

## **§6. Règles de gestion**

{{REGLES}}

## **§7. Consignes**

{{CONSIGNES}}

---

## 🃏 FLASH CARD — Résumé 30s

> **Objet** : {{OBJET_FLASH}}
> **Acteurs clés** : {{ACTEURS_FLASH}}
> **Délai pivot** : {{DELAI_PIVOT}}
> **Déclencheur** : {{DECLENCHEUR}}
> **Livrable principal** : {{LIVRABLE_PRINCIPAL}}
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

### Processus amont et aval

| Direction | Flux |
|-----------|------|
| **Amont** | {{AMONT_DESC}} ({{AMONT_SERVICE}}) |
| **Procédure** | {{PROC_DESC}} |
| **Aval** | {{AVAL_DESC}} ({{AVAL_SERVICE}}) |

---

## 🔄 Logigramme Mermaid

```mermaid
flowchart LR
    A[{{AMONT_NOEUD}}] -->|{{AMONT_SORTIE}}| B{{ETAPE_1_NOEUD}}
    B --> C{{ETAPE_2_NOEUD}}
    C --> D{{ETAPE_3_NOEUD}}
    D --> E{{ETAPE_4_NOEUD}}
    E --> F[{{AVAL_NOEUD}}]

    style A fill:#e1f5fe,stroke:#0288d1
    style B fill:#fff3e0,stroke:#f57c00
    style C fill:#fff3e0,stroke:#f57c00
    style D fill:#fff3e0,stroke:#f57c00
    style E fill:#fff3e0,stroke:#f57c00
    style F fill:#e8f5e9,stroke:#388e3c
```

### Légende

| Couleur | Signification |
|---------|---------------|
| 🔵 Bleu | Amont / Entrée |
| 🟠 Orange | Étapes de la procédure |
| 🟢 Vert | Aval / Sortie |

---

## 👥 RACI — Matrice des responsabilités

### Acteurs

| # | Rôle | Direction/Service | Rôle dans la procédure |
|---|------|-------------------|----------------------|
| 1 | {{ACTEUR_1_ROLE}} | {{ACTEUR_1_DIR}} | {{ACTEUR_1_DESC}} |
| 2 | {{ACTEUR_2_ROLE}} | {{ACTEUR_2_DIR}} | {{ACTEUR_2_DESC}} |
| 3 | {{ACTEUR_3_ROLE}} | {{ACTEUR_3_DIR}} | {{ACTEUR_3_DESC}} |
| 4 | {{ACTEUR_4_ROLE}} | {{ACTEUR_4_DIR}} | {{ACTEUR_4_DESC}} |
{% if ACTEUR_5 %}
| 5 | {{ACTEUR_5_ROLE}} | {{ACTEUR_5_DIR}} | {{ACTEUR_5_DESC}} |
{% endif %}

### Matrice RACI

| Phase / Activité | {{ACTEUR_1_ROLE}} | {{ACTEUR_2_ROLE}} | {{ACTEUR_3_ROLE}} | {{ACTEUR_4_ROLE}} |
|-----------------|:---:|:---:|:---:|:---:|
| {{PHASE_1}} | {{RACI_1_1}} | {{RACI_1_2}} | {{RACI_1_3}} | {{RACI_1_4}} |
| {{PHASE_2}} | {{RACI_2_1}} | {{RACI_2_2}} | {{RACI_2_3}} | {{RACI_2_4}} |
| {{PHASE_3}} | {{RACI_3_1}} | {{RACI_3_2}} | {{RACI_3_3}} | {{RACI_3_4}} |
| {{PHASE_4}} | {{RACI_4_1}} | {{RACI_4_2}} | {{RACI_4_3}} | {{RACI_4_4}} |

> **R** = Réalise · **A** = Approuve · **C** = Consulté · **I** = Informé

---

## 📝 Étapes détaillées

### Étape 1 : {{ETAPE_1_TITRE}}

| Champ | Valeur |
|-------|--------|
| **Action** | {{ETAPE_1_ACTION}} |
| **Acteur** | {{ETAPE_1_ACTEUR}} |
| **Délai** | {{ETAPE_1_DELAI}} |
| **Livrable** | {{ETAPE_1_LIVRABLE}} |
| **Outil** | {{ETAPE_1_OUTIL}} |
| **Condition de passage** | {{ETAPE_1_CONDITION}} |

### Étape 2 : {{ETAPE_2_TITRE}}

| Champ | Valeur |
|-------|--------|
| **Action** | {{ETAPE_2_ACTION}} |
| **Acteur** | {{ETAPE_2_ACTEUR}} |
| **Délai** | {{ETAPE_2_DELAI}} |
| **Livrable** | {{ETAPE_2_LIVRABLE}} |
| **Outil** | {{ETAPE_2_OUTIL}} |
| **Condition de passage** | {{ETAPE_2_CONDITION}} |

### Étape 3 : {{ETAPE_3_TITRE}}

| Champ | Valeur |
|-------|--------|
| **Action** | {{ETAPE_3_ACTION}} |
| **Acteur** | {{ETAPE_3_ACTEUR}} |
| **Délai** | {{ETAPE_3_DELAI}} |
| **Livrable** | {{ETAPE_3_LIVRABLE}} |
| **Outil** | {{ETAPE_3_OUTIL}} |
| **Condition de passage** | {{ETAPE_3_CONDITION}} |

### Étape 4 : {{ETAPE_4_TITRE}}

| Champ | Valeur |
|-------|--------|
| **Action** | {{ETAPE_4_ACTION}} |
| **Acteur** | {{ETAPE_4_ACTEUR}} |
| **Délai** | {{ETAPE_4_DELAI}} |
| **Livrable** | {{ETAPE_4_LIVRABLE}} |
| **Outil** | {{ETAPE_4_OUTIL}} |
| **Condition de passage** | {{ETAPE_4_CONDITION}} |

{% if ETAPE_5_TITRE %}
### Étape 5 : {{ETAPE_5_TITRE}}

| Champ | Valeur |
|-------|--------|
| **Action** | {{ETAPE_5_ACTION}} |
| **Acteur** | {{ETAPE_5_ACTEUR}} |
| **Délai** | {{ETAPE_5_DELAI}} |
| **Livrable** | {{ETAPE_5_LIVRABLE}} |
| **Outil** | {{ETAPE_5_OUTIL}} |
| **Condition de passage** | {{ETAPE_5_CONDITION}} |
{% endif %}

---

## ⚠️ Risques identifiés

| # | Code | Risque | Description | Impact | Probabilité |
|---|------|--------|-------------|--------|:-----------:|
| 1 | {{RISQUE_1_CODE}} | {{RISQUE_1_NOM}} | {{RISQUE_1_DESC}} | {{RISQUE_1_IMPACT}} | {{RISQUE_1_PROBA}} |
| 2 | {{RISQUE_2_CODE}} | {{RISQUE_2_NOM}} | {{RISQUE_2_DESC}} | {{RISQUE_2_IMPACT}} | {{RISQUE_2_PROBA}} |
| 3 | {{RISQUE_3_CODE}} | {{RISQUE_3_NOM}} | {{RISQUE_3_DESC}} | {{RISQUE_3_IMPACT}} | {{RISQUE_3_PROBA}} |
{% if RISQUE_4_CODE %}
| 4 | {{RISQUE_4_CODE}} | {{RISQUE_4_NOM}} | {{RISQUE_4_DESC}} | {{RISQUE_4_IMPACT}} | {{RISQUE_4_PROBA}} |
{% endif %}

### Criticité

| Risque | Niveau | Action requise |
|--------|--------|----------------|
| {{RISQUE_1_CODE}} | {{RISQUE_1_NIVEAU}} | {{RISQUE_1_ACTION}} |
| {{RISQUE_2_CODE}} | {{RISQUE_2_NIVEAU}} | {{RISQUE_2_ACTION}} |
| {{RISQUE_3_CODE}} | {{RISQUE_3_NIVEAU}} | {{RISQUE_3_ACTION}} |

> **Échelle** : Impact (1-5) × Probabilité (1-5) → **Criticité** : Faible (1-4) · Moyenne (5-9) · Élevée (10-16) · Critique (17-25)

---

## 📄 Documents de référence

| Type | Document | Référence | Emplacement |
|------|----------|-----------|-------------|
| Support | {{DOC_SUPPORT_1}} | {{DOC_SUPPORT_1_REF}} | {{DOC_SUPPORT_1_EMPL}} |
| Support | {{DOC_SUPPORT_2}} | {{DOC_SUPPORT_2_REF}} | {{DOC_SUPPORT_2_EMPL}} |
{% if DOC_SUPPORT_3 %}
| Support | {{DOC_SUPPORT_3}} | {{DOC_SUPPORT_3_REF}} | {{DOC_SUPPORT_3_EMPL}} |
{% endif %}
| Enregistrement | {{DOC_ENREG_1}} | {{DOC_ENREG_1_REF}} | {{DOC_ENREG_1_EMPL}} |
| Enregistrement | {{DOC_ENREG_2}} | {{DOC_ENREG_2_REF}} | {{DOC_ENREG_2_EMPL}} |

---

## 📋 Informations générales

| Champ | Valeur |
|-------|--------|
| **Périmètre** | {{PERIMETRE}} |
| **Directions concernées** | {{DIRECTIONS}} |
| **Services concernés** | {{SERVICES}} |
| **Date d'effet** | {{DATE_EFFET}} |
| **Validité** | {{VALIDITE}} |
| **Révision** | {{REVISION}} |

---

## 🔗 Références normatives

| Texte | Référence |
|-------|-----------|
| Texte fondateur | {{TEXTE_FONDATEUR}} |
| Convention collective | {{CONVENTION_COLLECTIVE}} |
| Accord d'entreprise | {{ACCORD_ENTREPRISE}} |
| Procédure liée | {{PROCEDURE_LIEE}} |

---

## ✅ Checklist Argent

- [ ] FLASH CARD complète (objet, acteurs, délai, livrable, risque, indicateur)
- [ ] Localisation CRAIE avec amont/aval
- [ ] Logigramme Mermaid (amont → procédure → aval)
- [ ] RACI (min 4 acteurs, min 3 phases)
- [ ] Étapes détaillées (action, acteur, délai, livrable)
- [ ] Risques (min 3 avec impact + probabilité)
- [ ] Documents de référence (support + enregistrement)

---

> **Généré par Hermes Agent — PROC v1.0**  
> **DOX v6.0 — Niveau Argent**  
> **Prochaine évolution suggérée** : `/proc upgrade --niveau or`
