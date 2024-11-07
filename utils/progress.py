from tqdm import tqdm
import asyncio

class ProgressBar:
    def __init__(self, total, desc="Downloading", unit="B", unit_scale=True, unit_divisor=1024):
        self.pbar = tqdm(total=total, desc=desc, unit=unit, unit_scale=unit_scale, unit_divisor=unit_divisor)

    async def update(self, n):
        self.pbar.update(n)

    def close(self):
        self.pbar.close()

async def download_with_progress(session, url, filename, total_size):
    progress = ProgressBar(total=total_size)
    async with session.get(url) as response:
        with open(filename, 'wb') as f:
            async for chunk in response.content.iter_chunked(1024):
                f.write(chunk)
                await progress.update(len(chunk))
    progress.close()
