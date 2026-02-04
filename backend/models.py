"""SQLAlchemy ORM models for UA FLOW backend."""

from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


class TaskStatus(str, enum.Enum):
    """Supported statuses for project tasks."""

    todo = "ToDo"
    in_progress = "In Progress"
    review = "Review"
    done = "Done"


class TaskPriority(str, enum.Enum):
    """Supported priority levels for tasks."""

    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"


class TicketStatus(str, enum.Enum):
    """Lifecycle statuses for Service Desk tickets."""

    new = "New"
    in_progress = "In Progress"
    waiting = "Waiting"
    resolved = "Resolved"
    closed = "Closed"


class TicketPriority(str, enum.Enum):
    """SLA-driven ticket priorities."""

    low = "Low"
    normal = "Normal"
    high = "High"
    urgent = "Urgent"


class IntegrationType(str, enum.Enum):
    """Available integration connector types."""

    one_c = "1C"
    medoc = "Medoc"
    spi = "SPI"
    diya = "Diia"
    prozorro = "Prozorro"
    webhook = "Webhook"


class InvoiceStatus(str, enum.Enum):
    """Lifecycle statuses for invoices."""

    draft = "draft"
    sent = "sent"
    paid = "paid"
    cancelled = "cancelled"


class SprintStatus(str, enum.Enum):
    """Scrum sprint lifecycle states."""

    planned = "Planned"
    active = "Active"
    completed = "Completed"
    closed = "Closed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="owner")
    assignments = relationship(
        "Task",
        back_populates="assignee",
        foreign_keys="Task.assignee_id",
    )
    tickets = relationship(
        "SupportTicket",
        back_populates="requester",
        foreign_keys="SupportTicket.requester_id",
    )
    ticket_assignments = relationship(
        "SupportTicket",
        back_populates="assignee",
        foreign_keys="SupportTicket.assignee_id",
    )


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), unique=True, nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="team")
    members = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
    )


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_user"),)

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="member")
    added_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="members")
    user = relationship("User")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    key = Column(String(15), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    methodology = Column(String(50), default="kanban")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    team = relationship("Team", back_populates="projects")
    owner = relationship("User")
    tasks = relationship("Task", back_populates="project")
    sprints = relationship(
        "Sprint",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), nullable=False)
    goal = Column(Text, default="")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(Enum(SprintStatus), default=SprintStatus.planned)

    project = relationship("Project", back_populates="sprints")
    tasks = relationship("Task", back_populates="sprint")


class Epic(Base):
    __tablename__ = "epics"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    color = Column(String(20), default="#005bbb")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")
    tasks = relationship("Task", back_populates="epic")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.todo)
    priority = Column(Enum(TaskPriority), default=TaskPriority.medium)
    type = Column(String(50), default="task")
    due_date = Column(Date, nullable=True)
    estimate_hours = Column(Integer, default=0)
    tags = Column(Text, default="")
    owner_id = Column(Integer, ForeignKey("users.id"))
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    sprint_id = Column(Integer, ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True)
    epic_id = Column(Integer, ForeignKey("epics.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="tasks", foreign_keys=[owner_id])
    assignee = relationship(
        "User",
        back_populates="assignments",
        foreign_keys=[assignee_id],
    )
    project = relationship("Project", back_populates="tasks")
    sprint = relationship("Sprint", back_populates="tasks")
    epic = relationship("Epic", back_populates="tasks")
    comments = relationship(
        "TaskComment",
        back_populates="task",
        cascade="all, delete-orphan",
    )


class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="comments")
    author = relationship("User")


class Doc(Base):
    __tablename__ = "docs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content_md = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship(
        "DocVersion",
        back_populates="doc",
        cascade="all, delete-orphan",
    )
    signatures = relationship(
        "DocSignature",
        back_populates="doc",
        cascade="all, delete-orphan",
    )


