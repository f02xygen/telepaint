import asyncio
import logging
from datetime import datetime, timezone
from aiogram import Bot
from aiogram.types import InputMediaPhoto, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from config import settings
from database import get_dirty_or_expiring_posts, mark_post_synced, mark_post_expired

logger = logging.getLogger(__name__)

async def periodic_sync_task(bot: Bot):
    while True:
        try:
            posts = await get_dirty_or_expiring_posts()
            now = datetime.now(timezone.utc)

            for post in posts:
                exp_at = post.expires_at
                if exp_at.tzinfo is None:
                    exp_at = exp_at.replace(tzinfo=timezone.utc)

                if now >= exp_at:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔒 Время рисования истекло", callback_data="expired")]
                    ])
                    media = InputMediaPhoto(
                        media=FSInputFile(post.current_image_path),
                        caption=post.caption
                    )
                    await bot.edit_message_media(
                        chat_id=settings.CHANNEL_ID,
                        message_id=post.channel_message_id,
                        media=media,
                        reply_markup=keyboard
                    )
                    await mark_post_expired(post.id)
                    logger.info(f"Пост {post.id} заблокирован по истечении времени.")

                elif post.is_dirty:
                    draw_url = f"{settings.BASE_URL}/draw/{post.id}"
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🎨 Нарисовать сверху", url=draw_url)]
                    ])
                    media = InputMediaPhoto(
                        media=FSInputFile(post.current_image_path),
                        caption=post.caption
                    )
                    await bot.edit_message_media(
                        chat_id=settings.CHANNEL_ID,
                        message_id=post.channel_message_id,
                        media=media,
                        reply_markup=keyboard
                    )
                    await mark_post_synced(post.id)
                    logger.info(f"Пост {post.id} успешно обновлен в Telegram.")

        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче синхронизации: {e}")

        await asyncio.sleep(settings.SYNC_INTERVAL)