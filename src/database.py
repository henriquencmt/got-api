import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


db_url = os.environ.get('DATABASE_URL')
if db_url: # pragma: no cover
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    engine = create_engine(db_url)
else:
    engine = create_engine(
        "sqlite:///./test.db",
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()