class DocVersion(Base):
    __tablename__ = "doc_versions"

    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer, ForeignKey("docs.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    content_md = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=datetime.utcnow)

    doc = relationship("Doc", back_populates="versions")
    author = relationship("User")


class DocSignature(Base):
    __tablename__ = "doc_signatures"

    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer, ForeignKey("docs.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    provider = Column(String(100), default="КЕП")
    signed_at = Column(DateTime, default=datetime.utcnow)
    signature_payload = Column(Text, default="")

    doc = relationship("Doc", back_populates="signatures")
    user = relationship("User")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.new)
    priority = Column(Enum(TicketPriority), default=TicketPriority.normal)
    channel = Column(String(50), default="web")
    sla_due = Column(DateTime, nullable=True)
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requester = relationship(
        "User",
        back_populates="tickets",
        foreign_keys=[requester_id],
    )
    assignee = relationship(
        "User",
        back_populates="ticket_assignments",
        foreign_keys=[assignee_id],
    )
    comments = relationship(
        "SupportComment",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )


class SupportComment(Base):
    __tablename__ = "support_comments"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    message = Column(Text, nullable=False)
    via = Column(String(50), default="web")
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("SupportTicket", back_populates="comments")
    author = relationship("User")


class IntegrationConnection(Base):
    __tablename__ = "integration_connections"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    integration_type = Column(Enum(IntegrationType), nullable=False)
    description = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(100), default="Never synced")

    logs = relationship(
        "IntegrationLog",
        back_populates="connection",
        cascade="all, delete-orphan",
    )


class IntegrationLog(Base):
    __tablename__ = "integration_logs"

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("integration_connections.id", ondelete="CASCADE"))
    direction = Column(String(50), default="outbound")
    status = Column(String(50), default="success")
    payload = Column(Text, default="")
    response_code = Column(Integer, default=200)
    created_at = Column(DateTime, default=datetime.utcnow)

    connection = relationship("IntegrationConnection", back_populates="logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String(255), nullable=False)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    actor = relationship("User")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TwoFactorSecret(Base):
    __tablename__ = "twofactor_secrets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    secret = Column(String(255), nullable=False)
    enabled = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class MarketplaceApp(Base):
    __tablename__ = "marketplace_apps"

    id = Column(Integer, primary_key=True)
    slug = Column(String(150), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    category = Column(String(120), default="general")
    website = Column(String(255), default="")
    icon = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    installations = relationship(
        "MarketplaceInstallation",
        back_populates="app",
        cascade="all, delete-orphan",
    )


class MarketplaceInstallation(Base):
    __tablename__ = "marketplace_installations"

    id = Column(Integer, primary_key=True)
    app_id = Column(Integer, ForeignKey("marketplace_apps.id", ondelete="CASCADE"))
    installed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    settings = Column(JSON, default=dict)
    installed_at = Column(DateTime, default=datetime.utcnow)

    app = relationship("MarketplaceApp", back_populates="installations")
    installer = relationship("User")


class Worklog(Base):
    __tablename__ = "worklogs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)

    spent_hours = Column(Integer, nullable=False)  # stored in minutes for precision
    work_date = Column(Date, nullable=False)
    description = Column(Text, default="")

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    task = relationship("Task")
    project = relationship("Project")


class UserRate(Base):
    __tablename__ = "user_rates"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    currency = Column(String(10), default="USD")
    hourly_rate = Column(Integer, nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class ProjectBudget(Base):
    __tablename__ = "project_budgets"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), unique=True)
    currency = Column(String(10), default="USD")
    planned_hours = Column(Integer, default=0)
    planned_cost = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")


class ProjectExpense(Base):
    __tablename__ = "project_expenses"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    description = Column(Text, default="")
    amount = Column(Integer, nullable=False)
    currency = Column(String(10), default="USD")
    expense_date = Column(Date, nullable=False)
    category = Column(String(100), default="general")

    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    external_id = Column(String(50), unique=True, nullable=False)

    client_name = Column(String(255), nullable=False)
    client_details = Column(Text, default="")

    currency = Column(String(10), default="USD")
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.draft)

    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)

    subtotal = Column(Integer, default=0)
    tax_amount = Column(Integer, default=0)
    total = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    project = relationship("Project")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"))
    description = Column(Text, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Integer, nullable=False)
    line_total = Column(Integer, nullable=False)

    invoice = relationship("Invoice", back_populates="items")
