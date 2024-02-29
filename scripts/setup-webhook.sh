set -euo pipefail
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook?url=https://url-summarizer-telegram-bot.azurewebsites.net/api/bot?code=$FUNCTION_KEY"
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"
