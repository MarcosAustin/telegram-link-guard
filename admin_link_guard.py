import os
import re
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

URL_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+)",
    re.IGNORECASE
)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args):
        pass

def run_server():
    HTTPServer(("0.0.0.0", 10000), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message:
        return

    if getattr(message, "story", None):
        try:
            member = await context.bot.get_chat_member(chat.id, user.id)
            if member.status not in ["administrator", "creator"]:
                await message.delete()
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=f"⚠️ {user.first_name}, only admins are allowed to share stories."
                )
        except Exception as e:
            print("ERROR:", e)
        return

    content_parts = []

    if message.text:
        content_parts.append(message.text)

    if message.caption:
        content_parts.append(message.caption)

    if not content_parts:
        return

    content = " ".join(content_parts)

    if not URL_PATTERN.search(content):
        return

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ["administrator", "creator"]:
            return

        await message.delete()

        await context.bot.send_message(
            chat_id=chat.id,
            text=f"⚠️ {user.first_name}, only admins are allowed to send links."
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
        await asyncio.sleep(float("inf"))
        await app.updater.stop()
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())