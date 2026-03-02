import logging
import random
from typing import List, Dict, Any

from pydantic import ValidationError
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tenacity import retry, stop_after_attempt, wait_exponential
from webdriver_manager.chrome import ChromeDriverManager

from app.core.config import settings
from app.schemas.schemas import OscarDataSchema
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class OscarScraper(BaseScraper):
    URL = "https://www.scrapethissite.com/pages/ajax-javascript/"

    def _setup_driver(self) -> webdriver.Chrome:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        if settings.CHROME_EXECUTABLE_PATH:
            chrome_options.binary_location = settings.CHROME_EXECUTABLE_PATH

        if settings.CHROMEDRIVER_PATH:
            service = Service(settings.CHROMEDRIVER_PATH)
        else:
            service = Service(ChromeDriverManager().install())

        return webdriver.Chrome(service=service, options=chrome_options)

    def _wait_for_ajax(self, driver: webdriver.Chrome):
        """Wait for loading mask to disappear and for films to be present."""
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.ID, "loading"))
            )
        except Exception:
            pass

        def _wait_for_films(d):
            try:
                f = d.find_elements(By.CLASS_NAME, "film")
                return len(f) > 0
            except StaleElementReferenceException:
                return False

        WebDriverWait(driver, 10).until(_wait_for_films)

    def _select_year(self, driver: webdriver.Chrome, year: str):
        """Clicks on the year link, handling potential stale elements."""
        try:
            link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, year))
            )
            link.click()
        except StaleElementReferenceException:
            link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, year))
            )
            link.click()

    def _extract_film_data(self, film_element, year: str) -> Dict[str, Any]:
        """Extracts data from a single film element and validates it."""

        def get_text(element, class_name):
            return element.find_element(By.CLASS_NAME, class_name).text.strip()

        try:
            title = get_text(film_element, "film-title")
            nominations_text = get_text(film_element, "film-nominations")
            awards_text = get_text(film_element, "film-awards")

            best_picture = False
            try:
                film_element.find_element(By.CLASS_NAME, "glyphicon-flag")
                best_picture = True
            except (StaleElementReferenceException, Exception):
                pass

            raw_info = {
                "year": year,
                "title": title,
                "nominations": nominations_text,
                "awards": awards_text,
                "best_picture": best_picture,
            }
            return OscarDataSchema(**raw_info).model_dump()
        except StaleElementReferenceException:
            logger.warning(
                f"Stale element encountered for film in year {year}, skipping item."
            )
            raise
        except (ValidationError, ValueError) as e:
            logger.error(f"Validation error for film row in year {year}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def scrape(self) -> List[Dict[str, Any]]:
        driver = self._setup_driver()
        all_films = []
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        ]
        try:
            self._log_progress(f"Opening URL: {self.URL}")
            # Random User-Agent
            driver.execute_cdp_cmd(
                "Network.setUserAgentOverride",
                {"userAgent": random.choice(user_agents)},
            )
            driver.get(self.URL)

            years_links = WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "year-link"))
            )
            years = [link.text for link in years_links]

            for year in years:
                self._log_progress(f"Scraping year: {year}")
                self._select_year(driver, year)
                self._wait_for_ajax(driver)

                films = driver.find_elements(By.CLASS_NAME, "film")
                for film in films:
                    try:
                        validated_film = self._extract_film_data(film, year)
                        all_films.append(validated_film)
                    except (
                        StaleElementReferenceException,
                        ValidationError,
                        ValueError,
                    ):
                        continue

        except Exception as e:
            logger.error(f"Error during Oscar scraping: {e}")
            raise
        finally:
            driver.quit()

        self._log_progress(f"Scraped {len(all_films)} films in total")
        return all_films
