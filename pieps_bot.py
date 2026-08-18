import os
from dataclasses import dataclass
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from agents import Runner, SQLiteSession, InputGuardrailTripwireTriggered
from pieps import pieps

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


# --- CP21: RunContext --- shared state für den gesamten Run
@dataclass
class PiepsContext:
    chat_id: str
    username: str


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    username = update.effective_user.first_name or "Kunde"
    user_input = update.message.text

    session = SQLiteSession(
        session_id=f"pieps_{chat_id}",
        db_path="pieps_memory.db",
    )

    run_context = PiepsContext(chat_id=chat_id, username=username)

    try:
        result = await Runner.run(
            pieps,
            user_input,
            session=session,
            context=run_context,
        )
        await update.message.reply_text(result.final_output)

    except InputGuardrailTripwireTriggered:
        await update.message.reply_text(
            "Ich bin ausschließlich für Fragen rund um Grünspecht Gartentechnik zuständig. "
            "Wie kann ich Ihnen bei Ihrem Mähroboter, Ihrer Heckenschere oder einem anderen "
            "Grünspecht-Produkt helfen?"
        )


def main() -> None:
    port = int(os.environ.get("PORT", 8000))
    webhook_url = os.getenv("WEBHOOK_URL")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print(f"PIEPS-Bot gestartet (Webhook auf Port {port}).")
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{webhook_url}/{TELEGRAM_TOKEN}",
    )


if __name__ == "__main__":
    main()
