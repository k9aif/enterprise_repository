import os
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, LargeBinary, ForeignKey, CheckConstraint
from pydantic import BaseModel
from typing import Optional
from backend.database import Base

_SCHEMA = os.getenv("POSTGRES_SCHEMA", "enterprise_repository")


# ── ORM models ────────────────────────────────────────────────────────────────

class Artifact(Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        CheckConstraint("content_text IS NOT NULL OR content_bytes IS NOT NULL", name="artifacts_content_check"),
        CheckConstraint("entity_type IN ('sbb','abb')", name="artifacts_entity_type_check"),
        {"schema": _SCHEMA},
    )

    id            = Column(Integer, primary_key=True, index=True)
    entity_type   = Column(String(10), nullable=False)
    entity_id     = Column(Integer, nullable=False)
    entity_name   = Column(String(255), nullable=False)
    artifact_type = Column(String(50), nullable=False)
    filename      = Column(String(255), nullable=False)
    mime_type     = Column(String(100), default="text/plain")
    content_text  = Column(Text)
    content_bytes = Column(LargeBinary)
    content_hash  = Column(String(64), nullable=False)
    size_bytes    = Column(Integer, nullable=False)
    version       = Column(String(20), default="1.0.0")
    git_ref       = Column(String(500))
    captured_by   = Column(String(255))
    created_at    = Column(DateTime, server_default="now()")


class Standard(Base):
    __tablename__ = "standards"
    __table_args__ = {"schema": _SCHEMA}

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(255), nullable=False)
    framework      = Column(String(50), nullable=False)
    version        = Column(String(20))
    mandatory      = Column(Boolean, default=True)
    description    = Column(Text)
    effective_date = Column(Date)
    created_at     = Column(DateTime, server_default="now()")


class EntityStandard(Base):
    __tablename__ = "entity_standards"
    __table_args__ = {"schema": _SCHEMA}

    entity_type = Column(String(10), primary_key=True)
    entity_id   = Column(Integer, primary_key=True)
    entity_name = Column(String(255), nullable=False)
    standard_id = Column(Integer, ForeignKey(f"{_SCHEMA}.standards.id", ondelete="CASCADE"), primary_key=True)


class ComplianceAssessment(Base):
    __tablename__ = "compliance_assessments"
    __table_args__ = {"schema": _SCHEMA}

    id          = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(10), nullable=False)
    entity_id   = Column(Integer, nullable=False)
    entity_name = Column(String(255), nullable=False)
    criteria    = Column(Text, nullable=False)
    verdict     = Column(String(20), nullable=False)
    assessor    = Column(String(255), nullable=False)
    notes       = Column(Text)
    assessed_at = Column(DateTime, server_default="now()")


class Dispensation(Base):
    __tablename__ = "dispensations"
    __table_args__ = {"schema": _SCHEMA}

    id          = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(10), nullable=False)
    entity_id   = Column(Integer, nullable=False)
    entity_name = Column(String(255), nullable=False)
    standard_id = Column(Integer, ForeignKey(f"{_SCHEMA}.standards.id"))
    reason      = Column(Text, nullable=False)
    approver    = Column(String(255), nullable=False)
    granted_at  = Column(DateTime, server_default="now()")
    expires_at  = Column(DateTime, nullable=False)
    status      = Column(String(20), default="active")


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ArtifactCreate(BaseModel):
    entity_type: str
    entity_id: int
    entity_name: str
    artifact_type: str
    filename: str
    mime_type: str = "text/plain"
    content_text: Optional[str] = None
    version: str = "1.0.0"
    git_ref: Optional[str] = None
    captured_by: Optional[str] = None


class ArtifactOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    entity_name: str
    artifact_type: str
    filename: str
    mime_type: str
    content_text: Optional[str]
    content_hash: str
    size_bytes: int
    version: str
    git_ref: Optional[str]
    captured_by: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ArtifactListItem(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    entity_name: str
    artifact_type: str
    filename: str
    version: str
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class StandardCreate(BaseModel):
    name: str
    framework: str
    version: Optional[str] = None
    mandatory: bool = True
    description: Optional[str] = None
    effective_date: Optional[date] = None


class StandardOut(BaseModel):
    id: int
    name: str
    framework: str
    version: Optional[str]
    mandatory: bool
    description: Optional[str]
    effective_date: Optional[date]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class EntityStandardCreate(BaseModel):
    entity_type: str
    entity_id: int
    entity_name: str
    standard_id: int


class DispensationCreate(BaseModel):
    entity_type: str
    entity_id: int
    entity_name: str
    standard_id: Optional[int] = None
    reason: str
    approver: str
    expires_at: datetime


class DispensationOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    entity_name: str
    standard_id: Optional[int]
    reason: str
    approver: str
    granted_at: Optional[datetime]
    expires_at: datetime
    status: str

    model_config = {"from_attributes": True}
