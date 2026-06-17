"""
Scraper untuk Tempo.co — kanal Politik
URL: https://www.tempo.co/politik
"""

import logging
import re

from models import NewsItem, ScrapeResult
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

TEMPO_POLITIK_URL = "https://www.tempo.co/politik"


class TempoScraper(BaseScraper):
    source = "tempo"

    def scrape(self) -> ScrapeResult:
        result = ScrapeResult(source=self.source)

        soup = self._fetch(TEMPO_POLITIK_URL)
        if soup is None:
            result.error = "Gagal mengakses Tempo.co"
            return result

        try:
            articles = soup.select(
                "article, .card, .list-item, [class*='berita'], [class*='news']"
            )

            if not articles:
                # Fallback: cari semua link yang mengarah ke artikel
                articles = soup.select("a[href*='/politik/']")

            seen_urls = set()
            for art in articles[:20]:  # maks 20 berita
                try:
                    # Cari link
                    link_tag = art if art.name == "a" else art.find("a")
                    if not link_tag:
                        continue

                    url = link_tag.get("href", "")
                    if not url:
                        continue

                    # Normalisasi URL
                    if url.startswith("/"):
                        url = "https://www.tempo.co" + url
                    if "tempo.co" not in url:
                        continue
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # Cari judul
                    title = (
                        link_tag.get("title")
                        or link_tag.get("aria-label")
                        or link_tag.get_text(strip=True)
                    )
                    if not title or len(title) < 10:
                        continue

                    # Cari tanggal
                    date_tag = art.find(
                        ["time", "span", "div"], class_=re.compile(r"date|time", re.I)
                    )
                    date_str = (
                        date_tag.get("datetime") or date_tag.get_text(strip=True)
                        if date_tag
                        else None
                    )
                    published_at = self._parse_date(date_str) if date_str else None

                    # Cari ringkasan
                    summary_tag = art.find(
                        ["p", "span", "div"],
                        class_=re.compile(r"excerpt|summary|desc", re.I),
                    )
                    summary = summary_tag.get_text(strip=True) if summary_tag else ""

                    item = NewsItem(
                        title=title,
                        url=url,
                        source=self.source,
                        published_at=published_at,
                        summary=summary,
                    )
                    result.items.append(item)

                except Exception as e:
                    logger.warning(f"Error parsing Tempo article: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping Tempo: {e}")
            result.error = str(e)

        return result
