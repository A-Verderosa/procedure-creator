---
niveau: platine
code: PT
emoji: "💎"
finalite: "Procédure audit-ready avec gouvernance et déploiement"
couverture: 23
dox_version: "6.0"
---

# {{TITRE}}

> **Référence** : `{{REFERENCE}}`
> **Niveau** : 💎 Platine
> **Type RH** : {{TYPE_RH}}
> **Version** : {{VERSION}}
> **Date de création** : {{DATE_CREATION}}
> **Dernière mise à jour** : {{DERNIERE_MAJ}}
> **Statut** : {{STATUT}}
> **Valid DOX** : {{VALID_DOX}}

---

## 🃏 FLASH CARD — Résumé 30s

> **Objet** : {{OBJET_FLASH}}
> **Acteurs clés** : {{ACTEURS_FLASH}}
> **Déclencheur** : {{DECLENCHEUR}}
> **Délai pivot** : {{DELAI_PIVOT}} ({{DELAI_UNITE}})
> **Livrable principal** : {{LIVRABLE_PRINCIPAL}}
> **Risque majeur** : {{RISQUE_MAJEUR}}
> **KPI principal** : {{KPI_PRINCIPAL}} | Cible : {{KPI_CIBLE}}
> **Score QG** : {{SCORE_QG}}%
> **Prochaine revue** : {{PROCHAINE_REVUE}}

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

| Direction | Flux | Référence | Responsable |
|-----------|------|-----------|-------------|
| **Amont** | {{AMONT_DESC}} ({{AMONT_SERVICE}}) | {{AMONT_REF}} | {{AMONT_RESP}} |
| **Procédure** | {{PROC_DESC}} |
| **Aval** | {{AVAL_DESC}} ({{AVAL_SERVICE}}) | {{AVAL_REF}} | {{AVAL_RESP}} |

---

## 🔄 Logigramme Mermaid

```mermaid
flowchart LR
    A([{{AMONT_NOEUD}}]) -->|{{AMONT_SORTIE}}| B[{{ETAPE_1_NOEUD}}]
    B --> C{ {{DECISION_1}} }
    C -->|{{CONDITION_OK}}| D[{{ETAPE_2_NOEUD}}]
    C -->|{{CONDITION_KO}}| E[{{ETAPE_CONTINGENCE_1}}]
    E --> D
    D --> F[{{ETAPE_3_NOEUD}}]
    F --> G{ {{DECISION_2}} }
    G -->|{{CONDITION_2_OK}}| H[{{ETAPE_4_NOEUD}}]
    G -->|{{CONDITION_2_KO}}| I[{{ETAPE_CONTINGENCE_2}}]
    I --> H
    H --> J[{{ETAPE_5_NOEUD}}]
    J --> K([{{AVAL_NOEUD}}])

    style A fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style B fill:#fff3e0,stroke:#f57c00
    style C fill:#fce4ec,stroke:#d32f2f,stroke-width:2px
    style D fill:#fff3e0,stroke:#f57c00
    style E fill:#f3e5f5,stroke:#7b1fa2
    style F fill:#fff3e0,stroke:#f57c00
    style G fill:#fce4ec,stroke:#d32f2f,stroke-width:2px
    style H fill:#fff3e0,stroke:#f57c00
    style I fill:#f3e5f5,stroke:#7b1fa2
    style J fill:#fff3e0,stroke:#f57c00
    style K fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
```

### Légende

| Symbole | Signification |
|---------|---------------|
| 🔵 🟢 | Entrée / Sortie du processus |
| 🟠 | Étape standard |
| 🔴 | Décision / Point de contrôle |
| 🟣 | Contingence / Circuit exceptionnel |

---

## 👥 RACI — Matrice des responsabilités

### Acteurs

