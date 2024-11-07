from enum import Enum

class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AudioFormat(Enum):
    MP3 = "mp3"
    FLAC = "flac"
    M4A = "m4a"
    WAV = "wav"

class AudioQuality(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    LOSSLESS = "lossless"

# Bot messages
MESSAGES = {
    'start': (
        "👋 Welcome to Music Downloader Bot!\n\n"
        "I can help you download music from various sources. "
        "Send me a music link to get started!"
    ),
    'help': (
        "ℹ️ *Available Commands*:\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/settings - Configure download settings\n"
        "/quality - Change audio quality\n"
        "/format - Change audio format\n"
        "/history - View download history\n"
        "/cancel - Cancel current download"
    ),
    'error': "❌ An error occurred: {error}",
    'download_started': "⏳ Download started...",
    'download_progress': "📥 Downloading: {progress}%",
    'download_complete': "✅ Download complete!",
    'invalid_url': "❌ Invalid URL. Please send a valid music link.",
    'unsupported_source': "❌ Unsupported music source.",
    'queue_position': "🔄 You are in queue position: {position}"
}

# Supported music sources
SUPPORTED_SOURCES = {
    'spotify.com': 'Spotify',
    'music.youtube.com': 'YouTube Music',
    'soundcloud.com': 'SoundCloud',
    'deezer.com': 'Deezer'
}

# Quality settings
QUALITY_SETTINGS = {
    AudioQuality.LOW: {
        AudioFormat.MP3: "128k",
        AudioFormat.M4A: "128k"
    },
    AudioQuality.MEDIUM: {
        AudioFormat.MP3: "256k",
        AudioFormat.M4A: "256k"
    },
    AudioQuality.HIGH: {
        AudioFormat.MP3: "320k",
        AudioFormat.M4A: "320k"
    },
    AudioQuality.LOSSLESS: {
        AudioFormat.FLAC: "lossless",
        AudioFormat.WAV: "lossless"
    }
}

# File size limits (in MB)
FILE_SIZE_LIMITS = {
    'document': 50,
    'audio': 50
}
