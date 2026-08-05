---
niveau: or
code: OR
emoji: "🥇"
finalite: "Procédure professionnelle stabilisée"
couverture: 17
dox_version: "6.0"
---

# {{TITRE}}

> **Référence** : `{{REFERENCE}}`
> **Niveau** : 🥇 Or
> **Type RH** : {{TYPE_RH}}
> **Version** : {{VERSION}}
> **Date de création** : {{DATE_CREATION}}
> **Dernière mise à jour** : {{DERNIERE_MAJ}}
> **Statut** : {{STATUT}}

---

## 🃏 FLASH CARD — Résumé 30s

> **Objet** : {{OBJET_FLASH}}
> **Acteurs clés** : {{ACTEURS_FLASH}}
> **Déclencheur** : {{DECLENCHEUR}}
> **Délai pivot** : {{DELAI_PIVOT}} ({{DELAI_UNITE}})
> **Livrable principal** : {{LIVRABLE_PRINCIPAL}}
> **Risque majeur** : {{RISQUE_MAJEUR}}
> **KPI principal** : {{KPI_PRINCIPAL}}
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

| Direction | Flux | Référence |
|-----------|------|-----------|
| **Amont** | {{AMONT_DESC}} ({{AMONT_SERVICE}}) | {{AMONT_REF}} |
| **Procédure** | {{PROC_DESC}} |
| **Aval** | {{AVAL_DESC}} ({{AVAL_SERVICE}}) | {{AVAL_REF}} |

---

## 🔄 Logigramme Mermaid

```mermaid
flowchart LR
    A([{{AMONT_NOEUD}}]) -->|{{AMONT_SORTIE}}| B[{{ETAPE_1_NOEUD}}]
    B --> C{{{ETAPE_2_NOEUD}}}
    C -->|{{CONDITION_OK}}| D[{{ETAPE_3_NOEUD}}]
    C -->|{{CONDITION_KO}}| E[{{ETAPE_CONTINGENCE}}]
    E --> D
    D --> F[{{ETAPE_4_NOEUD}}]
    F --> G([{{AVAL_NOEUD}}])

    style A fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style B fill:#fff3e0,stroke:#f57c00
    style C fill:#fce4ec,stroke:#d32f2f
    style D fill:#fff3e0,stroke:#f57c00
    style E fill:#f3e5f5,stroke:#7b1fa2
    style F fill:#fff3e0,stroke:#f57c00
    style G fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
```

### Légende

| Couleur | Signification |
|---------|---------------|
| 🔵 Bleu | Amont / Entrée |
| 🟠 Orange | Étapes standards |
| 🔴 Rouge | Décision / Point de contrôle |
| 🟣 Violet | Contingence / Exception |
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
| 5 | {{ACTEUR_5_ROLE}} | {{ACTEUR_5_DIR}} | {{ACTEUR_5_DESC}} |
| 6 | {{ACTEUR_6_ROLE}} | {{ACTEUR_6_DIR}} | {{ACTEUR_6_DESC}} |
{% if ACTEUR_7 %}
| 7 | {{ACTEUR_7_ROLE}} | {{ACTEUR_7_DIR}} | {{ACTEUR_7_DESC}} |
{% endif %}

### Matrice RACI

| Phase / Activité | {{ACTEUR_1_ROLE}} | {{ACTEUR_2_ROLE}} | {{ACTEUR_3_ROLE}} | {{ACTEUR_4_ROLE}} | {{ACTEUR_5_ROLE}} | {{ACTEUR_6_ROLE}} |
|-----------------|:---:|:---:|:---:|:---:|:---:|:---:|
| {{PHASE_1}} | {{RACI_1_1}} | {{RACI_1_2}} | {{RACI_1_3}} | {{RACI_1_4}} | {{RACI_1_5}} | {{RACI_1_6}} |
| {{PHASE_2}} | {{RACI_2_1}} | {{RACI_2_2}} | {{RACI_2_3}} | {{RACI_2_4}} | {{RACI_2_5}} | {{RACI_2_6}} |
| {{PHASE_3}} | {{RACI_3_1}} | {{RACI_3_2}} | {{RACI_3_3}} | {{RACI_3_4}} | {{RACI_3_5}} | {{RACI_3_6}} |
| {{PHASE_4}} | {{RACI_4_1}} | {{RACI_4_2}} | {{RACI_4_3}} | {{RACI_4_4}} | {{RACI_4_5}} | {{RACI_4_6}} |
| {{PHASE_5}} | {{RACI_5_1}} | {{RACI_5_2}} | {{RACI_5_3}} | {{RACI_5_4}} | {{RACI_5_5}} | {{RACI_5_6}} |
{% if PHASE_6 %}
| {{PHASE_6}} | {{RACI_6_1}} | {{RACI_6_2}} | {{RACI_6_3}} | {{RACI_6_4}} | {{RACI_6_5}} | {{RACI_6_6}} |
{% endif %}

