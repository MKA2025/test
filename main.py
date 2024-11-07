import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from config import BOT_TOKEN, OWNER_ID, AUTHORIZED_USERS
from handlers import (
    start_handler,
    help_handler,
    settings_handler,
    download_handler,
    callback_handler
)
from utils.auth import check_auth
from utils.error_handler import error_handler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_SERVICE, SELECTING_QUALITY, SELECTING_FORMAT = range(3)

async def start(update: Update, context):
    """Start command handler"""
    if not check_auth(update.effective_user.id):
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    await start_handler.handle_start(update, context)

async def help_command(update: Update, context):
    """Help command handler"""
    if not check_auth(update.effective_user.id):
        return
    
    await help_handler.handle_help(update, context)

async def settings(update: Update, context):
    """Settings command handler"""
    if not check_auth(update.effective_user.id):
        return
    
    await settings_handler.handle_settings(update, context)

async def handle_url(update: Update, context):
    """Handle music URLs"""
    if not check_auth(update.effective_user.id):
        return
    
    await download_handler.handle_url(update, context)

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings))

    # Add conversation handler for settings
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("settings", settings)],
        states={
            SELECTING_SERVICE: [
                CallbackQueryHandler(settings_handler.service_selection, pattern='^service_')
            ],
            SELECTING_QUALITY: [
                CallbackQueryHandler(settings_handler.quality_selection, pattern='^quality_')
            ],
            SELECTING_FORMAT: [
                CallbackQueryHandler(settings_handler.format_selection, pattern='^format_')
            ],
        },
        fallbacks=[CommandHandler("cancel", settings_handler.cancel)]
    )
    application.add_handler(conv_handler)

    # Add URL handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    # Add callback query handler
    application.add_handler(CallbackQueryHandler(callback_handler.handle_callback))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
