# Prozorro Integration

## Overview
- **Protocol:** REST JSON
- **Base URL example:** `https://public.api.openprocurement.org/api/2.5`
- **Queue route:** `ua_flow.integrations`

## Authentication
- Public data API does not require authentication.
- Optional API token for higher rate limits can be stored in integration settings (`headers.Authorization = "Bearer ..."`).

## Endpoints
| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/tenders` | GET | Fetch tenders filtered by query/CPV/status. Supports pagination via `offset`. |
| `/tenders/{id}` | GET | Fetch tender detail. |
| `/contracts` | GET | Monitor contracts tied to UA FLOW customers. |

## Payload Example
```json
{
  "endpoint": "/tenders",
  "method": "GET",
  "payload": {
    "q": "CRM",
    "status": "active"
  }
}
```

## Scheduling & Retries
- Monitoring job every hour for keywords configured in integration settings.
- For each tender, store summary in UA FLOW analytics module.
- Retry policy default (5 attempts, exponential backoff).

## Sandbox
```
POST /api/v1/integrations/sandboxes/prozorro
{
  "endpoint": "/tenders",
  "method": "GET",
  "payload": {"q": "CRM", "status": "active"}
}
```
Sandbox returns two static tender entries for UI visualization.
