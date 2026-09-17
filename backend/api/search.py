from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import Optional
from backend.database import get_db
from backend.models import Artifact, Standard

router = APIRouter(prefix="/api/v1/search", tags=["Search"])


@router.get("")
def search(q: str, framework: Optional[str] = None, artifact_type: Optional[str] = None,
           business_unit: Optional[str] = None, db: Session = Depends(get_db)):
    """Unified search — matches entity names and artifact body content (via
    Postgres full-text search), the way a wiki search reaches into article
    text, not just titles."""
    aq = db.query(
        Artifact.entity_type, Artifact.entity_id, Artifact.entity_name,
        func.max(Artifact.artifact_type).label("artifact_type"),
        func.max(Artifact.business_unit).label("business_unit"),
        func.count(Artifact.id).label("artifact_count"),
    ).filter(
        Artifact.entity_name.ilike(f"%{q}%") |
        func.to_tsvector("english", func.coalesce(Artifact.content_text, "")).match(q)
    )
    if artifact_type:
        aq = aq.filter(Artifact.artifact_type == artifact_type)
    if business_unit:
        aq = aq.filter(Artifact.business_unit == business_unit)
    aq = aq.group_by(Artifact.entity_type, Artifact.entity_id, Artifact.entity_name)

    standards_q = db.query(Standard).filter(Standard.name.ilike(f"%{q}%") | Standard.description.ilike(f"%{q}%"))
    if framework:
        standards_q = standards_q.filter(Standard.framework == framework)

    return {
        "entities": [
            {"entity_type": r.entity_type, "entity_id": r.entity_id, "entity_name": r.entity_name,
             "artifact_type": r.artifact_type, "business_unit": r.business_unit,
             "artifact_count": r.artifact_count}
            for r in aq.limit(50).all()
        ],
        "standards": [
            {"id": s.id, "name": s.name, "framework": s.framework, "description": s.description}
            for s in standards_q.limit(20).all()
        ],
    }


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    """Wikipedia-style category browse: business units, frameworks, and
    artifact types as entry points into the catalog, independent of
    free-text search."""
    frameworks = [r[0] for r in db.query(distinct(Standard.framework)).all()]
    artifact_types = [r[0] for r in db.query(distinct(Artifact.artifact_type)).all()]
    business_units = [r[0] for r in db.query(distinct(Artifact.business_unit))
                                       .filter(Artifact.business_unit.isnot(None)).all()]
    return {"business_units": sorted(business_units), "frameworks": frameworks, "artifact_types": artifact_types}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    """Browse-page dashboard: business units with a distinct-entity count
    each, the number that actually matters (an entity with 3 artifacts is
    still 1 thing to reuse, not 3)."""
    distinct_entities = (db.query(Artifact.business_unit, Artifact.entity_type, Artifact.entity_id)
                            .filter(Artifact.business_unit.isnot(None))
                            .distinct()
                            .subquery())
    rows = (db.query(distinct_entities.c.business_unit, func.count().label("entity_count"))
              .group_by(distinct_entities.c.business_unit)
              .order_by(distinct_entities.c.business_unit)
              .all())
    return {"business_units": [{"name": r.business_unit, "count": r.entity_count} for r in rows]}
