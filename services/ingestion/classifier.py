import re
from typing import Dict, List, Tuple


class DomainClassifier:
    """
    Classifies SRMAP documents and web content into authoritative knowledge domains.
    Strictly differentiates employee recruitment from student placements,
    and distinct internship policies.
    """

    POLICY_RULES: List[Tuple[re.Pattern, str, str, str]] = [
        # (Pattern, Title, Primary Domain, Secondary Domain)
        (
            re.compile(r"student.*attendance.*policy", re.IGNORECASE),
            "Student Attendance Policy",
            "ATTENDANCE",
            "ACADEMICS"
        ),
        (
            re.compile(r"student.*on[- ]duty.*policy", re.IGNORECASE),
            "Student On-Duty (OD) Policy",
            "ON_DUTY",
            "ATTENDANCE"
        ),
        (
            re.compile(r"student.*code.*of.*conduct", re.IGNORECASE),
            "Student Code of Conduct Policy",
            "CODE_OF_CONDUCT",
            "STUDENT_AFFAIRS"
        ),
        (
            re.compile(r"urop.*project.*policy", re.IGNORECASE),
            "Undergraduate Research Opportunities Programme (UROP) Policy",
            "UROP",
            "RESEARCH"
        ),
        (
            re.compile(r"b\.?tech.*placement.*policy", re.IGNORECASE),
            "B.Tech Placement Policy",
            "PLACEMENTS",
            "CAREER_SERVICES"
        ),
        (
            re.compile(r"deferred.*placement.*policy", re.IGNORECASE),
            "Deferred Placement Policy of SRM University-AP",
            "DEFERRED_PLACEMENT",
            "ENTREPRENEURSHIP"
        ),
        (
            re.compile(r"professional.*internship.*policy", re.IGNORECASE),
            "Professional Internship Policy of SRM University-AP",
            "INTERNSHIPS",
            "ACADEMICS"
        ),
        (
            re.compile(r"student.*internship.*policy", re.IGNORECASE),
            "Student Internship Policy",
            "INTERNSHIPS",
            "STUDENT_AFFAIRS"
        ),
        (
            re.compile(r"community.*engagement.*social.*responsibility.*co[- ]curricular", re.IGNORECASE),
            "Policy on Credits for Community Engagement & Social Responsibility and Co-Curricular Activities",
            "CO_CURRICULAR",
            "COMMUNITY_ENGAGEMENT"
        ),
        (
            re.compile(r"seed.*funding.*research.*grant.*policy", re.IGNORECASE),
            "SRM University-AP Seed Funding & Research Grant Policy",
            "RESEARCH",
            "RESEARCH_FUNDING"
        ),
        (
            re.compile(r"sponsored.*research.*industrial.*consultancy", re.IGNORECASE),
            "Sponsored Research & Industrial Consultancy Rules and Regulations",
            "RESEARCH",
            "CONSULTANCY"
        ),
        (
            re.compile(r"recruitment.*policy", re.IGNORECASE),
            "SRM University-AP Recruitment Policy (Staff/Faculty)",
            "RECRUITMENT",
            "HR"
        ),
    ]

    @classmethod
    def classify_document(cls, filename: str, sample_text: str = "") -> Dict[str, str]:
        """
        Identifies official title, primary domain, and secondary domain.
        """
        combined = f"{filename} {sample_text[:1000]}"
        for pattern, title, primary, secondary in cls.POLICY_RULES:
            if pattern.search(filename) or pattern.search(sample_text[:500]):
                return {
                    "title": title,
                    "primary_domain": primary,
                    "secondary_domain": secondary
                }

        # Fallback keyword classification
        lower = combined.lower()
        if "attendance" in lower:
            return {"title": filename, "primary_domain": "ATTENDANCE", "secondary_domain": "ACADEMICS"}
        if "placement" in lower:
            return {"title": filename, "primary_domain": "PLACEMENTS", "secondary_domain": "CAREER_SERVICES"}
        if "internship" in lower:
            return {"title": filename, "primary_domain": "INTERNSHIPS", "secondary_domain": "ACADEMICS"}
        if "research" in lower or "funding" in lower:
            return {"title": filename, "primary_domain": "RESEARCH", "secondary_domain": "RESEARCH_FUNDING"}

        return {"title": filename, "primary_domain": "GENERAL_UNIVERSITY_INFORMATION", "secondary_domain": "ACADEMICS"}