| # | Rôle | Direction/Service | Rôle dans la procédure | Suppléance |
|---|------|-------------------|----------------------|------------|
| 1 | {{ACTEUR_1_ROLE}} | {{ACTEUR_1_DIR}} | {{ACTEUR_1_DESC}} | {{ACTEUR_1_SUPP}} |
| 2 | {{ACTEUR_2_ROLE}} | {{ACTEUR_2_DIR}} | {{ACTEUR_2_DESC}} | {{ACTEUR_2_SUPP}} |
| 3 | {{ACTEUR_3_ROLE}} | {{ACTEUR_3_DIR}} | {{ACTEUR_3_DESC}} | {{ACTEUR_3_SUPP}} |
| 4 | {{ACTEUR_4_ROLE}} | {{ACTEUR_4_DIR}} | {{ACTEUR_4_DESC}} | {{ACTEUR_4_SUPP}} |
| 5 | {{ACTEUR_5_ROLE}} | {{ACTEUR_5_DIR}} | {{ACTEUR_5_DESC}} | {{ACTEUR_5_SUPP}} |
| 6 | {{ACTEUR_6_ROLE}} | {{ACTEUR_6_DIR}} | {{ACTEUR_6_DESC}} | {{ACTEUR_6_SUPP}} |
| 7 | {{ACTEUR_7_ROLE}} | {{ACTEUR_7_DIR}} | {{ACTEUR_7_DESC}} | {{ACTEUR_7_SUPP}} |
| 8 | {{ACTEUR_8_ROLE}} | {{ACTEUR_8_DIR}} | {{ACTEUR_8_DESC}} | {{ACTEUR_8_SUPP}} |

### Matrice RACI

| Phase / Activité | {{ACTEUR_1_ROLE}} | {{ACTEUR_2_ROLE}} | {{ACTEUR_3_ROLE}} | {{ACTEUR_4_ROLE}} | {{ACTEUR_5_ROLE}} | {{ACTEUR_6_ROLE}} | {{ACTEUR_7_ROLE}} | {{ACTEUR_8_ROLE}} |
|-----------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| {{PHASE_1}} | {{RACI_1_1}} | {{RACI_1_2}} | {{RACI_1_3}} | {{RACI_1_4}} | {{RACI_1_5}} | {{RACI_1_6}} | {{RACI_1_7}} | {{RACI_1_8}} |
| {{PHASE_2}} | {{RACI_2_1}} | {{RACI_2_2}} | {{RACI_2_3}} | {{RACI_2_4}} | {{RACI_2_5}} | {{RACI_2_6}} | {{RACI_2_7}} | {{RACI_2_8}} |
| {{PHASE_3}} | {{RACI_3_1}} | {{RACI_3_2}} | {{RACI_3_3}} | {{RACI_3_4}} | {{RACI_3_5}} | {{RACI_3_6}} | {{RACI_3_7}} | {{RACI_3_8}} |
| {{PHASE_4}} | {{RACI_4_1}} | {{RACI_4_2}} | {{RACI_4_3}} | {{RACI_4_4}} | {{RACI_4_5}} | {{RACI_4_6}} | {{RACI_4_7}} | {{RACI_4_8}} |
| {{PHASE_5}} | {{RACI_5_1}} | {{RACI_5_2}} | {{RACI_5_3}} | {{RACI_5_4}} | {{RACI_5_5}} | {{RACI_5_6}} | {{RACI_5_7}} | {{RACI_5_8}} |
| {{PHASE_6}} | {{RACI_6_1}} | {{RACI_6_2}} | {{RACI_6_3}} | {{RACI_6_4}} | {{RACI_6_5}} | {{RACI_6_6}} | {{RACI_6_7}} | {{RACI_6_8}} |

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
| **Risque associé** | {{ETAPE_1_RISQUE}} |

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
| **Risque associé** | {{ETAPE_2_RISQUE}} |

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
| **Risque associé** | {{ETAPE_3_RISQUE}} |

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
| **Risque associé** | {{ETAPE_4_RISQUE}} |

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
| **Risque associé** | {{ETAPE_5_RISQUE}} |

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
| **Risque associé** | {{ETAPE_6_RISQUE}} |

---

## ⚠️ Risques identifiés (liés SBRX)

