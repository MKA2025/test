from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from keyboards import *
from utils import *
import logging

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start_command(update: Update, context: CallbackContext) -> None:
    """Handle /start command."""
    if not is_authorized(update.effective_user.id):
        update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    welcome_text = (
        "🎵 *Welcome to Music Download Bot!*\n\n"
        "I can help you download music in various qualities and formats.\n\n"
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show help message\n"
        "/settings - Show current settings\n\n"
        "Just send me a music link to start downloading!"
    )
    
    reply_markup = InlineKeyboardMarkup(main_menu_keyboard)
    update.message.reply_text(welcome_text, 
                              reply_markup=reply_markup,
                              parse_mode=ParseMode.MARKDOWN)

def help_command(update: Update, context: CallbackContext) -> None:
    """Handle /help command."""
    if not is_authorized(update.effective_user.id):
        return

    help_text = (
        "*Available Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/settings - Show current settings\n\n"
        "*Supported Formats:*\n"
        "• Dolby Atmos\n"
        "• Sony 360 Audio\n"
        "• MQA (Master)\n"
        "• FLAC (HiFi)\n"
        "• AAC\n"
        "• MP3\n\n"
        "*How to use:*\n"
        "1. Set your preferred quality and format\n"
        "2. Send a music link\n"
        "3. Wait for the download to complete\n"
    )
    
    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

def settings_command(update: Update, context: CallbackContext) -> None:
    """Handle /settings command."""
    if not is_authorized(update.effective_user.id):
        return

    quality = context.user_data.get('quality', DEFAULT_QUALITY)
    audio_format = context.user_data.get('format', DEFAULT_FORMAT)
    
    settings_text = (
        "*Current Settings:*\n"
        f"Quality: {get_quality_name(quality)}\n"
        f"Format: {get_format_name(audio_format)}\n\n"
        "Use the buttons below to change settings."
    )
    
    reply_markup = InlineKeyboardMarkup(main_menu_keyboard)
    update.message.reply_text(settings_text,
                              reply_markup=reply_markup , parse_mode=ParseMode.MARKDOWN)

def handle_callback(update: Update, context: CallbackContext) -> None:
    """Handle callback queries from inline buttons."""
    query = update.callback_query
    query.answer()

    if query.data.startswith('quality_'):
        quality = query.data.split('_')[1]
        context.user_data['quality'] = quality
        query.edit_message_text(text=f"Quality set to: {get_quality_name(quality)}", parse_mode=ParseMode.MARKDOWN)

    elif query.data.startswith('format_'):
        audio_format = query.data.split('_')[1]
        context.user_data['format'] = audio_format
        query.edit_message_text(text=f"Format set to: {get_format_name(audio_format)}", parse_mode=ParseMode.MARKDOWN)

    elif query.data == 'menu_main':
        start_command(update, context)

def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages."""
    if not is_authorized(update.effective_user.id):
        update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    # Here you can add logic to handle music links and initiate downloads
    update.message.reply_text("Please send a valid music link to download.")
  
