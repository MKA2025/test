from telegram import Update, ParseMode

async def handle_help(update: Update, context):
    """Handle /help command"""
    help_text = (
        "*🎵 Music Download Bot Help*\n\n"
        "*Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/settings - Configure download settings\n\n"
        "*Supported Services:*\n"
        "• Tidal (MQA, Dolby Atmos, Sony 360)\n"
        "• Qobuz (up to 24-bit/192kHz)\n"
        "• Deezer (FLAC, MP3)\n\n"
        "*How to use:*\n"
        "1. Configure your settings using /settings\n"
        "2. Send a music link (track/album/playlist)\n"
        "3. Select download options if prompted\n"
        "4. Wait for your download to complete\n\n"
        "*Supported Quality:*\n"
        "• Master (MQA)\n"
        "• HiFi (FLAC)\n"
        "• High (320kbps)\n"
        "• Medium (128kbps)\n\n"
        "*Note:* Available quality depends on your subscription level"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN
    )