> **R** = Réalise · **A** = Approuve · **C** = Consulté · **I** = Informé · **S** = Support

---

## 📝 Étapes détaillées

### Étape 1 : {{ETAPE_1_TITRE}}

| Champ | Valeur |
|-------|--------|
| **Action** | {{ETAPE_1_ACTION}} |
| **Acteur** | {{ETAPE_1_ACTEUR}} |
| **RACI** | {{ETAPE_1_RACI}} |
| **Délai** | {{ETAPE_1_DELAI}} |
| **Livrable** | {{ETAPE_1_LIVRABLE}} |
| **Outil / Système** | {{ETAPE_1_OUTIL}} |
| **Condition de passage** | {{ETAPE_1_CONDITION}} |
| **Point de contrôle** | {{ETAPE_1_CONTROLE}} |

### Étape 2 : {{ETAPE_2_TITRE}}

| Champ | Valeur |
|-------|--------|
| **Action** | {{ETAPE_2_ACTION}} |
| **Acteur** | {{ETAPE_2_ACTEUR}} |
| **RACI** | {{ETAPE_2_RACI}} |
| **Délai** | {{ETAPE_2_DELAI}} |
| **Livrable** | {{ETAPE_2_LIVRABLE}} |
| **Outil / Système** | {{ETAPE_2_OUTIL}} |
| **Condition de passage** | {{ETAPE_2_CONDITION}} |
| **Point de contrôle** | {{ETAPE_2_CONTROLE}} |

### Étape 3 : {{ETAPE_3_TITRE}}

| Champ | Valeur |
|-------|--------|
| **Action** | {{ETAPE_3_ACTION}} |
| **Acteur** | {{ETAPE_3_ACTEUR}} |
| **RACI** | {{ETAPE_3_RACI}} |
| **Délai** | {{ETAPE_3_DELAI}} |
| **Livrable** | {{ETAPE_3_LIVRABLE}} |
| **Outil / Système** | {{ETAPE_3_OUTIL}} |
| **Condition de passage** | {{ETAPE_3_CONDITION}} |
| **Point de contrôle** | {{ETAPE_3_CONTROLE}} |

### Étape 4 : {{ETAPE_4_TITRE}}

| Champ | Valeur |
|-------|--------|
| **Action** | {{ETAPE_4_ACTION}} |
| **Acteur** | {{ETAPE_4_ACTEUR}} |
| **RACI** | {{ETAPE_4_RACI}} |
| **Délai** | {{ETAPE_4_DELAI}} |
| **Livrable** | {{ETAPE_4_LIVRABLE}} |
| **Outil / Système** | {{ETAPE_4_OUTIL}} |
| **Condition de passage** | {{ETAPE_4_CONDITION}} |
| **Point de contrôle** | {{ETAPE_4_CONTROLE}} |

### Étape 5 : {{ETAPE_5_TITRE}}

| Champ | Valeur |
|-------|--------|
| **Action** | {{ETAPE_5_ACTION}} |
| **Acteur** | {{ETAPE_5_ACTEUR}} |
| **RACI** | {{ETAPE_5_RACI}} |
| **Délai** | {{ETAPE_5_DELAI}} |
| **Livrable** | {{ETAPE_5_LIVRABLE}} |
| **Outil / Système** | {{ETAPE_5_OUTIL}} |
| **Condition de passage** | {{ETAPE_5_CONDITION}} |
| **Point de contrôle** | {{ETAPE_5_CONTROLE}} |

