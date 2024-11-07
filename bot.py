import os
import logging
import tempfile
import zipfile
from time import gmtime, strftime
from dotenv import load_dotenv
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
from utils.models import TrackInfo, AlbumInfo, codec_data, CodecEnum

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
DOWNLOAD_PATH = os.environ.get("DOWNLOAD_PATH", "./downloads")

# States for ConversationHandler
CHOOSING, TYPING_REPLY, CHOOSING_QUALITY, ADDING_USER = range(4)

# Store authorized users
authorized_users = {OWNER_ID}

# OrpheusDL instance
orpheus = Orpheus()

def beauty_format_seconds(seconds: int) -> str:
    """Format seconds to human readable time."""
    time_data = gmtime(seconds)
    time_format = "%Mm:%Ss"
    if time_data.tm_hour > 0:
        time_format = "%Hh:" + time_format
    return strftime(time_format, time_data)

def format_file_size(size_bytes):
    """Format file size to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def create_album_zip(album_info):
    """Create a ZIP file containing all tracks of an album."""
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, f"{album_info.name}.zip")
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            for track_id in album_info.tracks:
                track_info = orpheus.get_track_info(MediaIdentification(
                    media_type=DownloadTypeEnum.track,
                    media_id=track_id
                ))
                
                # Download the track
                track_path = orpheus.download_track(track_info)
                
                # Add the track to the ZIP file
                zip_file.write(track_path, 
                             f"{track_info.name}.{codec_data[track_info.codec].container.name}")
                
                # Clean up the downloaded track file
                os.remove(track_path)
            
            # Add album cover if available
            if album_info.cover_url:
                cover_path = download_cover(album_info.cover_url)
                zip_file.write(cover_path, "cover.jpg")
                os.remove(cover_path)
        
        return zip_path

def download_cover(cover_url):
    """Download album cover."""
    cover_path = tempfile.mktemp(suffix=".jpg")
    orpheus.download_file(cover_url, cover_path)
    return cover_path

def send_track_metadata(update: Update, context: CallbackContext, track_info: TrackInfo, reply_markup=None):
    """Send track metadata as a formatted message."""
    message = (
        f"🎵 *Track Information*\n\n"
        f"Title: `{track_info.name}`\n"
        f"Artist: `{', '.join(track_info.artists)}`\n"
        f"Album: `{track_info.album}`\n"
        f"Quality: `{codec_data[track_info.codec].pretty_name}`\n"
        f"Duration: `{beauty_format_seconds(track_info.duration)}`\n"
        f"Year: `{track_info.release_year}`"
    )
    
    if track_info.explicit:
        message += "\n⚠️ *Explicit Content*"
        
    return update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

def send_album_metadata(update: Update, context: CallbackContext, album_info: AlbumInfo, reply_markup=None):
    """Send album metadata as a formatted message."""
    message = (
        f"💿 *Album Information*\n\n"
        f"Title: `{album_info.name}`\n"
        f"Artist: `{album_info.artist}`\n"
        f"Tracks: `{len(album_info.tracks)}`\n"
        f"Year: `{album_info.release_year}`\n"
        f"Duration: `{beauty_format_seconds(album_info.duration)}`"
    )
    
    if album_info.explicit:
        message += "\n⚠️ *Explicit Content*"
    
    return update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

def show_download_progress(context: CallbackContext, message, current, total):
    """Show download progress."""
    progress = (current / total) * 100
    message.edit_text(
        f"⏳ Downloading: {progress:.1f}%\n"
        f"({format_file_size(current)}/{format_file_size(total)})"
    )

def handle_download_error(update: Update, context: CallbackContext, error_message: str):
    """Handle download errors."""
    logger.error(f"Download error: {error_message}")
    update.message.reply_text(
        f"❌ Error during download:\n{error_message}",
        parse_mode=ParseMode.MARKDOWN
    )

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
            
