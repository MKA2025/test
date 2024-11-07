import os
from typing import Optional
from telegram import Update
from telegram.ext import CallbackContext
from config import OWNER_ID, AUTHORIZED_USERS, DOWNLOAD_PATH

def is_authorized(user_id: int) -> bool:
    """Check if user is authorized to use the bot."""
    return user_id == OWNER_ID or user_id in AUTHORIZED_USERS

def get_quality_name(quality_code: str) -> str:
    """Convert quality code to readable name."""
    quality_names = {
        'mqa': 'Master (MQA)',
        'hifi': 'HiFi',
        'high': 'High',
        'medium': 'Medium',
        'low': 'Low'
    }
    return quality_names.get(quality_code, quality_code.upper())

def get_format_name(format_code: str) -> str:
    """Convert format code to readable name."""
    format_names = {
        'atmos': 'Dolby Atmos',
        '360': 'Sony 360',
        'flac': 'FLAC',
        'aac': 'AAC',
        'mp3': 'MP3'
    }
    return format_names.get(format_code, format_code.upper())

def create_download_folder():
    """Create download folder if it doesn't exist."""
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

def format_file_size(size_in_bytes: int) -> str:
    """Convert file size to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} TB"

# Add your download functions here
# For example:
# def download_track(url: str, quality: str, format: str) -> Optional[str]:
#     """Download track and return the file path."""
#     # Your download logic here
#     pass
