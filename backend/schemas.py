"""Pydantic schemas for API payloads and responses."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field

from backend.models import (
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
# Time & Billing
# ---------------------------------------------------------------------------


class WorklogCreate(BaseModel):
    task_id: Optional[int] = None
    project_id: Optional[int] = None
    spent_hours: int = Field(gt=0)
    work_date: date
    description: Optional[str] = ""


class WorklogOut(BaseModel):
    id: int
    user_id: int
    task_id: Optional[int]
    project_id: Optional[int]
    spent_hours: int
    work_date: date
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserRateCreate(BaseModel):
    user_id: int
    currency: str = "USD"
    hourly_rate: int = Field(gt=0)
    valid_from: date
    valid_to: Optional[date] = None


class UserRateOut(BaseModel):
    id: int
    user_id: int
    currency: str
    hourly_rate: int
    valid_from: date
    valid_to: Optional[date]

    class Config:
        from_attributes = True


class ProjectBudgetUpsert(BaseModel):
    project_id: int
    currency: str = "USD"
    planned_hours: int = Field(ge=0)
    planned_cost: int = Field(ge=0)


class ProjectBudgetOut(BaseModel):
    id: int
    project_id: int
    currency: str
    planned_hours: int
    planned_cost: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectExpenseCreate(BaseModel):
    project_id: int
    description: Optional[str] = ""
    amount: int = Field(gt=0)
    currency: str = "USD"
    expense_date: date
    category: Optional[str] = "general"


class ProjectExpenseOut(BaseModel):
    id: int
    project_id: int
    description: str
    amount: int
    currency: str
    expense_date: date
    category: str
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceItemCreate(BaseModel):
    description: str
    quantity: int = Field(gt=0)
    unit_price: int = Field(gt=0)


class InvoiceCreate(BaseModel):
    project_id: Optional[int] = None
    client_name: str
    client_details: Optional[str] = ""
    currency: str = "USD"
    issue_date: date
    due_date: Optional[date] = None
    tax_percent: Optional[float] = 0.0
    items: List[InvoiceItemCreate]


class InvoiceItemOut(BaseModel):
    id: int
    description: str
    quantity: int
    unit_price: int
    line_total: int

    class Config:
        from_attributes = True


class InvoiceOut(BaseModel):
    id: int
    project_id: Optional[int]
    external_id: str
    client_name: str
    client_details: str
    currency: str
    status: str
    issue_date: date
    due_date: Optional[date]
    subtotal: int
    tax_amount: int
    total: int
    created_at: datetime
    items: List[InvoiceItemOut]

    class Config:
        from_attributes = True


class IntegrationLogOut(BaseModel):
    id: int
    direction: str
    status: str
    payload: str
    created_at: datetime

    class Config:
        from_attributes = True


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
