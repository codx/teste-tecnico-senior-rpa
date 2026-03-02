from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.main import app
from app.db.database import get_db
from app.models.models import Base, Job, HockeyData, OscarData

# Configuração do banco de dados em memória para testes
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@patch("app.api.main.publish_job")
def test_crawl_hockey(mock_publish, client):
    response = client.post("/crawl/hockey")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "hockey"
    assert data["status"] == "pending"
    assert "id" in data
    mock_publish.assert_called_once()


@patch("app.api.main.publish_job")
def test_crawl_oscar(mock_publish, client):
    response = client.post("/crawl/oscar")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "oscar"
    assert data["status"] == "pending"
    mock_publish.assert_called_once()


@patch("app.api.main.publish_job")
def test_crawl_all(mock_publish, client):
    response = client.post("/crawl/all")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "all"
    assert data["status"] == "pending"
    mock_publish.assert_called_once()


def test_list_jobs(client):
    # Adiciona um job manualmente
    db = TestingSessionLocal()
    job = Job(id="test-id", type="hockey", status="pending")
    db.add(job)
    db.commit()

    response = client.get("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Find the job we just added
    job_found = next((j for j in data if j["id"] == "test-id"), None)
    assert job_found is not None
    assert job_found["id"] == "test-id"
    db.close()


def test_get_job(client):
    db = TestingSessionLocal()
    # Explicitly clear any existing data to avoid conflicts
    db.query(Job).delete()
    job = Job(id="test-id-2", type="oscar", status="completed")
    db.add(job)
    db.commit()

    response = client.get("/jobs/test-id-2")
    assert response.status_code == 200
    assert response.json()["id"] == "test-id-2"
    db.close()


def test_get_job_not_found(client):
    response = client.get("/jobs/non-existent")
    assert response.status_code == 404


def test_get_job_results(client):
    db = TestingSessionLocal()
    # Use a unique job_id and ensure job exists
    job_id = "test-results-unique"
    job = Job(id=job_id, type="hockey", status="completed")
    db.add(job)
    hockey_entry = HockeyData(
        job_id=job_id,
        team_name="Test Team",
        year=2023,
        wins=10,
        losses=5,
        ot_losses=1,
        win_pct=0.6,
        goals_for=50,
        goals_against=40,
        goal_diff=10,
    )
    db.add(hockey_entry)
    db.commit()

    response = client.get(f"/jobs/{job_id}/results")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results_hockey"]) == 1
    assert data["results_hockey"][0]["team_name"] == "Test Team"
    db.close()


def test_get_hockey_results_all(client):
    db = TestingSessionLocal()
    job_id = "job-hockey-all"
    job = Job(id=job_id, type="hockey", status="completed")
    db.add(job)
    hockey_entry = HockeyData(
        job_id=job_id,
        team_name="Global Team",
        year=2023,
        wins=10,
        losses=5,
        win_pct=0.6,
        goals_for=50,
        goals_against=40,
        goal_diff=10,
    )
    db.add(hockey_entry)
    db.commit()

    response = client.get("/results/hockey")
    assert response.status_code == 200
    data = response.json()
    assert any(item["team_name"] == "Global Team" for item in data)
    db.close()


def test_get_oscar_results_all(client):
    db = TestingSessionLocal()
    job_id = "job-oscar-all"
    job = Job(id=job_id, type="oscar", status="completed")
    db.add(job)
    oscar_entry = OscarData(
        job_id=job_id,
        year=2023,
        title="Best Movie",
        nominations=10,
        awards=5,
        best_picture=True,
    )
    db.add(oscar_entry)
    db.commit()

    response = client.get("/results/oscar")
    assert response.status_code == 200
    data = response.json()
    assert any(item["title"] == "Best Movie" for item in data)
    db.close()