| # | Code SBRX | Risque | Description | Cause | Impact | Probabilité | Criticité | Mitigation | Pilote |
|---|-----------|--------|-------------|-------|--------|:-----------:|:---------:|------------|--------|
| 1 | {{RISQUE_1_CODE}} | {{RISQUE_1_NOM}} | {{RISQUE_1_DESC}} | {{RISQUE_1_CAUSE}} | {{RISQUE_1_IMPACT}} | {{RISQUE_1_PROBA}} | {{RISQUE_1_CRIT}} | {{RISQUE_1_MITIG}} | {{RISQUE_1_PILOTE}} |
| 2 | {{RISQUE_2_CODE}} | {{RISQUE_2_NOM}} | {{RISQUE_2_DESC}} | {{RISQUE_2_CAUSE}} | {{RISQUE_2_IMPACT}} | {{RISQUE_2_PROBA}} | {{RISQUE_2_CRIT}} | {{RISQUE_2_MITIG}} | {{RISQUE_2_PILOTE}} |
| 3 | {{RISQUE_3_CODE}} | {{RISQUE_3_NOM}} | {{RISQUE_3_DESC}} | {{RISQUE_3_CAUSE}} | {{RISQUE_3_IMPACT}} | {{RISQUE_3_PROBA}} | {{RISQUE_3_CRIT}} | {{RISQUE_3_MITIG}} | {{RISQUE_3_PILOTE}} |
| 4 | {{RISQUE_4_CODE}} | {{RISQUE_4_NOM}} | {{RISQUE_4_DESC}} | {{RISQUE_4_CAUSE}} | {{RISQUE_4_IMPACT}} | {{RISQUE_4_PROBA}} | {{RISQUE_4_CRIT}} | {{RISQUE_4_MITIG}} | {{RISQUE_4_PILOTE}} |
| 5 | {{RISQUE_5_CODE}} | {{RISQUE_5_NOM}} | {{RISQUE_5_DESC}} | {{RISQUE_5_CAUSE}} | {{RISQUE_5_IMPACT}} | {{RISQUE_5_PROBA}} | {{RISQUE_5_CRIT}} | {{RISQUE_5_MITIG}} | {{RISQUE_5_PILOTE}} |
| 6 | {{RISQUE_6_CODE}} | {{RISQUE_6_NOM}} | {{RISQUE_6_DESC}} | {{RISQUE_6_CAUSE}} | {{RISQUE_6_IMPACT}} | {{RISQUE_6_PROBA}} | {{RISQUE_6_CRIT}} | {{RISQUE_6_MITIG}} | {{RISQUE_6_PILOTE}} |

> **Échelle** : Impact (1-5) × Probabilité (1-5) → **Criticité** : Faible (1-4) · Moyenne (5-9) · Élevée (10-16) · Critique (17-25)

---

## 📄 Documents support (liés GED)

| Document | Référence | Version | Émetteur | Emplacement GED | Type |
|----------|-----------|:-------:|----------|-----------------|------|
| {{DOC_SUPPORT_1}} | {{DOC_SUPPORT_1_REF}} | {{DOC_SUPPORT_1_VERS}} | {{DOC_SUPPORT_1_EMET}} | {{DOC_SUPPORT_1_GED}} | {{DOC_SUPPORT_1_TYPE}} |
| {{DOC_SUPPORT_2}} | {{DOC_SUPPORT_2_REF}} | {{DOC_SUPPORT_2_VERS}} | {{DOC_SUPPORT_2_EMET}} | {{DOC_SUPPORT_2_GED}} | {{DOC_SUPPORT_2_TYPE}} |
| {{DOC_SUPPORT_3}} | {{DOC_SUPPORT_3_REF}} | {{DOC_SUPPORT_3_VERS}} | {{DOC_SUPPORT_3_EMET}} | {{DOC_SUPPORT_3_GED}} | {{DOC_SUPPORT_3_TYPE}} |
| {{DOC_SUPPORT_4}} | {{DOC_SUPPORT_4_REF}} | {{DOC_SUPPORT_4_VERS}} | {{DOC_SUPPORT_4_EMET}} | {{DOC_SUPPORT_4_GED}} | {{DOC_SUPPORT_4_TYPE}} |
| {{DOC_SUPPORT_5}} | {{DOC_SUPPORT_5_REF}} | {{DOC_SUPPORT_5_VERS}} | {{DOC_SUPPORT_5_EMET}} | {{DOC_SUPPORT_5_GED}} | {{DOC_SUPPORT_5_TYPE}} |

