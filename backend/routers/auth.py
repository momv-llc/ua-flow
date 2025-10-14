from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import UserCreate, UserOut, TokenOut
from models import User
from database import get_db
from security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token

router = APIRouter()

@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(email=payload.email, password_hash=get_password_hash(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenOut)
def login(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id)})
    return TokenOut(access_token=access, refresh_token=refresh)

@router.get("/me", response_model=UserOut)
def me(token: str, db: Session = Depends(get_db)):
    try:
        data = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).get(int(data.get("sub")))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
