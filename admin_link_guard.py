import os
import re
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Read the bot token securely from Render's environment variables
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# Detect common URL patterns
URL_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+)",
    re.IGNORECASE
)

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not message:
        return

    content_parts = []

    if message.text:
        content_parts.append(message.text)

    if message.caption:
        content_parts.append(message.caption)

    if getattr(message, "story", None):
        story = message.story

        if getattr(story, "caption", None):
            content_parts.append(story.caption)

        if getattr(story, "text", None):
            content_parts.append(story.text)

    if not content_parts:
        return

    content = " ".join(content_parts)

    if not URL_PATTERN.search(content):
        return

    chat = update.effective_chat
    user = update.effective_user

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ["administrator", "creator"]:
            return

        await message.delete()

        await chat.send_message(
            f"⚠️ {user.first_name}, only admins are allowed to send links."
        )

    except Exception as e:
        print("ERROR:", e)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(~filters.COMMAND, check_message)
    )

    print("Advanced anti-link bot is running on Render...")

    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.sleep(float("inf"))  # Keep running forever
        await app.updater.stop()
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())