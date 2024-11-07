import asyncio
import aiohttp
from utils.progress import ProgressBar

class Downloader:
    def __init__(self):
        self.tasks = {}

    async def download(self, url, filename, total_size):
        task = asyncio.create_task(self._download(url, filename, total_size))
        self.tasks[filename] = task
        await task

    async def _download(self, url, filename, total_size):
        progress = ProgressBar(total=total_size)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                with open(filename, 'wb') as f:
                    async for chunk in response.content.iter_chunked(1024):
                        if asyncio.current_task().cancelled():
                            raise asyncio.CancelledError
                        f.write(chunk)
                        await progress.update(len(chunk))
        progress.close()

    def cancel_download(self, filename):
        if filename in self.tasks:
            self.tasks[filename].cancel()
