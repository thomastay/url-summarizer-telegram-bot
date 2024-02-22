import azure.functions as func
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
from summarizer.bot_handlers import (
    telegram_bot_token,
    start,
    help_command,
    summarize_guess,
    report_command,
)

app = func.FunctionApp()

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


@app.function_name(name="httpTrigger")
@app.route(route="bot")
async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Start the bot."""
    try:
        body = req.get_json()
        await application.initialize()
        await application.process_update(Update.de_json(body, application.bot))
        return func.HttpResponse("Success")
    except Exception as exc:
        return func.HttpResponse(f"Failure: {exc}", status_code=500)
