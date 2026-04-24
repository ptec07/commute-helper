import pytest

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import engine


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
