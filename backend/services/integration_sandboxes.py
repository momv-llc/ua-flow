"""Static sandbox profiles that mimic external partner APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class IntegrationSandbox:
    slug: str
    title: str
    description: str
    request_example: Dict[str, Any]
    response_example: Dict[str, Any]
    notes: List[str]


SANDBOXES: Dict[str, IntegrationSandbox] = {
    "medoc": IntegrationSandbox(
        slug="medoc",
        title="ME.Doc (M.E.Doc)",
        description=(
            "Отправка бухгалтерской отчётности и актов через SOAP/XML API. "
            "Ответ содержит идентификатор документа и статус приёма."
        ),
        request_example={
            "action": "SendDocument",
            "document": "<Act><Number>123</Number><Date>2024-09-18</Date></Act>",
            "recipient_code": "12345678",
        },
        response_example={
            "status": "accepted",
            "document_id": "md-2024-09-18-0001",
            "processing_time_ms": 820,
        },
        notes=[
            "Документы кодируются в base64 перед отправкой.",
            "Тестовая площадка принимает только идентификаторы получателя, оканчивающиеся на '8'.",
        ],
    ),
    "spi": IntegrationSandbox(
        slug="spi",
        title="СПІ (ДПС)",
        description="REST API для подачи налоговой отчётности и запросов на выписки.",
        request_example={
            "endpoint": "/v1/reports",
            "method": "POST",
            "payload": {"report_type": "pdv", "period": "2024-08"},
        },
        response_example={
            "status": "queued",
            "ticket": "spi-req-2024-09-18-771",
            "sla_minutes": 30,
        },
        notes=[
            "Ответ содержит SLA по готовности результатa.",
            "В песочнице доступна только операция `reports`.",
        ],
    ),
    "diia": IntegrationSandbox(
        slug="diia",
        title="Дія",
        description="REST интеграция для проверки данных пользователя и подписания документов.",
        request_example={
            "endpoint": "/partner/v1/notifications",
            "method": "POST",
            "payload": {"event": "document.sign", "entity_id": "doc-455"},
        },
        response_example={
            "status": "delivered",
            "received_at": "2024-09-18T09:21:00Z",
        },
        notes=[
            "Используется OAuth2 Client Credentials.",
            "Песочница возвращает статус `delivered` сразу же.",
        ],
    ),
    "prozorro": IntegrationSandbox(
        slug="prozorro",
        title="Prozorro",
        description="Публичное API закупок с фильтрацией по ключевым словам и категориям.",
        request_example={
            "endpoint": "/tenders",
            "method": "GET",
            "payload": {"q": "CRM", "status": "active"},
        },
        response_example={
            "total": 2,
            "items": [
                {"tender_id": "UA-2024-08-10-000123", "buyer": "Мінцифра", "amount": 2500000},
                {"tender_id": "UA-2024-08-18-000981", "buyer": "ПриватБанк", "amount": 1250000},
            ],
        },
        notes=[
            "Ответ ограничен первыми двумя результатами.",
            "Для песочницы доступен только фильтр по `q` и `status`.",
        ],
    ),
    "one_c": IntegrationSandbox(
        slug="one_c",
        title="1C:Підприємство",
        description="OData/REST обмен каталогами и документами.",
        request_example={
            "operation": "catalogs",
            "method": "GET",
            "payload": {"limit": 5},
        },
        response_example={
            "items": [
                {"code": "SKU-001", "name": "Генератор 5кВт"},
                {"code": "SKU-002", "name": "Ноутбук UA FLOW"},
            ],
            "next_page_token": "cursor-6",
        },
        notes=[
            "Поддерживаются операции `catalogs`, `documents`, `accounts`.",
            "В песочнице для `documents` возвращается фиктивный номер счета.",
        ],
    ),
}


def list_sandboxes() -> Iterable[IntegrationSandbox]:
    return SANDBOXES.values()


def simulate_exchange(slug: str, payload: Dict[str, Any] | None) -> Dict[str, Any]:
    sandbox = SANDBOXES.get(slug)
    if not sandbox:
        raise KeyError(slug)

    payload = payload or {}

    response = {
        "sandbox": sandbox.slug,
        "echo": payload,
        "response": sandbox.response_example,
        "notes": sandbox.notes,
    }

    if slug == "medoc" and payload.get("document"):
        response["response"] = {
            **sandbox.response_example,
            "checksum": hex(abs(hash(payload["document"])) & 0xFFFF)[2:],
        }
    elif slug == "spi" and payload.get("payload"):
        response["response"] = {
            **sandbox.response_example,
            "payload_digest": len(str(payload["payload"])),
        }

    return response

