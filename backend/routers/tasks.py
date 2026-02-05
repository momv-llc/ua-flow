"""Routers for UA Flow Core task management features."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import audit_log, get_current_user
from models import Epic, Project, Sprint, Task, TaskComment, TaskStatus, User
from schemas import (
    ReportFilters,
    TaskCommentCreate,
    TaskCommentOut,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)


router = APIRouter()


def _ensure_project_membership(project: Project | None, user: User) -> None:
    if project and user.role not in {"admin", "moderator"}:
        team_member_ids = {member.user_id for member in project.team.members} if project.team else {project.owner_id}
        if user.id not in team_member_ids:
            raise HTTPException(status_code=403, detail="User is not part of this project")


@router.get("/", response_model=List[TaskOut])
def list_tasks(
    project_id: Optional[int] = None,
    sprint_id: Optional[int] = None,
    status: Optional[TaskStatus] = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return tasks for the current user with optional filters."""

    query = db.query(Task)
    if user.role not in {"admin", "moderator"}:
        query = query.filter((Task.owner_id == user.id) | (Task.assignee_id == user.id))
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if sprint_id:
        query = query.filter(Task.sprint_id == sprint_id)
    if status:
        query = query.filter(Task.status == status)
    return query.order_by(Task.created_at.desc()).all()


@router.post("/", response_model=TaskOut, status_code=201)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new task inside a project or backlog."""

    project = db.get(Project, payload.project_id) if payload.project_id else None
    if project:
        _ensure_project_membership(project, user)
    sprint = db.get(Sprint, payload.sprint_id) if payload.sprint_id else None
    epic = db.get(Epic, payload.epic_id) if payload.epic_id else None

    task = Task(
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        type=payload.type,
        due_date=payload.due_date,
        estimate_hours=payload.estimate_hours or 0,
        tags=payload.tags or "",
        owner_id=user.id,
        assignee_id=payload.assignee_id,
        project_id=project.id if project else None,
        sprint_id=sprint.id if sprint else None,
        epic_id=epic.id if epic else None,
    )

    db.add(task)
    db.commit()
    db.refresh(task)
    audit_log(user, "task.created", {"task_id": task.id}, db)
    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _ensure_project_membership(task.project, user)
    if user.role not in {"admin", "moderator"} and user.id not in {task.owner_id, task.assignee_id}:
        raise HTTPException(status_code=403, detail="Forbidden")
    return task


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    _ensure_project_membership(task.project, user)
    if user.role not in {"admin", "moderator"} and task.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    audit_log(user, "task.updated", {"task_id": task.id}, db)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if user.role not in {"admin", "moderator"} and task.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    db.delete(task)
    db.commit()
    audit_log(user, "task.deleted", {"task_id": task_id}, db)


@router.post("/{task_id}/comments", response_model=TaskCommentOut, status_code=201)
def add_comment(
    task_id: int,
    payload: TaskCommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    comment = TaskComment(task_id=task.id, author_id=user.id, message=payload.message)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    audit_log(user, "task.comment.added", {"task_id": task.id, "comment_id": comment.id}, db)
    return comment


@router.get("/board/view", response_model=Dict[str, List[TaskOut]])
def kanban_board(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _ensure_project_membership(project, user)

    lanes: Dict[str, List[TaskOut]] = defaultdict(list)
    for task in project.tasks:
        lanes[task.status.value].append(task)
    return lanes


@router.post("/reports/burndown")
def burndown_report(
    filters: ReportFilters,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return a simplified burndown data structure for charts."""

    query = db.query(Task)
    if filters.project_id:
        project = db.get(Project, filters.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        _ensure_project_membership(project, user)
        query = query.filter(Task.project_id == filters.project_id)
    if filters.team_id:
        query = query.join(Project).filter(Project.team_id == filters.team_id)
    if filters.sprint_id:
        query = query.filter(Task.sprint_id == filters.sprint_id)

    tasks = query.all()
    total = len(tasks)
    done = len([t for t in tasks if t.status == TaskStatus.done])
    remaining = total - done
    today = date.today()

    # Simplified timeline with 5 data points.
    chart = []
    for idx in range(5):
        days_from_start = idx * 2
        chart.append(
            {
                "date": (today - timedelta(days=days_from_start)).isoformat(),
                "remaining": max(remaining - idx, 0),
            }
        )

    return {
        "total": total,
        "done": done,
        "remaining": remaining,
        "chart": list(reversed(chart)),
    }
