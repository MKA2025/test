import asyncio
from typing import Optional, Callable
from pathlib import Path
import aiohttp
from .progress import ProgressTracker
from .models import DownloadRequest

class DownloadManager:
    def __init__(self, max_concurrent_downloads: int = 3):
        self.semaphore = asyncio.Semaphore(max_concurrent_downloads)
        self.active_downloads: dict = {}

    async def download(self, 
                      request: DownloadRequest, 
                      progress_callback: Optional[Callable] = None) -> str:
        """Handle download with concurrency control"""
        async with self.semaphore:
            return await self._download_file(request, progress_callback)

    async def _download_file(self, 
                           request: DownloadRequest,
                           progress_callback: Optional[Callable]) -> str:
        """Download file with progress tracking"""
        output_path = Path(request.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(request.url) as response:
                if response.status != 200:
                    raise Exception(f"Download failed with status {response.status}")

                total_size = int(response.headers.get('content-length', 0))
                chunk_size = 64 * 1024  # 64KB chunks
                downloaded = 0

                with open(output_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        if request.cancelled:
                            raise Exception("Download cancelled")
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback:
                            await progress_callback(downloaded, total_size)

        return str(output_path)

    def cancel_download(self, download_id: str):
        """Cancel an active download"""
        if download_id in self.active_downloads:
            self.active_downloads[download_id].cancelled = True