### Étape 6 : {{ETAPE_6_TITRE}}

| Champ | Valeur |
|-------|--------|
| **Action** | {{ETAPE_6_ACTION}} |
| **Acteur** | {{ETAPE_6_ACTEUR}} |
| **RACI** | {{ETAPE_6_RACI}} |
| **Délai** | {{ETAPE_6_DELAI}} |
| **Livrable** | {{ETAPE_6_LIVRABLE}} |
| **Outil / Système** | {{ETAPE_6_OUTIL}} |
| **Condition de passage** | {{ETAPE_6_CONDITION}} |
| **Point de contrôle** | {{ETAPE_6_CONTROLE}} |

---

## ⚠️ Risques identifiés

| # | Code | Risque | Description | Cause | Impact | Probabilité | Criticité | Mitigation |
|---|------|--------|-------------|-------|--------|:-----------:|:---------:|------------|
| 1 | {{RISQUE_1_CODE}} | {{RISQUE_1_NOM}} | {{RISQUE_1_DESC}} | {{RISQUE_1_CAUSE}} | {{RISQUE_1_IMPACT}} | {{RISQUE_1_PROBA}} | {{RISQUE_1_CRIT}} | {{RISQUE_1_MITIG}} |
| 2 | {{RISQUE_2_CODE}} | {{RISQUE_2_NOM}} | {{RISQUE_2_DESC}} | {{RISQUE_2_CAUSE}} | {{RISQUE_2_IMPACT}} | {{RISQUE_2_PROBA}} | {{RISQUE_2_CRIT}} | {{RISQUE_2_MITIG}} |
| 3 | {{RISQUE_3_CODE}} | {{RISQUE_3_NOM}} | {{RISQUE_3_DESC}} | {{RISQUE_3_CAUSE}} | {{RISQUE_3_IMPACT}} | {{RISQUE_3_PROBA}} | {{RISQUE_3_CRIT}} | {{RISQUE_3_MITIG}} |
| 4 | {{RISQUE_4_CODE}} | {{RISQUE_4_NOM}} | {{RISQUE_4_DESC}} | {{RISQUE_4_CAUSE}} | {{RISQUE_4_IMPACT}} | {{RISQUE_4_PROBA}} | {{RISQUE_4_CRIT}} | {{RISQUE_4_MITIG}} |
| 5 | {{RISQUE_5_CODE}} | {{RISQUE_5_NOM}} | {{RISQUE_5_DESC}} | {{RISQUE_5_CAUSE}} | {{RISQUE_5_IMPACT}} | {{RISQUE_5_PROBA}} | {{RISQUE_5_CRIT}} | {{RISQUE_5_MITIG}} |

> **Échelle** : Impact (1-5) × Probabilité (1-5) → **Criticité** : Faible (1-4) · Moyenne (5-9) · Élevée (10-16) · Critique (17-25)

---

## 📄 Documents support

| Document | Référence | Version | Émetteur | Emplacement GED |
|----------|-----------|:-------:|----------|-----------------|
| {{DOC_SUPPORT_1}} | {{DOC_SUPPORT_1_REF}} | {{DOC_SUPPORT_1_VERS}} | {{DOC_SUPPORT_1_EMET}} | {{DOC_SUPPORT_1_GED}} |
| {{DOC_SUPPORT_2}} | {{DOC_SUPPORT_2_REF}} | {{DOC_SUPPORT_2_VERS}} | {{DOC_SUPPORT_2_EMET}} | {{DOC_SUPPORT_2_GED}} |
| {{DOC_SUPPORT_3}} | {{DOC_SUPPORT_3_REF}} | {{DOC_SUPPORT_3_VERS}} | {{DOC_SUPPORT_3_EMET}} | {{DOC_SUPPORT_3_GED}} |
| {{DOC_SUPPORT_4}} | {{DOC_SUPPORT_4_REF}} | {{DOC_SUPPORT_4_VERS}} | {{DOC_SUPPORT_4_EMET}} | {{DOC_SUPPORT_4_GED}} |

## 📋 Documents d'enregistrement

