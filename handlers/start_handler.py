from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

async def handle_start(update: Update, context):
    """Handle /start command"""
    keyboard = [
        [
            InlineKeyboardButton("Settings ⚙️", callback_data='settings'),
            InlineKeyboardButton("Help ℹ️", callback_data='help')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "👋 *Welcome to Music Download Bot!*\n\n"
        "I can help you download music from:\n"
        "• Tidal (Including Dolby Atmos & Sony 360)\n"
        "• Qobuz (Up to 24-bit/192kHz)\n"
        "• Deezer (FLAC & MP3)\n\n"
        "Send me a music link to start downloading or use /help for more information."
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
