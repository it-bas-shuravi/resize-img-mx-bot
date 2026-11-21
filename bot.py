#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telegram bot that returns any photo as a 640x360 (16:9) image.

What it does:
  * takes a photo from the user;
  * fits it into a 640x360 frame, keeping the proportions;
  * crops the extra part from the center (no stretching, no squeezing);
  * sends the result back as a PNG.

There are no secrets in this file: the token comes from the BOT_TOKEN
environment variable. Copy .env.example to .env and put your own token there.
User-facing bot replies are in Russian; see start() and photo_handler().
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


def looks_like_bot_token(value: str) -> bool:
    """Rough shape check for a Telegram bot token — digits, colon, long tail.

    Guards against pasting some other secret into BOT_TOKEN. The value itself
    is never logged or printed anywhere.
    """
    head, _, tail = value.partition(":")
    return head.isdigit() and len(head) >= 8 and len(tail) >= 30


def resize_to_target(img: Image.Image) -> Image.Image:
    """Fit the image into a 640x360 frame and crop the extra part from the center.

    Proportions are kept: the image is never stretched. A source wider than the
    frame loses its sides, a taller one loses its top and bottom.
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
            "BOT_TOKEN is not set. Copy .env.example to .env and put your own "
            "token from @BotFather there — .env never goes to the repository.\n"
            "BOT_TOKEN не задан: скопируйте .env.example в .env и впишите свой "
            "токен — файл .env в репозиторий не попадает."
        )
    if not looks_like_bot_token(token):
        raise SystemExit(
            "BOT_TOKEN does not look like a Telegram bot token. Check .env. "
            "The value is not printed here on purpose.\n"
            "BOT_TOKEN не похож на токен Telegram — проверьте .env. "
            "Само значение не печатается намеренно."
        )

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    log.info("Бот запущен, жду фото")
    app.run_polling()


if __name__ == "__main__":
    main()
