# СПІ / ДПС Integration

## Overview
- **Protocol:** REST JSON
- **Base URL example:** `https://api.tax.gov.ua/spi/v1`
- **Queue route:** `ua_flow.integrations`

## Authentication
- OAuth2 Client Credentials; tokens cached in Redis with TTL 55 minutes.
- Required scopes: `reports.submit`, `reports.status`.

## Endpoints
| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/reports` | POST | Submit PDV/ESV reports. Returns ticket id. |
| `/reports/{ticket}` | GET | Poll ticket status; statuses: `queued`, `processing`, `accepted`, `rejected`. |
| `/extracts` | GET | Download tax extracts. Query params: `type`, `period_from`, `period_to`. |

## Payload Example
```json
{
  "endpoint": "/reports",
  "method": "POST",
  "payload": {
    "report_type": "pdv",
    "period": "2024-08",
    "attachments": ["base64-pdf"]
  }
}
```

## Scheduling & Retries
- Report submission: triggered manually or via automation; automatic retry if status != `accepted` after 30 minutes.
- Ticket polling: Celery beat every 5 minutes until final status.
- Retry policy identical to other integrations (5 attempts, exponential backoff).

## Sandbox
```
POST /api/v1/integrations/sandboxes/spi
{
  "endpoint": "/reports",
  "method": "POST",
  "payload": {"report_type": "pdv", "period": "2024-08"}
}
```
Sandbox returns a fake ticket id and SLA value for UI previews.
