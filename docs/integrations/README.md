# UA FLOW Integration Specifications

This directory consolidates the partner interface profiles that back the Integration Hub. Each document captures:

- Supported operations and payload schemas
- Authentication requirements
- Scheduling cadence and retry policy (Celery + Redis)
- Sandbox endpoints that developers can use without touching production services

## Contents

| Integration | Description |
| --- | --- |
| [1C (OData)](1c.md) | Exchange of catalogs, documents, and accounts over 1C OData REST. |
| [ME.Doc](medoc.md) | XML/SOAP exchange with ME.Doc/М.E.Doc including signing flows. |
| [СПІ / ДПС](spi.md) | REST API for tax submissions and report ticketing. |
| [Дія](diia.md) | Partner REST API for notifications, signing, and status checks. |
| [Prozorro](prozorro.md) | Public procurement dataset synchronization and monitoring. |

All integrations share the Celery queue `ua_flow.integrations` with exponential backoff retries (5 attempts, max 10 minutes backoff). See `backend/tasks/integration.py` for task wiring and `docker-compose.yml` for the Redis broker definition.