| Document | Référence | Supports | Durée conservation | Emplacement GED |
|----------|-----------|----------|:------------------:|-----------------|
| {{DOC_ENREG_1}} | {{DOC_ENREG_1_REF}} | {{DOC_ENREG_1_SUPP}} | {{DOC_ENREG_1_DUREE}} | {{DOC_ENREG_1_GED}} |
| {{DOC_ENREG_2}} | {{DOC_ENREG_2_REF}} | {{DOC_ENREG_2_SUPP}} | {{DOC_ENREG_2_DUREE}} | {{DOC_ENREG_2_GED}} |
| {{DOC_ENREG_3}} | {{DOC_ENREG_3_REF}} | {{DOC_ENREG_3_SUPP}} | {{DOC_ENREG_3_DUREE}} | {{DOC_ENREG_3_GED}} |

---

## 📊 Indicateurs de performance (KPI)

| # | Indicateur | Cible | Seuil alerte | Fréquence mesure | Responsable |
|---|------------|:-----:|:------------:|:----------------:|-------------|
| 1 | {{KPI_1_NOM}} | {{KPI_1_CIBLE}} | {{KPI_1_ALERTE}} | {{KPI_1_FREQ}} | {{KPI_1_RESP}} |
| 2 | {{KPI_2_NOM}} | {{KPI_2_CIBLE}} | {{KPI_2_ALERTE}} | {{KPI_2_FREQ}} | {{KPI_2_RESP}} |
| 3 | {{KPI_3_NOM}} | {{KPI_3_CIBLE}} | {{KPI_3_ALERTE}} | {{KPI_3_FREQ}} | {{KPI_3_RESP}} |
{% if KPI_4_NOM %}
| 4 | {{KPI_4_NOM}} | {{KPI_4_CIBLE}} | {{KPI_4_ALERTE}} | {{KPI_4_FREQ}} | {{KPI_4_RESP}} |
{% endif %}

### Tableau de bord simple

| KPI | Valeur actuelle | Tendance | Statut |
|-----|:---------------:|:--------:|:------:|
| {{KPI_1_NOM}} | {{KPI_1_VALEUR}} | {{KPI_1_TENDANCE}} | {{KPI_1_STATUT}} |
| {{KPI_2_NOM}} | {{KPI_2_VALEUR}} | {{KPI_2_TENDANCE}} | {{KPI_2_STATUT}} |
| {{KPI_3_NOM}} | {{KPI_3_VALEUR}} | {{KPI_3_TENDANCE}} | {{KPI_3_STATUT}} |

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
| **Rédacteur** | {{REDACTEUR}} |
| **Vérificateur** | {{VERIFICATEUR}} |
| **Approbateur** | {{APPROBATEUR}} |

---

## 🔗 Références normatives

| Texte | Référence | Date |
|-------|-----------|:----:|
| Texte fondateur | {{TEXTE_FONDATEUR}} | {{TEXTE_DATE}} |
| Convention collective | {{CONVENTION_COLLECTIVE}} | {{CONVENTION_DATE}} |
| Accord d'entreprise | {{ACCORD_ENTREPRISE}} | {{ACCORD_DATE}} |
| Décision unilatérale | {{DECISION_UNILATERALE}} | {{DECISION_DATE}} |
| Procédure liée | {{PROCEDURE_LIEE}} | {{PROCEDURE_LIEE_REF}} |

---

## ✅ Checklist Or

- [ ] FLASH CARD complète (8 éléments)
- [ ] Localisation CRAIE avec amont/aval référencés
- [ ] Logigramme Mermaid avec décision et contingence
- [ ] RACI complet (min 6 acteurs, min 5 phases)
- [ ] Étapes détaillées (tous les champs)
- [ ] Risques (min 5 avec cause, impact, probabilité, criticité, mitigation)
- [ ] Documents support (min 4) listés avec références GED
- [ ] Documents d'enregistrement (min 3) avec durée de conservation
- [ ] KPI (min 3) avec cible, seuil alerte, fréquence
- [ ] Tableau de bord simple avec tendance
- [ ] Références normatives complètes

---

> **Généré par Hermes Agent — PROC v1.0**  
> **DOX v6.0 — Niveau Or**  
> **Prochaine évolution suggérée** : `/proc upgrade --niveau platine`
