from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

SELECTING_SERVICE, SELECTING_QUALITY, SELECTING_FORMAT = range(3)

async def handle_settings(update: Update, context):
    """Handle /settings command"""
    keyboard = [
        [
            InlineKeyboardButton("Quality 🎵", callback_data='settings_quality'),
            InlineKeyboardButton("Format 📁", callback_data='settings_format')
        ],
        [
            InlineKeyboardButton("Service 🔧", callback_data='settings_service'),
            InlineKeyboardButton("Done ✅", callback_data='settings_done')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚙️ *Settings*\n\nChoose what to configure:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    return SELECTING_SERVICE

async def service_selection(update: Update, context):
    """Handle service selection"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("Tidal", callback_data='service_tidal'),
            InlineKeyboardButton("Qobuz", callback_data='service_qobuz')
        ],
        [
            InlineKeyboardButton("Deezer", callback_data='service_deezer'),
            InlineKeyboardButton("Back", callback_data='settings_back')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Select a service to configure:",
        reply_markup=reply_markup
    )
    return SELECTING_QUALITY

async def quality_selection(update: Update, context):
    """Handle quality selection"""
