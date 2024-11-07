from telegram import Message
from typing import Optional
import asyncio

class ProgressTracker:
    def __init__(self, message: Message, filename: str):
        self.message = message
        self.filename = filename
        self.last_update_time = 0
        self._last_edit_message: Optional[Message] = None

    async def update_progress(self, current: int, total: int):
        """Update download progress message with rate limiting"""
        now = asyncio.get_event_loop().time()
        
        # Update only every 2 seconds to avoid Telegram API limits
        if now - self.last_update_time < 2:
            return

        self.last_update_time = now
        percentage = current * 100 / total
        progress_bar = self._generate_progress_bar(percentage)
        
        text = (
            f"Downloading: {self.filename}\n"
            f"{progress_bar} {percentage:.1f}%\n"
            f"Size: {self._format_size(current)}/{self._format_size(total)}"
        )

        try:
            if self._last_edit_message:
                await self._last_edit_message.edit_text(text)
            else:
                self._last_edit_message = await self.message.edit_text(text)
        except Exception:
            pass

    @staticmethod
    def _generate_progress_bar(percentage: float) -> str:
        """Generate a progress bar string"""
        filled = int(percentage / 5)
        return f"{'▓' * filled}{'░' * (20 - filled)}"

    @staticmethod
    def _format_size(size: int) -> str:
        """Format size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
