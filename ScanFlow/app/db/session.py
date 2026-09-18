import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

password = os.getenv("DB_PASSWORD")
dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")

engine = create_engine(
    f"postgresql+psycopg://{user}:{password}@localhost:5432/{dbname}",
    echo=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)