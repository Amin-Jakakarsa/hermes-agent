"""
Package scrapers — berisi scraper untuk tiap sumber berita
"""

from scrapers.cnn import CNNScraper
from scrapers.reuters import ReutersScraper
from scrapers.tempo import TempoScraper

__all__ = ["TempoScraper", "CNNScraper", "ReutersScraper"]
