"""
Generasi Artikel — menggunakan LLM (OpenAI-compatible) untuk membuat ringkasan
berita dalam bentuk artikel jurnalistik 3-5 halaman.
"""

import logging

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from models import NewsItem

logger = logging.getLogger(__name__)

# Client OpenAI
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    return _client


SYSTEM_PROMPT = """Kamu adalah seorang jurnalis politik senior Indonesia yang berpengalaman.
Tugasmu adalah menulis artikel ringkasan berita politik berdasarkan berita sumber yang diberikan.

Aturan penulisan:
1. Tulis dalam Bahasa Indonesia yang formal, lugas, dan mengalir seperti artikel jurnalistik.
2. Gunakan struktur artikel:
   - **Headline**: Judul yang informatif, menarik, dan mencerminkan isi berita (gaya headline koran).
   - **Lead**: Paragraf pembuka yang merangkum 5W+1H (What, Who, When, Where, Why, How).
   - **Body**: Uraian mendalam — kronologi, konteks politik, latar belakang, data pendukung, dan analisis objektif.
   - **Penutup**: Kesimpulan dan implikasi dari berita tersebut terhadap dinamika politik Indonesia.
3. Panjang artikel 3-5 halaman:
   - Jika berita pendek/sederhana → sekitar 3 halaman.
   - Jika berita panjang/kompleks → hingga 5 halaman.
   - 1 halaman ≈ 4-5 paragraf.
4. Bersikap netral dan objektif. Jangan menambahkan opini pribadi. Setia pada fakta dari berita sumber.
5. Jangan membuat informasi palsu. Jika ada data yang tidak tersedia di berita sumber, jangan dikarang.
6. Di akhir artikel, wajib cantumkan sumber berita dengan format:
   **Sumber: [Nama Media] — [Judul Berita Asli] ([URL])**
"""


def fetch_article_content(url: str, timeout: int = 15) -> str:
    """
    Mengambil konten teks dari halaman berita (untuk digunakan sebagai input LLM).
    """
    import requests
    from bs4 import BeautifulSoup

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Hapus script, style, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Ambil teks dari elemen artikel/body
        article = soup.find("article") or soup.find("body")
        if article:
            text = article.get_text(separator="\n", strip=True)
            # Batasi panjang konten (biar tidak terlalu besar untuk LLM)
            return text[:8000]
        return ""
    except Exception as e:
        logger.warning(f"Gagal fetch konten artikel {url}: {e}")
        return ""


def _estimate_pages(title: str, content: str) -> str:
    """
    Estimasi instruksi panjang artikel untuk LLM.
    """
    total_length = len(title) + len(content)
    if total_length < 2000:
        return "sekitar 3 halaman (berita pendek)"
    elif total_length < 5000:
        return "sekitar 4 halaman (berita sedang)"
    else:
        return "sekitar 5 halaman (berita panjang dan kompleks)"


def generate_article(news: NewsItem) -> str:
    """
    Menghasilkan artikel ringkasan dari satu NewsItem menggunakan LLM.

    Args:
        news: Berita yang akan diringkas menjadi artikel.

    Returns:
        Teks artikel lengkap dalam format Markdown.
    """
    client = _get_client()

    # Ambil konten lengkap jika belum ada
    if not news.content:
        logger.info(f"Mengambil konten artikel dari {news.url}")
        news.content = fetch_article_content(news.url)

    # Estimasi panjang
    page_estimation = _estimate_pages(news.title, news.content)

    user_prompt = f"""Tulis artikel ringkasan berdasarkan berita berikut:

**Judul Berita Sumber:** {news.title}
**Sumber:** {news.source.upper()}
**URL:** {news.url}
**Ringkasan Singkat:** {news.summary}

**Konten Berita (hasil scraping):**
```
{news.content[:6000]}
```

Instruksi panjang: artikel harus {page_estimation}.
Gunakan format Markdown untuk judul, subjudul, dan paragraf."""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=4000,
        )
        article = response.choices[0].message.content or ""
        return article
    except Exception as e:
        logger.error(f"Gagal generate artikel: {e}")
        return f"*[Gagal menghasilkan artikel: {e}]*"
