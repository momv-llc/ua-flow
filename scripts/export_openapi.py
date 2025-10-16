"""Generate OpenAPI schema and a Postman collection from the FastAPI app."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

from fastapi.openapi.utils import get_openapi

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from backend.main import app

DOCS_DIR = Path("docs/api")
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def export_openapi() -> Dict:
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    output = DOCS_DIR / "openapi.json"
    output.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    return schema


def build_postman_collection(schema: Dict) -> Dict:
    base_url = "{{baseUrl}}"
    collection = {
        "info": {
            "name": "UA FLOW API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": "Collection generated from the UA FLOW OpenAPI schema.",
        },
        "item": [],
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8000/api/v1"},
            {"key": "authToken", "value": ""},
        ],
    }

    folders: Dict[str, Dict[str, List]] = {}
    for path, methods in schema.get("paths", {}).items():
        for method, spec in methods.items():
            name = spec.get("summary") or f"{method.upper()} {path}"
            tag = (spec.get("tags") or ["general"])[0]
            folder = folders.setdefault(tag, {"name": tag.title(), "item": []})
            request = {
                "name": name,
                "request": {
                    "method": method.upper(),
                    "header": [],
                    "url": {
                        "raw": f"{base_url}{path}",
                        "host": [base_url],
                        "path": [segment for segment in path.strip("/").split("/") if segment],
                    },
                },
            }
            auth = spec.get("security")
            if auth:
                request["request"]["header"].append(
                    {
                        "key": "Authorization",
                        "value": "Bearer {{authToken}}",
                        "type": "text",
                    }
                )
            folder["item"].append(request)

    collection["item"] = list(folders.values())
    return collection


def export_postman(schema: Dict) -> None:
    collection = build_postman_collection(schema)
    output = DOCS_DIR / "postman_collection.json"
    output.write_text(json.dumps(collection, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    schema = export_openapi()
    export_postman(schema)
    print(f"OpenAPI schema written to {DOCS_DIR / 'openapi.json'}")
    print(f"Postman collection written to {DOCS_DIR / 'postman_collection.json'}")