## 📋 Documents d'enregistrement

| Document | Référence | Supports | Durée conservation | Responsable | Emplacement GED |
|----------|-----------|----------|:------------------:|-------------|-----------------|
| {{DOC_ENREG_1}} | {{DOC_ENREG_1_REF}} | {{DOC_ENREG_1_SUPP}} | {{DOC_ENREG_1_DUREE}} | {{DOC_ENREG_1_RESP}} | {{DOC_ENREG_1_GED}} |
| {{DOC_ENREG_2}} | {{DOC_ENREG_2_REF}} | {{DOC_ENREG_2_SUPP}} | {{DOC_ENREG_2_DUREE}} | {{DOC_ENREG_2_RESP}} | {{DOC_ENREG_2_GED}} |
| {{DOC_ENREG_3}} | {{DOC_ENREG_3_REF}} | {{DOC_ENREG_3_SUPP}} | {{DOC_ENREG_3_DUREE}} | {{DOC_ENREG_3_RESP}} | {{DOC_ENREG_3_GED}} |
| {{DOC_ENREG_4}} | {{DOC_ENREG_4_REF}} | {{DOC_ENREG_4_SUPP}} | {{DOC_ENREG_4_DUREE}} | {{DOC_ENREG_4_RESP}} | {{DOC_ENREG_4_GED}} |

---

## 📊 Indicateurs de performance (KPI)

| # | Indicateur | Cible | Seuil alerte | Fréquence mesure | Formule | Responsable |
|---|------------|:-----:|:------------:|:----------------:|---------|-------------|
| 1 | {{KPI_1_NOM}} | {{KPI_1_CIBLE}} | {{KPI_1_ALERTE}} | {{KPI_1_FREQ}} | {{KPI_1_FORMULE}} | {{KPI_1_RESP}} |
| 2 | {{KPI_2_NOM}} | {{KPI_2_CIBLE}} | {{KPI_2_ALERTE}} | {{KPI_2_FREQ}} | {{KPI_2_FORMULE}} | {{KPI_2_RESP}} |
| 3 | {{KPI_3_NOM}} | {{KPI_3_CIBLE}} | {{KPI_3_ALERTE}} | {{KPI_3_FREQ}} | {{KPI_3_FORMULE}} | {{KPI_3_RESP}} |
| 4 | {{KPI_4_NOM}} | {{KPI_4_CIBLE}} | {{KPI_4_ALERTE}} | {{KPI_4_FREQ}} | {{KPI_4_FORMULE}} | {{KPI_4_RESP}} |
| 5 | {{KPI_5_NOM}} | {{KPI_5_CIBLE}} | {{KPI_5_ALERTE}} | {{KPI_5_FREQ}} | {{KPI_5_FORMULE}} | {{KPI_5_RESP}} |

### Tableau de bord

| KPI | Valeur actuelle | Cible | Tendance | Statut | Action si alerte |
|-----|:---------------:|:-----:|:--------:|:------:|------------------|
| {{KPI_1_NOM}} | {{KPI_1_VALEUR}} | {{KPI_1_CIBLE}} | {{KPI_1_TENDANCE}} | {{KPI_1_STATUT}} | {{KPI_1_ACTION}} |
| {{KPI_2_NOM}} | {{KPI_2_VALEUR}} | {{KPI_2_CIBLE}} | {{KPI_2_TENDANCE}} | {{KPI_2_STATUT}} | {{KPI_2_ACTION}} |
| {{KPI_3_NOM}} | {{KPI_3_VALEUR}} | {{KPI_3_CIBLE}} | {{KPI_3_TENDANCE}} | {{KPI_3_STATUT}} | {{KPI_3_ACTION}} |
| {{KPI_4_NOM}} | {{KPI_4_VALEUR}} | {{KPI_4_CIBLE}} | {{KPI_4_TENDANCE}} | {{KPI_4_STATUT}} | {{KPI_4_ACTION}} |
| {{KPI_5_NOM}} | {{KPI_5_VALEUR}} | {{KPI_5_CIBLE}} | {{KPI_5_TENDANCE}} | {{KPI_5_STATUT}} | {{KPI_5_ACTION}} |

