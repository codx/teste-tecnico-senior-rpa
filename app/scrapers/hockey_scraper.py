import logging
import random
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup, Tag
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.schemas.schemas import HockeyDataSchema
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class HockeyScraper(BaseScraper):
    BASE_URL = "https://www.scrapethissite.com/pages/forms/"

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def _fetch_page(self, page: int) -> str:
        """Fetches a single page of results with retry logic."""
        self._log_progress(f"Fetching page {page}")
        response = requests.get(
            f"{self.BASE_URL}?page_num={page}&per_page=100",
            timeout=15,
            headers={"User-Agent": random.choice(self.USER_AGENTS)},
        )
        response.raise_for_status()
        return response.text

    def _parse_row(self, row: Tag) -> Optional[Dict[str, Any]]:
        """Parses a single HTML table row and returns validated data."""
        cols = row.find_all("td")
        if not cols or len(cols) < 9:
            return None

        try:
            raw_data = {
                "team_name": cols[0].text.strip(),
                "year": cols[1].text.strip(),
                "wins": cols[2].text.strip(),
                "losses": cols[3].text.strip(),
                "ot_losses": cols[4].text.strip() or 0,
                "win_pct": cols[5].text.strip(),
                "goals_for": cols[6].text.strip(),
                "goals_against": cols[7].text.strip(),
                "goal_diff": cols[8].text.strip(),
            }

            # Validate and convert types using Pydantic
            return HockeyDataSchema(**raw_data).model_dump()
        except (ValidationError, ValueError, IndexError) as e:
            logger.error(f"Validation error for hockey team row: {e}")
            return None

    def _has_next_page(self, soup: BeautifulSoup) -> bool:
        """Checks if there is a next page in the pagination."""
        pagination = soup.find("ul", class_="pagination")
        if not pagination:
            return False

        next_page = pagination.find("a", attrs={"aria-label": "Next"})
        return next_page is not None

    def scrape(self) -> List[Dict[str, Any]]:
        """Main entry point for scraping hockey teams."""
        all_data = []
        page = 1
        max_pages = settings.HOCKEY_MAX_PAGES

        while page <= max_pages:
            try:
                html = self._fetch_page(page)
            except Exception as e:
                logger.error(f"Failed to fetch page {page}: {e}")
                break

            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", class_="table")
            if not table:
                self._log_progress("Table not found, stopping.")
                break

            rows = table.find_all("tr", class_="team")
            if not rows:
                self._log_progress("No more rows found, stopping.")
                break

            for row in rows:
                validated_item = self._parse_row(row)
                if validated_item:
                    all_data.append(validated_item)

            if not self._has_next_page(soup):
                break

            page += 1

        self._log_progress(f"Scraped {len(all_data)} teams from {page - 1} pages")
        return all_data
