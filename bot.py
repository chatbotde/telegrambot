from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
from database import Database
from gemini_utils import generate_gemini_response, analyze_image, analyze_pdf
from web_search import perform_web_search
from datetime import datetime
import logging
import os
# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Create database instance
db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    chat_id = update.effective_chat.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    # Register user
    db.register_user(chat_id, first_name, username)

    await update.message.reply_text(
        f"Hi {first_name}! I'm your Gemini-powered assistant. "
        "I can chat, analyze images/files, and search the web for you. "
        "To start, please share your phone number by clicking the button below.",
        reply_markup=ReplyKeyboardMarkup.from_button(
            KeyboardButton("Share Contact", request_contact=True),
            one_time_keyboard=True
        )
    )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles contact sharing."""
    chat_id = update.effective_chat.id
    phone_number = update.message.contact.phone_number

    # Update phone number in database
    db.update_phone_number(chat_id, phone_number)

    await update.message.reply_text(
        f"Thank you! Your phone number {phone_number} has been saved. "
        "You can now start using the bot's features.",
        reply_markup=ReplyKeyboardRemove()
    )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text messages and generates Gemini responses."""
    chat_id = update.effective_chat.id
    user_message = update.message.text

    # Check if user is registered and has shared phone number
    user = db.get_user(chat_id)
    if not user or not user.get("phone_number"):
        await update.message.reply_text(
            "Please use /start to register and share your contact information."
        )
        return

    if user_message.startswith("/websearch"):
        # Extract query from the command
        query = user_message[len("/websearch"):].strip()
        if not query:
            await update.message.reply_text("Please provide a search query after /websearch.")
            return
        # Perform web search and get results
        search_results = perform_web_search(query)

        # Send search results to the user
        if search_results:
            await update.message.reply_text(search_results, parse_mode="Markdown", disable_web_page_preview=False)
        else:
            await update.message.reply_text("Sorry, I couldn't find any results for that query.")
    else:
        # Generate Gemini response
        bot_response = await generate_gemini_response(user_message)

        # Save chat history
        db.save_chat_message(chat_id, user_message, bot_response)

        await update.message.reply_text(bot_response)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles document (especially PDF) messages."""
    chat_id = update.effective_chat.id
    file_id = update.message.document.file_id
    file_name = update.message.document.file_name
    new_file = await context.bot.get_file(file_id)

    # Check if user is registered and has shared phone number
    user = db.get_user(chat_id)
    if not user or not user.get("phone_number"):
        await update.message.reply_text(
            "Please use /start to register and share your contact information."
        )
        return

    # Download the file
    file_path = f"{file_id}_{file_name}"
    await new_file.download_to_drive(file_path)

    description = ""
    if file_name.lower().endswith(".pdf"):
        description = await analyze_pdf(file_path)

    # Save file metadata and description
    db.save_file_metadata(chat_id, file_id, file_name, description)

    # Send the description to the user
    await update.message.reply_text(description)

    # Clean up: delete the downloaded file
    os.remove(file_path)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles photo messages."""
    chat_id = update.effective_chat.id
    file_id = update.message.photo[-1].file_id  # Get highest resolution photo
    file_name = f"{file_id}.jpg"  # Assume JPG for photos
    new_file = await context.bot.get_file(file_id)

    # Check if user is registered and has shared phone number
    user = db.get_user(chat_id)
    if not user or not user.get("phone_number"):
        await update.message.reply_text(
            "Please use /start to register and share your contact information."
        )
        return

    # Download the file
    file_path = f"{file_id}_{file_name}"  # Save with original name
    await new_file.download_to_drive(file_path)

    # Analyze image with Gemini
    description = await analyze_image(file_path)

    # Save file metadata and description
    db.save_file_metadata(chat_id, file_id, file_name, description)

    # Send analysis to user
    await update.message.reply_text(description)

    # Clean up: delete the downloaded file
    os.remove(file_path)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def setup_bot_application(token):
    """Set up and return a bot application instance."""
    try:
        application = ApplicationBuilder().token(token).build()

        # Register handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        application.add_handler(MessageHandler(filters.Document.PDF, handle_document))  # Handle PDFs specifically
        # Add error handler
        application.add_error_handler(error)

        return application
    except Exception as e:
        logger.error(f"Failed to set up bot application: {e}")
        raise