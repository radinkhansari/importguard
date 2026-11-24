import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import database_url, get_db
from app.main import app
from app.models import Base


@pytest.fixture(scope="session")
def test_engine():
    test_url = database_url.set(database="importguard_test")
    engine = create_engine(test_url)

    Base.metadata.create_all(engine)

    yield engine

    engine.dispose()


@pytest.fixture
def client(test_engine):
    with test_engine.connect() as connection:
        transaction = connection.begin()

        def override_get_db():
            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as test_client:
                yield test_client
        finally:
            app.dependency_overrides.pop(get_db, None)
            transaction.rollback()