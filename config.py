"""
Hermes Agent — Konfigurasi
"""

import os

from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# LLM — DeepSeek V4 Flash (OpenAI-compatible)
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "deepseek-v4-flash")

# Scraper
SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "30"))

# Kata kunci politik Indonesia untuk filtering
POLITICAL_KEYWORDS = [
    # Pemerintahan & Lembaga
    "presiden",
    "wakil presiden",
    "menteri",
    "kementerian",
    "pemerintah",
    "dpr",
    "mpr",
    "dprd",
    "parlemen",
    "senayan",
    "dewan",
    "mk",
    "mahkamah konstitusi",
    "ma",
    "mahkamah agung",
    "ky",
    "komisi yudisial",
    "kpk",
    "bawaslu",
    "kpu",
    "dkpp",
    # Partai & Politik
    "partai",
    "politik",
    "politisi",
    "golkar",
    "pdi",
    "demokrat",
    "gerindra",
    "pks",
    "pkb",
    "nasdem",
    "pan",
    "ppp",
    "koalisi",
    "oposisi",
    # Pemilu & Pilkada
    "pemilu",
    "pilkada",
    "pilpres",
    "pileg",
    "pemilihan",
    "kampanye",
    "suara",
    "suara rakyat",
    "pencoblosan",
    "tps",
    # Kebijakan & Regulasi
    "uu",
    "undang-undang",
    "perppu",
    "peraturan",
    "ruu",
    "revisi uu",
    "kebijakan",
    "regulasi",
    "rapbn",
    "apbn",
    "anggaran",
    # Isu Politik Domestik
    "reshuffle",
    "kabinet",
    "jokowi",
    "prabowo",
    "gibran",
    "buzzer",
    "dpr ri",
    "fraksi",
    "komisi",
    "pansus",
    "hak angket",
    "kudeta",
    "makzul",
    "impeachment",
    "demonstrasi",
    "unjuk rasa",
]
