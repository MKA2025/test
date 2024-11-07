from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class QueueItem:
    user_id: int
    file_url: str
    quality: str
    format: str
    added_time: datetime
    status: str = 'pending'
    progress: float = 0.0

class QueueManager:
    def __init__(self):
        self.queue: List[QueueItem] = []
        self.active_downloads: Dict[int, QueueItem] = {}
        self.max_concurrent = 3

    async def add_to_queue(self, user_id: int, file_url: str, quality: str, format: str) -> QueueItem:
        """Add new item to queue"""
        item = QueueItem(
            user_id=user_id,
            file_url=file_url,
            quality=quality,
            format=format,
            added_time=datetime.now()
        )
        self.queue.append(item)
        await self.process_queue()
        return item

    async def process_queue(self):
        """Process items in queue"""
        while len(self.active_downloads) < self.max_concurrent and self.queue:
            next_item = self.queue.pop(0)
            self.active_downloads[next_item.user_id] = next_item
            asyncio.create_task(self.process_download(next_item))

    async def process_download(self, item: QueueItem):
        """Process individual download"""
        try:
            item.status = 'downloading'
            # Add your download logic here
            # Update progress using item.progress
            item.status = 'completed'
        except Exception as e:
            item.status = 'failed'
        finally:
            del self.active_downloads[item.user_id]
            await self.process_queue()

    def get_user_position(self, user_id: int) -> Optional[int]:
        """Get user's position in queue"""
        for i, item in enumerate(self.queue):
            if item.user_id == user_id:
                return i + 1
        return None
