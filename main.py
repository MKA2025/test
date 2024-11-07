import os
import logging
import asyncio
from typing import Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

from config import (
    BOT_TOKEN,
    OWNER_ID,
    AUTHORIZED_USERS,
    DOWNLOAD_PATH
)

from handlers import (
    start_command,
    help_command,
    settings_command,
    auth_command,
    quality_command,
    format_command
)

from service_handlers.tidal_handler import TidalHandler
from service_handlers.qobuz_handler import QobuzHandler
from service_handlers.deezer_handler import DeezerHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    CHOOSING_SERVICE,
    ENTER_CREDENTIALS,
    CHOOSING_QUALITY,
    CHOOSING_FORMAT,
    DOWNLOADING
) = range(5)

class MusicBot:
    def __init__(self):
        self.active_downloads: Dict[int, Any] = {}
        self.user_settings: Dict[int, Dict[str, str]] = {}
        self.service_handlers = {}
        
    async def initialize(self):
        """Initialize bot and create download directory"""
        self.app = Application.builder().token(BOT_TOKEN).build()
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)
        await self.setup_handlers()
        
    async def setup_handlers(self):
        """Set up all command and message handlers"""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CommandHandler("settings", self.settings))
        
        # Authentication conversation handler
        auth_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("auth", self.auth_start)],
            states={
                CHOOSING_SERVICE: [
                    CallbackQueryHandler(self.auth_service_choice, pattern='^auth_')
                ],
                ENTER_CREDENTIALS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.auth_credentials)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        self.app.add_handler(auth_conv_handler)
        
        # Settings conversation handler
        settings_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("quality", self.quality_start),
                CommandHandler("format", self.format_start)
            ],
            states={
                CHOOSING_QUALITY: [
                    CallbackQueryHandler(self.quality_choice, pattern='^quality_')
                ],
                CHOOSING_FORMAT: [
                    CallbackQueryHandler(self.format_choice, pattern='^format_')
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        self.app.add_handler(settings_conv_handler)
        
        # URL handler
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_url
        ))
        
        # Callback query handler for download options
        self.app.add_handler(CallbackQueryHandler(
            self.handle_download_callback,
            pattern='^download_'
        ))
        
        # Error handler
        self.app.add_error_handler(self.error_handler)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        if not self.is_authorized(user_id):
            await update.message.reply_text(
                "Sorry, you are not authorized to use this bot."
            )
            return
        
        welcome_text = (
            "🎵 *Welcome to Music Download Bot!*\n\n"
            "I can help you download music from:\n"
            "• Tidal (Including Dolby Atmos & 360)\n"
            "• Qobuz\n"
            "• Deezer\n\n"
            "Please use /auth to login to your preferred service first.\n"
            "Use /help to see all available commands."
        )
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        if not self.is_authorized(update.effective_user.id):
            return
            
        help_text = (
            "*Available Commands:*\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/auth - Authenticate with music services\n"
            "/quality - Set download quality\n"
            "/format - Set download format\n"
            "/settings - Show current settings\n\n"
            "*Supported Services:*\n"
            "• Tidal (MQA, Dolby Atmos, 360)\n"
            "• Qobuz (up to 24-bit/192kHz)\n"
            "• Deezer (MP3, FLAC)\n\n"
            "*How to use:*\n"
            "1. Use /auth to login to your preferred service\n"
            "2. Set quality and format using /quality and /format\n"
            "3. Send a track/album/playlist URL\n"
            "4. Wait for the download to complete"
        )
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )

    async def auth_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the authentication process"""
        if not self.is_authorized(update.effective_user.id):
            return
            
        keyboard = [
            [
                InlineKeyboardButton("Tidal", callback_data='auth_tidal'),
                InlineKeyboardButton("Qobuz", callback_data='auth_qobuz')
            ],
            [InlineKeyboardButton("Deezer", callback_data='auth_deezer')]
        ]
        
        await update.message.reply_text(
            "Choose a service to authenticate:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return CHOOSING_SERVICE

    async def auth_service_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle service choice for authentication"""
        query = update.callback_query
        await query.answer()
        
        service = query.data.split('_')[1]
        context.user_data['auth_service'] = service
        
        auth_messages = {
            'tidal': (
                "Please enter your Tidal credentials in this format:\n"
                "email password"
            ),
            'qobuz': (
                "Please enter your Qobuz credentials in this format:\n"
                "email password"
            ),
            'deezer': (
                "Please enter your Deezer credentials in this format:\n"
                "email password"
            )
        }
        
        await query.edit_message_text(auth_messages[service])
        return ENTER_CREDENTIALS

    async def auth_credentials(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle credential input and authentication"""
        try:
            email, password = update.message.text.split()
            service = context.user_data['auth_service']
            
            if service == 'tidal':
                tidal_handler = TidalHandler(email, password)
                await tidal_handler.authenticate()
            elif service == 'qobuz':
                qobuz_handler = QobuzHandler(email, password)
                await qobuz_handler.authenticate()
            elif service == 'deezer':
                deezer_handler = DeezerHandler(email)
                await deezer_handler.authenticate()
            
            await update.message.reply_text("Authentication successful!")
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("Invalid format. Please enter your credentials in the format: email password")
            return ENTER_CREDENTIALS
        except Exception as e:
            await update.message.reply_text(f"Authentication failed: {str(e)}")
            return ConversationHandler.END

    async def quality_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the quality selection process"""
        if not self.is_authorized(update.effective_user.id):
            return
            
        keyboard = [
            [InlineKeyboardButton("MP3 128kbps", callback_data='quality_MP3_128')],
            [InlineKeyboardButton("MP3 320kbps", callback_data='quality_MP3_320')],
            [InlineKeyboardButton("FLAC", callback_data='quality_FLAC')]
        ]
        
        await update.message.reply_text(
            "Choose the download quality:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return CHOOSING_QUALITY

    async def quality_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle quality choice"""
        query = update.callback_query
        await query.answer()
        
        quality = query.data.split('_')[1]
        context.user_data['download_quality'] = quality
        
        await query.edit_message_text(f"Download quality set to: {quality}")
        return ConversationHandler.END

    async def format_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the format selection process"""
        if not self.is_authorized(update.effective_user.id):
            return
            
        keyboard = [
            [InlineKeyboardButton("MP3", callback_data='format_MP3')],
            [InlineKeyboardButton("FLAC", callback_data='format_FLAC')]
        ]
        
        await update.message.reply_text(
            "Choose the download format:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return CHOOSING_FORMAT

    async def format_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle format choice"""
        query = update.callback_query
        await query.answer()
        
        format_choice = query.data.split('_')[1]
        context.user_data['download_format'] = format_choice
        
        await query.edit_message_text(f"Download format set to: {format_choice}")
        return ConversationHandler.END

    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming URLs for downloading"""
        user_id = update.effective_user.id
        if not self.is_authorized(user_id):
            await update.message.reply_text("You need to authenticate first using /auth.")
            return
        
        url = update.message.text
        quality = context.user_data.get('download_quality', 'MP3_320')
        format_choice = context.user_data.get('download_format', 'MP3')
        
        # Process the URL and initiate download
        await self.process_download(url, quality, format_choice)

    async def process_download(self, url: str, quality: str, format_choice: str):
        """Process the download based on the URL"""
        # Logic to handle the download based on the URL and user settings
        pass

    async def handle_download_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle download callback queries"""
        query = update.callback_query
        await query.answer()
        
        # Logic to handle download options
        pass

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        await update.message.reply_text("An error occurred. Please try again later.")

    def is_authorized(self, user_id: int) -> bool:
        """Check if the user is authorized"""
        return user_id in AUTHORIZED_USERS

    async def run(self):
        """Run the bot"""
        await self.initialize()
        await self.app.run_polling()

if __name__ == "__main__":
    bot = MusicBot()
    asyncio.run(bot.run())
