
import csv
from pathlib import Path
from uuid import uuid4

from faker import Faker

from app.core.security import hash_password


OUTPUT_DIR = Path("data")
USER_COUNT_PER_ROLE = 10
ROLES = ["clinician", "radiologist", "admin"]

fake = Faker("en_IN")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_users():
    plain_rows = []
    hashed_rows = []

    for role in ROLES:
        for _ in range(USER_COUNT_PER_ROLE):
            user_id = str(uuid4())
            email = fake.unique.email()
            password = fake.password(length=16)

            plain_rows.append({
                "id": user_id,
                "email": email,
                "password": password,
                "role": role,
            })

            hashed_rows.append({
                "id": user_id,
                "email": email,
                "hashed_password": hash_password(password),
                "role": role,
            })

    with (OUTPUT_DIR / "users.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["id", "email", "password", "role"],
        )
        writer.writeheader()
        writer.writerows(plain_rows)

    with (OUTPUT_DIR / "users_hashed.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["id", "email", "hashed_password", "role"],
        )
        writer.writeheader()
        writer.writerows(hashed_rows)

    print(f"Generated {len(plain_rows)} users.")
    print("Plain passwords: data/users.csv")
    print("Hashed passwords: data/users_hashed.csv")


if __name__ == "__main__":
    generate_users()
