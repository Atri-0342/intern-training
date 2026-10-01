import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models.models import Scan
from datetime import datetime, timezone

load_dotenv()

password = os.getenv("DB_PASSWORD")
dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")

engine = create_engine(f"postgresql+psycopg://{user}:{password}@localhost:5432/{dbname}", echo=True)

def get_scan(scan_id: str):
    with Session(engine) as session:
        stmt = select(Scan).where(Scan.id == scan_id)
        return session.scalars(stmt).first()


def create_scan(scan_id, patient_id, modality, body_part, acquired_at, status):
    with Session(engine, expire_on_commit=False) as session:
        scan = Scan(
            id=scan_id,
            patient_id=patient_id,
            modality=modality,
            body_part=body_part,
            acquired_at=acquired_at,
            status=status
        )
        session.add(scan)
        session.commit()
        return scan

scan = create_scan(
    "11111111-1111-1111-1111-111111111111",
    "22222222-2222-2222-2222-222222222222",
    "CT",
    "chest",
    datetime.now(timezone.utc),
    "uploaded"
)

print(scan.id, scan.modality, scan.status)
print(get_scan("11111111-1111-1111-1111-111111111111"))
