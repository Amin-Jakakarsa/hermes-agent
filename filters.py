"""
Filter berita berdasarkan kategori politik internal Indonesia
"""

from config import POLITICAL_KEYWORDS
from models import NewsItem


def is_political_indonesia(news: NewsItem) -> bool:
    """
    Memeriksa apakah sebuah berita termasuk kategori politik internal Indonesia.
    Menggunakan kombinasi keyword matching pada judul dan ringkasan.
    """
    text = f"{news.title} {news.summary}".lower()

    # Cek keyword politik
    matched_keywords = [kw for kw in POLITICAL_KEYWORDS if kw in text]

    # Minimal 1 keyword politik cocok
    if not matched_keywords:
        return False

    # Eksklusi: berita luar negeri yang menyebut Indonesia sekilas
    foreign_indicators = [
        "luar negeri",
        "internasional",
        "dunia",
        "global",
        "malaysia",
        "singapura",
        "thailand",
        "filipina",
        "vietnam",
        "amerika serikat",
        "china",
        "tiongkok",
        "rusia",
        "eropa",
        "timur tengah",
        "afrika",
        "australia",
        "pbb",
        "asean",
        "who",
        "imf",
        "world bank",
    ]
    # Jika mayoritas konteks adalah luar negeri, tolak
    foreign_count = sum(1 for fi in foreign_indicators if fi in text)
    if foreign_count > len(matched_keywords):
        return False

    return True


def filter_news(items: list[NewsItem]) -> list[NewsItem]:
    """
    Filter daftar berita, hanya kembalikan yang termasuk politik internal Indonesia.
    """
    return [item for item in items if is_political_indonesia(item)]


def sort_by_latest(items: list[NewsItem]) -> list[NewsItem]:
    """
    Urutkan berita dari yang paling baru.
    Berita tanpa tanggal ditaruh di akhir.
    """
    from datetime import datetime as dt

    def sort_key(item: NewsItem):
        return item.published_at if item.published_at else dt.min

    return sorted(items, key=sort_key, reverse=True)
