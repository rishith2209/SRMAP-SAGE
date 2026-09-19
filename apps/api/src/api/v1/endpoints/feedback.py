import logging
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_async_db
from src.core.config import settings
from src.models.db_models import CommunityReport
from src.models.schemas import CommunityReportRequest, CommunityReportResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("/report", response_model=CommunityReportResponse)
async def submit_discrepancy_report(
    payload: CommunityReportRequest,
    db: AsyncSession = Depends(get_async_db)
):
    # 1. Save to local database
    report = CommunityReport(
        query_text=payload.query_text,
        generated_answer=payload.generated_answer,
        category=payload.category,
        report_reason=payload.report_reason,
        suggested_correction=payload.suggested_correction,
        provided_evidence_url=payload.provided_evidence_url,
        status="pending"
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    issue_number = None

    # 2. Bridge to GitHub Issues if configured
    if settings.GITHUB_FEEDBACK_TOKEN and settings.GITHUB_REPO_OWNER and settings.GITHUB_REPO_NAME:
        try:
            issue_title = f"[COMMUNITY CORRECTION]: Discrepancy reported in {payload.category}"
            issue_body = f"""### Discrepancy Report ID: `{report.id}`

**Report Reason:** {payload.report_reason}
**Category:** {payload.category}

#### User Query:
> {payload.query_text}

#### SAGE Response:
> {payload.generated_answer}

#### Suggested Correction:
{payload.suggested_correction or "None provided"}

#### Evidence URL / Reference:
{payload.provided_evidence_url or "None provided"}
"""
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    f"https://api.github.com/repos/{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}/issues",
                    headers={
                        "Authorization": f"Bearer {settings.GITHUB_FEEDBACK_TOKEN}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28"
                    },
                    json={
                        "title": issue_title,
                        "body": issue_body,
                        "labels": ["needs-verification", "community-correction"]
                    },
                    timeout=5.0
                )
                if res.status_code == 201:
                    data = res.json()
                    issue_number = data.get("number")
                    report.github_issue_number = issue_number
                    await db.commit()
        except Exception as e:
            logger.error(f"Failed to bridge report to GitHub: {e}")

    return CommunityReportResponse(
        id=str(report.id),
        status="recorded",
        github_issue_number=issue_number,
        message="Thank you! Your feedback has been recorded for maintainer review."
    )
