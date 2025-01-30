from bot import setup_bot_application
import os
from dotenv import load_dotenv
from utils import setup_logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
def main():
    """Main function to start the bot."""
    # Get the bot token from environment variables
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set.")
    # Setup and run the bot
    application = setup_bot_application(telegram_token)
    application.run_polling()

if __name__ == "__main__":
    main()