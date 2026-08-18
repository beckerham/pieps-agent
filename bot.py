import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sendet jede empfangene Textnachricht unverändert zurück."""
    await update.message.reply_text(update.message.text)


def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    print("Echo-Bot gestartet. Abbruch mit Ctrl+C.")
    app.run_polling()


if __name__ == "__main__":
    main()
