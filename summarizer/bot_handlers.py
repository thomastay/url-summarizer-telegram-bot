#!/usr/bin/env python
import logging

from telegram import ForceReply, Update
from telegram.ext import ContextTypes
from summarizer.text import get_text_and_title
from summarizer.openai_summarizer import (
    summarize_openai_sync,
    summary_model,
)
from summarizer.database import (
    create_summary,
    is_valid_invite_code,
    create_user,
    is_user_authorized,
    create_article,
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
    logging.debug("Received invite code **redacted**")
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
        "archive.org",
        "archive.is",
        "archive.ph",
        "bloomberg.com",  # Bloomberg has a robots blocker
        "www.bloomberg.com",  # Bloomberg has a robots blocker
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

    logging.debug("Valid URL")
    try:
        title, text = get_text_and_title(url)
        logging.debug("url", url, "title", title[:50], "text", text[:50])
    except Exception as e:
        logging.debug("Error getting text and title", e)
        await update.message.reply_text(
            f"Sorry, I couldn't fetch the article from {url}. Sometimes I am blocked from certain domains. Please report this using /report.",
            disable_web_page_preview=True,
        )
        return
    await update.message.reply_text(
        f"Got your article from {url}. Summarizing it now...",
        disable_web_page_preview=True,
    )
    summary = summarize_openai_sync(text)
    await reply_chunked(update, summary)
    save_summary(summary, url, title, text, update.effective_user.id)


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
    logging.debug("Received user message to summarize", user_message)
    match = naive_url_regex.search(user_message)
    if not match:
        await update.message.reply_text(
            "Could not find a URL in your message to summarize."
        )
        return
    user_message = match.group(0)
    await summarize_url(update, user_message)


def save_summary(summary, url, title, text, user_id):
    logging.debug("summary", summary[:50])

    value = {
        "url": url,
        "title": title,
        "text": text,
        "summary_model": summary_model,
        "summary": summary,
        "user_id": user_id,
        "source": "telegram",
        "type": "bullet_point",
    }
    # Azure table storage has a limit of 32k characters per field
    # Mark it as "text in blob"
    if len(text) > 32_000:
        value["text"] = ""
        value["is_text_in_blob"] = True
        create_article(url, text)
    create_summary(value)
    return summary
