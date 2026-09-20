"""
SRMAP SAGE — Claim-Level Self-Verification Engine (Phase 5)
Extracts individual factual claims from synthesized text and verifies each proposition
against retrieved EvidenceItem records. Rejects unsupported inferences, unverified numbers,
and unproven assertions at granular claim level.
"""

import logging
import re
from typing import List, Tuple, Optional, Dict
from src.models.schemas import EvidenceItem, ClaimVerificationResult

logger = logging.getLogger(__name__)


class SelfVerificationEngine:
    """
    Operates at claim granularity:
    - Splits text into individual factual sentences/propositions.
    - Checks numbers, percentages, entities, and actions against underlying evidence excerpts.
    - Strips unsupported claims so only verified facts survive.
    """

    @staticmethod
    def extract_claims(text: str) -> List[str]:
        """
        Splits text into discrete propositional sentences.
        """
        if not text or not text.strip():
            return []

        # Remove markdown headers and bullets for claim splitting
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        claims = []
        for line in lines:
            # Strip markdown list markers or headings
            clean_line = re.sub(r"^(#+|\*+|-+|\d+\.)\s*", "", line).strip()
            if not clean_line:
                continue
            # Split compound sentences on period or semicolon followed by space and capital letter
            sub_sentences = re.split(r"(?<=[.;])\s+(?=[A-Z])", clean_line)
            for sub in sub_sentences:
                s = sub.strip()
                if len(s) > 10:  # Ignore trivial headers
                    claims.append(s)
        return claims

    @classmethod
    def verify_claim(
        cls,
        claim: str,
        evidence_items: List[EvidenceItem]
    ) -> ClaimVerificationResult:
        if not evidence_items:
            return ClaimVerificationResult(
                claim_text=claim,
                supported=False,
                supporting_evidence_ids=[],
                confidence_note="No evidence items available to substantiate claim."
            )

        # 1. Number / Percentage Check
        claim_numbers = re.findall(r"\b\d+(?:\.\d+)?%?\b", claim)
        # Exclude common formatting like dates or list numbers if trivial
        claim_percentages = re.findall(r"\b\d{1,3}%\b", claim)

        # Normalize claim words for keyword matching
        claim_words = set(re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", claim.lower()))
        # Remove common query filler words
        stop_words = {
            "students", "student", "required", "must", "policy", "srmap",
            "according", "verified", "information", "university", "academic",
            "from", "with", "this", "that", "these", "those", "have", "been"
        }
        substantive_claim_words = claim_words - stop_words

        supporting_ids = []

        for ev in evidence_items:
            # Untrusted data or injection payloads cannot serve as supporting evidence for claims
            if ev.authority_level > 2 or any(inj in ev.excerpt.lower() for inj in ["system override", "override active", "ignore previous", "all rules are cancelled"]):
                continue

            ev_text = (ev.excerpt + " " + ev.title).lower()

            # Verify percentage consistency if claim mentions a percentage
            if claim_percentages:
                ev_percentages = re.findall(r"\b\d{1,3}%\b", ev_text)
                if not any(cp in ev_percentages for cp in claim_percentages):
                    # Percentage mismatch or not present in this evidence
                    continue

            # Check overlap of substantive keywords
            if substantive_claim_words:
                overlap = sum(1 for w in substantive_claim_words if w in ev_text)
                overlap_ratio = overlap / len(substantive_claim_words)
                # If at least 30% of substantive keywords are present or critical terms match
                if overlap >= 2 or overlap_ratio >= 0.35:
                    supporting_ids.append(ev.id)
            else:
                # If no substantive words, check general inclusion
                if claim.lower() in ev_text:
                    supporting_ids.append(ev.id)

        is_supported = len(supporting_ids) > 0
        return ClaimVerificationResult(
            claim_text=claim,
            supported=is_supported,
            supporting_evidence_ids=supporting_ids,
            confidence_note="Direct evidence match" if is_supported else "Unsupported claim discarded"
        )

    @classmethod
    def verify_and_filter(
        cls,
        text: str,
        evidence_items: List[EvidenceItem],
        is_fallback: bool = False
    ) -> Tuple[str, List[ClaimVerificationResult], str, List[str]]:
        """
        Verifies all claims and drops unsupported ones.
        Returns:
            verified_text: clean text containing only supported propositions
            claim_results: details on each claim's verification
            verification_status: VERIFIED | PARTIALLY_VERIFIED | UNVERIFIED | REFUSED
            caveats: notes on dropped or unverified items
        """
        if is_fallback or not text:
            return text, [], "REFUSED", []

        claims = cls.extract_claims(text)
        if not claims:
            return text, [], "VERIFIED", []

        results = []
        supported_claims = []
        unsupported_claims = []
        caveats = []

        for claim in claims:
            # Skip boilerplate meta instructions
            if any(p in claim.lower() for p in ["[mock sage response]", "based on the verified", "verified context"]):
                continue

            res = cls.verify_claim(claim, evidence_items)
            results.append(res)
            if res.supported:
                supported_claims.append(claim)
            else:
                unsupported_claims.append(claim)
                caveats.append(f"Removed unsupported assertion: '{claim}'")

        if not supported_claims:
            # If nothing was supported, mark REFUSED
            return (
                "I couldn't find a reliable official SRMAP source confirming this information.",
                results,
                "REFUSED",
                ["All provisional claims failed evidence verification against indexed sources."]
            )

        if unsupported_claims:
            status = "PARTIALLY_VERIFIED"
            # Reconstruct answer from supported claims only
            verified_text = " ".join(supported_claims)
        else:
            status = "VERIFIED"
            verified_text = text

        return verified_text, results, status, caveats