---

## ✅ Quality Gate Checklist

### G1-G7B : Structurels

| # | Quality Gate | Statut | Commentaire |
|---|-------------|:------:|-------------|
| G1 | Titre et référence présents (EVP-xxx, PRH-xxx) | {{QG_G1}} | {{QG_G1_CMT}} |
| G2 | FLASH CARD — Résumé exécutif 30s complet | {{QG_G2}} | {{QG_G2_CMT}} |
| G3 | Localisation CRAIE explicite | {{QG_G3}} | {{QG_G3_CMT}} |
| G4 | Logigramme Mermaid (amont → procédure → aval) | {{QG_G4}} | {{QG_G4_CMT}} |
| G5 | RACI complet (min 4 acteurs, min 3 phases) | {{QG_G5}} | {{QG_G5_CMT}} |
| G6 | Sections étapes détaillées (action, acteur, délai, livrable) | {{QG_G6}} | {{QG_G6_CMT}} |
| G7 | Risques identifiés (min 3 documentés) | {{QG_G7}} | {{QG_G7_CMT}} |
| G7B | Documents support et enregistrement listés | {{QG_G7B}} | {{QG_G7B_CMT}} |

### G8-G11 : Package / Modularité

| # | Quality Gate | Statut | Commentaire |
|---|-------------|:------:|-------------|
| G8 | Synthèse de modularité présente | {{QG_G8}} | {{QG_G8_CMT}} |
| G9 | Tableau comparatif des niveaux | {{QG_G9}} | {{QG_G9_CMT}} |
| G10 | Couverture cumulative validée | {{QG_G10}} | {{QG_G10_CMT}} |
| G11 | Scorecard de niveau présente | {{QG_G11}} | {{QG_G11_CMT}} |

### G12-G21 : Cycle de vie

| # | Quality Gate | Statut | Commentaire |
|---|-------------|:------:|-------------|
| G14 | Dernière revue renseignée | {{QG_G14}} | {{QG_G14_CMT}} |
| G15 | Périodicité définie | {{QG_G15}} | {{QG_G15_CMT}} |
| G16 | Prochaine revue cohérente | {{QG_G16}} | {{QG_G16_CMT}} |
| G21 | QG Global 🟢 OK | {{QG_G21}} | {{QG_G21_CMT}} |

---

## 🎚️ Scorecard DOX v6.0

### Critères d'évaluation

| # | Critère | Poids | Score max | Score obtenu | Commentaire |
|---|---------|:-----:|:---------:|:------------:|-------------|
| 1 | Complétude des sections | 20 | 20 | {{SCORE_1}} | {{SCORE_1_CMT}} |
| 2 | Qualité du FLASH CARD | 10 | 10 | {{SCORE_2}} | {{SCORE_2_CMT}} |
| 3 | Logigramme et flux | 10 | 10 | {{SCORE_3}} | {{SCORE_3_CMT}} |
| 4 | RACI et responsabilités | 10 | 10 | {{SCORE_4}} | {{SCORE_4_CMT}} |
| 5 | Étapes et livrables | 15 | 15 | {{SCORE_5}} | {{SCORE_5_CMT}} |
| 6 | Risques et mitigations | 10 | 10 | {{SCORE_6}} | {{SCORE_6_CMT}} |
| 7 | Documents et traçabilité | 10 | 10 | {{SCORE_7}} | {{SCORE_7_CMT}} |
| 8 | KPI et tableau de bord | 10 | 10 | {{SCORE_8}} | {{SCORE_8_CMT}} |
| 9 | Cycle de vie et revue | 5 | 5 | {{SCORE_9}} | {{SCORE_9_CMT}} |

| Total | Moyenne |
|:-----:|:-------:|
| **{{SCORE_TOTAL}} / {{SCORE_MAX}}** | **{{SCORE_POURCENTAGE}}%** |

**Trophée** : {{TROPHEE}}

| Seuil | Niveau |
|:-----:|--------|
| ≥ 90% | 🥇 Or |
| ≥ 80% | 🥈 Argent |
| ≥ 70% | 🥉 Bronze |
| < 70% | ❌ Non classé |

