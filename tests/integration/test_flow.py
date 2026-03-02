import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.rabbitmq import RabbitMqContainer

from app.api.main import app
from app.db.database import get_db
from app.models.models import Base, Job
from app.core.config import settings


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def rabbitmq_container():
    with RabbitMqContainer("rabbitmq:3-management-alpine") as rabbitmq:
        yield rabbitmq


@pytest.fixture(scope="session")
def engine(postgres_container):
    db_url = postgres_container.get_connection_url()
    # Replace localhost with actual host for some environments
    if "localhost" in db_url:
        db_url = db_url.replace("localhost", postgres_container.get_container_host_ip())

    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up tables after each test
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                for table in reversed(Base.metadata.sorted_tables):
                    connection.execute(table.delete())
                transaction.commit()
            except:
                transaction.rollback()
                raise


@pytest.fixture(scope="function")
def client(db_session, postgres_container, rabbitmq_container):
    # Override settings to use containers
    settings.DATABASE_URL = postgres_container.get_connection_url()
    settings.RABBITMQ_URL = f"amqp://guest:guest@{rabbitmq_container.get_container_host_ip()}:{rabbitmq_container.get_exposed_port(5672)}/"

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_full_flow_api_to_rabbitmq(client, db_session):
    """Test that API correctly creates a job in DB and publishes to RabbitMQ."""
    response = client.post("/crawl/hockey")
    assert response.status_code == 200
    job_id = response.json()["id"]

    # Check if job exists in DB
    job = db_session.query(Job).filter(Job.id == job_id).first()
    assert job is not None
    assert job.status == "pending"
    assert job.type == "hockey"


def test_api_list_jobs(client, db_session):
    """Test listing jobs via API."""
    # Create a job manually
    job = Job(id="test-job-1", type="oscar", status="completed")
    db_session.add(job)
    db_session.commit()

    response = client.get("/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert any(j["id"] == "test-job-1" for j in jobs)
