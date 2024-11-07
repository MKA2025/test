import os
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from deezer_api import DeezerAPI
from utils.models import TrackInfo, AlbumInfo, PlaylistInfo
from config import DOWNLOAD_PATH

logger = logging.getLogger(__name__)

class DeezerHandler:
    def __init__(self, arl: str):
        self.api = DeezerAPI(arl)
        self.supported_qualities = ['MP3_128', 'MP3_320', 'FLAC']
        
    async def extract_deezer_id(self, url: str) -> Dict[str, Any]:
        """Extract media type and ID from Deezer URL"""
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) < 2:
                raise ValueError("Invalid Deezer URL")
                
            media_type = path_parts[0]
            media_id = path_parts[1]
            
            return {
                'type': media_type,  # track, album, playlist, artist
                'id': media_id
            }
        except Exception as e:
            logger.error(f"Error extracting Deezer ID: {str(e)}")
            raise ValueError("Invalid Deezer URL format")

    async def get_track_info(self, track_id: str) -> TrackInfo:
        """Get track information"""
        try:
            track_data = await self.api.get_track(track_id)
            
            return TrackInfo(
                id=track_id,
                title=track_data['title'],
                artist=track_data['artist']['name'],
                album=track_data['album']['title'],
                duration=track_data['duration'],
                cover_url=track_data['album']['cover_xl'],
                release_date=track_data['release_date'],
                isrc=track_data.get('isrc'),
                explicit=track_data['explicit_lyrics']
            )
        except Exception as e:
            logger.error(f"Error getting track info: {str(e)}")
            raise

    async def get_album_info(self, album_id: str) -> AlbumInfo:
        """Get album information"""
        try:
            album_data = await self.api.get_album(album_id)
            
            tracks = [track['id'] for track in album_data['tracks']['data']]
            
            return AlbumInfo(
                id=album_id,
                title=album_data['title'],
                artist=album_data['artist']['name'],
                tracks=tracks,
                release_date=album_data['release_date'],
                cover_url=album_data['cover_xl'],
                total_tracks=album_data['nb_tracks']
            )
        except Exception as e:
            logger.error(f"Error getting album info: {str(e)}")
            raise

    async def get_playlist_info(self, playlist_id: str) -> PlaylistInfo:
        """Get playlist information"""
        try:
            playlist_data = await self.api.get_playlist(playlist_id)
            
            tracks = [track['id'] for track in playlist_data['tracks']['data']]
            
            return PlaylistInfo(
                id=playlist_id,
                title=playlist_data['title'],
                creator=playlist_data['creator']['name'],
                tracks=tracks,
                cover_url=playlist_data['picture_xl'],
                total_tracks=playlist_data['nb_tracks']
            )
        except Exception as e:
            logger.error(f"Error getting playlist info: {str(e)}")
            raise

    async def download_track(self, track_id: str, quality: str = 'MP3_320') -> Dict[str, Any]:
        """Download a single track"""
        try:
            if quality not in self.supported_qualities:
                raise ValueError(f"Unsupported quality: {quality}")

            track_info = await self.get_track_info(track_id)
            
            # Get download URL
            download_url = await self.api.get_track_download_url(track_id, quality)
            
            # Create filename
            filename = f"{track_info.artist} - {track_info.title}"
            filename = "".join(x for x in filename if x.isalnum() or x in (' ', '-', '_')).strip()
            
            extension = 'mp3' if quality.startswith('MP3') else 'flac'
            file_path = os.path.join(DOWNLOAD_PATH, f"{filename}.{extension}")
            
            # Download file
            await self.api.download_file(download_url, file_path)
            
            # Add metadata
            await self.add_metadata(file_path, track_info)
            
            return {
                'success': True,
                'file_path': file_path,
                'title': track_info.title,
                'artist': track_info.artist,
                'duration': track_info.duration,
                'quality': quality
            }
            
        except Exception as e:
            logger.error(f"Error downloading track: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def download_album(self, album_id: str, quality: str = 'MP3_320') -> List[Dict[str, Any]]:
        """Download complete album"""
        try:
            album_info = await self.get_album_info(album_id)
            results = []
            
            for track_id in album_info.tracks:
                result = await self.download_track(track_id, quality)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error downloading album: {str(e)}")
            raise

    async def download_playlist(self, playlist_id: str, quality: str = 'MP3_320') -> List[Dict[str, Any]]:
        """Download complete playlist"""
        try:
            playlist_info = await self.get_playlist_info(playlist_id)
            results = []
            
            for track_id in playlist_info.tracks:
                result = await self.download_track(track_id, quality)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error downloading playlist: {str(e)}")
            raise

    async def add_metadata(self, file_path: str, track_info: TrackInfo) -> None:
        """Add metadata to downloaded file"""
        try:
            import mutagen
            from mutagen.easyid3 import EasyID3
            from mutagen.flac import FLAC
            
            extension = os.path.splitext(file_path)[1].lower()
            
            if extension == '.mp3':
                audio = EasyID3(file_path)
            elif extension == '.flac':
                audio = FLAC(file_path)
            else:
                return
                
            # Add basic metadata
            audio['title'] = track_info.title
            audio['artist'] = track_info.artist
            audio['album'] = track_info.album
            if track_info.isrc:
                audio['isrc'] = track_info.isrc
            
            # Add cover art if available
            if track_info.cover_url:
                await self.add_cover_art(file_path, track_info.cover_url)
                
            audio.save()
            
        except Exception as e:
            logger.error(f"Error adding metadata: {str(e)}")

    async def add_cover_art(self, file_ path: str, cover_url: str) -> None:
        """Add cover art to the downloaded file"""
        try:
            import requests
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3, APIC

            # Download cover art
            response = requests.get(cover_url)
            cover_path = f"{file_path}.cover.jpg"
            with open(cover_path, 'wb') as cover_file:
                cover_file.write(response.content)

            # Add cover art to audio file
            audio = MP3(file_path, ID3=ID3)
            with open(cover_path, 'rb') as cover_file:
                audio.tags.add(APIC(
                    encoding=3,  # 3 is for ID3v2.3
                    mime='image/jpeg',  # image/jpeg or image/png
                    type=3,  # 3 is for the cover image
                    desc='Cover',
                    data=cover_file.read()
                ))
            audio.save()
        except Exception as e:
            logger.error(f"Error adding cover art: {str(e)}")
