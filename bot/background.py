import asyncio
import logging
import os
from datetime import datetime, timezone
from aiogram import Bot
from aiogram.types import InputMediaPhoto, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from config import settings
from database import get_dirty_or_expiring_posts, mark_post_synced, mark_post_expired

logger = logging.getLogger(__name__)

async def periodic_sync_task(bot: Bot):
    while True:
        try:
            posts = await get_dirty_or_expiring_posts()
            now = datetime.now(timezone.utc)

            for post in posts:
                # Внутренний try/except, чтобы ошибка одного поста не останавливала обработку других
                try:
                    exp_at = post.expires_at
                    if exp_at.tzinfo is None:
                        exp_at = exp_at.replace(tzinfo=timezone.utc)

                    file_path = post.current_image_path

                    # 1. Проверяем существование файла и отсутствие 0-байтовой пустоты
                    if not file_path or not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                        logger.warning(f"Пропуск поста {post.id}: файл {file_path} отсутствует или пуст (0B).")
                        continue

                    # 2. Считываем байты из файла безопасным способом
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()

                    if not file_bytes:
                        logger.warning(f"Пропуск поста {post.id}: не удалось прочитать байты из {file_path}.")
                        continue

                    input_file = BufferedInputFile(file_bytes, filename=f"image_{post.id}.png")

                    # Вариант 1: Время истекло
                    if now >= exp_at:
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🔒 Время рисования истекло", callback_data="expired")]
                        ])
                        media = InputMediaPhoto(
                            media=input_file,
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

                    # Вариант 2: Есть новые изменения (is_dirty)
                    elif post.is_dirty:
                        draw_url = f"{settings.BASE_URL}/draw/{post.id}"
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🎨 Нарисовать сверху", url=draw_url)]
                        ])
                        media = InputMediaPhoto(
                            media=input_file,
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

                except Exception as post_err:
                    logger.error(f"Ошибка при синхронизации поста {getattr(post, 'id', 'unknown')}: {post_err}")

        except Exception as e:
            logger.error(f"Ошибка в глобальном цикле задачи синхронизации: {e}")

        await asyncio.sleep(settings.SYNC_INTERVAL)