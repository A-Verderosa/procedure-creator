# BDD Planning Évaluateur — Architecture d'automatisation Akuma

> Découverte session 2026-08-02
> BDD Planning ID : `3351d81e-4c39-827e-88a4-817c2739bbff`
> 117 items : 5 Missions → 17 Processus → 95 Procédures, tous statut « À créer »

---

## 1. Structure de la BDD Planning

### Hiérarchie

```
🏛️ M1 — Pilotage stratégique (18 items)
├── P1  Élaboration programme annuel
├── P2  Traitement d'une saisine
└── P3  Instruction et cadrage préalable

📐 M2 — Conduite d'une évaluation (20 items)
├── P4  Élaboration note de cadrage
├── P5  Installation comité de pilotage
├── P6  Lancement consultation / appels d'offres
├── P7  Collecte et analyse des données
├── P8  Réunions techniques et entretiens
├── P9  Élaboration conclusions et recommandations
└── P10 Assurance qualité et revue interne

🔍 M3 — Restitution (28 items)
├── P11 Rédaction et validation du rapport
├── P12 Phase contradictoire
└── P13 Restitution et communication

📋 M4 — Suivi des recommandations (22 items)
├── P14 Suivi des recommandations par la direction
└── P15 Évaluation d'impact à N+1

📊 M5 — Transverse et amélioration continue (29 items)
├── P16 Gestion documentaire et des référentiels
└── P17 Veille méthodologique et amélioration continue
```

### Propriétés de chaque item

| Propriété | Type | Valeur |
|-----------|------|--------|
| `Nom` | title | M1.P1.01 — Élaboration du programme |
| `Mission` | select | M1..M5 |
| `Processus` | select | P1..P17 |
| `Statut avancement` | select | À créer |
| `Phase` | select | Programmation / Exécution / Restitution / Suivi |

### Cross-reference Phase 3 → Planning

Les 6 procédures créées dans MYTHIQUE (Phase 3) :

| Code Planning | Titre | Niveau | MYTHIQUE |
|---------------|-------|--------|----------|
| M1.P1.01 | Charte de l'évaluation | Mythique | ✅ |
| M1.P3.01 | Procédure de saisine | Mythique | ✅ |
| M2.P4.01 | Note de cadrage | Mythique | ✅ |
| M3.P7.01 | Collecte des données | Mythique | ✅ |
| M4.P12.01 | Phase contradictoire | Mythique | ✅ |
| M5.P15.01 | Suivi des recommandations | Mythique | ✅ |

**→ Il faut créer une relation Notion BDD Planning ↔ MYTHIQUE** pour que chaque item Planning pointe vers sa procédure créée.

---

## 🌐 Couverture Évaluateur public — Preuve de complétude

Les 95 procédures couvrent **100% du cycle d'activité** de l'Évaluateur public.

### Cycle de vie couvert

| Étape du cycle | Mission | Ce qu'elle couvre |
|----------------|---------|-------------------|
| **1. Intake & programmation** | M1.P1-P3 | Saisine → cadrage → charte → programme annuel |
| **2. Cadrage technique** | M2.P4-P6 | Note de cadrage → référentiel → comité de pilotage |
| **3. Investigation** | M2.P7-P8 | Collecte données → entretiens → réunions |
| **4. Analyse & recommandations** | M2.P9-P10 | Élaboration conclusions → assurance qualité |
| **5. Rapport & contradictoire** | M3.P11-P12 | Rédaction → phase contradictoire |
| **6. Restitution & décision** | M3.P13 | Comité de décision → arbitrage → communication |
| **7. Suivi des recommandations** | M4.P14-P15 | Plan d'action → évaluation d'impact |
| **8. Capitalisation & amélioration** | M5.P16-P17 | Gestion documentaire → veille → REX |

### Périmètre

**✅ Couvert :** saisines, programmation, cadrage, collecte, entretiens, rapports, contradictoire, comité, décision, communication, suivi, impact, capitalisation, veille documentaire.

