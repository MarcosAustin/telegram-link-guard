import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Read the bot token securely from Render's environment variables
TOKEN = os.environ["8651941139:AAHy3-xYOR7gfhS7rbSi95VX0ufknWxfZfU"]

# Detect common URL patterns
URL_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+)",
    re.IGNORECASE
)

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    # Ignore updates without a message
    if not message:
        return

    # Collect all possible text-bearing fields:
    # normal messages, captions, and shared/forwarded stories
    content_parts = []

    if message.text:
        content_parts.append(message.text)

    if message.caption:
        content_parts.append(message.caption)

    # Check shared or forwarded Telegram stories
    if getattr(message, "story", None):
        story = message.story

        if getattr(story, "caption", None):
            content_parts.append(story.caption)

        if getattr(story, "text", None):
            content_parts.append(story.text)

    # Nothing to scan
    if not content_parts:
        return

    content = " ".join(content_parts)

    # No URL found
    if not URL_PATTERN.search(content):
        return

    chat = update.effective_chat
    user = update.effective_user

    try:
        # Allow admins and group creators to post links
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ["administrator", "creator"]:
            return

        # Delete the offending message
        await message.delete()

        # Optional warning message
        await chat.send_message(
            f"⚠️ {user.first_name}, only admins are allowed to send links."
        )

    except Exception as e:
        print("ERROR:", e)

def main():
    # Build the application using the token from Render
    app = ApplicationBuilder().token(TOKEN).build()

    # Monitor all message types except commands
    app.add_handler(
        MessageHandler(~filters.COMMAND, check_message)
    )

    print("Advanced anti-link bot is running on Render...")
    app.run_polling()

if __name__ == "__main__":
    main()