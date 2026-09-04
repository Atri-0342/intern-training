import csv
import logging
from collections import Counter

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s:%(name)s:%(message)s"
)

logger = logging.getLogger(__name__)


def count_by_scan_type(
    patients: list[dict[str, str]],
) -> dict[str, int]:

    scan_types = [patient["scan_type"] for patient in patients]

    return dict(Counter(scan_types))


def read_patients(filename: str) -> list[dict[str, str]]:
    # CSV values are read as strings
    with open(filename, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def avg_age_by_scan_type(
    patients: list[dict[str, str]],
) -> dict[str, float]:

    ages: dict[str, list[int]] = {}

    for i in patients:
        scan_type = i["scan_type"]
        age = int(i["age"])

        if scan_type not in ages:
            ages[scan_type] = []

        ages[scan_type].append(age)

    return {
        scan_type: sum(scan_ages) / len(scan_ages)
        for scan_type, scan_ages in ages.items()
    }


def find_empty_reports(
    patients: list[dict[str, str]],
) -> list[dict[str, str]]:

    return [
        patient
        for patient in patients
        if not patient["report_text"].strip()
    ]


patients = read_patients("patients.csv")

counts = count_by_scan_type(patients)
averages = avg_age_by_scan_type(patients)
empty_reports = find_empty_reports(patients)

logger.info("Empty reports: %d", len(empty_reports))
logger.info("Average ages: %s", averages)
logger.debug("Scan counts: %s", counts)