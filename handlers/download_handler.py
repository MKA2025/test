import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.url_parser import parse_url
from utils.download_manager import DownloadManager
from utils.error_handler import handle_error
from config import DOWNLOAD_PATH
from . import QUALITY_OPTIONS, FORMAT_OPTIONS

class DownloadStatus:
    def __init__(self):
        self.message = None
        self.progress = 0
        self.is_completed = False
        self.error = None

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming music URLs"""
    try:
        url = update.message.text
        service, media_type, media_id = parse_url(url)
        
        if not service:
            await update.message.reply_text(
                "❌ Invalid URL. Please send a valid Tidal, Qobuz, or Deezer link."
            )
            return

        # Store URL info in context
        context.user_data['current_download'] = {
            'url': url,
            'service': service,
            'media_type': media_type,
            'media_id': media_id
        }

        # Show quality selection keyboard
        keyboard = [
            [InlineKeyboardButton(text, callback_data=f"quality_{key}")]
            for key, text in QUALITY_OPTIONS.items()
            if _is_quality_available(service, key)
        ]
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="download_cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📥 *Download Setup*\n\n"
            f"Service: *{service.title()}*\n"
            f"Type: *{media_type.title()}*\n\n"
            "Please select quality:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        await handle_error(update, context, e)

async def process_download(update: Update, context: ContextTypes.DEFAULT_TYPE, quality: str, format: str):
    """Process the actual download"""
    query = update.callback_query
    download_info = context.user_data.get('current_download')
    
    if not download_info:
        await query.edit_message_text("❌ Download session expired. Please try again.")
        return

    status = DownloadStatus()
    
    try:
        # Initialize download manager
        download_manager = DownloadManager(
            service=download_info['service'],
            media_type=download_info['media_type'],
            media_id=download_info['media_id'],
            quality=quality,
            format=format
        )

        # Send initial progress message
        status.message = await query.edit_message_text(
            "⏳ Initializing download...",
            parse_mode='Markdown'
        )

        # Start progress updater
        asyncio.create_task(_update_progress(status))

        # Start download
        output_path = await download_manager.start_download(
            progress_callback=lambda p: _update_download_progress(status, p)
        )

        status.is_completed = True
        
        # Send the file
        if os.path.exists(output_path):
            await _send_downloaded_file(update, context, output_path)
            os.remove(output_path)  # Clean up
            
            await status.message.edit_text(
                "✅ Download completed successfully!",
                parse_mode='Markdown'
            )
        else:
            raise Exception("Download failed - file not found")

    except Exception as e:
        status.error = str(e)
        await handle_error(update, context, e)

async def _update_progress(status: DownloadStatus):
    """Update progress message periodically"""
    while not status.is_completed and not status.error:
        try:
            if status.message:
                await status.message.edit_text(
                    f"⏳ Downloading... {status.progress}%\n"
                    f"{'▓' * (status.progress // 5)}{'░' * (20 - status.progress // 5)}",
                    parse_mode='Markdown'
                )
        except Exception:
            pass
        await asyncio.sleep(2)

def _update_download_progress(status: DownloadStatus, progress: float):
    """Update download progress"""
    status.progress = int(progress * 100)

async def _send_downloaded_file(update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: str):
    """Send downloaded file to user"""
    file_size = os.path.getsize(file_path)
    
    if file_size > 50 * 1024 * 1024:  # If file is larger than 50MB
        # Split file or send as document
        pass
    else:
        await context.bot.send_audio(
            chat_id=update.effective_chat.id,
            audio=open(file_path, 'rb'),
            caption="🎵 Here's your downloaded track!"
        )

def _is_quality_available(service: str, quality: str) -> bool:
    """Check if quality is available for given service"""
    if service == 'tidal':
        return True
    elif service == 'qobuz':
        return quality not in ['mqa', 'dolby', 'sony360']
    elif service == 'deezer':
        return quality in ['high', 'medium']
    return False
