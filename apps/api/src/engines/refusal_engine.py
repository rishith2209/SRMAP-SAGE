"""
SRMAP SAGE — Structured Refusal Engine (Phase 5)
Provides explicit, typed refusals when facts cannot be verified with 100% certainty.
Prevents guessing, inferring, or hallucinating across all domains.
"""

import logging
from typing import Optional, Tuple
from src.models.schemas import RefusalReason

logger = logging.getLogger(__name__)

STRICT_FALLBACK_PHRASE = "I couldn't find a reliable official SRMAP source confirming this information."


class RefusalEngine:
    """
    Constructs informative, evidence-grounded refusals.
    Never invents facts, cabin numbers, dates, or fees when official evidence is missing.
    """

    @staticmethod
    def create_refusal(
        code: str,
        query: str,
        missing_detail: str,
        required_evidence: Optional[str] = None
    ) -> Tuple[str, RefusalReason]:
        """
        Returns (formatted_user_message, RefusalReason object).
        """
        if code == "INSUFFICIENT_EVIDENCE":
            req = required_evidence or "Official SRMAP policy document or signed circular"
            msg = (
                f"{STRICT_FALLBACK_PHRASE} The official knowledge base does not contain verified "
                f"documentation regarding {missing_detail}."
            )
        elif code == "SOURCE_UNAVAILABLE":
            req = required_evidence or "Official university registrar or departmental circular"
            msg = (
                f"{STRICT_FALLBACK_PHRASE} The specific official document covering {missing_detail} "
                f"is currently not published or indexed in SAGE."
            )
        elif code == "AUTHENTICATION_REQUIRED":
            req = required_evidence or "Authenticated SRMAP Student Portal (ERP / HRD Portal)"
            msg = (
                f"This information requires authentication through internal SRMAP portals. "
                f"{missing_detail} cannot be retrieved via public unauthenticated channels."
            )
        elif code == "CONFLICT_UNRESOLVED":
            req = required_evidence or "Official Registrar Clarification Circular"
            msg = (
                f"I found conflicting official records regarding {missing_detail}, and no superseding "
                f"circular has been established. I cannot make a definitive claim without official clarification."
            )
        elif code == "OUTDATED_INFORMATION":
            req = required_evidence or "Current Academic Year Circular"
            msg = (
                f"The available records for {missing_detail} are archived/superseded historical notices. "
                f"No verified active circular for the current term is on record."
            )
        elif code == "UNKNOWN_ENTITY":
            req = required_evidence or "Official SRMAP Faculty/Department Directory or Campus Master Plan"
            msg = (
                f"{STRICT_FALLBACK_PHRASE} The requested entity ({missing_detail}) is not registered "
                f"in the official university directory or campus spatial registry."
            )
        elif code == "UNVERIFIED_CURRENT_INFORMATION":
            req = required_evidence or "Official 2026-27 Finance Committee / Academic Circular"
            msg = (
                f"I don't have a verified official source for {missing_detail}. "
                f"Official schedules have not yet been released or verified for this period."
            )
        else:
            req = required_evidence or "Official SRMAP Publication"
            msg = f"{STRICT_FALLBACK_PHRASE} {missing_detail}"

        reason = RefusalReason(
            code=code,
            message=msg,
            required_evidence=req
        )
        return msg, reason
