"""
Orkestrator Scraper — menjalankan semua scraper dan mengembalikan hasil gabungan
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from filters import filter_news, sort_by_latest
from models import NewsItem, ScrapeResult
from scrapers import CNNScraper, ReutersScraper, TempoScraper

logger = logging.getLogger(__name__)

# Daftar scraper yang aktif
SCRAPERS = [TempoScraper, CNNScraper, ReutersScraper]


def run_all_scrapers() -> list[NewsItem]:
    """
    Menjalankan semua scraper secara paralel.
    Return daftar berita yang sudah difilter dan diurutkan.
    """
    all_items: list[NewsItem] = []
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=len(SCRAPERS)) as executor:
        futures = {executor.submit(cls().scrape): cls.source for cls in SCRAPERS}

        for future in as_completed(futures):
            source = futures[future]
            try:
                result: ScrapeResult = future.result()
                if result.error:
                    errors.append(f"[{source}] {result.error}")
                    logger.warning(f"Scraper {source} error: {result.error}")
                else:
                    all_items.extend(result.items)
                    logger.info(f"[{source}] Mendapat {len(result.items)} berita")
            except Exception as e:
                errors.append(f"[{source}] Exception: {e}")
                logger.error(f"Scraper {source} gagal: {e}")

    if errors:
        logger.warning(f"Scraping errors: {'; '.join(errors)}")

    # Filter politik Indonesia
    filtered = filter_news(all_items)
    logger.info(f"Setelah filter: {len(filtered)} dari {len(all_items)} berita")

    # Urutkan terbaru
    sorted_news = sort_by_latest(filtered)

    return sorted_news
