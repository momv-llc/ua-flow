"""Pydantic schemas for API payloads and responses."""

from __future__ import annotations

from decimal import Decimal
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field

from backend.models import (
    PaymentGateway,
    PaymentMethodType,
    PaymentPlanInterval,
    SubscriptionStatus,
    TransactionStatus,
    IntegrationType,
    SprintStatus,
    TaskPriority,
    TaskStatus,
    TicketPriority,
    TicketStatus,
)


# ---------------------------------------------------------------------------
# Auth & Users
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    twofa_code: Optional[str] = Field(default=None, min_length=6, max_length=6)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenIn(BaseModel):
    refresh_token: str


class TwoFactorSetupOut(BaseModel):
    secret: str
    uri: str


class TwoFactorVerifyIn(BaseModel):
    code: str


class RoleUpdate(BaseModel):
    role: str


class SettingOut(BaseModel):
    key: str
    value: str
    updated_at: datetime

    class Config:
        from_attributes = True


class SettingUpdate(BaseModel):
    value: str


# ---------------------------------------------------------------------------
# Teams & Projects
# ---------------------------------------------------------------------------


class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class TeamMemberOut(BaseModel):
    id: int
    user_id: int
    role: str
    added_at: datetime

    class Config:
        from_attributes = True


class TeamOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    members: List[TeamMemberOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    key: str = Field(min_length=2, max_length=10)
    name: str
    description: Optional[str] = ""
    methodology: str = Field(default="kanban")
    team_id: Optional[int] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    methodology: Optional[str] = None
    team_id: Optional[int] = None


class ProjectOut(BaseModel):
    id: int
    key: str
    name: str
    description: str
    methodology: str
    owner_id: int
    team_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SprintCreate(BaseModel):
    name: str
    goal: Optional[str] = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class SprintUpdate(BaseModel):
    name: Optional[str] = None
    goal: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[SprintStatus] = None


class SprintOut(BaseModel):
    id: int
    project_id: int
    name: str
    goal: str
    start_date: Optional[date]
    end_date: Optional[date]
    status: SprintStatus

    class Config:
        from_attributes = True


class EpicCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    color: Optional[str] = "#005bbb"


class EpicOut(BaseModel):
    id: int
    project_id: int
    name: str
    description: str
    color: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    type: str = "task"
    due_date: Optional[date] = None
    estimate_hours: Optional[int] = Field(default=0, ge=0)
    tags: Optional[str] = ""
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None
    sprint_id: Optional[int] = None
    epic_id: Optional[int] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    type: Optional[str] = None
    due_date: Optional[date] = None
    estimate_hours: Optional[int] = Field(default=None, ge=0)
    tags: Optional[str] = None
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None
    sprint_id: Optional[int] = None
    epic_id: Optional[int] = None


class TaskOut(TaskBase):
    id: int
    owner_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TaskCommentCreate(BaseModel):
    message: str


class TaskCommentOut(BaseModel):
    id: int
    task_id: int
    author_id: Optional[int]
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Docs
# ---------------------------------------------------------------------------


class DocCreate(BaseModel):
    title: str
    content_md: Optional[str] = ""


class DocUpdate(BaseModel):
    title: Optional[str] = None
    content_md: Optional[str] = None


class DocOut(BaseModel):
    id: int
    title: str
    content_md: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocVersionOut(BaseModel):
    id: int
    version: int
    content_md: Optional[str]
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class DocSignatureCreate(BaseModel):
    provider: Optional[str] = "КЕП"
    signature_payload: str


class DocSignatureOut(BaseModel):
    id: int
    doc_id: int
    user_id: Optional[int]
    provider: str
    signed_at: datetime
    signature_payload: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Support Desk
# ---------------------------------------------------------------------------


class TicketCreate(BaseModel):
    subject: str
    body: str
    priority: TicketPriority = TicketPriority.normal
    channel: str = "web"


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assignee_id: Optional[int] = None


class TicketOut(BaseModel):
    id: int
    subject: str
    body: str
    status: TicketStatus
    priority: TicketPriority
    channel: str
    sla_due: Optional[datetime]
    requester_id: Optional[int]
    assignee_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class TicketCommentCreate(BaseModel):
    message: str
    via: str = "web"


class TicketCommentOut(BaseModel):
    id: int
    ticket_id: int
    author_id: Optional[int]
    message: str
    via: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Integrations & Analytics
# ---------------------------------------------------------------------------


class IntegrationCreate(BaseModel):
    name: str
    integration_type: IntegrationType
    description: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class IntegrationOut(BaseModel):
    id: int
    name: str
    integration_type: IntegrationType
    description: str
    is_active: bool
    status: str
    last_synced_at: Optional[datetime]
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IntegrationLogOut(BaseModel):
    id: int
    direction: str
    status: str
    payload: str
    response_code: int
    created_at: datetime

    class Config:
        from_attributes = True


class IntegrationActionResult(BaseModel):
    status: str
    details: Dict[str, Any]


class IntegrationTaskStatus(BaseModel):
    task_id: str
    state: str
    retries: int
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class IntegrationSandboxOut(BaseModel):
    slug: str
    title: str
    description: str
    request_example: Dict[str, Any]
    response_example: Dict[str, Any]
    notes: list[str]


class IntegrationSandboxExchange(BaseModel):
    sandbox: str
    echo: Dict[str, Any]
    response: Dict[str, Any]
    notes: list[str]


class MarketplaceAppOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    category: str
    website: Optional[str]
    icon: Optional[str]
    installed: bool = False
    installed_at: Optional[datetime] = None


class MarketplaceInstallOut(BaseModel):
    message: str
    app: MarketplaceAppOut


class DashboardMetric(BaseModel):
    name: str
    value: Any
    delta: Optional[float] = None


class ReportFilters(BaseModel):
    project_id: Optional[int] = None
    sprint_id: Optional[int] = None
    team_id: Optional[int] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None


# ---------------------------------------------------------------------------
# Billing & Payments
# ---------------------------------------------------------------------------


class PaymentPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3, default="UAH")
    interval: PaymentPlanInterval = PaymentPlanInterval.monthly
    trial_days: int = Field(default=14, ge=0)
    features: List[str] = Field(default_factory=list)
    is_active: bool = True


