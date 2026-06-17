"""
Model data untuk berita
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NewsItem:
    """Satu item berita hasil scraping."""
    title: str
    url: str
    source: str  # "tempo", "cnn", "reuters"
    published_at: Optional[datetime] = None
    summary: str = ""  # ringkasan singkat dari scraper
    content: str = ""  # konten lengkap (opsional, untuk generasi artikel)

    def __str__(self) -> str:
        time_str = ""
        if self.published_at:
            time_str = self.published_at.strftime("%Y-%m-%d %H:%M")
        return f"[{self.source.upper()}] {self.title} ({time_str})"


@dataclass
class ScrapeResult:
    """Hasil scraping dari satu sumber."""
    source: str
    items: list[NewsItem] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None
