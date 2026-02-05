"""Client helpers for UA FLOW integration hub."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Dict

import httpx

from backend.models import IntegrationType
from models import IntegrationType


class IntegrationError(Exception):
    """Raised when an integration exchange fails."""


@dataclass
class IntegrationResult:
    """Structured response from an integration client."""

    status_code: int
    body: Any
    request_payload: Dict[str, Any]


class IntegrationClient:
    """Base client with convenience helpers for REST and SOAP style APIs."""

    def __init__(self, settings: Dict[str, Any] | None = None) -> None:
        self.settings = settings or {}
        self.base_url: str | None = self.settings.get("base_url")
        self.timeout: float = float(self.settings.get("timeout", 10))
        self.headers: Dict[str, str] = self.settings.get("headers", {})
        self.username: str | None = self.settings.get("username")
        self.password: str | None = self.settings.get("password")
        # Dry run mode allows QA environments without network access to still succeed.
        self.dry_run: bool = bool(self.settings.get("dry_run", not bool(self.base_url)))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def ping(self) -> IntegrationResult:
        """Check that credentials and endpoints are reachable."""

        return self._execute("GET", self.settings.get("ping_path", "/health"), {})

    def sync(self, payload: Dict[str, Any]) -> IntegrationResult:
        """Perform a synchronization exchange."""

        return self._execute("POST", self.settings.get("sync_path", "/sync"), payload)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _execute(self, method: str, path: str, payload: Dict[str, Any]) -> IntegrationResult:
        if self.dry_run:
            body = {
                "mode": "dry-run",
                "method": method,
                "path": path,
                "payload": payload,
            }
            return IntegrationResult(status_code=200, body=body, request_payload=payload)

        if not self.base_url:
            raise IntegrationError("Base URL is not configured for the integration")

        auth = None
        if self.username and self.password:
            auth = (self.username, self.password)

        json_payload = payload or None
        params = None
        if method.upper() == "GET":
            params = payload or None
            json_payload = None

        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                response = client.request(
                    method,
                    path,
                    json=json_payload,
                    params=params,
                    headers=self.headers,
                    auth=auth,
                )
        except httpx.HTTPError as exc:  # pragma: no cover - network errors
            raise IntegrationError(str(exc)) from exc

        content_type = response.headers.get("content-type", "")
        body: Any
        if "application/json" in content_type.lower():
            body = response.json()
        else:
            body = response.text

        if response.is_error:
            raise IntegrationError(f"{response.status_code}: {body}")

        return IntegrationResult(
            status_code=response.status_code,
            body=body,
            request_payload=payload,
        )


class OneCClient(IntegrationClient):
    """Connects to 1C REST gateway."""

    def sync(self, payload: Dict[str, Any]) -> IntegrationResult:
        operation = payload.get("operation", "catalogs")
        route_map = self.settings.get(
            "routes",
            {
                "catalogs": "/odata/standard.odata/Catalog_Products",
                "documents": "/odata/standard.odata/Document_SalesOrder",
                "accounts": "/odata/standard.odata/Document_Invoice",
            },
        )
        path = route_map.get(operation, self.settings.get("sync_path", "/sync"))
        method = payload.get("method", "GET" if operation == "catalogs" else "POST").upper()
        # The 1C API expects query parameters for filters.
        request_payload = payload.get("payload", {})
        if method == "GET":
            return self._execute("GET", path, request_payload)
        return self._execute(method, path, request_payload)


class MedocClient(IntegrationClient):
    """SOAP-like client for Medoc XML exchanges."""

    def sync(self, payload: Dict[str, Any]) -> IntegrationResult:
        document = payload.get("document") or "<Document/>"
        # Medoc often expects base64-encoded XML payloads.
        encoded = base64.b64encode(document.encode("utf-8")).decode("utf-8")
        envelope = {
            "action": payload.get("action", "SendDocument"),
            "document": encoded,
        }
        return self._execute("POST", self.settings.get("sync_path", "/api/xml"), envelope)


class SPIClient(IntegrationClient):
    """Integrator for the ДПС/СПІ REST endpoints."""

    def sync(self, payload: Dict[str, Any]) -> IntegrationResult:
        path = payload.get("endpoint", "/v1/reports")
        method = payload.get("method", "GET").upper()
        data = payload.get("payload", {})
        return self._execute(method, path, data)


class DiiaClient(IntegrationClient):
    """API client for Дія."""

    def ping(self) -> IntegrationResult:
        # Diia provides a status endpoint for partner integrations.
        return self._execute("GET", self.settings.get("ping_path", "/partner/v1/status"), {})

    def sync(self, payload: Dict[str, Any]) -> IntegrationResult:
        path = payload.get("endpoint", "/partner/v1/notifications")
        method = payload.get("method", "POST").upper()
        data = payload.get("payload", {})
        return self._execute(method, path, data)


class ProzorroClient(IntegrationClient):
    """REST client for Prozorro public procurement."""

    def sync(self, payload: Dict[str, Any]) -> IntegrationResult:
        path = payload.get("endpoint", "/tenders")
        method = payload.get("method", "GET").upper()
        data = payload.get("payload", {})
        return self._execute(method, path, data)


class WebhookClient(IntegrationClient):
    """Simple webhook dispatcher."""

    def sync(self, payload: Dict[str, Any]) -> IntegrationResult:
        path = self.settings.get("sync_path") or "/"
        method = payload.get("method", "POST").upper()
        body = payload.get("payload", payload)
        return self._execute(method, path, body)

    def ping(self) -> IntegrationResult:
        handshake_payload = {"event": "handshake", "timestamp": payload_timestamp()}
        return self._execute("POST", self.settings.get("sync_path") or "/", handshake_payload)


def payload_timestamp() -> str:
    from datetime import datetime

    return datetime.utcnow().isoformat() + "Z"


def build_client(integration_type: IntegrationType, settings: Dict[str, Any] | None) -> IntegrationClient:
    """Factory returning the correct client implementation."""

    client_map = {
        IntegrationType.one_c: OneCClient,
        IntegrationType.medoc: MedocClient,
        IntegrationType.spi: SPIClient,
        IntegrationType.diya: DiiaClient,
        IntegrationType.prozorro: ProzorroClient,
        IntegrationType.webhook: WebhookClient,
    }
    try:
        client_cls = client_map[integration_type]
    except KeyError as exc:  # pragma: no cover - defensive programming
        raise IntegrationError(f"Unsupported integration type: {integration_type}") from exc

    return client_cls(settings)
