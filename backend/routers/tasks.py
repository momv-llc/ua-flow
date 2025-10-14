from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from schemas import TaskCreate, TaskOut
from models import Task, User
from database import get_db
from security import decode_token
from typing import List, Optional

router = APIRouter()

def current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        data = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).get(int(data.get("sub")))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=List[TaskOut])
def list_tasks(user: User = Depends(current_user), db: Session = Depends(get_db)):
    items = db.query(Task).filter((Task.owner_id == user.id) | (user.role == "admin")).all()
    return items

@router.post("/", response_model=TaskOut)
def create_task(payload: TaskCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    task = Task(title=payload.title, description=payload.description, owner_id=user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    task.title = payload.title
    task.description = payload.description
    db.commit()
    db.refresh(task)
    return task

@router.patch("/{task_id}/status", response_model=TaskOut)
def set_status(task_id: int, status: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if status not in ["ToDo", "In Progress", "Done"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    task.status = status
    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}")
def delete_task(task_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(task)
    db.commit()
    return {"ok": True}
