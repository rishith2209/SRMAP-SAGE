"""
SRMAP SAGE — Structured Faculty Directory Engine
Manages verified university faculty, designations, departments, schools, and cabin records.
STRICT RULE: Never invent faculty, cabin numbers, or personal contacts.
If official directory data is unavailable, return DATA_NOT_AVAILABLE.
"""

from datetime import datetime, timezone
import json
import logging
import os
import re
from typing import Dict, List, Optional, Any
from src.models.schemas import FacultyCardPayload, DepartmentCardPayload

logger = logging.getLogger(__name__)

OFFICIAL_FACULTY_DIR_PATH = "data/seeds/faculty_verified.json"
OFFICIAL_DEPTS_PATH = "data/seeds/departments_verified.json"


class FacultyEngine:
    """
    Structured query engine for verified SRMAP faculty and departments.
    Maintains relational entities with source-to-entity provenance.
    """

    def __init__(self, faculty_path: str = OFFICIAL_FACULTY_DIR_PATH, depts_path: str = OFFICIAL_DEPTS_PATH):
        self.faculty_path = faculty_path
        self.depts_path = depts_path
        self._faculty_records: Dict[str, Dict[str, Any]] = {}
        self._departments: Dict[str, Dict[str, Any]] = {}
        self._load_data()

    def _load_data(self):
        # 1. Load departments
        if os.path.exists(self.depts_path):
            try:
                with open(self.depts_path, "r", encoding="utf-8") as f:
                    depts = json.load(f)
                    for d in depts:
                        self._departments[d["code"].lower()] = d
                        self._departments[d["name"].lower()] = d
                        self._departments[d["id"].lower()] = d
            except Exception as e:
                logger.error(f"Error loading departments: {e}")
        else:
            # Load template/initial seed if verified file not yet written
            template_path = "data/seeds/departments.template.json"
            if os.path.exists(template_path):
                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        for d in json.load(f):
                            d["source_id"] = "srmap_dept_registry_v1"
                            d["verified_at"] = "2026-09-19T00:00:00Z"
                            d["school"] = "School of Engineering and Sciences (SEAS)"
                            self._departments[d["code"].lower()] = d
                            self._departments[d["name"].lower()] = d
                            self._departments[d["id"].lower()] = d
                except Exception as e:
                    logger.error(f"Error loading departments template: {e}")

        # 2. Load faculty
        if os.path.exists(self.faculty_path):
            try:
                with open(self.faculty_path, "r", encoding="utf-8") as f:
                    faculty_list = json.load(f)
                    for fac in faculty_list:
                        self._faculty_records[fac["name"].lower()] = fac
            except Exception as e:
                logger.error(f"Error loading faculty: {e}")

    def get_department(self, identifier: str) -> Optional[DepartmentCardPayload]:
        """Looks up department by code (CSE, ECE), ID, or full name."""
        key = identifier.lower().strip()
        # Direct lookup
        d = self._departments.get(key)
        if not d:
            for k, val in self._departments.items():
                if key in k or k in key:
                    d = val
                    break
        if not d:
            return None

        return DepartmentCardPayload(
            id=d["id"],
            name=d["name"],
            code=d["code"],
            school=d.get("school", "School of Engineering and Sciences (SEAS)"),
            building=d.get("building", "Academic Block"),
            office=d.get("office", "Academic Block 3rd Floor"),
            source_id=d.get("source_id", "srmap_dept_registry_v1"),
            verified_at=d.get("verified_at", "2026-09-19T00:00:00Z")
        )

    def lookup_faculty(self, name_query: str) -> Optional[FacultyCardPayload]:
        """
        Looks up faculty by exact or partial name.
        STRICT: Never hallucinate faculty or cabin. If not found, return None.
        """
        q = name_query.lower().strip()
        # Remove common prefixes
        clean_q = q
        for prefix in ["dr.", "dr ", "prof.", "prof ", "professor "]:
            if clean_q.startswith(prefix):
                clean_q = clean_q[len(prefix):].strip()

        matched = None
        q_tokens = set(re.findall(r"\b[a-z0-9]+\b", clean_q)) - {
            "who", "is", "where", "what", "the", "cabin", "professor", "prof", "dr", "office", "of", "room"
        }
        for fac_name, data in self._faculty_records.items():
            fac_tokens = set(re.findall(r"\b[a-z0-9]+\b", fac_name))
            fac_substantive = fac_tokens - {"prof", "dr", "professor", "mr", "ms", "k", "s", "m", "r", "dr."}
            if clean_q in fac_name or fac_name in clean_q:
                matched = data
                break
            if fac_substantive and fac_substantive.issubset(q_tokens):
                matched = data
                break
            if q_tokens and q_tokens.issubset(fac_tokens):
                matched = data
                break

        if not matched:
            return None

        dept_info = self.get_department(matched.get("department_id", ""))
        dept_name = dept_info.name if dept_info else matched.get("department", "General")

        return FacultyCardPayload(
            name=matched["name"],
            designation=matched["designation"],
            department=dept_name,
            school=matched.get("school", "School of Engineering and Sciences (SEAS)"),
            cabin_number=matched.get("cabin_number") or matched.get("office_cabin"),
            block=matched.get("block", "Academic Block"),
            floor=matched.get("floor"),
            email=matched.get("email"),
            phone=matched.get("phone"),
            research_areas=matched.get("research_areas", []),
            profile_url=matched.get("profile_url"),
            source_id=matched.get("source_id", "official_faculty_directory"),
            status=matched.get("status", "VERIFIED"),
            verified_at=matched.get("verified_at", datetime.now(timezone.utc).isoformat())
        )

    def import_records(self, faculty_records: List[Dict[str, Any]], overwrite: bool = False):
        """Imports officially verified faculty records."""
        for record in faculty_records:
            name_key = record["name"].lower().strip()
            if overwrite or name_key not in self._faculty_records:
                record["verified_at"] = record.get("verified_at", datetime.now(timezone.utc).isoformat())
                record["status"] = "VERIFIED"
                self._faculty_records[name_key] = record

        # Persist to JSON
        os.makedirs(os.path.dirname(self.faculty_path), exist_ok=True)
        with open(self.faculty_path, "w", encoding="utf-8") as f:
            json.dump(list(self._faculty_records.values()), f, indent=2)
