import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models import Artifact, ArtifactCreate, ArtifactOut, ArtifactListItem
from backend.auth_deps import require_api_key

router = APIRouter(prefix="/api/v1/artifacts", tags=["Artifacts"])


@router.get("", response_model=List[ArtifactListItem])
def list_artifacts(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    artifact_type: Optional[str] = None,
    business_unit: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Artifact)
    if entity_type:
        q = q.filter(Artifact.entity_type == entity_type)
    if entity_id is not None:
        q = q.filter(Artifact.entity_id == entity_id)
    if artifact_type:
        q = q.filter(Artifact.artifact_type == artifact_type)
    if business_unit:
        q = q.filter(Artifact.business_unit == business_unit)
    return q.order_by(Artifact.created_at.desc()).all()


@router.get("/{artifact_id}", response_model=ArtifactOut)
def get_artifact(artifact_id: int, db: Session = Depends(get_db)):
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(404, "Artifact not found")
    return artifact


@router.get("/{artifact_id}/raw")
def get_artifact_raw(artifact_id: int, db: Session = Depends(get_db)):
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(404, "Artifact not found")
    if artifact.content_text is not None:
        return Response(content=artifact.content_text, media_type=artifact.mime_type)
    return Response(content=bytes(artifact.content_bytes), media_type=artifact.mime_type)


@router.post("", response_model=ArtifactOut, status_code=201)
def publish_artifact(payload: ArtifactCreate, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    if not payload.content_text:
        raise HTTPException(422, "content_text is required (binary artifact capture is a later phase)")
    content_bytes = payload.content_text.encode("utf-8")
    if len(content_bytes) > 5 * 1024 * 1024:
        raise HTTPException(422, "Artifact exceeds 5MB — this MVP stores text content only in Postgres")
    artifact = Artifact(
        **payload.model_dump(),
        content_hash=hashlib.sha256(content_bytes).hexdigest(),
        size_bytes=len(content_bytes),
        created_at=datetime.now(timezone.utc),
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


@router.delete("/{artifact_id}", status_code=204)
def delete_artifact(artifact_id: int, db: Session = Depends(get_db), _: None = Depends(require_api_key)):
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(404, "Artifact not found")
    db.delete(artifact)
    db.commit()
