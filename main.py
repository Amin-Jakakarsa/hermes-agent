"""
Hermes Agent — Telegram Bot

Alur kerja:
1. User kirim "cari berita terbaru sekarang" → bot mencari berita dari Tempo, CNN, Reuters
2. Bot mengirim daftar berita (filter politik internal Indonesia)
3. User memilih berita dan mengirim "approved" → bot membuat artikel ringkasan
4. Bot mengirim artikel 3-5 halaman, lengkap dengan sumber
"""

import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from article_generator import generate_article
from config import TELEGRAM_BOT_TOKEN
from models import NewsItem
from scraper import run_all_scrapers

# Setup logging
logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("hermes-bot")

# State: menyimpan berita yang sedang menunggu approval
_pending_news: dict[int, list[NewsItem]] = {}  # chat_id -> list berita


# ─── PERINTAH ────────────────────────────────────────────────


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /start"""
    await update.message.reply_text(
        "👋 *Hermes Agent* siap membantu!\n\n"
        "Saya memantau berita politik Indonesia dari:\n"
        "• Tempo\\.co\n"
        "• CNN Indonesia\n"
        "• Reuters\n\n"
        "Kirim perintah:\n"
        "📰 `cari berita terbaru sekarang` — mencari berita terkini\n"
        "✅ `approved` — menyetujui berita untuk dibuatkan artikel",
        parse_mode="MarkdownV2",
    )


# ─── PENCARIAN BERITA ───────────────────────────────────────


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk semua pesan teks dari user."""
    text = update.message.text.strip().lower()
    chat_id = update.effective_chat.id

    # Perintah: cari berita
    if text == "cari berita terbaru sekarang":
        await search_and_report(update, chat_id)
        return

    # Perintah: approved
    if text == "approved":
        await approve_and_generate(update, chat_id)
        return

    # Perintah tidak dikenal
    await update.message.reply_text(
        "Perintah tidak dikenal\\. Gunakan:\n"
        "• `cari berita terbaru sekarang`\n"
        "• `approved`",
        parse_mode="MarkdownV2",
    )


async def search_and_report(update: Update, chat_id: int):
    """Menjalankan scraper dan melaporkan hasil ke user."""
    await update.message.reply_text(
        "🔍 *Mencari berita terbaru\\.\\.\\.*", parse_mode="MarkdownV2"
    )

    # Jalankan scraper (sync di thread terpisah)
    loop = asyncio.get_event_loop()
    news_list: list[NewsItem] = await loop.run_in_executor(None, run_all_scrapers)

    if not news_list:
        await update.message.reply_text(
            "😔 Tidak ditemukan berita politik Indonesia terbaru saat ini\\.",
            parse_mode="MarkdownV2",
        )
        return

    # Simpan untuk approval
    _pending_news[chat_id] = news_list

    # Format laporan
    report_lines = [f"📰 *{len(news_list)} Berita Politik Terbaru*:\n"]
    for i, news in enumerate(news_list, 1):
        time_str = ""
        if news.published_at:
            time_str = news.published_at.strftime("%d/%m %H:%M")

        # Escape markdown special chars
        title_escaped = _escape_md(news.title)
        source_escaped = _escape_md(news.source.upper())

        report_lines.append(
            f"*{i}\\.* {title_escaped}\n"
            f"   📍 {source_escaped}  🕐 {time_str}\n"
            f"   🔗 {_escape_md(news.url)}\n"
        )

    report_lines.append(
        "\n✅ Kirim `approved` untuk menyetujui berita *nomor 1* dan membuat artikel\\.\n"
        "   Atau ketik nomor berita dulu untuk memilih\\.'"
    )

    # Kirim sebagai beberapa pesan jika terlalu panjang
    full_report = "\n".join(report_lines)
    if len(full_report) > 4000:
        # Split into chunks
        for i in range(0, len(report_lines), 15):
            chunk = "\n".join(report_lines[i : i + 15])
            await update.message.reply_text(
                chunk, parse_mode="MarkdownV2", disable_web_page_preview=True
            )
    else:
        await update.message.reply_text(
            full_report, parse_mode="MarkdownV2", disable_web_page_preview=True
        )


# ─── APPROVAL & GENERASI ARTIKEL ────────────────────────────


async def approve_and_generate(update: Update, chat_id: int):
    """User menyetujui → generate artikel untuk berita pertama di daftar pending."""
    if chat_id not in _pending_news or not _pending_news[chat_id]:
        await update.message.reply_text(
            "⚠️ Tidak ada berita yang menunggu persetujuan\\. Kirim `cari berita terbaru sekarang` dulu\\.",
            parse_mode="MarkdownV2",
        )
        return

    news_list = _pending_news[chat_id]
    selected = news_list[0]  # default: berita pertama (paling baru)

    await update.message.reply_text(
        f"✅ *Disetujui\\!* Memproses berita:\n{_escape_md(selected.title)}\n\n"
        f"✍️ *Menulis artikel\\.\\.\\.* mohon tunggu ~30-60 detik",
        parse_mode="MarkdownV2",
    )

    # Generate artikel (sync di thread terpisah)
    loop = asyncio.get_event_loop()
    article = await loop.run_in_executor(None, generate_article, selected)

    # Kirim artikel
    if article:
        # Split jika terlalu panjang (>4000 karakter Telegram limit)
        if len(article) > 4000:
            chunks = _split_text(article, 3800)
            for i, chunk in enumerate(chunks):
                prefix = (
                    f"📄 *Artikel Bagian {i + 1}/{len(chunks)}*\n\n"
                    if len(chunks) > 1
                    else ""
                )
                await update.message.reply_text(
                    prefix + chunk,
                    parse_mode="MarkdownV2",
                    disable_web_page_preview=True,
                )
        else:
            await update.message.reply_text(
                article,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True,
            )
    else:
        await update.message.reply_text("❌ Gagal menghasilkan artikel.")

    # Bersihkan pending
    del _pending_news[chat_id]


# ─── HELPERS ─────────────────────────────────────────────────


def _escape_md(text: str) -> str:
    """Escape karakter MarkdownV2 Telegram."""
    chars = "_*[]()~`>#+-=|{}.!"
    for ch in chars:
        text = text.replace(ch, f"\\{ch}")
    return text


def _split_text(text: str, max_len: int) -> list[str]:
    """Split teks menjadi chunk tanpa memotong di tengah kata."""
    chunks = []
    while len(text) > max_len:
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = text.rfind(" ", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks


# ─── MAIN ────────────────────────────────────────────────────


def main():
    """Entry point bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN belum dikonfigurasi di .env")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Hermes Agent Bot berjalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
