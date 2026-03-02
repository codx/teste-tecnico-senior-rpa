import logging
from typing import List, Dict, Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.models import Job, HockeyData, OscarData
from app.scrapers.hockey_scraper import HockeyScraper
from app.scrapers.oscar_scraper import OscarScraper

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self, db: Session):
        self.db = db

    def update_job_status(self, job_id: str, status: str, error: str = None):
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            if error:
                job.error = error
            self.db.commit()
            logger.info(f"Job {job_id} updated to {status}")
        else:
            logger.warning(f"Job {job_id} not found for status update")

    def run_hockey_scrape(self, job_id: str):
        logger.info(f"Starting hockey scraping for job {job_id}")
        scraper = HockeyScraper()
        results = scraper.scrape()
        self._save_hockey_data(job_id, results)

    def run_oscar_scrape(self, job_id: str):
        logger.info(f"Starting oscar scraping for job {job_id}")
        scraper = OscarScraper()
        results = scraper.scrape()
        self._save_oscar_data(job_id, results)

    def _save_hockey_data(self, job_id: str, results: List[Dict[str, Any]]):
        for item in results:
            stmt = insert(HockeyData).values(**item, job_id=job_id)
            stmt = stmt.on_conflict_do_update(
                constraint="_team_year_uc",
                set_={
                    "wins": stmt.excluded.wins,
                    "losses": stmt.excluded.losses,
                    "ot_losses": stmt.excluded.ot_losses,
                    "win_pct": stmt.excluded.win_pct,
                    "goals_for": stmt.excluded.goals_for,
                    "goals_against": stmt.excluded.goals_against,
                    "goal_diff": stmt.excluded.goal_diff,
                    "job_id": job_id,
                },
            )
            self.db.execute(stmt)
        self.db.commit()
        logger.info(f"Saved {len(results)} hockey records for job {job_id}")

    def _save_oscar_data(self, job_id: str, results: List[Dict[str, Any]]):
        for item in results:
            stmt = insert(OscarData).values(**item, job_id=job_id)
            stmt = stmt.on_conflict_do_update(
                constraint="_title_year_uc",
                set_={
                    "nominations": stmt.excluded.nominations,
                    "awards": stmt.excluded.awards,
                    "best_picture": stmt.excluded.best_picture,
                    "job_id": job_id,
                },
            )
            self.db.execute(stmt)
        self.db.commit()
        logger.info(f"Saved {len(results)} oscar records for job {job_id}")