class PaymentPlanCreate(PaymentPlanBase):
    pass


class PaymentPlanOut(PaymentPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentMethodCreate(BaseModel):
    method_type: PaymentMethodType
    gateway: PaymentGateway
    label: str
    details: Dict[str, Any] = Field(default_factory=dict)


class PaymentMethodOut(BaseModel):
    id: int
    method_type: PaymentMethodType
    gateway: PaymentGateway
    label: str
    details: Dict[str, Any]
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    plan_id: int
    payment_method_id: Optional[int] = None
    auto_renew: bool = True


class SubscriptionOut(BaseModel):
    id: int
    plan_id: int
    status: SubscriptionStatus
    auto_renew: bool
    current_period_end: Optional[datetime]
    trial_ends_at: Optional[datetime]
    payment_method_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata_json")

    class Config:
        from_attributes = True
        populate_by_name = True


class CheckoutRequest(BaseModel):
    plan_id: int
    payment_method_id: Optional[int] = None
    gateway: Optional[PaymentGateway] = None
    amount_override: Optional[Decimal] = Field(default=None, ge=0)


class CheckoutResponse(BaseModel):
    reference: str
    status: TransactionStatus
    amount: Decimal
    currency: str
    payment_url: Optional[str] = None


class PaymentTransactionOut(BaseModel):
    id: int
    reference: str
    gateway: PaymentGateway
    amount: Decimal
    currency: str
    status: TransactionStatus
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
    subscription_id: Optional[int]
    plan_id: Optional[int]

    class Config:
        from_attributes = True


class TransactionStatusUpdate(BaseModel):
    status: TransactionStatus
    error_message: Optional[str] = None
