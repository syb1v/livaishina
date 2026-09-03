import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from bot.apps.deadlines.handlers import router as deadlines_router
from bot.apps.question.handlers import router as question_router
from bot.apps.schedule.handlers import router as schedule_router
from bot.apps.start.handlers import router as start_router
from bot.database.session import Base, engine
from bot.middlewares.db import DbSessionMiddleware
import bot.database.models  # noqa: F401  (register models)
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware())

    for router in (
        start_router,
        question_router,
        deadlines_router,
        schedule_router,
    ):
        dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=False)
    await init_db()
    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
