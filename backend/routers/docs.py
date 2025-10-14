"""Routes for collaborative documentation and e-signature flows."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import audit_log, get_current_user
from models import Doc, DocSignature, DocVersion, User
from schemas import (
    DocCreate,
    DocOut,
    DocSignatureCreate,
    DocSignatureOut,
    DocUpdate,
    DocVersionOut,
)


router = APIRouter()


@router.get("/", response_model=list[DocOut])
def list_docs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Doc).order_by(Doc.updated_at.desc()).all()


@router.post("/", response_model=DocOut, status_code=201)
def create_doc(
    payload: DocCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = Doc(title=payload.title, content_md=payload.content_md or "", created_by=user.id)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    version = DocVersion(doc_id=doc.id, version=1, content_md=doc.content_md, created_by=user.id)
    db.add(version)
    db.commit()
    audit_log(user, "doc.created", {"doc_id": doc.id}, db)
    return doc


@router.get("/{doc_id}", response_model=DocOut)
def get_doc(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.get(Doc, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.put("/{doc_id}", response_model=DocOut)
def update_doc(
    doc_id: int,
    payload: DocUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.get(Doc, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(doc, field, value)
    db.commit()
    db.refresh(doc)

    latest_version = (
        db.query(DocVersion)
        .filter(DocVersion.doc_id == doc.id)
        .order_by(DocVersion.version.desc())
        .first()
    )
    new_version_number = (latest_version.version if latest_version else 0) + 1
    db.add(
        DocVersion(
            doc_id=doc.id,
            version=new_version_number,
            content_md=doc.content_md,
            created_by=user.id,
        )
    )
    db.commit()
    audit_log(user, "doc.updated", {"doc_id": doc.id, "version": new_version_number}, db)
    return doc


@router.delete("/{doc_id}", status_code=204)
def delete_doc(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.get(Doc, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    audit_log(user, "doc.deleted", {"doc_id": doc_id}, db)


@router.get("/{doc_id}/versions", response_model=list[DocVersionOut])
def list_versions(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.get(Doc, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return (
        db.query(DocVersion)
        .filter(DocVersion.doc_id == doc_id)
        .order_by(DocVersion.version.desc())
        .all()
    )


@router.post("/{doc_id}/sign", response_model=DocSignatureOut, status_code=201)
def sign_document(
    doc_id: int,
    payload: DocSignatureCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.get(Doc, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    signature = DocSignature(
        doc_id=doc.id,
        user_id=user.id,
        provider=payload.provider or "КЕП",
        signature_payload=payload.signature_payload,
    )
    db.add(signature)
    db.commit()
    db.refresh(signature)
    audit_log(
        user,
        "doc.signed",
        {"doc_id": doc.id, "provider": signature.provider, "signature_id": signature.id},
        db,
    )
    return signature


@router.get("/{doc_id}/signatures", response_model=list[DocSignatureOut])
def get_signatures(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.get(Doc, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return (
        db.query(DocSignature)
        .filter(DocSignature.doc_id == doc_id)
        .order_by(DocSignature.signed_at.desc())
        .all()
    )
