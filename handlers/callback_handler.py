from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import ContextTypes
from typing import Dict, Any
import logging

from . import (
    handle_settings,
    service_selection,
    quality_selection,
    format_selection,
    process_download,
    QUALITY_OPTIONS,
    FORMAT_OPTIONS
)
from utils.error_handler import handle_error
from config import DEFAULT_QUALITY, DEFAULT_FORMAT

logger = logging.getLogger(__name__)

class CallbackStates:
    SELECTING_SERVICE = 'SELECTING_SERVICE'
    SELECTING_QUALITY = 'SELECTING_QUALITY'
    SELECTING_FORMAT = 'SELECTING_FORMAT'
    DOWNLOADING = 'DOWNLOADING'

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline buttons."""
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data
        user_data = context.user_data

        if data.startswith('settings'):
            await handle_settings_callback(update, context)
        
        elif data.startswith('service_'):
            await handle_service_callback(update, context)
        
        elif data.startswith('quality_'):
            await handle_quality_callback(update, context)
        
        elif data.startswith('format_'):
            await handle_format_callback(update, context)
        
        elif data.startswith('download_'):
            await handle_download_callback(update, context)
        
        elif data == 'cancel':
            await handle_cancel_callback(update, context)
        
        elif data == 'back_to_main':
            await handle_back_to_main_callback(update, context)
        
        else:
            await query.edit_message_text("Invalid callback query")
            logger.warning(f"Received invalid callback query: {data}")

    except Exception as e:
        await handle_error(update, context, e)
        logger.error(f"Error in callback handler: {str(e)}", exc_info=True)

async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings menu callbacks"""
    query = update.callback_query
    action = query.data.split('_')[1] if len(query.data.split('_')) > 1 else None
    
    keyboard = []
    
    if action == 'main':
        keyboard = [
            [
                InlineKeyboardButton("Quality", callback_data="settings_quality"),
                InlineKeyboardButton("Format", callback_data="settings_format")
            ],
            [
                InlineKeyboardButton("Services", callback_data="settings_services"),
                InlineKeyboardButton("Downloads", callback_data="settings_downloads")
            ],
            [InlineKeyboardButton("Back to Main", callback_data="back_to_main")]
        ]
        
        await query.edit_message_text(
            "⚙️ *Settings*\n\nSelect a setting to modify:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif action == 'quality':
        keyboard = [
            [InlineKeyboardButton(text, callback_data=f"quality_{key}")]
            for key, text in QUALITY_OPTIONS.items()
        ]
        keyboard.append([InlineKeyboardButton("Back", callback_data="settings_main")])
        
        current_quality = context.user_data.get('quality', DEFAULT_QUALITY)
        
        await query.edit_message_text(
            f"🎯 *Quality Settings*\n\nCurrent quality: {QUALITY_OPTIONS.get(current_quality, 'Not set')}\n\n"
            "Select new quality:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif action == 'format':
        keyboard = [
            [InlineKeyboardButton(text, callback_data=f"format_{key}")]
            for key, text in FORMAT_OPTIONS.items()
        ]
        keyboard.append([InlineKeyboardButton("Back", callback_data="settings_main")])
        
        current_format = context.user_data.get('format', DEFAULT_FORMAT)
        
        await query.edit_message_text(
            f"📦 *Format Settings*\n\nCurrent format: {FORMAT_OPTIONS.get(current_format, 'Not set')}\n\n"
            "Select new format:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle service selection callbacks"""
    query = update.callback_query
    service = query.data.split('_')[1]
    
    context.user_data['service'] = service
    
    # Show quality options for selected service
    keyboard = [
        [InlineKeyboardButton(text, callback_data=f"quality_{key}")]
        for key, text in QUALITY_OPTIONS.items()
        if is_quality_available(service, key)
    ]
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    
    await query.edit_message_text(
        f"Selected service: *{service.title()}*\n\n"
        "Choose quality:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quality selection callbacks"""
    query = update.callback_query
    quality = query.data.split('_')[1]
    
    context.user_data['quality'] = quality
    service = context.user_data.get('service')
    
    # Show format options based on selected quality and service
    keyboard = [
        [InlineKeyboardButton(text, callback_data=f"format_{key}")]
        for key, text in FORMAT_OPTIONS.items()
        if is_format_available(service, quality, key)
    ]
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    
    await query.edit_message_text(
        f"Selected quality: *{QUALITY_OPTIONS[quality]}*\n\n"
        "Choose format:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_format_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle format selection callbacks"""
    query = update.callback_query
    format = query.data.split('_')[1]
    
    context.user_data['format'] = format
    
    # Show download confirmation
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="download_start"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        ]
    ]
    
    service = context.user_data.get('service', 'Unknown')
    quality = context.user_data.get('quality', 'Unknown')
    
    await query.edit_message_text(
        "📝 *Download Summary*\n\n"
        f"Service: *{service.title()}*\n"
        f"Quality: *{QUALITY_OPTIONS.get(quality, 'Unknown')}*\n"
        f"Format: *{FORMAT_OPTIONS.get(format, 'Unknown')}*\n\n"
        "Confirm your selection:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle download-related callbacks"""
    query ```python
    = update.callback_query
    await query.answer()
    
    quality = context.user_data.get('quality')
    format = context.user_data.get('format')
    
    if not quality or not format:
        await query.edit_message_text("❌ Please select quality and format before downloading.")
        return
    
    await process_download(update, context, quality, format)

async def handle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel callbacks"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("❌ Action cancelled. You can start over by sending a new URL.")

async def handle_back_to_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to main menu callbacks"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("🔙 Back to main menu. Please select an option.")
    # Here you would typically show the main menu options again

def is_quality_available(service: str, quality: str) -> bool:
    """Check if quality is available for given service"""
    if service == 'tidal':
        return True
    elif service == 'qobuz':
        return quality not in ['mqa', 'dolby', 'sony360']
    elif service == 'deezer':
        return quality in ['high', 'medium']
    return False

def is_format_available(service: str, quality: str, format: str) -> bool:
    """Check if format is available for given service and quality"""
    if service == 'tidal':
        return True  # All formats available for Tidal
    elif service == 'qobuz':
        return format in ['flac', 'mp3', 'aac']  # Example formats for Qobuz
    elif service == 'deezer':
        return format in ['mp3', 'aac']  # Example formats for Deezer
    return False
