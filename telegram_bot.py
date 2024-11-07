import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler
from orpheus.core import Orpheus, DownloadTypeEnum, MediaIdentification, QualityEnum
from orpheus.music_downloader import beauty_format_seconds

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TOKEN = 'YOUR_BOT_TOKEN_HERE'

# OrpheusDL instance
orpheus = Orpheus()

# Owner ID
OWNER_ID = 123456789  # Replace with your Telegram User ID

# Authorized Users Set
authorized_users = set()

# Conversation states
CHOOSING, TYPING_REPLY, CHOOSING_QUALITY, ADDING_USER = range(4)

# Service selection keyboard
service_keyboard = [
    [InlineKeyboardButton("Tidal", callback_data='auth_tidal')],
    [InlineKeyboardButton("Qobuz", callback_data='auth_qobuz')],
    [InlineKeyboardButton("Deezer", callback_data='auth_deezer')]
]
service_markup = InlineKeyboardMarkup(service_keyboard)

# Quality selection keyboard
quality_keyboard = [
    [InlineKeyboardButton("MINIMUM", callback_data='quality_MINIMUM')],
    [InlineKeyboardButton("LOW", callback_data='quality_LOW')],
    [InlineKeyboardButton("MEDIUM", callback_data='quality_MEDIUM')],
    [InlineKeyboardButton("HIGH", callback_data='quality_HIGH')],
    [InlineKeyboardButton("LOSSLESS", callback_data='quality_LOSSLESS')],
    [InlineKeyboardButton("HIFI", callback_data='quality_HIFI')]
]
quality_markup = InlineKeyboardMarkup(quality_keyboard)

def start(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id == OWNER_ID or update.effective_user.id in authorized_users:
        update.message.reply_text(
            'Welcome to the OrpheusDL Bot! Use the /auth command to authorize your accounts.\n'
            'Send a song link or use the /search command to find music.\n'
            'Use the /set_quality command to change the download quality.'
        )
    else:
        update.message.reply_text('You are not authorized to use this bot.')

def auth(update: Update, context: CallbackContext) -> int:
    if update.effective_user.id == OWNER_ID or update.effective_user.id in authorized_users:
        update.message.reply_text('Which service would you like to authorize?', reply_markup=service_markup)
        return CHOOSING
    else:
        update.message.reply_text('You are not authorized to use this command.')
        return ConversationHandler.END

def auth_callback(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    service = query.data.split('_')[1]
    context.user_data['service'] = service
    query.edit_message_text(f"Please enter your username for {service.capitalize()}:")
    return TYPING_REPLY

def received_information(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    service = context.user_data['service']
    
    if 'username' not in context.user_data:
        context.user_data['username'] = user_input
        update.message.reply_text(f"Please enter your password for {service.capitalize()}:")
        return TYPING_REPLY
    else:
        password = user_input
        username = context.user_data['username']
        try:
            # Here, you would use the OrpheusDL methods to authenticate with the service
            if service == 'tidal':
                # Use Tidal authentication method
                pass
            elif service == 'qobuz':
                # Use Qobuz authentication method
                pass
            elif service == 'deezer':
                # Use Deezer authentication method
                pass
            
            update.message.reply_text(f"Successfully authorized {service.capitalize()} account.")
        except Exception as e:
            logger.error(f"Error during {service} authentication: {str(e)}")
            update.message.reply_text(f"An error occurred while authorizing {service.capitalize()} account: {str(e)}")
        
        del context.user_data['username']
        del context.user_data['service']
        return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END

def set_quality(update: Update, context: CallbackContext) -> int:
    if update.effective_user.id == OWNER_ID or update.effective_user.id in authorized_users:
        update.message.reply_text('Select the download quality:', reply_markup=quality_markup)
        return CHOOSING_QUALITY
    else:
        update.message.reply_text('You are not authorized to use this command.')
        return ConversationHandler.END

def quality_callback(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    quality = query.data.split('_')[1]
    context.user_data['quality'] = QualityEnum[quality]
    query.edit_message_text(f"Download quality has been set to {quality}.")
    return ConversationHandler.END

def handle_link(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id == OWNER_ID or update.effective_user.id in authorized_users:
        link = update.message.text
        try:
            update.message.reply_text('Downloading the song...')
            
            quality = context.user_data.get('quality', QualityEnum.LOSSLESS)  # Default to LOSSLESS if not set
            orpheus.orpheus_core_download({orpheus.service_name: [MediaIdentification(media_type=DownloadTypeEnum.track, media_id=link)]}, {}, quality, './downloads')
            
            for root, dirs, files in os.walk('./downloads'):
                for file in files:
                    if file.endswith('.mp3') or file.endswith('.flac'):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'rb') as audio_file:
                            update.message.reply_audio(audio_file)
                        os.remove(file_path)
                        return
            
            update.message.reply_text('Failed to download the song.')
        except Exception as e:
            logger.error(f"Error downloading: {str(e)}")
            update.message.reply_text(f'An error occurred: {str(e)}')
    else:
        update.message.reply_text('You are not authorized to use this bot.')

def search(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id == OWNER_ID or update.effective_user.id in authorized_users:
        if not context.args:
            update.message.reply_text('Please enter a song
