from .start_handler import handle_start
from .help_handler import handle_help
from .settings_handler import (
    handle_settings,
    service_selection,
    quality_selection,
    format_selection,
    cancel,
    SELECTING_SERVICE,
    SELECTING_QUALITY,
    SELECTING_FORMAT
)
from .download_handler import handle_url, process_download
from .callback_handler import handle_callback, handle_download_callback

# Constants
SUPPORTED_SERVICES = ['tidal', 'qobuz', 'deezer']
QUALITY_OPTIONS = {
    'master': 'Master Quality (MQA/Hi-Res)',
    'hifi': 'HiFi (FLAC)',
    'high': 'High (320kbps)',
    'medium': 'Medium (128kbps)'
}
FORMAT_OPTIONS = {
    'flac': 'FLAC',
    'mp3': 'MP3',
    'aac': 'AAC',
    'mqa': 'MQA (Tidal Only)',
    'dolby': 'Dolby Atmos (Tidal Only)',
    'sony360': 'Sony 360 RA (Tidal Only)'
}

__all__ = [
    'handle_start',
    'handle_help',
    'handle_settings',
    'service_selection',
    'quality_selection',
    'format_selection',
    'cancel',
    'handle_url',
    'process_download',
    'handle_callback',
    'handle_download_callback',
    'SELECTING_SERVICE',
    'SELECTING_QUALITY',
    'SELECTING_FORMAT',
    'SUPPORTED_SERVICES',
    'QUALITY_OPTIONS',
    'FORMAT_OPTIONS'
]
