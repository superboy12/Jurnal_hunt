"""Telegram Bot Integration for AI Journal Hunter.
Allows researchers to discover, search, and verify academic journals directly via Telegram.
"""
from __future__ import annotations
import asyncio
import logging
from typing import Optional, Dict, Any, List
import httpx

from ..core.config import settings
from ..core.database import SessionLocal
from ..schemas.schemas import SearchParameterSchema
from ..services.command_interpreter import interpret_command
from ..services.search_pipeline import run_search_pipeline
from ..models.models import Search, SearchArticle, Article

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"


class TelegramJournalBot:
    """Lightweight asynchronous Telegram Bot runner."""

    def __init__(self):
        self.token = settings.telegram_token
        self.running = False
        self.last_update_id = 0
        self.task: Optional[asyncio.Task] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.token and len(self.token) > 10)

    @property
    def base_url(self) -> str:
        return TELEGRAM_API_BASE.format(token=self.token)

    async def send_message(self, chat_id: int | str, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to a Telegram chat."""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False,
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, json=payload)
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def start(self):
        """Start long-polling loop."""
        if not self.is_configured:
            logger.info("Telegram Bot token not provided, bot service disabled.")
            return

        self.running = True
        logger.info(f"Starting Telegram Bot @{settings.telegram_bot_username} listener...")
        self.task = asyncio.create_task(self._poll_loop())

    async def stop(self):
        """Stop polling loop."""
        self.running = False
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Telegram Bot listener stopped.")

    async def _poll_loop(self):
        """Long polling updates from Telegram."""
        async with httpx.AsyncClient(timeout=35.0) as client:
            while self.running:
                try:
                    url = f"{self.base_url}/getUpdates"
                    params = {
                        "offset": self.last_update_id + 1,
                        "timeout": 25,
                    }
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        updates = data.get("result", [])
                        for update in updates:
                            self.last_update_id = update["update_id"]
                            await self._handle_update(update)
                    elif resp.status_code == 409:
                        logger.warning("Telegram conflict error: another instance is polling.")
                        await asyncio.sleep(10)
                    else:
                        logger.warning(f"Telegram getUpdates returned {resp.status_code}")
                        await asyncio.sleep(5)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Telegram polling error: {e}")
                    await asyncio.sleep(5)

    async def _handle_update(self, update: Dict[str, Any]):
        """Handle individual incoming Telegram message."""
        message = update.get("message")
        if not message or "text" not in message:
            return

        chat_id = message["chat"]["id"]
        text = message["text"].strip()
        user_name = message["from"].get("first_name", "Researcher")

        logger.info(f"Telegram message from {user_name} ({chat_id}): {text}")

        # Command handling
        if text.startswith("/start") or text.startswith("/help"):
            welcome_text = (
                f"👋 <b>Halo {user_name}! Selamat datang di AI Journal Hunter Bot</b>\n\n"
                "Sistem pencarian dan verifikasi jurnal ilmiah otomatis berbasis AI dengan indeksasi Scopus & SINTA.\n\n"
                "🔍 <b>Contoh Perintah Pencarian:</b>\n"
                "• <code>Cari 5 artikel Generative AI untuk pemerintahan 2023-2026</code>\n"
                "• <code>Cari jurnal SINTA 2 tentang cloud computing</code>\n"
                "• <code>Artikel machine learning open access terbaru</code>\n\n"
                "Ketik instruksi apa saja dalam bahasa Indonesia atau Inggris untuk memulai pencarian!"
            )
            await self.send_message(chat_id, welcome_text)
            return

        # Natural language search query
        await self.send_message(
            chat_id,
            f"🔎 <i>Menganalisis perintah dengan AI dan menelusuri database akademik...</i>\n"
            f"<b>Perintah:</b> <code>{text[:100]}</code>"
        )

        # Run search asynchronously
        try:
            db = SessionLocal()
            try:
                # 1. Interpret
                interpreted = interpret_command(text)
                limit = min(interpreted.max_results, 5)

                params_schema = SearchParameterSchema(
                    topic=interpreted.topic,
                    keywords=interpreted.keywords,
                    synonyms=interpreted.synonyms,
                    language=interpreted.language,
                    year_from=interpreted.year_from,
                    year_to=interpreted.year_to,
                    max_results=limit,
                    indexing_target=interpreted.indexing_target,
                    sinta_rank_min=interpreted.sinta_rank_min,
                    sinta_rank_max=interpreted.sinta_rank_max,
                    open_access_only=interpreted.open_access_only,
                    require_doi=interpreted.require_doi,
                    require_pdf=interpreted.require_pdf,
                    sources=interpreted.sources,
                )

                # Create Search record
                search_rec = Search(user_command=text)
                db.add(search_rec)
                db.commit()
                db.refresh(search_rec)

                # Execute pipeline
                await run_search_pipeline(search_rec.id, params_schema, db)

                # Retrieve saved results
                results = db.query(SearchArticle).filter(
                    SearchArticle.search_id == search_rec.id
                ).order_by(SearchArticle.rank).limit(5).all()

                if not results:
                    await self.send_message(
                        chat_id,
                        f"⚠️ Tidak ditemukan artikel yang cocok untuk perintah: <i>{text}</i>\n"
                        "Cobalah gunakan kata kunci yang lebih umum atau perluas rentang tahun."
                    )
                    return

                msg_parts = [
                    f"📚 <b>Ditemukan {len(results)} Artikel Terbaik:</b>\n"
                    f"🎯 Topik: <i>{interpreted.topic}</i>\n"
                ]

                for idx, sa in enumerate(results, 1):
                    art = sa.article
                    authors_str = ", ".join(a.name for a in (art.authors or [])[:2])
                    if len(art.authors or []) > 2:
                        authors_str += " et al."

                    # Badges
                    badge_str = ""
                    if art.journal:
                        if art.journal.sinta_rank:
                            badge_str += f" [SINTA {art.journal.sinta_rank}]"
                        if art.journal.is_scopus_indexed:
                            badge_str += " [Scopus]"
                    if art.is_open_access:
                        badge_str += " [Open Access]"

                    item_text = (
                        f"<b>{idx}. {art.title}</b>\n"
                        f"👤 {authors_str} ({art.year or 'N/A'})\n"
                        f"🏛️ <i>{art.journal_name or 'Journal'}</i>{badge_str}\n"
                    )

                    links = []
                    if art.doi:
                        links.append(f"<a href='https://doi.org/{art.doi}'>DOI</a>")
                    if art.pdf_url:
                        links.append(f"<a href='{art.pdf_url}'>PDF Full-text</a>")
                    if art.open_access_url and art.open_access_url != art.pdf_url:
                        links.append(f"<a href='{art.open_access_url}'>OA Link</a>")

                    if links:
                        item_text += f"🔗 {' · '.join(links)}\n"

                    msg_parts.append(item_text)

                msg_parts.append(
                    "🌐 <i>Akses dashboard lengkap di web browser: http://localhost:5173</i>"
                )

                await self.send_message(chat_id, "\n".join(msg_parts))

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling Telegram search: {e}", exc_info=True)
            await self.send_message(
                chat_id,
                f"❌ Maaf, terjadi kesalahan saat memproses pencarian: <code>{str(e)[:150]}</code>"
            )


telegram_bot = TelegramJournalBot()
