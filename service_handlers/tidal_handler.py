import os
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import asyncio
import json
from datetime import datetime

from config import DOWNLOAD_PATH, TIDAL_CLIENT_ID, TIDAL_CLIENT_SECRET
from utils.models import TrackInfo, AlbumInfo, PlaylistInfo
from tidal_api import TidalAPI, TidalRequestError, SessionType

logger = logging.getLogger(__name__)

class TidalHandler:
    def __init__(self, email: str = None, password: str = None):
        self.email = email
        self.password = password
        self.api = None
        self.quality_map = {
            'LOW': 'AAC 96',
            'HIGH': 'AAC 320',
            'LOSSLESS': 'FLAC 16/44.1',
            'HI_RES': 'MQA 24/96'
        }
        self.format_map = {
            'stereo': 'STEREO',
            'mqa': 'MQA',
            'dolby_atmos': 'DOLBY_ATMOS',
            '360': 'SONY_360RA'
        }

    async def authenticate(self) -> bool:
        """Authenticate with Tidal"""
        try:
            self.api = TidalAPI(
                client_id=TIDAL_CLIENT_ID,
                client_secret=TIDAL_CLIENT_SECRET
            )
            
            # Try TV-style authentication first
            try:
                await self.api.auth_oauth()
                return True
            except Exception as e:
                logger.warning(f"TV authentication failed, trying password auth: {str(e)}")

            # Fall back to password authentication
            if self.email and self.password:
                await self.api.auth_password(self.email, self.password)
                return True
            
            raise Exception("No valid authentication method available")
            
        except Exception as e:
            logger.error(f"Tidal authentication failed: {str(e)}")
            raise

    async def check_subscription(self) -> str:
        """Check user's subscription type"""
        if not self.api:
            raise Exception("Not authenticated")
            
        subscription = await self.api.get_subscription()
        return subscription.type

    async def extract_media_info(self, url: str) -> Dict[str, Any]:
        """Extract media type and ID from Tidal URL"""
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) < 2:
                raise ValueError("Invalid Tidal URL")
                
            media_type = path_parts[0]  # track, album, playlist, mix
            media_id = path_parts[1]
            
            # Handle different URL formats
            if media_type == 'browse':
                media_type = path_parts[1]
                media_id = path_parts[2]
            
            return {
                'type': media_type,
                'id': media_id
            }
        except Exception as e:
            logger.error(f"Error extracting Tidal info: {str(e)}")
            raise ValueError("Invalid Tidal URL format")

    async def get_track_info(self, track_id: str) -> TrackInfo:
        """Get track information"""
        try:
            track_data = await self.api.get_track(track_id)
            
            # Get available qualities and formats
            available_formats = []
            if track_data.get('audioModes'):
                if 'DOLBY_ATMOS' in track_data['audioModes']:
                    available_formats.append('DOLBY_ATMOS')
                if 'SONY_360RA' in track_data['audioModes']:
                    available_formats.append('SONY_360RA')
                
            quality = track_data.get('audioQuality', 'LOSSLESS')
            if quality == 'HI_RES':
                available_formats.append('MQA')
            
            return TrackInfo(
                id=track_id,
                title=track_data['title'],
                artist=track_data['artist']['name'],
                album=track_data['album']['title'],
                duration=track_data['duration'],
                cover_url=track_data['album']['cover'],
                release_date=track_data['releaseDate'],
                isrc=track_data.get('isrc'),
                explicit=track_data['explicit'],
                available_formats=available_formats,
                quality=self.quality_map.get(quality, quality)
            )
        except Exception as e:
            logger.error(f"Error getting track info: {str(e)}")
            raise

    async def get_album_info(self, album_id: str) -> AlbumInfo:
        """Get album information"""
        try:
            album_data = await self.api.get_album(album_id)
            tracks_data = await self.api.get_album_tracks(album_id)
            
            tracks = [track['id'] for track in tracks_data['items']]
            
            # Check if album has special formats
            available_formats = []
            if album_data.get('audioModes'):
                if 'DOLBY_ATMOS' in album_data['audioModes']:
                    available_formats.append('DOLBY_ATMOS')
                if 'SONY_360RA' in album_data['audioModes']:
                    available_formats.append('SONY_360RA')
            
            quality = album_data.get('audioQuality', 'LOSSLESS')
            if quality == 'HI_RES':
                available_formats.append('MQA')
            
            return AlbumInfo(
                id=album_id,
                title=album_data['title'],
                artist=album_data['artist']['name'],
                tracks=tracks,
                release_date=album_data['releaseDate'],
                cover_url=album_data['cover'],
                total_tracks=len(tracks),
                available_formats=available_formats,
                quality=self.quality_map.get(quality, quality)
            )
        except Exception as e:
            logger.error(f"Error getting album info: {str(e)}")
            raise

    async def get_playlist_info(self, playlist_id: str) -> PlaylistInfo:
        """Get playlist information"""
        try:
            playlist_data = await self.api.get_playlist(playlist_id)
            tracks_data = await self.api.get_playlist_tracks(playlist_id)
            
            tracks = [track['id'] for track in tracks_data['items']]
            
            return PlaylistInfo(
                id=playlist_id,
                title=playlist_data['title'],
                creator=playlist_data['creator']['name'],
                tracks=tracks,
                cover_url=playlist_data.get('squareImage'),
                total_tracks=len(tracks)
            )
        except Exception as e:
            logger.error(f"Error getting playlist info: {str(e)}")
            raise

    async def download_track(self, track_id: str, quality: str = 'LOSSLESS', format: str = 'STEREO') -> Dict[str, Any]:
        """Download a single track"""
        try:
            track_info = await self.get_track_info(track_id)
            
            # Validate and map format
            if format not in self.format_map:
                raise ValueError(f"Unsupported format: {format}")
            
            tidal_format = self.format_map[format]
            
            # Check if requested format is available
            if tidal_format != 'STEREO' and tidal_format not in track_info.available_formats:
                raise ValueError(f"Format {format} not available for this track")
            
            # ```python
            # Logic to download the track
            download_url = await self.api.get_download_url(track_id, quality, tidal_format)
            file_path = os.path.join(DOWNLOAD_PATH, f"{track_info.title}.{format.lower()}")
            
            async with aiofiles.open(file_path, 'wb') as f:
                async with self.api.download_file(download_url) as response:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        await f.write(chunk)
            
            return {
                'status': 'success',
                'file_path': file_path,
                'track_info': track_info
            }
        except Exception as e:
            logger.error(f"Error downloading track: {str(e)}")
            raise

    async def download_album(self, album_id: str, quality: str = 'LOSSLESS', format: str = 'STEREO') -> List[Dict[str, Any]]:
        """Download all tracks in an album"""
        try:
            album_info = await self.get_album_info(album_id)
            download_results = []
            
            for track_id in album_info.tracks:
                result = await self.download_track(track_id, quality, format)
                download_results.append(result)
            
            return download_results
        except Exception as e:
            logger.error(f"Error downloading album: {str(e)}")
            raise

    async def download_playlist(self, playlist_id: str, quality: str = 'LOSSLESS', format: str = 'STEREO') -> List[Dict[str, Any]]:
        """Download all tracks in a playlist"""
        try:
            playlist_info = await self.get_playlist_info(playlist_id)
            download_results = []
            
            for track_id in playlist_info.tracks:
                result = await self.download_track(track_id, quality, format)
                download_results.append(result)
            
            return download_results
        except Exception as e:
            logger.error(f"Error downloading playlist: {str(e)}")
            raise
