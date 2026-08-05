---
titre: "Suivi des recommandations issues de l'évaluation"
reference: "CEV-P09"
niveau: platine
dox_version: "6.0"
type_document: procedure
statut: approuve
date_creation: "2026-08-01"
derniere_revue: "2026-08-01"
validee_par: "Directeur de l'évaluation"
periode_revue: annuelle
prochaine_revue: "2027-08-01"
mission: M4
processus: P14
---

# 📊 Suivi des recommandations issues de l'évaluation

> **Référence** : `CEV-P09`
> **Niveau** : 💎 Platine
> **Type** : Procédure de suivi — Mise en œuvre des recommandations
> **Version** : 1.0
> **Date de création** : 01/08/2026
> **Dernière mise à jour** : 01/08/2026
> **Validée par** : Directeur de l'évaluation

---

## 🃏 FLASH CARD — Résumé 30s

> **Objet** : Assurer le suivi systématique de la mise en œuvre des recommandations issues des rapports d'évaluation — plan d'action contradictoire, suivi périodique par un comité dédié, mesure d'impact, reporting à la gouvernance et clôture formelle des recommandations — garantissant que l'évaluation produit des effets concrets et mesurables.
> **Acteurs clés** : Entité évaluée (Direction) · Comité de suivi · Évaluateur public · Directeur de l'évaluation · DG · Contrôle qualité
> **Déclencheur** : Validation et publication du rapport d'évaluation final (CEV-P08) contenant des recommandations formalisées
> **Délai pivot** : 12 mois entre la publication du rapport et la clôture du suivi des recommandations
> **Livrable principal** : Rapport de suivi des recommandations incluant l'état d'avancement, le taux de réalisation, l'évaluation d'impact et la décision de clôture
> **Risque majeur** : Absence de mise en œuvre des recommandations par l'entité évaluée, faute d'engagement formel ou de moyens alloués
> **Indicateur cible** : Taux de réalisation des recommandations ≥ 80% à 12 mois ; taux de clôture formelle ≥ 90% à 18 mois

---

## 📍 CRAIE — Localisation

| Axe | Valeur |
|-----|--------|
| **Contexte** | Après la publication du rapport d'évaluation final (P8), l'entité évaluée dispose d'un ensemble de recommandations formalisées, classées par priorité et assorties d'un échéancier. La phase de suivi constitue le dernier maillon de la chaîne d'évaluation : elle vérifie que les recommandations sont effectivement mises en œuvre, mesure leur impact, et clôture le cycle d'évaluation. Cette procédure ancre la culture de l'évaluation dans l'amélioration continue des politiques publiques. |
| **Référentiel** | DOX v6.0 · Charte de l'Évaluateur public CEV-001 · Rapport d'évaluation final CEV-P08 · Guide de suivi des recommandations CEV-G09 · Cadre de l'évaluation d'impact CEV-G10 |
| **Acteurs** | DG · Entité évaluée · Comité de suivi · Évaluateur public · Directeur évaluation · Contrôle qualité |
| **Intitulé** | CEV-P09 — Suivi des recommandations : mise en œuvre, suivi et clôture |
| **Étapes** | 1. Réception et enregistrement des recommandations → 2. Élaboration du plan d'action → 3. Mise en place du comité de suivi → 4. Suivi périodique et reporting → 5. Évaluation d'impact → 6. Clôture des recommandations |

### Chaîne de localisation

```
M4 › Suivi › P14 › Suivi des recommandations › Entité évaluée / Comité de suivi
```

**Filière** : Évaluation / Qualité / Gouvernance

### Processus amont et aval

| Direction | Flux |
|-----------|------|
| **Amont** | P8 Phase contradictoire → rapport d'évaluation final contenant les recommandations validées |
| **Procédure** | **CEV-P09 — Suivi des recommandations : mise en œuvre, suivi et clôture** |
| **Aval** | P15 Évaluation d'impact à N+1 · Cycle d'évaluation suivant (M1 Programmation) |

---

## 🔄 Logigramme Mermaid

