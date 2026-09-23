import time

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.dependencies import get_async_db, get_db
from app.models.models import Scan


router = APIRouter(
    prefix="/v1/bench",
    tags=["benchmark"],
)


@router.get("/patients-sync")
def patients_sync(
    db: Session = Depends(get_db),
):
    start = time.perf_counter()

    # Deliberately slow down the database operation by 1 second.
    db.execute(
        select(func.pg_sleep(1))
    )

    patients = (
        db.query(Scan)
        .limit(20)
        .all()
    )

    elapsed = time.perf_counter() - start

    return {
        "type": "sync",
        "patient_count": len(patients),
        "elapsed": elapsed,
    }


@router.get("/patients-async")
async def patients_async(
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    start = time.perf_counter()

    # Deliberately slow down the database operation by 1 second.
    await db.execute(
        select(func.pg_sleep(1))
    )

    result = await db.execute(
        select(Scan).limit(20)
    )

    patients = result.scalars().all()

    elapsed = time.perf_counter() - start

    return {
        "type": "async",
        "patient_count": len(patients),
        "elapsed": elapsed,
    }