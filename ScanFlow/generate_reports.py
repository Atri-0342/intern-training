
import csv
import random
from pathlib import Path
from uuid import uuid4


DATA_DIR = Path("data")
SCANS_FILE = DATA_DIR / "scans.csv"
USERS_FILE = DATA_DIR / "users.csv"
OUTPUT_FILE = DATA_DIR / "reports.csv"

REPORT_LIMIT = 150000
RANDOM_SEED = 42

FINDINGS = [
    "No significant abnormality identified.",
    "No acute abnormality identified.",
    "Visualized structures appear unremarkable.",
    "No focal abnormality identified.",
    "Mild soft tissue swelling is noted.",
    "No acute osseous abnormality identified.",
    "Alignment is maintained.",
    "No significant interval abnormality identified.",
    "Visualized structures are within expected limits.",
    "Further clinical correlation is recommended.",
]


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Required CSV not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def generate_reports() -> None:
    rng = random.Random(RANDOM_SEED)

    scans = read_csv(SCANS_FILE)
    users = read_csv(USERS_FILE)

    scan_ids = [
        row["id"]
        for row in scans
        if row.get("id")
    ]

    radiologist_ids = [
        row["id"]
        for row in users
        if row.get("id") and row.get("role") == "radiologist"
    ]

    if not scan_ids:
        raise ValueError("No scan IDs found in data/scans.csv.")

    if not radiologist_ids:
        raise ValueError(
            "No radiologist IDs found in data/users.csv."
        )

    if REPORT_LIMIT is not None:
        scan_ids = scan_ids[:REPORT_LIMIT]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "id",
                "scan_id",
                "findings",
                "radiologist_id",
                "pdf_key",
                "finalized_at",
            ],
        )
        writer.writeheader()

        for scan_id in scan_ids:
            writer.writerow({
                "id": str(uuid4()),
                "scan_id": scan_id,
                "findings": rng.choice(FINDINGS),
                "radiologist_id": rng.choice(radiologist_ids),
                "pdf_key": "",
                "finalized_at": "",
            })

    print(f"Generated {len(scan_ids)} synthetic reports.")
    print(f"Output: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    generate_reports()