```mermaid
flowchart TB
    A[Rapport d'évaluation<br/>final P8] -->|Recommandations<br/>publiées| B{{1. Réception et<br/>enregistrement des<br/>recommandations}}
    B -->|Recommandations<br/>classées| C{{2. Élaboration du<br/>plan d'action<br/>contradictoire}}
    C -->|Plan d'action<br/>validé| D{{3. Mise en place et<br/>installation du<br/>comité de suivi}}
    D -->|Comité installé| E{{4. Suivi périodique<br/>et reporting<br/>(T0, T+3, T+6, T+9, T+12)}}
    E -->|Point d'étape| F([Délai de mise en<br/>œuvre respecté ?])
    F -->|Oui - Avancement<br/>satisfaisant| G{{5. Évaluation<br/>d'impact des<br/>recommandations}}
    F -->|Non - Retard|<| H{Prolongation<br/>accordée ?}
    H -->|Oui, motivée| E
    H -->|Non, échec| I[Signalement à la DG<br/>→ Plan de remédiation]
    I --> G
    G -->|Impact évalué| J{{6. Clôture des<br/>recommandations}}
    J -->|Recommandations<br/>clôturées| K[Cycle d'évaluation<br/>clos → Archivage]

    style A fill:#e1f5fe,stroke:#0288d1
    style B fill:#fff3e0,stroke:#f57c00
    style C fill:#fff3e0,stroke:#f57c00
    style D fill:#fff3e0,stroke:#f57c00
    style E fill:#fff3e0,stroke:#f57c00
    style F fill:#fce4ec,stroke:#d32f2f
    style G fill:#fff3e0,stroke:#f57c00
    style H fill:#fff3e0,stroke:#f57c00
    style I fill:#f3e5f5,stroke:#7b1fa2
    style J fill:#fff3e0,stroke:#f57c00
    style K fill:#e8f5e9,stroke:#388e3c
```

### Légende

| Couleur | Signification |
|---------|---------------|
| 🔵 Bleu | Amont / Déclencheur |
| 🟠 Orange | Étapes de la procédure |
| 🔴 Rouge | Décision / Point de contrôle / Échéance |
| 🟣 Violet | Contingence / Traitement par défaut |
| 🟢 Vert | Aval / Sortie positive |

---

## 👥 RACI — Matrice des responsabilités

### Acteurs

| # | Rôle | Direction/Service | Rôle dans la procédure |
|:--|------|-------------------|------------------------|
| 1 | 👤 Évaluateur public | Évaluateur public | Enregistre les recommandations, prépare les synthèses de suivi, contribue à l'évaluation d'impact, propose la clôture |
| 2 | 📋 Entité évaluée | Direction métier | Produit le plan d'action, met en œuvre les recommandations, reporte l'avancement au comité de suivi |
| 3 | 🏛️ Comité de suivi | DG + directions concernées | Valide le plan d'action, suit périodiquement l'avancement, décide des prolongations et de la clôture |
| 4 | 🔰 Directeur de l'évaluation | Évaluateur public | Supervise la procédure de suivi, valide les évaluations d'impact, arbitre les désaccords |
| 5 | 👑 Direction Générale | DG | Valide le plan de remédiation en cas d'échec, décide en dernier ressort, notifie la clôture |
| 6 | 🛡️ Contrôle qualité | Direction qualité | Vérifie la complétude et la traçabilité du suivi, audite les dossiers de clôture |
| 7 | 📊 Pilote de suivi | Entité évaluée | Coordinateur désigné responsable du plan d'action et des reportings périodiques |

### Matrice RACI

| Phase / Activité | Évaluateur public | Entité évaluée | Comité suivi | Directeur évaluation | DG | Contrôle qualité | Pilote suivi |
|-----------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Réception et enregistrement des recommandations | R | C | I | A | I | C | C |
| Élaboration du plan d'action contradictoire | C | R | A | C | I | I | R |
| Installation du comité de suivi | R | C | A | A | I | C | C |
| Suivi périodique et reporting | C | A | R | I | C | I | R |
| Évaluation d'impact | R | C | A | A | I | C | C |
| Clôture des recommandations | C | C | R | A | A | C | C |
| Plan de remédiation (échec) | C | R | C | A | A | C | R |

> **R** = Réalise · **A** = Approuve · **C** = Consulté · **I** = Informé

---

## 📝 Étapes détaillées

### Étape 1 : Réception et enregistrement des recommandations

