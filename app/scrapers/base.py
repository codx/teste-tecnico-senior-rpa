import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        pass

    def _log_progress(self, message: str):
        logger.info(f"[{self.__class__.__name__}] {message}")
