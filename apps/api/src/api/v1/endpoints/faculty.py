from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.database import get_async_db
from src.models.db_models import Faculty, Department
from src.models.schemas import FacultyCardPayload

router = APIRouter(prefix="/faculty", tags=["Faculty"])


@router.get("/search", response_model=List[FacultyCardPayload])
async def search_faculty(
    name: Optional[str] = Query(None, description="Search by faculty name"),
    department: Optional[str] = Query(None, description="Filter by department code"),
    db: AsyncSession = Depends(get_async_db)
):
    stmt = select(Faculty).join(Department, Faculty.department_id == Department.id, isouter=True)

    if name:
        stmt = stmt.where(Faculty.name.ilike(f"%{name}%"))
    if department:
        stmt = stmt.where(Department.code == department.upper())

    result = await db.execute(stmt.limit(20))
    faculty_records = result.scalars().all()

    payloads = []
    for f in faculty_records:
        dept_name = f.department.name if f.department else "General"
        payloads.append(
            FacultyCardPayload(
                name=f.name,
                designation=f.designation,
                department=dept_name,
                cabin_number=f.cabin_number,
                block=f.block,
                floor=f.floor,
                email=f.email,
                phone=f.phone,
                research_areas=f.research_areas or [],
                profile_url=f.profile_url
            )
        )
    return payloads
