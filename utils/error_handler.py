import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

# Custom exceptions
from .exceptions import (
    DownloadError,
    RateLimitError,
    InvalidURLError,
    AuthenticationError,
    UnsupportedMediaError,
    NetworkError
)

logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors occurred in the bot"""
    try:
        raise context.error
    except InvalidURLError as e:
        await handle_invalid_url_error(update, str(e))
    except DownloadError as e:
        await handle_download_error(update, str(e))
    except RateLimitError as e:
        await handle_rate_limit_error(update, str(e))
    except AuthenticationError as e:
        await handle_authentication_error(update, str(e))
    except UnsupportedMediaError as e:
        await handle_unsupported_media_error(update, str(e))
    except NetworkError as e:
        await handle_network_error(update, str(e))
    except Exception as e:
        await handle_general_error(update, str(e))
    
    # Log the error
    logger.error(f"Error occurred: {str(context.error)}", exc_info=context.error)

async def handle_invalid_url_error(update: Update, error_message: str):
    """Handle invalid URL errors"""
    await update.message.reply_text(
        f"❌ Invalid URL: {error_message}\n"
        "Please make sure you're using a supported music service URL.",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_download_error(update: Update, error_message: str):
    """Handle download errors"""
    await update.message.reply_text(
        f"❌ Download failed: {error_message}\n"
        "Please try again later or contact support if the issue persists.",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_rate_limit_error(update: Update, error_message: str):
    """Handle rate limit errors"""
    await update.message.reply_text(
        f"⏳ Rate limit reached: {error_message}\n"
        "Please wait a while before making another request.",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_authentication_error(update: Update, error_message: str):
    """Handle authentication errors"""
    await update.message.reply_text(
        f"🔒 Authentication failed: {error_message}\n"
        "Please check your credentials or contact support.",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_unsupported_media_error(update: Update, error_message: str):
    """Handle unsupported media errors"""
    await update.message.reply_text(
        f"⚠️ Unsupported media: {error_message}\n"
        "This type of media is not supported for download.",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_network_error(update: Update, error_message: str):
    """Handle network-related errors"""
    await update.message.reply_text(
        f"🌐 Network error: {error_message}\n"
        "Please check your internet connection and try again.",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_general_error(update: Update, error_message: str):
    """Handle general errors"""
    await update.message.reply_text(
        f"❗ An error occurred: {error_message}\n"
        "Please try again later or contact support if the issue persists.",
        parse_mode=ParseMode.MARKDOWN
    )

def log_error(error: Exception):
    """Log errors to file and/or external service"""
    logger.error(f"An error occurred: {str(error)}", exc_info=error)
    # You can add additional logging here, such as sending to an external error tracking service
