from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models import (
    Standard, StandardCreate, StandardOut,
    EntityStandard, EntityStandardCreate,
    Dispensation, DispensationCreate, DispensationOut,
)
from backend.auth_deps import require_api_key

router = APIRouter(prefix="/api/v1/standards", tags=["Standards"])
dispensations_router = APIRouter(prefix="/api/v1/dispensations", tags=["Dispensations"])


@router.get("", response_model=List[StandardOut])
def list_standards(framework: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Standard)
    if framework:
        q = q.filter(Standard.framework == framework)
    return q.order_by(Standard.framework, Standard.name).all()


@router.post("", response_model=StandardOut, status_code=201)
def create_standard(payload: StandardCreate, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    existing = db.query(Standard).filter(Standard.name == payload.name, Standard.framework == payload.framework).first()
    if existing:
        raise HTTPException(409, "Standard already registered for this framework")
    standard = Standard(**payload.model_dump())
    db.add(standard)
    db.commit()
    db.refresh(standard)
    return standard


@router.get("/{standard_id}/entities")
def entities_for_standard(standard_id: int, db: Session = Depends(get_db)):
    rows = db.query(EntityStandard).filter(EntityStandard.standard_id == standard_id).all()
    return [{"entity_type": r.entity_type, "entity_id": r.entity_id, "entity_name": r.entity_name} for r in rows]


@router.post("/link", status_code=201)
def link_entity_to_standard(payload: EntityStandardCreate, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    if not db.query(Standard).filter(Standard.id == payload.standard_id).first():
        raise HTTPException(404, "Standard not found")
    link = EntityStandard(**payload.model_dump())
    db.merge(link)
    db.commit()
    return {"linked": True}


@dispensations_router.get("", response_model=List[DispensationOut])
def list_dispensations(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Dispensation)
    if status:
        q = q.filter(Dispensation.status == status)
    return q.order_by(Dispensation.expires_at.asc()).all()


@dispensations_router.post("", response_model=DispensationOut, status_code=201)
def grant_dispensation(payload: DispensationCreate, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    dispensation = Dispensation(**payload.model_dump(), granted_at=datetime.now(timezone.utc))
    db.add(dispensation)
    db.commit()
    db.refresh(dispensation)
    return dispensation


@dispensations_router.patch("/{dispensation_id}/revoke", response_model=DispensationOut)
def revoke_dispensation(dispensation_id: int, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    dispensation = db.query(Dispensation).filter(Dispensation.id == dispensation_id).first()
    if not dispensation:
        raise HTTPException(404, "Dispensation not found")
    dispensation.status = "revoked"
    db.commit()
    db.refresh(dispensation)
    return dispensation
