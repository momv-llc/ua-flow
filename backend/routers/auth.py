"""Authentication and identity management routes."""

from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import audit_log, get_current_user
from models import TwoFactorSecret, User
from schemas import (
    RefreshTokenIn,
    RoleUpdate,
    TokenOut,
    TwoFactorSetupOut,
    TwoFactorVerifyIn,
    UserCreate,
    UserLogin,
    UserOut,
)
from security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_totp_secret,
    get_password_hash,
    verify_password,
    verify_totp,
)


router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(email=payload.email, password_hash=get_password_hash(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    audit_log(user, "user.registered", {"user_id": user.id}, db)
    return user


@router.post("/login", response_model=TokenOut)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    twofa = db.query(TwoFactorSecret).filter(TwoFactorSecret.user_id == user.id).first()
    if twofa and twofa.enabled:
        if not payload.twofa_code or not verify_totp(payload.twofa_code, twofa.secret):
            raise HTTPException(status_code=401, detail="Invalid 2FA code")

    access = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    refresh = create_refresh_token({"sub": str(user.id)})
    audit_log(user, "user.login", {"user_id": user.id}, db)
    return TokenOut(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenOut)
def refresh(payload: RefreshTokenIn, db: Session = Depends(get_db)):
    try:
        data = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    if data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    user = db.get(User, int(data.get("sub", 0)))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    access = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenOut(access_token=access, refresh_token=refresh_token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/me/role", response_model=UserOut)
def update_role(
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can change role")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    audit_log(user, "user.role_updated", {"role": user.role}, db)
    return user


@router.post("/2fa/setup", response_model=TwoFactorSetupOut)
def setup_2fa(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    secret = generate_totp_secret()
    record = db.query(TwoFactorSecret).filter(TwoFactorSecret.user_id == user.id).first()
    if record:
        record.secret = secret
        record.enabled = 0
    else:
        record = TwoFactorSecret(user_id=user.id, secret=secret, enabled=0)
        db.add(record)
    db.commit()

    issuer = quote("UA FLOW")
    uri = f"otpauth://totp/{issuer}:{quote(user.email)}?secret={secret}&issuer={issuer}"
    audit_log(user, "user.2fa.setup", {"user_id": user.id}, db)
    return TwoFactorSetupOut(secret=secret, uri=uri)


@router.post("/2fa/enable")
def enable_2fa(
    payload: TwoFactorVerifyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = db.query(TwoFactorSecret).filter(TwoFactorSecret.user_id == user.id).first()
    if not record:
        raise HTTPException(status_code=400, detail="2FA not initialized")
    if not verify_totp(payload.code, record.secret):
        raise HTTPException(status_code=400, detail="Invalid verification code")
    record.enabled = 1
    db.commit()
    audit_log(user, "user.2fa.enabled", {"user_id": user.id}, db)
    return {"enabled": True}


@router.post("/2fa/disable")
def disable_2fa(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(TwoFactorSecret).filter(TwoFactorSecret.user_id == user.id).first()
    if not record:
        raise HTTPException(status_code=400, detail="2FA not enabled")
    record.enabled = 0
    db.commit()
    audit_log(user, "user.2fa.disabled", {"user_id": user.id}, db)
    return {"enabled": False}
