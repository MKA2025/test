import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
)
from orpheus.core import Orpheus, DownloadTypeEnum, MediaIdentification, QualityEnum
from orpheus.music_downloader import beauty_format_seconds
from utils.models import TrackInfo, AlbumInfo, codec_data, CodecEnum

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))

# States for ConversationHandler
CHOOSING, TYPING_REPLY, CHOOSING_QUALITY, ADDING_USER = range(4)

# Store authorized users (you might want to use a database in production)
authorized_users = {OWNER_ID}  # Initialize with owner ID

# OrpheusDL instance
orpheus = Orpheus()

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    if user.id not in authorized_users:
        update.message.reply_text(
            "You are not authorized to use this bot. Please contact the owner."
        )
        return
    
    update.message.reply_text(
        f"Hi {user.first_name}! I'm a music download bot.\n"
        "Send me a music link to download or use /help to see available commands."
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    if update.effective_user.id not in authorized_users:
        return
    
    update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/auth - Authenticate with music services\n"
        "/set_quality - Set download quality\n"
        "/add_user - Add a new authorized user (owner only)\n"
        "\nJust send me a music link to download!"
    )

def auth(update: Update, context: CallbackContext) -> int:
    """Start the authentication process."""
    if update.effective_user.id not in authorized_users:
        return ConversationHandler.END
    
    keyboard = [
        [
            InlineKeyboardButton("Qobuz", callback_data='auth_qobuz'),
            InlineKeyboardButton("Tidal", callback_data='auth_tidal'),
        ],
        [
            InlineKeyboardButton("Deezer", callback_data='auth_deezer'),
            InlineKeyboardButton("Cancel", callback_data='auth_cancel'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Please choose a service to authenticate:", reply_markup=reply_markup)
    return CHOOSING

def auth_callback(update: Update, context: CallbackContext) -> int:
    """Handle authentication service selection."""
    query = update.callback_query
    query.answer()
    
    if query.data == 'auth_cancel':
        query.edit_message_text("Authentication cancelled.")
        return ConversationHandler.END
    
    service = query.data.split('_')[1]
    context.user_data['auth_service'] = service
    query.edit_message_text(f"Please enter your {service} credentials in format:\nemail password")
    return TYPING_REPLY

def received_information(update: Update, context: CallbackContext) -> int:
    """Handle the received credentials."""
    credentials = update.message.text.split()
    if len(credentials) != 2:
        update.message.reply_text("Invalid format. Please use: email password")
        return TYPING_REPLY
    
    service = context.user_data['auth_service']
    email, password = credentials
    
    try:
        if service == 'qobuz':
            orpheus.load_module('qobuz').login(email, password)
        elif service == 'tidal':
            orpheus.load_module('tidal').login(email, password)
        elif service == 'deezer':
            orpheus.load_module('deezer').login(email, password)
        
        update.message.reply_text(f"Successfully authenticated with {service.capitalize()}.")
    except Exception as e:
        logger.error(f"Error during {service} authentication: {str(e)}")
        update.message.reply_text(f"An error occurred while authenticating with {service.capitalize()}: {str(e)}")
    
    # Clear sensitive data
    del context.user_data['auth_service']
    return ConversationHandler.END

def set_quality(update: Update, context: CallbackContext) -> int:
    """Start the quality setting process."""
    if update.effective_user.id not in authorized_users:
        return ConversationHandler.END
    
    keyboard = [
        [
            InlineKeyboardButton("HIFI", callback_data='quality_HIFI'),
            InlineKeyboardButton("Lossless", callback_data='quality_LOSSLESS'),
        ],
        [
            InlineKeyboardButton("High", callback_data='quality_HIGH'),
            InlineKeyboardButton("Medium", callback_data='quality_MEDIUM'),
        ],
        [
            InlineKeyboardButton("Low", callback_data='quality_LOW'),
            InlineKeyboardButton("Minimum", callback_data='quality_MINIMUM'),
        ],
        [
            InlineKeyboardButton("Cancel", callback_data='quality_cancel'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Please choose download quality:", reply_markup=reply_markup)
    return CHOOSING_QUALITY

def quality_callback(update: Update, context: CallbackContext) -> int:
    """Handle quality selection."""
    query = update.callback_query
    query.answer()
    
    if query.data == 'quality_cancel':
        query.edit_message_text("Quality setting cancelled.")
        return ConversationHandler.END
    
    quality = query.data.split('_')[1]
    context.user_data['quality'] = QualityEnum[quality]
    query.edit_message_text(f"Download quality has been set to {quality}.")
    return ConversationHandler.END

def add_user(update: Update, context: CallbackContext) -> None:
    """Add a new authorized user (owner only)."""
    if update.effective_user.id != OWNER_ID:
        update.message.reply_text("Only the owner can add new users.")
        return

    if len(context.args) != 1:
        update.message.reply_text("Please provide a user ID to add.")
        return
    
    try:
        new_user_id = int(context.args[0])
        if new_user_id in authorized_users:
            update.message.reply_text("This user is already authorized.")
        else:
            authorized_users.add(new_user_id)
            update.message.reply_text(f"User {new_user_id} has been added to authorized users.")
    except ValueError:
        update.message.reply_text("Invalid user ID. Please provide a valid integer ID.")

def send_track_metadata(update: Update, context: CallbackContext, track_info
