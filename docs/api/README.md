# UA FLOW API Artifacts

This folder contains generated assets for the public UA FLOW API:

- `openapi.json` — machine-readable OpenAPI schema, created via `python scripts/export_openapi.py`.
- `postman_collection.json` — Postman collection derived from the OpenAPI spec for quick testing.

Regenerate these assets whenever the FastAPI routes change:

```bash
python scripts/export_openapi.py
```
