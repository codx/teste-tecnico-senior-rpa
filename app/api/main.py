import logging
import uuid
from contextlib import asynccontextmanager
from typing import List, Dict

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import setup_logging
from app.core.rabbitmq import publish_job
from app.db.database import get_db
from app.models.models import Job, HockeyData, OscarData
from app.schemas.schemas import JobStatus, JobResults, HockeyDataSchema, OscarDataSchema

setup_logging()
logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API starting up")
    yield


app = FastAPI(title="RPA Scraper API", lifespan=lifespan)


@app.post("/crawl/hockey", response_model=JobStatus)
def crawl_hockey(db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    job = Job(id=job_id, type="hockey", status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    publish_job(job.id, "hockey")
    logger.info(f"Created hockey crawl job: {job_id}")
    return job


@app.post("/crawl/oscar", response_model=JobStatus)
def crawl_oscar(db: Session = Depends(get_db)):
    job = Job(id=str(uuid.uuid4()), type="oscar", status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    publish_job(job.id, "oscar")
    return job


@app.post("/crawl/all", response_model=JobStatus)
def crawl_all(db: Session = Depends(get_db)):
    job = Job(id=str(uuid.uuid4()), type="all", status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    publish_job(job.id, "all")
    return job


@app.get("/jobs", response_model=List[JobStatus])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()


@app.get("/jobs/{job_id}", response_model=JobStatus)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/jobs/{job_id}/results", response_model=JobResults)
def get_job_results(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/results/hockey", response_model=List[HockeyDataSchema])
def get_hockey_results(db: Session = Depends(get_db)):
    return db.query(HockeyData).all()


@app.get("/results/oscar", response_model=List[OscarDataSchema])
def get_oscar_results(db: Session = Depends(get_db)):
    return db.query(OscarData).all()


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    health_status: Dict[str, str] = {
        "status": "healthy",
        "database": "up",
        "rabbitmq": "up",
    }

    # Check database
    try:
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health check failed: Database is down: {e}")
        health_status["status"] = "unhealthy"
        health_status["database"] = "down"

    # Check RabbitMQ
    try:
        from app.core.rabbitmq import rabbitmq_manager

        rabbitmq_manager._connect()
    except Exception as e:
        logger.error(f"Health check failed: RabbitMQ is down: {e}")
        health_status["status"] = "unhealthy"
        health_status["rabbitmq"] = "down"

    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
