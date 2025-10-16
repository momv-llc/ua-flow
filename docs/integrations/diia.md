# Дія Integration

## Overview
- **Protocol:** REST JSON
- **Base URL example:** `https://diia.partner.gov.ua/partner/v1`
- **Queue route:** `ua_flow.integrations`

## Authentication
- OAuth2 Client Credentials (client id/secret from Мінцифра).
- Access tokens cached in Redis for 30 minutes.
- Required headers: `Authorization: Bearer <token>`, `X-Request-ID` (UUID).

## Supported Operations
| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/status` | GET | Health/status check (used by Integration Hub test endpoint). |
| `/notifications` | POST | Push document/signature events to Дія. |
| `/signatures/{document_id}` | GET | Retrieve signature details and verification hash. |

## Payload Example
```json
{
  "endpoint": "/notifications",
  "method": "POST",
  "payload": {
    "event": "document.sign",
    "entity_id": "doc-455",
    "callback_url": "https://uaflow.example.com/api/hooks/diia"
  }
}
```

## Scheduling & Retries
- Notifications are enqueued immediately upon document status change.
- Failed notifications retried with exponential backoff (up to 5 times).
- Signature status reconciliation every 30 minutes for pending documents.

## Sandbox
```
POST /api/v1/integrations/sandboxes/diia
{
  "endpoint": "/notifications",
  "method": "POST",
  "payload": {"event": "document.sign", "entity_id": "doc-455"}
}
```
Returns `{ "status": "delivered" }` and timestamp for UI confirmation.
