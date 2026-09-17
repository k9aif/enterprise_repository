from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import Optional
from backend.database import get_db
from backend.models import Artifact, Standard

router = APIRouter(prefix="/api/v1/search", tags=["Search"])


@router.get("")
def search(q: str, framework: Optional[str] = None, artifact_type: Optional[str] = None, db: Session = Depends(get_db)):
    """Unified search — matches entity names and artifact body content (via
    Postgres full-text search), the way a wiki search reaches into article
    text, not just titles."""
    aq = db.query(
        Artifact.entity_type, Artifact.entity_id, Artifact.entity_name,
        func.max(Artifact.artifact_type).label("artifact_type"),
        func.count(Artifact.id).label("artifact_count"),
    ).filter(
        Artifact.entity_name.ilike(f"%{q}%") |
        func.to_tsvector("english", func.coalesce(Artifact.content_text, "")).match(q)
    )
    if artifact_type:
        aq = aq.filter(Artifact.artifact_type == artifact_type)
    aq = aq.group_by(Artifact.entity_type, Artifact.entity_id, Artifact.entity_name)

    standards_q = db.query(Standard).filter(Standard.name.ilike(f"%{q}%") | Standard.description.ilike(f"%{q}%"))
    if framework:
        standards_q = standards_q.filter(Standard.framework == framework)

    return {
        "entities": [
            {"entity_type": r.entity_type, "entity_id": r.entity_id, "entity_name": r.entity_name,
             "artifact_type": r.artifact_type, "artifact_count": r.artifact_count}
            for r in aq.limit(50).all()
        ],
        "standards": [
            {"id": s.id, "name": s.name, "framework": s.framework, "description": s.description}
            for s in standards_q.limit(20).all()
        ],
    }


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    """Wikipedia-style category browse: frameworks and artifact types as
    entry points into the catalog, independent of free-text search."""
    frameworks = [r[0] for r in db.query(distinct(Standard.framework)).all()]
    artifact_types = [r[0] for r in db.query(distinct(Artifact.artifact_type)).all()]
    return {"frameworks": frameworks, "artifact_types": artifact_types}
