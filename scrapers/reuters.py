"""
Scraper untuk Reuters — Asia Pacific (filter Indonesia)
URL: https://www.reuters.com/world/asia-pacific/
"""

import logging
import re

from models import NewsItem, ScrapeResult
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

REUTERS_ASIA_URL = "https://www.reuters.com/world/asia-pacific/"


class ReutersScraper(BaseScraper):
    source = "reuters"

    def scrape(self) -> ScrapeResult:
        result = ScrapeResult(source=self.source)

        soup = self._fetch(REUTERS_ASIA_URL)
        if soup is None:
            result.error = "Gagal mengakses Reuters"
            return result

        try:
            articles = soup.select(
                "article, [data-testid*='story'], [class*='story'], [class*='article']"
            )

            if not articles:
                articles = soup.select("a[href*='/world/']")

            seen_urls = set()
            for art in articles[:20]:
                try:
                    link_tag = art if art.name == "a" else art.find("a")
                    if not link_tag:
                        continue

                    url = link_tag.get("href", "")
                    if not url:
                        continue

                    if url.startswith("/"):
                        url = "https://www.reuters.com" + url
                    if "reuters.com" not in url:
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

                    # Cek apakah berita terkait Indonesia
                    text_check = f"{title}".lower()
                    indonesia_keywords = [
                        "indonesia",
                        "indonesian",
                        "jakarta",
                        "jokowi",
                        "prabowo",
                        "java",
                        "sumatra",
                        "kalimantan",
                        "sulawesi",
                        "papua",
                        "bali",
                    ]
                    if not any(kw in text_check for kw in indonesia_keywords):
                        continue  # skip berita non-Indonesia

                    # Cari tanggal
                    date_tag = art.find(
                        ["time", "span"], class_=re.compile(r"date|time", re.I)
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
                        class_=re.compile(r"excerpt|summary|desc|synopsis", re.I),
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
                    logger.warning(f"Error parsing Reuters article: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping Reuters: {e}")
            result.error = str(e)

        return result
