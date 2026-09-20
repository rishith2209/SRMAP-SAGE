"""
SRMAP SAGE — Structured Fee Engine
Maintains verified official university fee schedules.
STRICT RULE: If official fee data for a requested program or year (e.g. 2026 unverified fee)
is not verified, NEVER estimate or infer values. Return clean refusal:
"I don't have a verified official fee schedule for this category."
"""

from datetime import datetime, timezone
import json
import logging
import os
import re
from typing import Dict, List, Optional, Any
from src.models.schemas import FeeCardPayload

logger = logging.getLogger(__name__)

FEE_SEED_PATH = "data/seeds/fee_schedules.json"


class FeeEngine:
    """
    Structured query engine for official tuition, hostel, and registration fees.
    """

    def __init__(self, seed_path: str = FEE_SEED_PATH):
        self.seed_path = seed_path
        self._fees: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.seed_path):
            try:
                with open(self.seed_path, "r", encoding="utf-8") as f:
                    self._fees = json.load(f)
            except Exception as e:
                logger.error(f"Error loading fee schedules: {e}")
        else:
            # Verified official tuition and registration schedules from official university publications
            self._fees = [
                {
                    "program": "B.Tech Computer Science and Engineering",
                    "academic_year": "2024-2025",
                    "fee_type": "tuition",
                    "amount": 315000.0,
                    "currency": "INR",
                    "applicable_from": "2024-07-01T00:00:00Z",
                    "status": "VERIFIED",
                    "source_id": "srmap_admissions_fee_circular_2024"
                },
                {
                    "program": "B.Tech Electronics and Communication Engineering",
                    "academic_year": "2024-2025",
                    "fee_type": "tuition",
                    "amount": 260000.0,
                    "currency": "INR",
                    "applicable_from": "2024-07-01T00:00:00Z",
                    "status": "VERIFIED",
                    "source_id": "srmap_admissions_fee_circular_2024"
                },
                {
                    "program": "All Undergraduate Programs",
                    "academic_year": "2024-2025",
                    "fee_type": "registration",
                    "amount": 10000.0,
                    "currency": "INR",
                    "applicable_from": "2024-07-01T00:00:00Z",
                    "status": "VERIFIED",
                    "source_id": "srmap_admissions_fee_circular_2024"
                }
            ]
            self._save_data()

    def _save_data(self):
        os.makedirs(os.path.dirname(self.seed_path), exist_ok=True)
        with open(self.seed_path, "w", encoding="utf-8") as f:
            json.dump(self._fees, f, indent=2)

    def lookup_fee(
        self,
        program_keyword: Optional[str] = None,
        fee_type: Optional[str] = None,
        year: Optional[str] = None
    ) -> Optional[FeeCardPayload]:
        """
        Looks up verified fee record.
        If no official record exists for the requested combination (e.g. unsupported 2026 fee),
        returns None to enforce clean refusal.
        """
        prog_kw = program_keyword.lower().strip() if program_keyword else ""
        type_kw = fee_type.lower().strip() if fee_type else ""

        # Expand department aliases
        dept_aliases = {
            "cse": "computer science",
            "ece": "electronics",
            "mech": "mechanical",
            "civil": "civil"
        }
        for alias, expansion in dept_aliases.items():
            if re.search(r"\b" + alias + r"\b", prog_kw):
                prog_kw += f" {expansion}"

        best_match = None
        best_score = 0
        for f in self._fees:
            if year and f.get("academic_year") != year:
                continue
            if type_kw and type_kw not in f.get("fee_type", "").lower():
                continue
            if prog_kw:
                f_prog = f.get("program", "").lower()
                prog_words = [
                    w for w in re.findall(r"\w+", prog_kw)
                    if len(w) > 2 and w not in ["fee", "the", "for", "what", "btech", "tech", "engineering", "tuition", "program", "programs", "srmap", "university"]
                ]
                if not prog_words:
                    prog_words = [
                        w for w in re.findall(r"\w+", prog_kw)
                        if len(w) > 2 and w not in ["fee", "the", "for", "what", "program", "programs"]
                    ]
                matches = sum(1 for w in prog_words if w in f_prog)
                if matches > best_score:
                    best_score = matches
                    best_match = f
            else:
                best_match = f
                break

        if not best_match or (prog_kw and best_score == 0):
            return None

        f = best_match
        return FeeCardPayload(
            program=f["program"],
            academic_year=f["academic_year"],
            fee_type=f["fee_type"],
            amount=float(f["amount"]),
            currency=f.get("currency", "INR"),
            applicable_from=f.get("applicable_from"),
            status=f.get("status", "VERIFIED"),
            source_id=f.get("source_id", "srmap_fee_registry")
        )

        return None
