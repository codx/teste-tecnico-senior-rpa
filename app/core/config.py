import logging
import sys
from pythonjsonlogger import json as jsonlogger
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RPA Scraper API"
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/rpa_db"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    HOCKEY_MAX_PAGES: int = 10

    # Chrome settings for Selenium
    CHROME_EXECUTABLE_PATH: str | None = None
    CHROMEDRIVER_PATH: str | None = None

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "text"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()


# Logging Configuration
def setup_logging():
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    if settings.LOG_FORMAT.lower() == "json":

        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel(level)
        # Clear existing handlers
        for h in root.handlers[:]:
            root.removeHandler(h)
        root.addHandler(handler)
    else:
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stdout,
        )

    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)
