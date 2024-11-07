import asyncio
from utils.downloader import Downloader

class BatchHandler:
    def __init__(self, tidal_handler, qobuz_handler, deezer_handler):
        self.handlers = {
            'tidal': tidal_handler,
            'qobuz': qobuz_handler,
            'deezer': deezer_handler
        }
        self.downloader = Downloader()

    async def batch_download(self, urls):
        tasks = []
        for url in urls:
            service = self.detect_service(url)
            if service:
                task = asyncio.create_task(self.download_single(service, url))
                tasks.append(task)
        await asyncio.gather(*tasks)

    def detect_service(self, url):
        for service, handler in self.handlers.items():
            if service in url:
                return service
        return None

    async def download_single(self, service, url):
        handler = self.handlers[service]
        info = await handler.extract_media_info(url)
        if info['type'] == 'track':
            await handler.download_track(info['id'])
        elif info['type'] == 'album':
            await handler.download_album(info['id'])
        elif info['type'] == 'playlist':
            await handler.download_playlist(info['id'])
