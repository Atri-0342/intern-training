import csv
from datetime import date
from typing import TypedDict

from faker import Faker

fake = Faker()


class Patient(TypedDict):
    id: int
    name: str
    age: int
    scan_type: str
    scan_date: date
    report_text: str

def generate_patient(patient_id: int) -> Patient:
    scan_types = ["MRI", "CT", "X-Ray", "Ultrasound"]

    reports = {
        "MRI": [
            "No acute abnormality identified on the MRI examination.",
            "Mild nonspecific signal changes noted. No focal lesion identified.",
            "MRI findings are within expected limits for this synthetic case.",
            "Small nonspecific area of increased signal observed. Clinical correlation recommended.",
        ],
        "CT": [
            "No acute abnormality identified on the CT examination.",
            "CT demonstrates mild nonspecific changes without acute findings.",
            "No significant abnormality detected on this synthetic CT study.",
            "A small nonspecific finding is noted. No acute complication identified.",
        ],
        "X-Ray": [
            "No acute abnormality identified on the X-ray examination.",
            "X-ray demonstrates no significant acute finding.",
            "Mild nonspecific changes noted on this synthetic radiograph.",
            "Radiographic appearance is within expected limits for this synthetic case.",
        ],
        "Ultrasound": [
            "No significant abnormality identified on the ultrasound examination.",
            "Ultrasound findings are within expected limits for this synthetic case.",
            "Mild nonspecific findings noted. No acute abnormality identified.",
            "A small nonspecific finding is observed without an acute complication.",
        ],
    }

    scan_type = fake.random_element(scan_types)
    report_text = fake.random_element(reports[scan_type])

    return {
        "id": patient_id,
        "name": fake.name(),
        "age": fake.random_int(min=1, max=100),
        "scan_type": scan_type,
        "scan_date": fake.date_between(start_date="-2y", end_date="today"),
        "report_text": report_text,
    }

def generate_patients(count: int) -> list[Patient]:
    patients = []

    for patient_id in range(1, count + 1):
        patients.append(generate_patient(patient_id))

    return patients


def save_patients_to_csv(patients: list[Patient],filename: str) -> None:
    fieldnames = [
        "id",
        "name",
        "age",
        "scan_type",
        "scan_date",
        "report_text",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(patients)


patients = generate_patients(500)
save_patients_to_csv(patients, "patients.csv")
