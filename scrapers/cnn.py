"""
Scraper untuk CNN Indonesia — kanal Politik
URL: https://www.cnnindonesia.com/politik
"""

import logging
import re

from models import NewsItem, ScrapeResult
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

CNN_POLITIK_URL = "https://www.cnnindonesia.com/politik"
CNN_NASIONAL_URL = "https://www.cnnindonesia.com/nasional"


class CNNScraper(BaseScraper):
    source = "cnn"

    def scrape(self) -> ScrapeResult:
        result = ScrapeResult(source=self.source)

        # Coba kanal politik dulu, fallback ke nasional
        for url in [CNN_POLITIK_URL, CNN_NASIONAL_URL]:
            soup = self._fetch(url)
            if soup is None:
                continue

            try:
                articles = soup.select(
                    "article, .list, .flex, [class*='news'], [class*='article']"
                )

                if not articles:
                    articles = soup.select(
                        "a[href*='/politik/'], a[href*='/nasional/']"
                    )

                seen_urls = set()
                for art in articles[:20]:
                    try:
                        link_tag = art if art.name == "a" else art.find("a")
                        if not link_tag:
                            continue

                        url_ = link_tag.get("href", "")
                        if not url_:
                            continue

                        if url_.startswith("/"):
                            url_ = "https://www.cnnindonesia.com" + url_
                        if "cnnindonesia.com" not in url_:
                            continue
                        if url_ in seen_urls:
                            continue
                        seen_urls.add(url_)

                        title = (
                            link_tag.get("title")
                            or link_tag.get("aria-label")
                            or link_tag.get_text(strip=True)
                        )
                        if not title or len(title) < 10:
                            continue

                        # Cari tanggal
                        date_tag = art.find(
                            ["time", "span", "div"],
                            class_=re.compile(r"date|time", re.I),
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
                        summary = (
                            summary_tag.get_text(strip=True) if summary_tag else ""
                        )

                        item = NewsItem(
                            title=title,
                            url=url_,
                            source=self.source,
                            published_at=published_at,
                            summary=summary,
                        )
                        result.items.append(item)

                    except Exception as e:
                        logger.warning(f"Error parsing CNN article: {e}")
                        continue

                if result.items:
                    break  # dapat hasil dari kanal politik, tidak perlu fallback

            except Exception as e:
                logger.error(f"Error scraping CNN ({url}): {e}")
                continue

        if not result.items and not result.error:
            result.error = "Tidak dapat mengambil berita dari CNN Indonesia"

        return result
