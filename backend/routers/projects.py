"""Routers covering teams, projects, sprints and epics."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import audit_log, get_current_user, require_roles
from models import Epic, Project, Sprint, Team, TeamMember, User
from schemas import (
    EpicCreate,
    EpicOut,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    SprintCreate,
    SprintOut,
    SprintUpdate,
    TeamCreate,
    TeamOut,
)


router = APIRouter()


@router.get("/teams", response_model=list[TeamOut])
def list_teams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role in {"admin", "moderator"}:
        return db.query(Team).all()
    return (
        db.query(Team)
        .join(TeamMember)
        .filter(TeamMember.user_id == user.id)
        .all()
    )


@router.post("/teams", response_model=TeamOut, status_code=201)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "moderator")),
):
    team = Team(name=payload.name, description=payload.description or "")
    db.add(team)
    db.commit()
    db.refresh(team)
    db.add(TeamMember(team_id=team.id, user_id=user.id, role="owner"))
    db.commit()
    audit_log(user, "team.created", {"team_id": team.id}, db)
    return team


@router.post("/teams/{team_id}/members", response_model=TeamOut)
def add_team_member(
    team_id: int,
    user_id: int,
    role: str = "member",
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "moderator")),
):
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    existing = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if existing:
        existing.role = role
    else:
        db.add(TeamMember(team_id=team_id, user_id=user_id, role=role))
    db.commit()
    db.refresh(team)
    audit_log(user, "team.member_added", {"team_id": team_id, "user_id": user_id}, db)
    return team


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Project)
    if user.role not in {"admin", "moderator"}:
        query = query.join(Team, isouter=True).join(TeamMember, isouter=True).filter(
            (Project.owner_id == user.id)
            | (TeamMember.user_id == user.id)
        )
    return query.order_by(Project.created_at.desc()).distinct().all()


@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if db.query(Project).filter(Project.key == payload.key).first():
        raise HTTPException(status_code=400, detail="Project key already exists")
    if payload.team_id and not db.get(Team, payload.team_id):
        raise HTTPException(status_code=404, detail="Team not found")
    project = Project(
        key=payload.key.upper(),
        name=payload.name,
        description=payload.description or "",
        methodology=payload.methodology,
        owner_id=user.id,
        team_id=payload.team_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    audit_log(user, "project.created", {"project_id": project.id}, db)
    return project


@router.put("/projects/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if payload.team_id and payload.team_id != project.team_id and not db.get(Team, payload.team_id):
        raise HTTPException(status_code=404, detail="Team not found")
    if user.role not in {"admin", "moderator"} and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    audit_log(user, "project.updated", {"project_id": project.id}, db)
    return project


@router.post("/projects/{project_id}/sprints", response_model=SprintOut, status_code=201)
def create_sprint(
    project_id: int,
    payload: SprintCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user.role not in {"admin", "moderator"} and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    sprint = Sprint(
        project_id=project.id,
        name=payload.name,
        goal=payload.goal or "",
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    audit_log(user, "sprint.created", {"project_id": project.id, "sprint_id": sprint.id}, db)
    return sprint


@router.put("/projects/{project_id}/sprints/{sprint_id}", response_model=SprintOut)
def update_sprint(
    project_id: int,
    sprint_id: int,
    payload: SprintUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sprint = db.get(Sprint, sprint_id)
    if not sprint or sprint.project_id != project_id:
        raise HTTPException(status_code=404, detail="Sprint not found")
    project = db.get(Project, project_id)
    if user.role not in {"admin", "moderator"} and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sprint, field, value)
    db.commit()
    db.refresh(sprint)
    audit_log(user, "sprint.updated", {"project_id": project_id, "sprint_id": sprint_id}, db)
    return sprint


@router.post("/projects/{project_id}/epics", response_model=EpicOut, status_code=201)
def create_epic(
    project_id: int,
    payload: EpicCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user.role not in {"admin", "moderator"} and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    epic = Epic(
        project_id=project.id,
        name=payload.name,
        description=payload.description or "",
        color=payload.color or "#005bbb",
    )
    db.add(epic)
    db.commit()
    db.refresh(epic)
    audit_log(user, "epic.created", {"project_id": project.id, "epic_id": epic.id}, db)
    return epic


@router.get("/projects/{project_id}/epics", response_model=list[EpicOut])
def list_epics(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if user.role not in {"admin", "moderator"} and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return db.query(Epic).filter(Epic.project_id == project_id).all()
