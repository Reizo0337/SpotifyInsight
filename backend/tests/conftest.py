import pytest
import os
import sys
from sqlalchemy import create_all
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add app to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.main import app
from app.db.session import get_db, Base, engine

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_nebula.db"

from sqlalchemy import create_engine
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_nebula.db"):
        os.remove("./test_nebula.db")

@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
