import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Numeric, Boolean,
    DateTime, ForeignKey, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from src.core.database import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    url = Column(Text, unique=True, nullable=True)
    source_type = Column(String(50), nullable=False)  # 'pdf', 'webpage', 'notice', 'dataset'
    authority_level = Column(Integer, nullable=False)  # 1 to 4
    published_at = Column(DateTime(timezone=True), nullable=True)
    crawled_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_verified_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    content_hash = Column(String(64), nullable=False)
    metadata_json = Column("metadata", JSONB, default=dict)

    chunks = relationship("DocumentChunk", back_populates="source", cascade="all, delete-orphan")
    faculty_members = relationship("Faculty", back_populates="source")
    placements = relationship("PlacementStat", back_populates="source")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    section_heading = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    tsv_content = Column(TSVECTOR)
    embedding = Column(Vector(768), nullable=True)

    source = relationship("Source", back_populates="chunks")


class Department(Base):
    __tablename__ = "departments"

    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(20), nullable=False, unique=True)
    block_id = Column(String(50), nullable=True)

    faculty_members = relationship("Faculty", back_populates="department")


class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    designation = Column(String(100), nullable=False)
    department_id = Column(String(50), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    cabin_number = Column(String(100), nullable=True)
    block = Column(String(50), nullable=True)
    floor = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    research_areas = Column(ARRAY(Text), nullable=True)
    profile_url = Column(Text, nullable=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    department = relationship("Department", back_populates="faculty_members")
    source = relationship("Source", back_populates="faculty_members")


class PlacementStat(Base):
    __tablename__ = "placement_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academic_year = Column(String(20), nullable=False)
    company_name = Column(String(200), nullable=False)
    industry = Column(String(100), nullable=True)
    ctc_lpa = Column(Numeric(6, 2), nullable=True)
    offers_count = Column(Integer, default=1)
    eligible_departments = Column(ARRAY(Text), nullable=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    verified = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    source = relationship("Source", back_populates="placements")


class CampusNode(Base):
    __tablename__ = "campus_nodes"

    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)  # 'building', 'hostel', 'lab', 'office', 'dining', 'medical'
    block_code = Column(String(20), nullable=True)
    floor = Column(String(20), nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    landmarks = Column(ARRAY(Text), nullable=True)

    outgoing_edges = relationship("CampusEdge", foreign_keys="CampusEdge.from_node", back_populates="source_node")
    incoming_edges = relationship("CampusEdge", foreign_keys="CampusEdge.to_node", back_populates="target_node")


class CampusEdge(Base):
    __tablename__ = "campus_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_node = Column(String(100), ForeignKey("campus_nodes.id", ondelete="CASCADE"), nullable=False)
    to_node = Column(String(100), ForeignKey("campus_nodes.id", ondelete="CASCADE"), nullable=False)
    distance_meters = Column(Numeric(6, 2), nullable=False)
    accessibility_type = Column(String(50), default="walking")
    instructions = Column(Text, nullable=True)

    source_node = relationship("CampusNode", foreign_keys=[from_node], back_populates="outgoing_edges")
    target_node = relationship("CampusNode", foreign_keys=[to_node], back_populates="incoming_edges")


class CommunityReport(Base):
    __tablename__ = "community_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False)
    generated_answer = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    report_reason = Column(String(100), nullable=False)
    suggested_correction = Column(Text, nullable=True)
    provided_evidence_url = Column(Text, nullable=True)
    github_issue_number = Column(Integer, nullable=True)
    status = Column(String(50), default="pending")  # 'pending', 'verified', 'rejected', 'merged'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Circular(Base):
    __tablename__ = "circulars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    circular_number = Column(String(100), nullable=True)
    title = Column(String(500), nullable=False)
    issuing_authority = Column(String(200), nullable=True)
    published_date = Column(DateTime(timezone=True), nullable=True)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_until = Column(DateTime(timezone=True), nullable=True)
    source_url = Column(Text, nullable=True)
    domain = Column(String(50), default="NOTICES")
    authority_level = Column(Integer, default=1)
    status = Column(String(50), default="CURRENT")  # 'CURRENT', 'SUPERSEDED', 'ARCHIVED'
    supersedes_id = Column(UUID(as_uuid=True), ForeignKey("circulars.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    version_tag = Column(String(50), nullable=False)
    published_date = Column(DateTime(timezone=True), nullable=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    content_hash = Column(String(64), nullable=False)
    superseded_by = Column(UUID(as_uuid=True), nullable=True)
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class SourceFetchLog(Base):
    __tablename__ = "source_fetch_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_url = Column(Text, nullable=False)
    fetch_status = Column(String(50), nullable=False)  # 'SUCCESS', 'AUTH_REQUIRED', 'FAILED'
    http_status = Column(Integer, nullable=True)
    content_hash = Column(String(64), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    fetched_at = Column(DateTime(timezone=True), default=datetime.utcnow)

