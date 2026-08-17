import uuid
from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import settings
from database import create_post_record

router = Router()

@router.message(F.photo)
async def handle_photo(message: Message):
    # Проверка списка админов
    if message.from_user.id not in settings.admin_ids_set:
        await message.reply("⛔ Сорян, только для админов @brainrotting_shitpost\nмб потом сделаю публичный доступ")
        return

    photo = message.photo[-1]
    post_id = str(uuid.uuid4())

    # Извлекаем подпись админа (или None, если отправлено без текста)
    caption = message.caption

    orig_path = f"media/orig_{post_id}.png"
    curr_path = f"media/current_{post_id}.png"

    # Сохраняем фото
    await message.bot.download(photo.file_id, destination=orig_path)
    with open(orig_path, "rb") as src, open(curr_path, "wb") as dst:
        dst.write(src.read())

    draw_url = f"{settings.BASE_URL}/draw/{post_id}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Paint", url=draw_url)]
    ])

    # Отправляем в канал с исходной подписью админа
    sent_msg = await message.bot.send_photo(
        chat_id=settings.CHANNEL_ID,
        photo=photo.file_id,
        caption=caption,
        reply_markup=keyboard
    )

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.EXPIRE_SECONDS)

    await create_post_record(
        post_id=post_id,
        channel_msg_id=sent_msg.message_id,
        orig_path=orig_path,
        curr_path=curr_path,
        caption=caption,
        expires_at=expires_at
    )

    await message.reply(f"✅ Опубликовано в канале!\nСсылка: {draw_url}")