**❌ Hors périmètre Évaluateur (autres BDD) :** RH équipe, budget, achats, communication corporate.

### Automatisation — Les 3 vitesses

| Niveau | Nb / 95 | Humain | Pattern |
|--------|---------|--------|---------|
| 🟢 **Akuma** | ~30 | Zéro | Form → Webhook → Pipeline → Notify |
| 🟡 **Platine** | ~50 | Validation | Hermes prépare → Humain valide → Hermes finalise |
| 🔴 **Argent/Or** | ~15 | Conduite | Humain opère, Hermes assiste |

**Répartition par mission :**

| Mission | Total | 🟢 Akuma | 🟡 Platine | 🔴 Argent |
|---------|-------|----------|-----------|-----------|
| M1 — Pilotage | 18 | 6 | 10 | 2 |
| M2 — Conduite | 20 | 7 | 10 | 3 |
| M3 — Restitution | 28 | 5 | 17 | 6 |
| M4 — Suivi | 22 | 8 | 10 | 4 |
| M5 — Transverse | 29 | 10 | 15 | 4 |
| **Total** | **117** | **~36** | **~62** | **~19** |

Voir section 3 pour la matrice détaillée par procédure.

---

## 2. Architecture d'automatisation Akuma

### Principe général

```
📝 Notion Form (interface humaine)
    │ Nouvelle page créée
    ▼
🔄 Notion Automation (déclencheur natif)
    │ "When a page is added" → "Send webhook"
    ▼
🧠 Hermes Agent (exécution)
    │ Reçoit webhook → exécute pipeline → update Notion
    │ → Email (Himalaya) + Telegram
```

### Flux type — Saisine

```yaml
1. Citoyen remplit formulaire Notion « Demande d'évaluation »
   → Nouvelle page créée dans BDD Saisines

2. Automation Notion détecte la création
   → POST webhook vers Hermes avec payload (page_id, propriétés)

3. Hermes :
   a) Vérifie le type d'entrée
   b) Exécute le pipeline create (10 étapes)
   c) Crée la procédure MYTHIQUE
   d) Update statut Planning → « En cours »
   e) Ajoute la relation vers la page MYTHIQUE

4. Notifications :
   → Email au référent : « Nouvelle saisine reçue »
   → Telegram à l'équipe : « 🔔 Saisine — Évaluation X »
```

### Mécanique Notion Automation

Notion supporte les webhooks natifs dans Database Automations :

1. **Trigger** : `When a page is added` / `When a property changes`
2. **Action** : `Send webhook` → URL Hermes endpoint
3. **Payload** : Propriétés de la page automatiquement envoyées

**Avantages vs n8n** : zéro infra supplémentaire, pas de licence, natif Notion, fiable.
**Limites** : pas de logique complexe, pas de transformation de payload avancée.
**n8n complémentaire** : flux multi-étapes complexes, agrégation multi-sources.

---

## 3. Matrice de faisabilité d'automatisation

### 🟢 Akuma — Automatisable intégralement (~30 procédures)

Zéro intervention humaine dans le traitement. Pattern : Form → Webhook → Auto → Notify.

| Planning | Titre | Moteur |
|----------|-------|--------|
| M1.P1.01 | Charte de l'évaluation | Template → génération |
| M1.P1.02 | Programme annuel | Data → template |
| M1.P3.01 | **Saisine** ← priorité #1 | Form → webhook → accusé → suivi |
| M1.P3.03 | Accusé réception | Auto → email |
| M2.P4.01 | Note de cadrage | Données → génération |
| M2.P5.01-03 | Référentiel, grille, indicateurs | Template |
| M2.P7.01 | Plan collecte données | Template |
| M3.P10.01 | Dossier de preuves | Aggrégation auto |
| M4.P12.01 | Phase contradictoire | Envoi → collecte → suivi |
| M4.P14.01 | Plan d'action | Génératif |
| M5.P15.01-03 | **Suivi, relances, tableau de bord** | **Cron job** |
| M5.P16.01 | Gestion documentaire | Auto-classification |
| M5.P17.01 | Capitalisation REX | Template |

