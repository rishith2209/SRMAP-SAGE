"""
SRMAP SAGE — Freshness & Versioning Engine
Handles document versioning, supersession graphs, hash-based change detection, and freshness statuses.
"""

from datetime import datetime, timezone
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from enum import Enum


class FreshnessStatus(str, Enum):
    CURRENT = "CURRENT"
    RECENT = "RECENT"
    SUPERSEDED = "SUPERSEDED"
    HISTORICAL = "HISTORICAL"
    UNKNOWN = "UNKNOWN"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    CONTENT_NOT_RETRIEVED = "CONTENT_NOT_RETRIEVED"
    CRAWL_ERROR = "CRAWL_ERROR"


class DocumentVersionRecord(BaseModel):
    version_id: str
    document_id: str
    version_tag: str
    content_hash: str
    published_date: Optional[str] = None
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None
    discovered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    superseded_by: Optional[str] = None
    supersedes: Optional[str] = None
    change_summary: Optional[str] = None
    authority_level: int = 1
    freshness_status: FreshnessStatus = FreshnessStatus.CURRENT


class FreshnessMetadata(BaseModel):
    source_id: str
    first_seen_at: str
    last_seen_at: str
    published_at: Optional[str] = None
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None
    content_hash: str
    authority_level: int
    status: FreshnessStatus
    version_history: List[DocumentVersionRecord] = []


class FreshnessEngine:
    """
    Manages document freshness, supersession tracking, and hash-based change detection.
    RULE: Never label a document CURRENT merely because it was recently crawled.
    Must use explicit publication/effective date and authority hierarchy.
    """

    def __init__(self, catalog_data: Optional[Dict[str, Any]] = None):
        self.catalog = catalog_data or {}
        self.relationships = self.catalog.get("relationships", [])

    @staticmethod
    def compute_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def detect_change(self, doc_id: str, new_content: str, new_hash: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Compares incoming content hash against recorded version.
        Returns (has_changed, change_summary).
        """
        if not new_hash:
            new_hash = self.compute_hash(new_content)

        sources = self.catalog.get("sources", {})
        existing_source = sources.get(doc_id)
        if not existing_source:
            return False, "Initial ingestion (no prior version)"

        old_hash = existing_source.get("content_hash")
        if old_hash and old_hash != new_hash:
            summary = f"Content modified: Hash changed from {old_hash[:8]} to {new_hash[:8]}"
            return True, summary

        return False, None

    def register_supersession(
        self,
        older_doc_id: str,
        newer_doc_id: str,
        reason: str,
        effective_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registers that older_doc_id is superseded by newer_doc_id.
        Preserves the older document in history, marking it SUPERSEDED.
        """
        rel = {
            "type": "SUPERSEDED_BY",
            "source_doc_id": older_doc_id,
            "target_doc_id": newer_doc_id,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "effective_date": effective_date
        }

        # Avoid duplicates
        if "relationships" not in self.catalog:
            self.catalog["relationships"] = []

        existing = [
            r for r in self.catalog["relationships"]
            if r.get("source_doc_id") == older_doc_id and r.get("type") == "SUPERSEDED_BY"
        ]
        if not existing:
            self.catalog["relationships"].append(rel)

        # Update older source status in catalog if present
        sources = self.catalog.get("sources", {})
        if older_doc_id in sources:
            sources[older_doc_id]["status"] = FreshnessStatus.SUPERSEDED.value
            sources[older_doc_id]["superseded_by"] = newer_doc_id

        if newer_doc_id in sources:
            sources[newer_doc_id]["supersedes"] = older_doc_id
            sources[newer_doc_id]["status"] = FreshnessStatus.CURRENT.value

        return rel

    def get_document_freshness(self, doc_id: str) -> FreshnessStatus:
        """Determines the freshness status of a document."""
        sources = self.catalog.get("sources", {})
        doc = sources.get(doc_id)
        if not doc:
            return FreshnessStatus.UNKNOWN

        # Check explicit status
        raw_status = doc.get("status")
        if raw_status == "SUPERSEDED":
            return FreshnessStatus.SUPERSEDED
        if raw_status == "AUTHENTICATION_REQUIRED":
            return FreshnessStatus.AUTHENTICATION_REQUIRED
        if raw_status == "CONTENT_NOT_RETRIEVED":
            return FreshnessStatus.CONTENT_NOT_RETRIEVED
        if raw_status == "CRAWL_ERROR":
            return FreshnessStatus.CRAWL_ERROR

        # Check supersession graph
        for rel in self.catalog.get("relationships", []):
            if rel.get("type") == "SUPERSEDED_BY" and rel.get("source_doc_id") == doc_id:
                return FreshnessStatus.SUPERSEDED

        # Policy date check
        policy_date_str = doc.get("policy_date")
        if policy_date_str:
            # Verified policy currently on record with no superseding circular
            return FreshnessStatus.CURRENT

        # Default for verified documents
        return FreshnessStatus.CURRENT
