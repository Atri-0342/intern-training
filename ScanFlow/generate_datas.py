import csv
import uuid
from datetime import datetime, timedelta, timezone

from faker import Faker

fake = Faker()


def generate_patients(count: int) -> list[dict]:
    patients = []

    for i in range(count):
        patients.append(
            {
                "synthetic_study_id": str(uuid.uuid4()),
                "dob": fake.date_of_birth(minimum_age=1,maximum_age=100).isoformat(),
                "sex": fake.random_element(["male", "female", "other"])
            }
        )
    return patients

def save_patients_to_csv(patients: list[dict], filename: str) -> None:
    fieldnames = [
        "synthetic_study_id",
        "dob",
        "sex",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(patients)

def generate_scans(count: int, patient_ids: list[str]) -> list[dict]:
    scans = []
    modalities = ["CT", "MRI", "X-ray"]
    body_parts = ["Brain","Chest","Abdomen","Pelvis","Spine","Knee","Shoulder","Head"]
    statuses = ["uploaded","processing","completed","failed"]

    start_date = datetime(2024,1,1,tzinfo=timezone.utc)
    end_date = datetime(2026,1,1,tzinfo=timezone.utc)

    total_seconds = int((end_date - start_date).total_seconds())

    for i in range(count):
        acquired_at = start_date + timedelta(seconds=fake.random_int(min=0,max=total_seconds))
        uploaded_at = acquired_at + timedelta(minutes=fake.random_int(min=1,max=120))

        scans.append(
            {
                "id": str(uuid.uuid4()),
                "patient_id": fake.random_element(patient_ids),
                "modality": fake.random_element(modalities),
                "body_part": fake.random_element(body_parts),
                "acquired_at": acquired_at.isoformat(),
                "uploaded_at": uploaded_at.isoformat(),
                "status": fake.random_element(statuses),
            }
        )

    return scans


def save_scans_to_csv(scans: list[dict], filename: str) -> None:
    fieldnames = [
        "id",
        "patient_id",
        "modality",
        "body_part",
        "acquired_at",
        "uploaded_at",
        "status",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(scans)

PATIENT_COUNT = 20_000
SCAN_COUNT = 200_000

patients = generate_patients(PATIENT_COUNT)

save_patients_to_csv(patients, "patients.csv")

patient_ids = [patient["synthetic_study_id"] for patient in patients]

scans = generate_scans(SCAN_COUNT, patient_ids)

save_scans_to_csv(scans, "scans.csv")

print(f"Generated {PATIENT_COUNT:,} patients.")
print(f"Generated {SCAN_COUNT:,} scans.")
print("Created patients.csv and scans.csv")
