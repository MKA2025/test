import asyncio
import aiohttp
import aiofiles
import os
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from utils.exceptions import DownloadError, InvalidURLError, QualityNotAvailableError, AuthenticationError
from utils.models import TrackInfo
from utils.tagger import Tagger
from config import DOWNLOAD_PATH, TIDAL_TOKEN, QOBUZ_APP_ID, QOBUZ_APP_SECRET, DEEZER_ARL

class MusicDownloader(ABC):
    """Abstract base class for music downloaders"""
    
    @abstractmethod
    async def download_track(self, url: str, quality: str) -> str:
        """Download a single track"""
        pass

    @abstractmethod
    async def get_track_info(self, url: str) -> TrackInfo:
        """Get track information"""
        pass

    @staticmethod
    async def download_file(url: str, filename: str):
        """Generic method to download a file"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(filename, mode='wb') as f:
                        await f.write(await response.read())
                else:
                    raise DownloadError(f"Failed to download file. Status: {response.status}")

class TidalDownloader(MusicDownloader):
    def __init__(self, token: str):
        self.token = token
        self.session = aiohttp.ClientSession(headers={"Authorization": f"Bearer {self.token}"})

    async def download_track(self, url: str, quality: str) -> str:
        track_info = await self.get_track_info(url)
        track_id = self.extract_track_id(url)
        download_url = await self.get_download_url(track_id, quality)
        
        filename = f"{track_info.artist} - {track_info.title}.flac"
        filepath = os.path.join(DOWNLOAD_PATH, filename)
        await self.download_file(download_url, filepath)
        
        Tagger.tag_file(filepath, track_info)
        
        return filepath

    async def get_track_info(self, url: str) -> TrackInfo:
        track_id = self.extract_track_id(url)
        async with self.session.get(f"https://api.tidal.com/v1/tracks/{track_id}") as response:
            if response.status == 200:
                data = await response.json()
                return TrackInfo(
                    title=data['title'],
                    artist=data['artist']['name'],
                    album=data['album']['title'],
                    release_date=data['album']['releaseDate'],
                    duration=data['duration'],
                    cover_url=f"https://resources.tidal.com/images/{data['album']['cover'].replace('-', '/')}/1280x1280.jpg"
                )
            else:
                raise InvalidURLError("Failed to retrieve track info from Tidal")

    @staticmethod
    def extract_track_id(url: str) -> str:
        return url.split('/')[-1]

    async def get_download_url(self, track_id: str, quality: str) -> str:
        quality_map = {"LOW": "LOW", "HIGH": "HIGH", "LOSSLESS": "LOSSLESS", "HI_RES": "HI_RES"}
        async with self.session.get(f"https://api.tidal.com/v1/tracks/{track_id}/streamUrl", 
                                    params={"soundQuality": quality_map.get(quality, "HIGH")}) as response:
            if response.status == 200:
                data = await response.json()
                return data['url']
            else:
                raise QualityNotAvailableError("Failed to get download URL for the specified quality")

class QobuzDownloader(MusicDownloader):
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.session = aiohttp.ClientSession()
        self.token = None

    async def authenticate(self):
        async with self.session.post("https://www.qobuz.com/api.json/0.2/user/login", 
                                     params={"app_id": self.app_id},
                                     data={"username": "your_username", "password": "your_password"}) as response:
            if response.status == 200:
                data = await response.json()
                self.token = data['user_auth_token']
            else:
                raise AuthenticationError("Failed to authenticate with Qobuz")

    async def download_track(self, url: str, quality: str) -> str:
        if not self.token:
            await self.authenticate()
        
        track_info = await self.get_track_info(url)
        track_id = self.extract_track_id(url)
        download_url = await self.get_download_url(track_id, quality)
        
        filename = f"{track_info.artist} - {track_info.title}.flac"
        filepath = os.path.join(DOWNLOAD_PATH, filename)
        await self.download_file(download_url, filepath)
        
        Tagger.tag_file(filepath, track_info)
        
        return filepath

    async def get_track_info(self, url: str) -> TrackInfo:
        track_id = self.extract_track_id(url)
        async with self.session.get(f"https://www.qobuz.com/api.json/0.2/track/get", 
                                    params={"app_id": self.app_id, "track_id": track_id}) as response:
            if response.status == 200:
                data = await response.json()
                return TrackInfo(
                    title=data['title'],
                    artist=data['performer']['name'],
                    album=data['album']['title'],
                    release_date=data['album']['release_date_original'],
                    duration=data['duration'],
                    cover_url=data['image']['large']
                )
            else:
                raise InvalidURLError("Failed to retrieve track info from Qobuz")

    @staticmethod
    def extract_track_id(url: str) -> str:
        return url.split('/')[-1]

    async def get_download_url(self, track_id: str, quality: str) -> str:
        quality_map = {"5": "5", "6": "6", "7": "7", "27": "27"}
        async with self.session.get("https://www.qobuz.com/api.json/0.2/track/getFileUrl", 
                                    params={
                                        "app_id": self.app_id,
                                        "track_id": track_id,
                                        "format_id": quality_map.get(quality, "6"),
                                        "user_auth_token": self.token
                                    }) as response:
            if response.status == 200:
                data = await response.json()
                return data['url']
            else:
                raise QualityNotAvailableError("Failed to get download URL for the specified quality")

class DeezerDownloader(MusicDownloader):
    def __init__(self, arl: str):
        self.arl = arl
        self.session = aiohttp.ClientSession(cookies={"arl": self.arl})

    async def download_track(self, url: str, quality: str) -> str:
        track_info = await self.get_track_info(url)
        track_id = self.extract_track_id(url)
        download_url = await self.get_download_url(track_id, quality)
        
        filename = f"{track_info.artist} - {track_info.title}.mp3"
        filepath = os.path.join(DOWNLOAD_PATH, filename)
        await self.download_file(download_url, filepath)
        
        Tagger.tag_file(filepath, track_info)
        
        return filepath

    async def get_track_info(self, url: str) -> TrackInfo:
        track_id = self.extract_track_id(url)
        async with self.session.get(f"https://api.deezer.com/track/{track_id}") as response:
            if response.status == 200:
                data = await response.json()
                return TrackInfo(
                    title=data['title'],
                    artist=data['artist']['name'],
                    album=data['album']['title'],
                    release_date=data['album']['release_date'],
                    duration=data['duration'],
                    cover_url=data['album']['cover_xl'],
                    isrc=data.get('isrc'),
                    bpm=data.get('bpm'),
                    genres=[genre['name'] for genre in data.get('genres', {}).get('data', [])]
                )
            else:
                raise InvalidURLError("Failed to retrieve track info from Deezer")

    @staticmethod
    def extract_track_id(url: str) -> str:
        try:
            return url.split('track/')[-1].split('?')[0]
        except:
            raise InvalidURLError("Invalid Deezer URL format")

    async def get_download_url(self, track_id: str, quality: str) -> str:
        quality_map = {
            "FLAC": "9",
            "MP3_320": "3",
            "MP3_128": "1"
        }
        
        # Get track token
        async with self.session.get(f"https://api.deezer.com/track/{track_id}") as response:
            if response.status != 200:
                raise DownloadError("Failed to get track information")
            track_data = await response.json()
            
        # Get download URL using track token and quality
        async with self.session.post("https://www.deezer.com/ajax/gw-light.php", 
                                   params={"api_version": "1.0", "api_token": track_data['token']},
                                   json={
                                       "method": "song.getFileUrl",
                                       "params": {
                                           "sng_id": track_id,
                                           "quality": quality_map.get(quality, "3")
                                       }
                                   }) as response:
            if response.status == 200:
                data = await response.json()
                if 'results' in data and 'url' in data['results']:
                    return data['results']['url']
                else:
                    raise QualityNotAvailableError("Failed to get download URL for the specified quality")
            else:
                raise DownloadError("Failed to get download URL")

    async def close(self):
        await self.session.close()

def get_downloader(service: str) -> MusicDownloader:
    """Factory function to get appropriate downloader based on service"""
    if service.lower() == "tidal":
        return TidalDownloader(TIDAL_TOKEN)
    elif service.lower() == "qobuz":
        return QobuzDownloader(QOBUZ_APP_ID, QOBUZ_APP_SECRET)
    elif service.lower() == "deezer":
        return DeezerDownloader(DEEZER_ARL)
    else:
        raise ValueError(f"Unsupported service: {service}")

def beauty_format_seconds(seconds: int) -> str:
    """Format seconds into mm:ss or hh:mm:ss format"""
    if seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:02d}:{remaining_seconds:02d}"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours:02d}:{remaining_minutes:02d}:{remaining_seconds:02d}"
