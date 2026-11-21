#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telegram-бот: приводит присланную картинку к размеру 640x360.

Что делает:
  * принимает фото от пользователя;
  * вписывает его в рамку 640x360 с сохранением пропорций;
  * обрезает лишнее по центру (без растягивания и «сплющивания»);
  * возвращает готовый PNG в ответ.

Токен бота берётся из переменной окружения BOT_TOKEN — в коде секретов нет.
Скопируйте .env.example в .env и впишите свой токен.
"""

import logging
import os
from io import BytesIO

from dotenv import load_dotenv
from PIL import Image
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, filters)

TARGET_WIDTH = 640
TARGET_HEIGHT = 360

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("resize-img-bot")


def resize_to_target(img: Image.Image) -> Image.Image:
    """Вписать картинку в рамку 640x360 и обрезать лишнее по центру.

    Пропорции сохраняются: картинка не растягивается. Если исходник шире
    рамки — обрезаются бока, если выше — верх и низ.
    """
    img_ratio = img.width / img.height
    target_ratio = TARGET_WIDTH / TARGET_HEIGHT

    if img_ratio > target_ratio:
        new_height = TARGET_HEIGHT
        new_width = round(new_height * img_ratio)
    else:
        new_width = TARGET_WIDTH
        new_height = round(new_width / img_ratio)

    img = img.resize((new_width, new_height), Image.LANCZOS)

    left = (new_width - TARGET_WIDTH) // 2
    top = (new_height - TARGET_HEIGHT) // 2
    return img.crop((left, top, left + TARGET_WIDTH, top + TARGET_HEIGHT))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Пришлите картинку — верну её в размере "
        f"{TARGET_WIDTH}x{TARGET_HEIGHT}."
    )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()

    with Image.open(BytesIO(photo_bytes)) as img:
        resized = resize_to_target(img.convert("RGB"))
        buffer = BytesIO()
        buffer.name = "resized.png"
        resized.save(buffer, "PNG")
        buffer.seek(0)

    await update.message.reply_photo(
        photo=buffer,
        caption=f"Готово: {TARGET_WIDTH}x{TARGET_HEIGHT}.",
    )


def main() -> None:
    load_dotenv()
    token = (os.getenv("BOT_TOKEN") or "").strip()
    if not token:
        raise SystemExit(
            "Не задан BOT_TOKEN. Скопируйте .env.example в .env и впишите токен "
            "от @BotFather — файл .env в репозиторий не попадает."
        )

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    log.info("Бот запущен, жду фото")
    app.run_polling()


if __name__ == "__main__":
    main()