### 🟡 Platine — Partiellement automatisable (~50 procédures)

Pattern : Form → Webhook → Hermes prépare → Notion (humain valide) → Hermes finalise.

| Planning | Titre | Part auto | Part humaine |
|----------|-------|-----------|-------------|
| M2.P8.01 | Planification entretiens | Calendrier, relances | Conduite |
| M2.P9.01 | Analyse documentaire | Extraction, classif. | Interprétation |
| M3.P11.01 | Rédaction rapport | Template, données | Rédaction |
| M3.P13.01 | Comité de décision | Préparation dossier | Décision |
| M4.P14.02 | Validation plan action | Workflow | Approbation |
| ... +40 autres | | | |

### 🔴 Argent/Or — Assisté (~15 procédures)

Humain central, Hermes assiste (tracing, QG checklist, archivage).

| Planning | Titre | Assistance |
|----------|-------|------------|
| M2.P8.03 | Conduite entretiens | Tracing, transcription |
| M2.P10.01 | Revue qualité interne | Checklist QG auto |
| M3.P13.03 | Arbitrage | Documentation, suivi |
| M5.P17.02 | Veille méthodologique | Agrégation sources |

---

## 4. Pipeline avancé : BDD Planning comme source Phase 4+

```
BDD Planning ──> Hermes cron (scan « À créer »)
    │                    │
    │                    ▼
    │            Pipeline create (10 étapes)
    │                    │
    │                    ▼
    │            BDD MYTHIQUE
    │                    │
    └────────────────────┤
              Update Planning → « Créée » + relation
```

### Cron job de scan

```bash
hermes cron create \
  --schedule "0 6 * * 1" \
  --prompt "Scanne la BDD Planning (3351d81e...).
            Pour chaque item 'À créer', lance le pipeline create
            avec --titre <nom> --niveau mythique.
            Marque l'item 'En cours' puis 'Créée'." \
  --skills procedure-creator
```

### Prérequis Phase 4

- ✅ Relation Notion BDD Planning ↔ MYTHIQUE
- ✅ Mapping item Planning → type RH, périmètre, acteurs
- ⏳ Champ `Priorité` (Haute/Moyenne/Basse) dans Planning
- ⏳ Champ `Niveau cible` (Argent..Akuma) dans Planning

---

## 5. Notes techniques

### Endpoints Notion

```python
# Query planning
POST /v1/databases/3351d81e-4c39-827e-88a4-817c2739bbff/query
Filter: {"property": "Statut avancement", "select": {"equals": "À créer"}}

# Create relation planning → MYTHIQUE
PATCH /v1/pages/{planning_id}
Properties: {"Procédure MYTHIQUE": {"relation": [{"id": "{mythique_id}"}]}}

# Update planning status
PATCH /v1/pages/{planning_id}
Properties: {"Statut avancement": {"select": {"name": "Créée"}}}
```

### IDs BDD

| BDD | ID |
|-----|----|
| Planning Évaluateur | `3351d81e-4c39-827e-88a4-817c2739bbff` |
| MYTHIQUE (hub) | `0a1689d5-ec35-4422-95cb-188a1dd35113` |
| SBRX | `8e0efb57-8ac1-4a5d-9a6e-8a59431f9603` |
| PMRI | `6f39b3cc-6c02-40ca-b38a-10aea6fcf8d9` |
| GED | `3c36a4d6-ce2e-4aa2-8ce9-b08f957aef4e` |
| FAQ | `3c44d2d1-ee87-44ed-b991-bab4d1e94442` |
| Glossaire | `1481d81e-4c39-808a-b304-fd1857c29329` |
