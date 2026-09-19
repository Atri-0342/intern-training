from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import DB_USER, DB_PASSWORD, DB_NAME


engine = create_engine(
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}",
    echo=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)