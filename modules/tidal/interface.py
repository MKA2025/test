from typing import Optional, Dict, Any, List
from utils.models import Track, Album, Playlist
from utils.exceptions import AuthenticationError, InvalidURLError, DownloadError
from .api import TidalApi
from .utils import parse_tidal_url, format_track_filename, get_quality_string

class TidalInterface:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api = TidalApi(
            tv_token=config.get('tv_token'),
            tv_secret=config.get('tv_secret'),
            mobile_token=config.get('mobile_atmos_token'),
            enable_mobile=config.get('enable_mobile', True)
        )
        
    async def login(self):
        """Login to Tidal"""
        try:
            await self.api.login()
        except Exception as e:
            raise AuthenticationError(f"Failed to login to Tidal: {str(e)}")

    async def get_track(self, url: str) -> Track:
        """Get track info from URL"""
        parsed = parse_tidal_url(url)
        if parsed['type'] != 'track':
            raise InvalidURLError("URL is not a Tidal track")
        
        try:
            track_data = await self.api.get_track(parsed['id'])
            return Track(
                id=track_data['id'],
                title=track_data['title'],
                artist=track_data['artist']['name'],
                album=track_data['album']['title'],
                duration=track_data['duration'],
                cover_url=self._get_cover_url(track_data['album']['cover']),
                quality=get_quality_string(self._get_quality_info(track_data))
            )
        except Exception as e:
            raise InvalidURLError(f"Failed to get track info: {str(e)}")

    async def get_album(self, url: str) -> Album:
        """Get album info from URL"""
        parsed = parse_tidal_url(url)
        if parsed['type'] != 'album':
            raise InvalidURLError("URL is not a Tidal album")
        
        try:
            album_data = await self.api.get_album(parsed['id'])
            tracks = []
            for track in album_data['tracks']['items']:
                tracks.append(Track(
                    id=track['id'],
                    title=track['title'],
                    artist=track['artist']['name'],
                    album=album_data['title'],
                    duration=track['duration'],
                    cover_url=self._get_cover_url(album_data['cover']),
                    quality=get_quality_string(self._get_quality_info(track))
                ))
            return Album(
                id=album_data['id'],
                title=album_data['title'],
                artist=album_data['artist']['name'],
                tracks=tracks,
                cover_url=self._get_cover_url(album_data['cover']),
                release_date=album_data.get('releaseDate')
            )
        except Exception as e:
            raise InvalidURLError(f"Failed to get album info: {str(e)}")

    async def get_playlist(self, url: str) -> Playlist:
        """Get playlist info from URL"""
        parsed = parse_tidal_url(url)
        if parsed['type'] != 'playlist':
            raise InvalidURLError("URL is not a Tidal playlist")
        
        try:
            playlist_data = await self.api.get_playlist(parsed['id'])
            tracks = []
            for item in playlist_data['tracks']['items']:
                track = item['item']
                tracks.append(Track(
                    id=track['id'],
                    title=track['title'],
                    artist=track['artist']['name'],
                    album=track['album']['title'],
                    duration=track['duration'],
                    cover_url=self._get_cover_url(track['album']['cover']),
                    quality=get_quality_string(self._get_quality_info(track))
                ))
            return Playlist(
                id=playlist_data['uuid'],
                title=playlist_data['title'],
                description=playlist_data.get('description'),
                author=playlist_data['creator']['name'],
                tracks=tracks,
                cover_url=self._get_cover_url(playlist_data.get('image'))
            )
        except Exception as e:
            raise InvalidURLError(f"Failed to get playlist info: {str(e)}")

    async def download_track(self, track: Track, quality: str) -> str:
        """Download track with specified quality"""
        try:
            download_url = await self.api.get_track_download_url(track.id, quality)
            file_path = await self.api.download_file(
                download_url, 
                format_track_filename(track)
            )
            return file_path
        except Exception as e:
            raise DownloadError(f"Failed to download track: {str(e)}")

    async def search(self, query: str, search_type: str = 'track', limit: int = 10) -> List[Dict[str, Any]]:
        """Search for tracks, albums, or playlists"""
        try:
            results = await self.api.search(query, search_type, limit)
            formatted_results = []
            for item in results[f'{search_type}s']['items']:
                if search_type == 'track':
                    formatted_results.append({
                        'id': item['id'],
                        'title': item['title'],
                        'artist': item['artist']['name'],
                        'album': item['album']['title'],
                        'duration': item['duration'],
                        'quality': get_quality_string(self._get_quality_info(item))
                    })
                elif search_type == 'album':
                    formatted_results.append({
                        'id': item['id'],
                        'title': item['title'],
                        'artist': item['artist']['name'],
                        'release_date': item.get('releaseDate'),
                        'tracks': item['numberOfTracks']
                    })
                elif search_type == 'playlist':
                    formatted_results.append({
                        'id': item['uuid'],
                        'title': item['title'],
                        'author': item['creator']['name'],
                        'tracks': item['numberOfTracks']
                    })
            return formatted_results
        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")

    def _get_cover_url(self, cover_id: str) -> str:
        """Generate cover URL from cover ID"""
        if not cover_id:
            return None
        return f"https://resources.tidal.com/images/{cover_id.replace('-', '/')}/1280x1280.jpg"

    def _get_quality_info(self, track_data: Dict) -> Dict[str, Any]:
        """Get available quality info for track"""
        quality_info = {}
        if track_data.get('audioQuality') == 'HI_RES':
            quality_info['hifi'] = True
            quality_info['mqa'] = True
        if track_data.get('audioModes'):
            if 'DOLBY_ATMOS' in track_data['audioModes']:
                quality_info['dolby_atmos'] = True
            if 'SONY_360RA' in track_data['audioModes']:
                quality_info['sony_360'] = True
        return quality_info