---

## 🔄 Cycle de vie

| Champ | Valeur |
|-------|--------|
| **Dernière revue** | {{DERNIERE_REVUE}} |
| **Reviseur** | {{REVISEUR}} |
| **Périodicité** | {{PERIODICITE}} |
| **Prochaine revue calculée** | {{PROCHAINE_REVUE_CALC}} |
| **Prochaine revue prévue** | {{PROCHAINE_REVUE_PREVUE}} |
| **Statut révision** | {{STATUT_REVISION}} |
| **Date de création** | {{DATE_CREATION}} |
| **Validité** | {{VALIDITE}} |

---

## 📊 Tableau de synthèse de modularité

| Niveau | Nb sections | Nb QG applicables | Score requis | Présent dans cette proc. |
|--------|:-----------:|:-----------------:|:------------:|:------------------------:|
| 🥉 Bronze | 11 | G1-G3 | ≥ 40% |
| 🥈 Argent | 14 | G1-G7B | ≥ 55% |
| 🥇 Or | 17 | G1-G7B | ≥ 70% |
| 💎 Platine | 23 | G1-G11 + G14-G16 | ≥ 80% | 🟢 |
| 💎 Ultra | 31 | G1-G21 | ≥ 85% |
| 🔮 Mythique | 31+9 | G1-G21 | ≥ 90% |
| 👹 Akuma | Diagnostic | G21 | Dynamique |

---

## 🏗️ Gouvernance et déploiement

| Aspect | Description |
|--------|-------------|
| **Rédacteur** | {{REDACTEUR}} |
| **Vérificateur** | {{VERIFICATEUR}} |
| **Approbateur** | {{APPROBATEUR}} |
| **Diffusion** | {{DIFFUSION}} |
| **Formation nécessaire** | {{FORMATION}} |
| **Date de déploiement** | {{DATE_DEPLOIEMENT}} |
| **Plan de communication** | {{PLAN_COMM}} |

---

## 🔗 Références normatives

| Texte | Référence | Date | Article(s) |
|-------|-----------|:----:|:----------:|
| Texte fondateur | {{TEXTE_FONDATEUR}} | {{TEXTE_DATE}} | {{TEXTE_ARTICLES}} |
| Convention collective | {{CONVENTION_COLLECTIVE}} | {{CONVENTION_DATE}} | {{CONVENTION_ARTICLES}} |
| Accord d'entreprise | {{ACCORD_ENTREPRISE}} | {{ACCORD_DATE}} | {{ACCORD_ARTICLES}} |
| Décision unilatérale | {{DECISION_UNILATERALE}} | {{DECISION_DATE}} | {{DECISION_ARTICLES}} |
| Procédure liée | {{PROCEDURE_LIEE}} | {{PROCEDURE_DATE}} | {{PROCEDURE_REF}} |
| Exigence GC | {{EXIGENCE_GC}} | {{EXIGENCE_GC_REF}} | |

---

## ✅ Checklist Platine

- [ ] FLASH CARD complète avec score QG
- [ ] Localisation CRAIE avec amont/aval + responsables
- [ ] Logigramme Mermaid avec décisions et contingences
- [ ] RACI complet (min 8 acteurs, min 6 phases) + suppléances
- [ ] Étapes détaillées avec risque associé par étape
- [ ] Risques SBRX (min 6) avec pilote et mitigation
- [ ] Documents support GED (min 5) + enregistrement (min 4)
- [ ] KPI (min 5) avec formule, tendance, action si alerte
- [ ] Quality Gate Checklist (G1-G11 + G14-G16 + G21)
- [ ] Scorecard DOX avec scores pondérés et trophée
- [ ] Cycle de vie verrouillé (dernière revue, périodicité, prochaine)
- [ ] Tableau de synthèse de modularité
- [ ] Gouvernance et déploiement documentés

---

> **Généré par Hermes Agent — PROC v1.0**  
> **DOX v6.0 — Niveau Platine**  
> **Prochaine évolution suggérée** : `/proc upgrade --niveau ultra`
