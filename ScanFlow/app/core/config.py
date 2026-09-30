import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

# 1. First, check if a secure secret file is mounted inside Docker
DOCKER_SECRET_FILE = Path("/app/.env.secret")

if DOCKER_SECRET_FILE.exists():
    load_dotenv(DOCKER_SECRET_FILE)
else:
    # 2. Fallback to your original .env path if running outside Docker
    ENV_FILE = BASE_DIR / ".env"
    load_dotenv(ENV_FILE)

# The rest of your code stays exactly the same!
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
TEST_DB_NAME = os.getenv("TEST_DB_NAME")

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

# Added a default value here just in case it reads as None during transitions
jwt_expire = os.getenv("JWT_EXPIRE_MINUTES")
JWT_EXPIRE_MINUTES = int(jwt_expire) if jwt_expire else 30
