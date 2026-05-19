import os
import re
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Read the bot token securely from Render's environment variables
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# Detect common URL patterns
URL_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+)",
    re.IGNORECASE
)

# Dummy HTTP server to satisfy Render's port requirement
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args):
        pass  # Silence HTTP logs

def run_server():
    HTTPServer(("0.0.0.0", 10000), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()


async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message:
        return

    # Block forwarded stories immediately
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

    # Collect text content
    content_parts = []

    if message.text:
        content_parts.append(message.text)

    if message.caption:
        content_parts.append(message.caption)

    # Nothing to scan
    if not content_parts:
        return

    content = " ".join(content_parts)

    # No URL found
    if not URL_PATTERN.search(content):
        return

    try:
        member = await context.bot.get_chat_member(chat