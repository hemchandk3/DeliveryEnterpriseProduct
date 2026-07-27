import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    import app.models  # noqa: F401  (register models on Base)

    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)
    db = TestSession()
    try:
        yield db
    finally:
        db.close()
