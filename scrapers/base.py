"""
Base class untuk semua scraper
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from config import SCRAPER_TIMEOUT
from models import NewsItem, ScrapeResult

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base scraper."""

    source: str = "unknown"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
            }
        )
        self.timeout = SCRAPER_TIMEOUT

    @abstractmethod
    def scrape(self) -> ScrapeResult:
        """Mengambil berita terbaru dari sumber. Return ScrapeResult."""
        ...

    def _fetch(self, url: str) -> BeautifulSoup | None:
        """Helper: fetch URL dan return BeautifulSoup object."""
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            logger.error(f"Gagal fetch {url}: {e}")
            return None

    def _parse_date(self, date_str: str) -> datetime | None:
        """
        Coba parse string tanggal dari berbagai format yang umum di berita Indonesia.
        """
        if not date_str:
            return None
        date_str = date_str.strip()

        formats = [
            "%Y-%m-%dT%H:%M:%S%z",  # ISO
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d %B %Y %H:%M",
            "%d %B %Y",
            "%A, %d %B %Y %H:%M",
            "%A, %d %B %Y",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%B %d, %Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
