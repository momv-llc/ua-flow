# ME.Doc / М.E.Doc Integration

## Overview
- **Protocol:** HTTPS + XML/SOAP over REST bridge
- **Base URL example:** `https://medoc.partner.ua/api/xml`
- **Queue route:** `ua_flow.integrations`

## Authentication
- Token-based header `X-Medoc-Token` issued per tenant.
- TLS mutual authentication optional (configurable per customer).
- Documents are base64-encoded before submission.

## Operations
| Action | Description | Request Body | Response |
| --- | --- | --- | --- |
| `SendDocument` | Передача первичных документов (акты, счета) | `<Document>` XML, base64 encoded | `document_id`, status `accepted`/`rejected` |
| `GetStatus` | Проверка статуса отправленного документа | `document_id` | `status`, `last_update` |
| `GetIncoming` | Загрузка входящих документов | Optional filters `date_from`, `company_code` | Array of documents |

## Payload Example
```json
{
  "action": "SendDocument",
  "document": "<Act><Number>123</Number><Date>2024-09-18</Date></Act>",
  "recipient_code": "12345678"
}
```

The Integration Hub encodes the document in Base64 and wraps it into the SOAP envelope expected by ME.Doc.

## Scheduling & Retries
- Outgoing queue every 5 minutes.
- Status reconciliation hourly for the last 48 hours of documents.
- Celery retries network/HTTP errors (5 attempts, exponential backoff, max 15 minutes).

## Sandbox
```
POST /api/v1/integrations/sandboxes/medoc
{
  "action": "SendDocument",
  "document": "<Act><Number>1</Number></Act>",
  "recipient_code": "00000008"
}
```
Returns a deterministic `document_id` and checksum for front-end testing.
