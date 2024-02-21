#!/usr/bin/env python
import logging

from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from summarizer.text import get_text_and_title
from summarizer.openai_summarizer import (
    questions_from_title,
    summarize_openai_sync,
    questions_model,
    summary_model,
)
from summarizer.database import (
    create_summary,
    is_valid_invite_code,
    create_user,
    is_user_authorized,
)
from urllib.parse import urlparse

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

import os
import json
import time

telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    if len(context.args) == 0:
        await update.message.reply_text(
            f"Please provide an invite code to get started. If you don't have one, please contact Thomas for one."
        )
        return
    user_message = context.args[0]
    print("Received invite code **redacted**")
    is_valid = is_valid_invite_code(user_message)
    if not is_valid:
        await update.message.reply_text(
            "Your invite code was not valid. Please try again with a valid invite code."
        )
        return
    exists = create_user(user.id, user_message, user.full_name)
    if not exists:
        await update.message.reply_html(
            f"Hi {user.mention_html()}! You are now authorized to use the summary bot. Send any link to get started.",
            reply_markup=ForceReply(selective=True),
        )
    else:
        await update.message.reply_text(
            "You are already authorized to use the summary bot. Send any link to get started."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "Just send me a link and I will summarize it for you."
    )


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # TODO implement reporting
    await update.message.reply_text("🕵️ Reported!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def is_known_failed_domains(url):
    # Requests to these domains don't seem to work / are not supported yet
    failed_domains = [
        "www.reuters.com",
        "reuters.com",
        "youtube.com",
        "twitter.com",
        "facebook.com",
        "instagram.com",
        "pinterest.com",
        "arxiv.org",
    ]
    result = urlparse(url)
    domain = result.netloc
    return domain in failed_domains


async def reply_chunked(update: Update, text: str):
    max_length = 4096
    for i in range(0, len(text), max_length):
        await update.message.reply_text(text[i : i + max_length])


async def summarize_url(update: Update, url: str) -> None:
    if not is_valid_url(url):
        await update.message.reply_text(
            f"I cannot parse the url {url}. Please provide a valid URL to summarize.",
            disable_web_page_preview=True,
        )
        return
    if is_known_failed_domains(url):
        await update.message.reply_text(
            f"Sorry, I cannot summarize articles from {url}.",
            disable_web_page_preview=True,
        )
        return

    print("Valid URL")
    try:
        title, text = get_text_and_title(url)
        print("url", url, "title", title[:50], "text", text[:50])
    except Exception as e:
        print("Error getting text and title", e)
        await update.message.reply_text(
            f"Sorry, I couldn't fetch the article from {url}. Sometimes I am blocked from certain domains. Please report this using /report.",
            disable_web_page_preview=True,
        )
        return
    await update.message.reply_text(
        f"Got your article from {url}. Summarizing it now...",
        disable_web_page_preview=True,
    )
    summary = summarize_and_save(url, title, text, update.effective_user.id)
    await reply_chunked(update, summary)


def check_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    return is_user_authorized(user_id)


import re

naive_url_regex = re.compile(r"https?://\S+")


async def summarize_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize the user's message. The user's message should contain an article URL, if not reject"""
    is_authorized = check_authorized(update, context)
    if not is_authorized:
        await update.message.reply_text(
            "You are not authorized to use the summary bot. Use /start to get authorized."
        )
        return
    user_message = update.message.text
    print("Received user message to summarize", user_message)
    match = naive_url_regex.search(user_message)
    if not match:
        await update.message.reply_text(
            "Could not find a URL in your message to summarize."
        )
        return
    user_message = match.group(0)
    await summarize_url(update, user_message)


def summarize_and_save(url, title, text, user_id):
    questions = questions_from_title(title)
    print("questions", questions[:50])
    summary = summarize_openai_sync(
        text,
        questions,
    )
    print("summary", summary[:50])

    value = {
        "url": url,
        "title": title,
        "text": text,
        "questions": json.dumps(questions),
        "questions_model": questions_model,
        "summary_model": summary_model,
        "summary": summary,
        "user_id": user_id,
        "source": "telegram",
    }
    create_summary(value)
    return summary


def run_bot() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(telegram_bot_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("report", report_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, summarize_guess)
    )

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
