# Exemple — Diagramme de Séquence CGSS-118 MYTHIQUE

```mermaid
sequenceDiagram
    box rgba(225,241,254,1) PHASE 1 — RÉCEPTION ET VÉRIFICATION
        participant Agent as Agent
        participant Gest as Service Gestionnaire
    end
    box rgba(255,243,224,1) PHASE 2 — TRAITEMENT ADMINISTRATIF
        participant Gest2 as Service Gestionnaire
        participant Rem as Service Rémunération
    end
    box rgba(252,228,236,1) PHASE 3 — TRANSMISSION CGSS
        participant Rem2 as Service Rémunération
        participant CGSS as CGSS
    end
    box rgba(232,245,233,1) PHASE 4 — VERSEMENT ET CONTRÔLE
        participant CGSS2 as CGSS
        participant Rem3 as Service Rémunération
    end

    %% Phase 1
    Agent->>Gest: Transmet avis d'arrêt (48h)
    activate Gest
    Gest-->>Agent: Accusé réception
    deactivate Gest

    Gest->>Gest: Vérifie conformité (Checklist DE1)
    activate Gest
    Note over Gest: Double contrôle obligatoire
    deactivate Gest

    %% Phase 2
    Gest2->>Rem: Saisie SIRH + arrêté absence
    activate Rem
    Rem-->>Gest2: Arrêté signé (J+5)
    deactivate Rem

    Rem->>Rem: Préparation attestation salaire
    activate Rem
    Note over Rem: Délai: avant fin M+1
    deactivate Rem

    %% Phase 3
    Rem2->>CGSS: Transmission DSN via Net Entreprise
    activate CGSS
    CGSS->>CGSS: Calcul IJ
    CGSS-->>Rem2: Accusé réception
    deactivate CGSS

    %% Phase 4
    CGSS2->>Rem3: Versement IJ (agent ou subrogation)
    activate Rem3
    Rem3-->>CGSS2: Notification reçue
    deactivate Rem3

    Rem3->>Rem3: Contrôle versement J+30
    activate Rem3
    Note over Rem3: Vérification DE4
    deactivate Rem3

    Rem3->>Gest: Clôture dossier
```

## Descriptif des étapes

| Étape | Phase | Action | Acteur | Livrable | Délai |
|:-----:|:-----:|--------|:------:|----------|:-----:|
| **1** | Réception et vérification | Transmet avis d'arrêt | Agent → S. Gestionnaire | Avis d'arrêt reçu | 48h |
| **2** | Réception et vérification | Vérification conformité | S. Gestionnaire | Checklist DE1 validée | J+1 |
| **3** | Traitement administratif | Saisie SIRH + arrêté | S. Gestionnaire → S. Rémunération | Arrêté signé | J+5 |
| **4** | Traitement administratif | Préparation attestation | S. Rémunération | Attestation prête | M+0 |
| **5** | Transmission CGSS | DSN via Net Entreprise | S. Rémunération → CGSS | Accusé réception CGSS | M+1 |
| **6** | Versement et contrôle | Calcul et versement IJ | CGSS → S. Rémunération | IJ versées | J+30 |
| **7** | Versement et contrôle | Contrôle versements | S. Rémunération | Tableau DE4 à jour | J+30 |
| **8** | — | Clôture dossier | S. Gestionnaire | Dossier archivé | — |