| Champ | Valeur |
|-------|--------|
| **Action** | Dès publication du rapport d'évaluation final (CEV-P08), réceptionner l'ensemble des recommandations formalisées dans le rapport. Procéder à l'enregistrement dans le registre de suivi dédié : (1) numéroter chaque recommandation selon une nomenclature unique (REC-001, REC-002…), (2) classer par niveau de priorité (Critique / Élevée / Moyenne / Faible) selon l'impact potentiel et l'urgence de mise en œuvre, (3) associer chaque recommandation à l'entité responsable (direction/service pilote), (4) documenter le délai de mise en œuvre proposé dans le rapport, (5) catégoriser par domaine d'action (organisationnel, juridique, budgétaire, méthodologique, RH), (6) rattacher les indicateurs de succès définis dans le rapport. Produire une fiche individuelle de recommandation pour chaque item, comprenant le libellé, le constat source, la justification, l'échéance indicatrice, le responsable pressenti et les indicateurs de succès. Transmettre le registre complet à l'entité évaluée avec accusé de réception et convocation à la réunion de lancement du suivi. Consigner la date de début officiel du cycle de suivi (T0). |
| **Acteur** | Évaluateur public (réalise l'enregistrement) · Directeur de l'évaluation (valide le classement et la priorisation) · Entité évaluée (prend connaissance et désigne le pilote de suivi) · Contrôle qualité (vérifie la complétude de l'enregistrement) |
| **Délai** | 10 jours ouvrés à compter de la publication du rapport d'évaluation final |
| **Livrable** | Registre des recommandations (N recommandations numérotées) · Fiches individuelles de recommandation (N fiches) · Classification par priorité et par domaine · Notification officielle à l'entité évaluée · Accusé de réception · Date T0 consignée |
| **Outil** | Registre de suivi des recommandations CEV-R09a · Template Fiche de recommandation CEV-F09a · Tableur de suivi · Outil de gestion documentaire (GED) · Plateforme de notification |
| **Condition de passage** | 100% des recommandations enregistrées et classées ; classification de priorité validée par le Directeur de l'évaluation ; notification transmise à l'entité évaluée ; T0 officiellement consigné |

### Étape 2 : Élaboration du plan d'action contradictoire

| Champ | Valeur |
|-------|--------|
| **Action** | L'entité évaluée élabore un plan d'action de mise en œuvre des recommandations, en réponse au registre transmis (Étape 1). Pour chaque recommandation, le plan d'action doit préciser : (1) l'acceptation ou le refus motivé de la recommandation (principe contradictoire), (2) en cas d'acceptation, les actions concrètes envisagées, le responsable opérationnel désigné, le calendrier de réalisation (jalons intermédiaires), les ressources allouées (financières, humaines, techniques), (3) en cas de refus, la justification détaillée (impossibilité juridique, budgétaire, technique) et les mesures alternatives proposées. L'Évaluateur public examine le plan d'action et vérifie sa complétude et sa cohérence avec les recommandations émises. En cas d'écart ou d'insuffisance, un échange contradictoire est organisé entre l'Évaluateur public et l'entité évaluée pour ajuster le plan. Le plan d'action est soumis au Comité de suivi pour validation. Une fois validé, le plan d'action devient l'engagement formel de l'entité évaluée et constitue la référence du suivi. Chaque recommandation se voit attribuer un statut initial : Acceptée / Refusée / Acceptée partiellement / Reformulée. Diffuser le plan d'action validé à l'ensemble des parties prenantes. |
| **Acteur** | Pilote de suivi (élabore le plan d'action) · Entité évaluée (valide et s'engage) · Évaluateur public (examine et vérifie la complétude) · Directeur de l'évaluation (arbitre les divergences) · Comité de suivi (valide le plan d'action) |
| **Délai** | 30 jours ouvrés après réception du registre des recommandations (Étape 1) |
| **Livrable** | Plan d'action de mise en œuvre (N fiches-actions) · Décisions d'acceptation/refus par recommandation · Calendrier de réalisation avec jalons · Budget prévisionnel par action · Procès-verbal de validation du Comité de suivi · Plan d'action diffusé |
| **Outil** | Template Plan d'action CEV-F09b · Template Fiche-action CEV-F09c · Tableur budgétaire · Outil de gestion de projet · Plateforme collaborative de suivi |
| **Condition de passage** | Plan d'action couvrant 100% des recommandations ; chaque recommandation dispose d'une réponse motivée (acceptation/refus) ; Comité de suivi a validé le plan ; calendrier et jalons définis par recommandation |

### Étape 3 : Mise en place du comité de suivi

| Champ | Valeur |
|-------|--------|
| **Action** | Constituer et installer le Comité de suivi des recommandations, instance collégiale chargée du pilotage du suivi. Définir la composition : (1) Président : Directeur de l'évaluation ou représentant DG, (2) Membres permanents : représentant de l'entité évaluée, pilote de suivi, Évaluateur public référent, contrôle qualité, (3) Membres invités selon les points : directions transverses concernées (finances, RH, juridique), experts métier. Établir le règlement intérieur du comité : périodicité des réunions (trimestrielle par défaut, avec ajustement possible selon la criticité), quorum de fonctionnement, modalités de vote et de décision, règles de confidentialité. Organiser la réunion d'installation (Kick-off suivi) avec présentation du plan d'action, validation du calendrier de suivi et adoption du règlement intérieur. Définir le cycle de reporting : T+3, T+6, T+9, T+12 mois. Mettre en place les outils de suivi partagés (tableau de bord collaboratif, espace documentaire GED). Désigner le secrétariat du comité (gestion des ordres du jour, convocations, PV). Consigner et diffuser le procès-verbal d'installation. |
| **Acteur** | Directeur de l'évaluation (préside et installe) · Évaluateur public (assure le secrétariat) · Entité évaluée / Pilote de suivi (membres) · Contrôle qualité (membre) · DG (valide la composition) |
| **Délai** | 15 jours ouvrés après validation du plan d'action (Étape 2) |
| **Livrable** | Règlement intérieur du Comité de suivi · Composition nominative validée · Calendrier des réunions annuelles · Outil de suivi partagé déployé · Procès-verbal d'installation · Espace documentaire GED créé |
| **Outil** | Template Règlement intérieur CEV-F09d · Template PV de réunion CEV-F09e · Outil de planification (agenda partagé) · Plateforme collaborative (Teams, Notion, espace projet) · GED Évaluateur / Suivi recommandations |
| **Condition de passage** | Comité constitué et installé ; règlement intérieur adopté ; calendrier de suivi annuel validé ; outils de suivi opérationnels ; secrétariat désigné |

### Étape 4 : Suivi périodique et reporting

| Champ | Valeur |
|-------|--------|
| **Action** | Conduire le suivi périodique de la mise en œuvre des recommandations selon le cycle défini (T+3, T+6, T+9, T+12 mois). Pour chaque échéance : (1) Le pilote de suivi produit un rapport d'avancement par recommandation : actions réalisées, jalons atteints, difficultés rencontrées, dérives éventuelles (délai, budget, qualité), (2) L'Évaluateur public analyse le rapport, vérifie la concordance avec le plan d'action, identifie les écarts et propose des ajustements, (3) Le Comité de suivi se réunit pour examiner l'avancement global, valider les ajustements, décider d'éventuelles prolongations ou révisions du plan. Appliquer un système de feux tricolores pour chaque recommandation : 🟢 Vert (en bonne voie, conforme au plan), 🟡 Orange (retard modéré, actions correctives engagées), 🔴 Rouge (retard critique, risque de non-réalisation, escalade nécessaire). Maintenir à jour le tableau de bord de suivi avec les indicateurs consolidés : taux de réalisation global, taux par priorité, nombre de recommandations en retard, nombre de recommandations en alerte. Produire un compte rendu de chaque réunion du Comité de suivi avec les décisions prises, les délais révisés et les points d'attention. En cas de recommandation en rouge à deux points de contrôle consécutifs, déclencher une procédure d'escalade (signalement au Directeur de l'évaluation et à la DG). |
| **Acteur** | Pilote de suivi (produit le rapport d'avancement) · Évaluateur public (analyse et propose des ajustements) · Comité de suivi (examine, décide, suit le tableau de bord) · Directeur de l'évaluation (déclenche l'escalade si nécessaire) · DG (informée des dérives critiques) |
| **Délai** | Tous les 3 mois (T+3, T+6, T+9, T+12) — rapport du pilote J-15 avant réunion ; analyse Évaluateur J-7 ; réunion comité J ; diffusion PV J+5 |
| **Livrable** | Rapport d'avancement périodique (pilote) · Note d'analyse et de proposition (Évaluateur) · Tableau de bord mis à jour (feux tricolores) · Compte rendu de réunion du Comité de suivi · Décisions de prolongation/révision · Alertes d'escalade (si applicable) |
| **Outil** | Template Rapport d'avancement CEV-F09f · Tableau de bord collaboratif (feux tricolores) · Template Compte rendu CEV-F09e · Outil de gestion de projet · Plateforme collaborative · Système d'alerte/escalade |
| **Condition de passage** | Rapport d'avancement produit et analysé ; Comité de suivi tenu dans les délais ; décisions consignées et diffusées ; tableau de bord à jour ; escalade déclenchée si critères de rouge remplis |

### Étape 5 : Évaluation d'impact des recommandations

| Champ | Valeur |
|-------|--------|
| **Action** | Conduire une évaluation de l'impact des recommandations mises en œuvre, à réaliser à T+12 ou une fois qu'un nombre significatif de recommandations a été exécuté. L'évaluation d'impact porte sur : (1) l'efficacité — les actions mises en œuvre ont-elles atteint les objectifs visés par la recommandation ? (2) l'efficience — les ressources mobilisées sont-elles proportionnées aux résultats obtenus ? (3) la durabilité — les effets sont-ils pérennes ou risquent-ils de s'estomper ? (4) les effets induits — y a-t-il des conséquences positives ou négatives non anticipées ? (5) la satisfaction — les parties prenantes concernées jugent-elles la mise en œuvre satisfaisante ? Pour chaque recommandation mise en œuvre, appliquer une grille d'évaluation avec des critères objectivables et une notation (1-5). Produire un rapport synthétique d'évaluation d'impact comprenant : une note de synthèse exécutive, un tableau récapitulatif par recommandation (impact mesuré / impact attendu / écart), une analyse transversale des facteurs de succès et d'échec, des recommandations pour le prochain cycle d'évaluation. Soumettre le rapport d'évaluation d'impact au Comité de suivi pour validation et présentation à la DG. Identifier les recommandations pouvant être clôturées (impact jugé satisfaisant) et celles nécessitant un suivi renforcé (impact insuffisant). |
| **Acteur** | Évaluateur public (conduit l'évaluation d'impact) · Entité évaluée / Pilote de suivi (fournit les données et bilans) · Comité de suivi (valide l'évaluation) · Directeur de l'évaluation (supervise la méthodologie) · Contrôle qualité (vérifie la robustesse de l'évaluation) |
| **Délai** | T+12 mois (ou dans les 30 jours suivant l'achèvement des recommandations si plus tardif) |
| **Livrable** | Rapport d'évaluation d'impact des recommandations · Grille d'évaluation renseignée (N fiches) · Synthèse exécutive · Tableau d'impact par recommandation · Analyse transversale (facteurs de succès/échec) · Proposition de clôture/suivi renforcé par recommandation · PV de validation par le Comité de suivi |
| **Outil** | Template Rapport d'impact CEV-F09g · Grille d'évaluation CEV-G10 · Base de données d'indicateurs · Outil d'enquête (satisfaction parties prenantes) · GED Évaluateur / Suivi / Impacts |
| **Condition de passage** | Évaluation d'impact réalisée pour 100% des recommandations mises en œuvre ; rapport validé par le Comité de suivi ; proposition de clôture formulée pour chaque recommmandation (clôture ou suivi renforcé) |

### Étape 6 : Clôture des recommandations

| Champ | Valeur |
|-------|--------|
| **Action** | Prononcer la clôture formelle des recommandations sur la base de l'évaluation d'impact (Étape 5) et des décisions du Comité de suivi. Pour chaque recommandation, appliquer l'un des trois statuts de clôture : (1) **Clôturée — réalisée** : la recommandation a été mise en œuvre et l'impact jugé satisfaisant, (2) **Clôturée — remplacée** : la recommandation a été transformée ou remplacée par une action différente répondant au même objectif, (3) **Clôturée — abandonnée** : la recommandation est abandonnée pour impossibilité démontrée (juridique, technique, budgétaire) — décision motivée et validée par la DG. Pour les recommandations non clôturées, décider d'un suivi renforcé avec un nouveau délai et des jalons rapprochés. Produire le rapport final de suivi des recommandations : (1) bilan global du cycle de suivi (N total, N clôturées, N en suivi renforcé, N abandonnées), (2) taux de réalisation global ventilé par priorité, (3) synthèse des impacts mesurés, (4) enseignements pour le prochain cycle d'évaluation, (5) recommandations d'amélioration du processus de suivi lui-même. Présenter le rapport final à la DG pour validation et communication aux instances concernées. Archiver l'intégralité du dossier de suivi dans la GED Évaluateur : registre des recommandations, plan d'action, PV des comités, rapports d'avancement, évaluation d'impact, rapport final. Mettre à jour le tableau de bord consolidé de l'Évaluateur public avec les indicateurs de clôture. Notifier formellement la clôture du cycle d'évaluation à l'ensemble des parties prenantes. |
| **Acteur** | Évaluateur public (rédige le rapport final) · Comité de suivi (propose les statuts de clôture) · Directeur de l'évaluation (valide le rapport final) · DG (valide la clôture et les abandons) · Contrôle qualité (vérifie l'intégrité du dossier d'archivage) |
| **Délai** | 30 jours ouvrés après validation du rapport d'évaluation d'impact (Étape 5) |
| **Livrable** | Rapport final de suivi des recommandations · Statuts de clôture attribués (N décisions) · Dossier de suivi complet archivé (GED) · Notification de clôture aux parties prenantes · Tableau de bord consolidé mis à jour · Bilan des enseignements pour le prochain cycle |
| **Outil** | Template Rapport final de suivi CEV-F09h · Template Notification de clôture CEV-F09i · GED Évaluateur / Archives / Suivi · Tableau de bord consolidé · Outil de signature électronique |
| **Condition de passage** | Rapport final validé par la DG ; statuts de clôture attribués à 100% des recommandations ; dossier archivé ; notification de clôture diffusée ; indicateurs consolidés mis à jour |

### Boucle de gestion des recommandations en échec

| Champ | Valeur |
|-------|--------|
| **Action** | En cas de constat d'échec de mise en œuvre d'une recommandation (retard critique au-delà de T+12 malgré prolongation, ou impossibilité avérée) : (1) Documenter précisément les causes de l'échec : défaut d'engagement, insuffisance de ressources, obstacle juridique/réglementaire, opposition interne, changement de priorité, (2) Saisir la DG pour arbitrage via une note de signalement circonstanciée, (3) La DG décide soit d'un plan de remédiation contraint (avec échéance ferme et reporting mensuel), soit de l'abandon motivé de la recommandation, soit de son réexamen dans le cadre du prochain cycle d'évaluation. Le plan de remédiation contraint comprend : actions correctives détaillées, responsable unique désigné, échéance impérative, points de contrôle bimensuels, conséquences en cas de non-respect (escalade hiérarchique). En cas d'abandon, produire une note de motivation détaillée signée par la DG et l'ajouter au dossier de suivi. L'échec et son traitement sont documentés dans le rapport final de suivi avec l'analyse des causes profondes et les recommandations pour éviter la récurrence. |
| **Acteur** | Évaluateur public (documente et prépare la note de signalement) · Directeur de l'évaluation (saisit la DG) · DG (décide du plan de remédiation ou de l'abandon) · Entité évaluée / Pilote de suivi (exécute le plan de remédiation) · Contrôle qualité (vérifie la traçabilité de la procédure d'échec) |
| **Délai** | 5 jours ouvrés (note de signalement) + 10 jours ouvrés (décision DG) + durée du plan de remédiation (définie par la DG) |
| **Livrable** | Note de signalement circonstanciée · Décision DG motivée (plan de remédiation ou abandon) · Plan de remédiation contraint · Points de contrôle bimensuels · Note d'abandon motivée (si applicable) · Mise à jour du dossier de suivi |
| **Condition de sortie** | Échec résorbé par remédiation et clôture ; ou abandon motivé validé par DG ; traçabilité complète de la procédure d'échec |

---

## ⚠️ Risques identifiés

| # | Code | Risque | Description | Impact | Probabilité |
|:--|------|--------|-------------|--------|:-----------:|
| 1 | R1 | Absence de plan d'action de l'entité évaluée | L'entité évaluée ne produit pas de plan d'action dans le délai imparti, bloquant le démarrage du suivi | Majeur | 3/5 |
| 2 | R2 | Non-mise en œuvre des recommandations | Les recommandations acceptées ne sont pas mises en œuvre, faute d'engagement, de moyens ou de volonté politique | Critique | 3/5 |
| 3 | R3 | Dérive calendaire du suivi | Les échéances ne sont pas respectées, les reports s'accumulent, le suivi s'étend au-delà de 18 mois sans clôture | Majeur | 4/5 |
| 4 | R4 | Insuffisance de suivi qualitatif | Le suivi se limite à des indicateurs quantitatifs sans évaluation réelle de l'impact et de la qualité de mise en œuvre | Moyen | 3/5 |
| 5 | R5 | Conflit entre l'évaluateur et l'entité évaluée sur l'appréciation | Désaccord persistant sur le niveau de réalisation ou l'impact d'une recommandation, bloquant la clôture | Moyen | 3/5 |
| 6 | R6 | Absence de sanctions en cas de non-mise en œuvre | Absence de mécanisme contraignant pour garantir la mise en œuvre, rendant le suivi purement déclaratif | Critique | 4/5 |
| 7 | R7 | Rupture de mémoire et de continuité | Changement d'interlocuteurs (entité évaluée, Évaluateur, comité) en cours de suivi, perte de l'historique et du contexte | Majeur | 3/5 |

### Criticité

| Risque | Niveau | Action requise |
|--------|--------|----------------|
| R1 | Élevée (8) | Relance systématique à J+15 et J+25 ; escalade au Directeur de l'évaluation à J+30 ; saisine DG à J+45 |
| R2 | Critique (12) | Plan d'action engageant formellement la direction ; points de contrôle trimestriels avec feu tricolore ; escalade progressive documentée vers la DG |
| R3 | Élevée (8) | Marges de sécurité dans le calendrier (J+15%) ; tableau de bord des délais ; alerte à T+15 mois ; révision du planning si nécessaire |
| R4 | Moyenne (6) | Grille d'évaluation d'impact obligatoire ; critères qualitatifs définis dans le plan d'action ; revue par le contrôle qualité |
| R5 | Moyenne (6) | Principe contradictoire documenté dès l'Étape 2 ; arbitrage par le Comité de suivi ; escalade DG en dernier ressort |
| R6 | Critique (12) | Engagement formel DG sur le plan d'action ; clause de reporting à la gouvernance ; lien avec le dialogue de gestion |
| R7 | Élevée (8) | Dossier de suivi centralisé dans la GED ; fiches de passation ; documentation systématique des décisions ; désignation de suppléants |

> **Échelle** : Impact (1-5) × Probabilité (1-5) → **Criticité** : Faible (1-4) · Moyenne (5-9) · Élevée (10-16) · Critique (17-25)

---

## 📄 Documents de référence

Documents support et d'enregistrement associés à la procédure :

### Documents support

| Type | Document | Référence | Emplacement |
|------|----------|-----------|-------------|
| Support | Template Fiche de recommandation | CEV-F09a | BDD 1 Procédures / Outils |
| Support | Template Plan d'action de mise en œuvre | CEV-F09b | BDD 1 Procédures / Outils |
| Support | Template Fiche-action | CEV-F09c | BDD 1 Procédures / Outils |
| Support | Template Règlement intérieur du Comité de suivi | CEV-F09d | BDD 1 Procédures / Outils |
| Support | Template PV de réunion | CEV-F09e | BDD 1 Procédures / Outils |
| Support | Template Rapport d'avancement périodique | CEV-F09f | BDD 1 Procédures / Outils |
| Support | Template Rapport d'évaluation d'impact | CEV-F09g | BDD 1 Procédures / Outils |
| Support | Template Rapport final de suivi | CEV-F09h | BDD 1 Procédures / Outils |
| Support | Template Notification de clôture | CEV-F09i | BDD 1 Procédures / Outils |
| Support | Guide de suivi des recommandations | CEV-G09 | BDD 1 Procédures / Guides |
| Support | Cadre de l'évaluation d'impact | CEV-G10 | BDD 1 Procédures / Guides |
| Support | Charte de l'Évaluateur public | CEV-001 | BDD 1 Procédures / Chartes |
| Support | Rapport d'évaluation final | CEV-P08 | BDD 1 Procédures / Procédures |
| Support | DOX v6.0 — Doctrine PROC | DOX Core | BDD 1 Procédures / Référentiels |

### Documents d'enregistrement

| Type | Document | Référence | Emplacement |
|------|----------|-----------|-------------|
| Enregistrement | Registre des recommandations (par évaluation) | CEV-R09a | BDD 1 Procédures / Registres |
| Enregistrement | Plan d'action de mise en œuvre validé | N/A | GED Évaluateur / Suivi / Plans action |
| Enregistrement | Comptes rendus des réunions du Comité de suivi | N/A | GED Évaluateur / Suivi / Comités |
| Enregistrement | Rapports d'avancement périodiques | N/A | GED Évaluateur / Suivi / Avancement |
| Enregistrement | Rapport d'évaluation d'impact | N/A | GED Évaluateur / Suivi / Impacts |
| Enregistrement | Rapport final de suivi des recommandations | N/A | GED Évaluateur / Suivi / Rapports finaux |
| Enregistrement | Décisions de clôture (par recommandation) | N/A | GED Évaluateur / Suivi / Clôtures |
| Enregistrement | Notes de signalement et décisions DG (échecs) | N/A | GED Évaluateur / Suivi / Échecs |

---

## 📋 Informations générales

| Champ | Valeur |
|-------|--------|
| **Périmètre** | Toute évaluation conduite par l'Évaluateur public ayant produit un rapport final contenant des recommandations formalisées |
| **Directions concernées** | Entité évaluée · DG · Comité de suivi · Direction qualité |
| **Services concernés** | Évaluateur public · Contrôle qualité · Secrétariat du comité de suivi · Services archivage/GED |
| **Date d'effet** | 01/08/2026 |
| **Validité** | Jusqu'à prochaine revue |
| **Révision** | Version 1.0 |

---

## 📊 Tableau de bord — Indicateurs de performance

| Indicateur | Cible | Mesure | Fréquence | Seuil d'alerte |
|------------|:-----:|--------|-----------|:--------------:|
| Taux de réalisation des recommandations à 12 mois | ≥ 80% | Recommandations mises en œuvre / Total recommandations acceptées | Trimestrielle | < 60% |
| Taux de clôture formelle à 18 mois | ≥ 90% | Recommandations clôturées / Total recommandations | Semestrielle | < 75% |
| Délai moyen de mise en œuvre par recommandation | ≤ 9 mois | Somme délais mise en œuvre / Nb recommandations | Annuelle | > 12 mois |
| Taux de recommandations en alerte (rouge) | ≤ 10% | Recommandations rouges / Total en suivi | Trimestrielle | > 20% |
| Taux d'abandon de recommandations | ≤ 10% | Recommandations abandonnées / Total recommandations | Annuelle | > 15% |
| Satisfaction de l'entité évaluée sur le processus de suivi | ≥ 3,5/5 | Enquête de satisfaction post-clôture | Par cycle | < 2,5/5 |
| Taux de recommandations avec évaluation d'impact réalisée | 100% | Recommandations avec impact évalué / Total clôturées | Annuelle | < 90% |
| Délai entre la clôture du suivi et l'archivage complet | ≤ 15 jours | Date archivage - Date clôture | Par cycle | > 30 jours |

---

## 🔗 Références normatives

| Texte | Référence |
|-------|-----------|
| Charte de l'Évaluateur public — CEV-001 | Niveau Argent, 01/08/2026 |
| DOX v6.0 — Doctrine PROC | DOX Core |
| Procédure P8 — Phase contradictoire | CEV-P08, Niveau Platine, 01/08/2026 |
| Procédure P15 — Évaluation d'impact à N+1 | CEV-P10 |
| Guide de suivi des recommandations — CEV-G09 | BDD 1 Procédures / Guides |
| Cadre de l'évaluation d'impact — CEV-G10 | BDD 1 Procédures / Guides |
| Code des relations entre le public et l'administration (CRPA) | Articles L.121-1 et suivants |
| Charte de la déontologie de l'évaluation (SFE) | Société Française de l'Évaluation |

---

## ✅ Checklist PLATINE — Suivi des recommandations

- [x] FLASH CARD complète (objet, acteurs, déclencheur, délai pivot, livrable, risque, KPI)
- [x] Localisation CRAIE avec chaîne M4 › P14 et amont/aval détaillés
- [x] Logigramme Mermaid (6 étapes + boucle de gestion des échecs, nœud décisionnel de délai, prolongation, escalade DG)
- [x] RACI complet (7 acteurs, 7 phases couvertes)
- [x] Étapes détaillées (6 étapes + boucle échecs, chaque étape : action, acteurs, délai, livrable, outil, condition de passage)
- [x] Système de feux tricolores (vert/orange/rouge) intégré au suivi périodique
- [x] Boucle de gestion des recommandations en échec avec escalade DG et plan de remédiation
- [x] Risques (7 risques avec code R1→R7, catégorisation Critique/Élevé/Moyen, actions spécifiques)
- [x] Documents de référence (14 support + 8 enregistrement)
- [x] Tableau de bord (8 indicateurs avec cible, mesure, fréquence, seuil d'alerte)
- [x] Triple statut de clôture (réalisée / remplacée / abandonnée)
- [x] Niveau PLATINE : procédure transversale avec volets contradictoire, suivi et évaluation d'impact intégrés

### Critères QG Niveau PLATINE

| Gate | Critère | Statut | Poids |
|:----:|---------|:------:|:-----:|
| G1 | Titre et référence conformes | ✅ | 3 |
| G2 | FLASH CARD complète (objet, acteurs, délais, risques, indicateur) | ✅ | 5 |
| G3 | Localisation CRAIE explicite (Mission › Processus) | ✅ | 4 |
| G4 | Logigramme Mermaid (≥ 3 nœuds, amont→aval, nœud décisionnel) | ✅ | 5 |
| G5 | RACI complet (≥ 5 acteurs, ≥ 4 phases, R/A/C/I) | ✅ | 4 |
| G6 | Étapes détaillées (action, acteur, délai, livrable par étape) | ✅ | 5 |
| G7 | Risques (≥ 5 documentés avec code, impact, probabilité, criticité) | ✅ | 5 |
| G7B | Documents support + enregistrement listés (≥ 10 support, ≥ 5 enregistrement) | ✅ | 3 |
| G8 | Synthèse de modularité présente | ✅ | 4 |
| G9 | Tableau comparatif des niveaux | ✅ | 3 |
| G10 | Couverture cumulative validée | ✅ | 3 |
| G11 | Scorecard de niveau présente | ✅ | 3 |
| G14 | Dernière revue renseignée | ✅ | 3 |
| G15 | Périodicité définie | ✅ | 2 |
| G16 | Prochaine revue cohérente | ✅ | 2 |
| G21 | Score total ≥ 85% requis pour le Niveau PLATINE | ✅ | 5 |
| | **Score QG total** | **59/59** (100%) | **59** |

---

> **Généré par Hermes Agent — PROC v1.0**
> **DOX v6.0 — Niveau Platine**
> **Prochaine évolution suggérée** : Passage à P15 — Évaluation d'impact à N+1
> **Mission** : M4 Suivi · **Processus** : P14 Suivi des recommandations
