from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Artifact, EntityStandard, Standard, ComplianceAssessment, Dispensation

router = APIRouter(prefix="/api/v1/entities", tags=["Entities"])


@router.get("/{entity_type}/{entity_id}")
def get_entity_article(entity_type: str, entity_id: int, db: Session = Depends(get_db)):
    """The 'article page' aggregate — everything the Repository knows about one
    SBB or ABB, assembled server-side so the webui can render a single
    Wikipedia-style page without N round-trips."""
    artifacts = (db.query(Artifact)
                   .filter(Artifact.entity_type == entity_type, Artifact.entity_id == entity_id)
                   .order_by(Artifact.created_at.desc())
                   .all())
    entity_name = artifacts[0].entity_name if artifacts else None
    business_unit = next((a.business_unit for a in artifacts if a.business_unit), None)

    standards = (db.query(Standard)
                   .join(EntityStandard, EntityStandard.standard_id == Standard.id)
                   .filter(EntityStandard.entity_type == entity_type, EntityStandard.entity_id == entity_id)
                   .all())

    assessments = (db.query(ComplianceAssessment)
                     .filter(ComplianceAssessment.entity_type == entity_type,
                             ComplianceAssessment.entity_id == entity_id)
                     .order_by(ComplianceAssessment.assessed_at.desc())
                     .all())

    dispensations = (db.query(Dispensation)
                        .filter(Dispensation.entity_type == entity_type, Dispensation.entity_id == entity_id)
                        .order_by(Dispensation.granted_at.desc())
                        .all())

    # "What links here" — other entities sharing at least one standard with this one.
    backlinks = []
    if standards:
        standard_ids = [s.id for s in standards]
        rows = (db.query(EntityStandard)
                  .filter(EntityStandard.standard_id.in_(standard_ids))
                  .filter(~((EntityStandard.entity_type == entity_type) & (EntityStandard.entity_id == entity_id)))
                  .distinct()
                  .all())
        seen = set()
        for r in rows:
            key = (r.entity_type, r.entity_id)
            if key not in seen:
                seen.add(key)
                backlinks.append({"entity_type": r.entity_type, "entity_id": r.entity_id, "entity_name": r.entity_name})

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "business_unit": business_unit,
        "artifacts": [
            {"id": a.id, "artifact_type": a.artifact_type, "filename": a.filename, "version": a.version,
             "content_hash": a.content_hash, "size_bytes": a.size_bytes, "created_at": a.created_at,
             "git_ref": a.git_ref, "captured_by": a.captured_by}
            for a in artifacts
        ],
        "standards": [{"id": s.id, "name": s.name, "framework": s.framework, "mandatory": s.mandatory} for s in standards],
        "compliance_assessments": [
            {"id": c.id, "criteria": c.criteria, "verdict": c.verdict, "assessor": c.assessor, "assessed_at": c.assessed_at}
            for c in assessments
        ],
        "dispensations": [
            {"id": d.id, "reason": d.reason, "approver": d.approver, "status": d.status, "expires_at": d.expires_at}
            for d in dispensations
        ],
        "backlinks": backlinks,
    }
