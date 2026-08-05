# Webhook Hermes — Configuration CLI

## Activer le webhook platform dans config.yaml

```bash
hermes config set platforms.webhook.enabled true
hermes config set platforms.webhook.extra.host "0.0.0.0"
hermes config set platforms.webhook.extra.port 8644
hermes config set platforms.webhook.extra.secret "<votre-secret>"
```

> Certaines installations utilisent `/data/config.yaml` plutôt que `~/.hermes/config.yaml`. Utiliser `hermes config set` fonctionne dans les deux cas.

## Souscrire un webhook

```bash
hermes webhook subscribe saisine \
  --prompt "Tu es l'agent Saisine... [prompt complet]" \
  --deliver telegram \
  --skills procedure-creator
```

- `--deliver telegram` : la réponse finale est envoyée sur Telegram
- `--skills procedure-creator` : charge le skill nécessaire
- Retourne un `webhook_id` (UUID)

## Voir les webhooks actifs

```bash
hermes webhook list
```

## Tester

```bash
curl -X POST http://localhost:8644/webhooks/saisine \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: <secret>" \
  -d '{"test": true, "title": "Demande test"}'
```

## Architecture Notion → Hermes

```
Notion Form (citoyen) 
  → BDD Saisines (page créée)
    → Notion Database Automation (trigger: When page is added)
      → Send webhook (POST natif vers Hermes)
        → Hermes Gateway reçoit le payload
          → Hermes exécute le prompt associé au webhook
            → Pipeline procedure-creator (10 étapes)
              → Update Notion + Email (Himalaya) + Telegram
```

## Pièges

- **Le webhook doit être accessible par Notion.** L'URL en localhost (`http://localhost:8644/...`) ne fonctionne que si Notion et Hermes sont sur la même machine (ou via tunneling ngrok/tailscale). En production, utiliser une URL publique ou un tunnel.
- **Le secret X-Webhook-Secret** doit correspondre entre config.yaml et le champ "secret" configuré dans l'Automation Notion. Sans match → 401.
- **Les webhooks Hermes ne sont persistants que si la gateway tourne.** Vérifier avec `hermes cron status` ou `systemctl --user status hermes-gateway`.
