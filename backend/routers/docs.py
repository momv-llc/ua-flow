from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from schemas import DocCreate, DocOut
from models import Doc, User
from database import get_db
from security import decode_token

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

@router.get("/", response_model=List[DocOut])
def list_docs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    items = db.query(Doc).order_by(Doc.id.desc()).all()
    return items

@router.post("/", response_model=DocOut)
def create_doc(payload: DocCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = Doc(title=payload.title, content_md=payload.content_md or "", created_by=user.id)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

@router.put("/{doc_id}", response_model=DocOut)
def update_doc(doc_id: int, payload: DocCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = db.query(Doc).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Doc not found")
    doc.title = payload.title
    doc.content_md = payload.content_md or ""
    db.commit()
    db.refresh(doc)
    return doc

@router.delete("/{doc_id}")
def delete_doc(doc_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = db.query(Doc).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Doc not found")
    db.delete(doc)
    db.commit()
    return {"ok": True}
