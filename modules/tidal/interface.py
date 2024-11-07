from typing import Optional, List
from orpheus.core import *
from .tidal_api import TidalApi
from .exceptions import *

class TidalInterface(ModuleInterface):
    def __init__(self, module_controller: ModuleController):
        super().__init__(module_controller)
        self.api = TidalApi(
            self.module_settings['tv_token'],
            self.module_settings['tv_secret'],
            self.module_settings['mobile_atmos_token'],
            self.module_settings['mobile_default_token'],
            self.module_settings['enable_mobile'],
            TidalError
        )

    def login(self, email: Optional[str] = None, password: Optional[str] = None):
        try:
            self.api.login()
        except Exception as e:
            raise ModuleError(str(e))

    def get_track_info(self, track_id: str, quality_tier: QualityEnum, codec_options: CodecOptions) -> TrackInfo:
        track = self.api.get_track(track_id)
        album = self.api.get_album(track['album']['id'])

        # Get codec and quality info
        quality_tier_map = {
            QualityEnum.MINIMUM: 'LOW',
            QualityEnum.LOW: 'LOW', 
            QualityEnum.MEDIUM: 'HIGH',
            QualityEnum.HIGH: 'HIGH',
            QualityEnum.LOSSLESS: 'LOSSLESS',
            QualityEnum.HIFI: 'HI_RES'
        }

        tags = Tags(
            album_artist=album['artist']['name'],
            track_number=track['trackNumber'],
            total_tracks=album['numberOfTracks'],
            disc_number=track['volumeNumber'],
            total_discs=album.get('numberOfVolumes', 1),
            isrc=track.get('isrc'),
            upc=album.get('upc'),
            release_date=album.get('releaseDate')
        )

        return TrackInfo(
            name=track['title'],
            album=album['title'],
            album_id=str(album['id']),
            artists=[artist['name'] for artist in track.get('artists', [])],
            artist_id=str(track['artist']['id']),
            tags=tags,
            codec=CodecEnum.FLAC,  # Will be updated based on quality
            cover_url=self._get_cover_url(track['album'].get('cover')),
            release_year=int(album['releaseDate'].split('-')[0]) if album.get('releaseDate') else None,
            explicit=track.get('explicit', False),
            duration=track.get('duration', 0),
            bit_depth=track.get('audioQuality', {}).get('bitDepth'),
            sample_rate=track.get('audioQuality', {}).get('sampleRate'),
            bitrate=track.get('audioQuality', {}).get('bitrate')
        )

    def get_album_info(self, album_id: str) -> AlbumInfo:
        album = self.api.get_album(album_id)
        tracks = album.get('items', [])

        return AlbumInfo(
            name=album['title'],
            artist=album['artist']['name'],
            tracks=[str(track['id']) for track in tracks],
            release_year=int(album['releaseDate'].split('-')[0]) if album.get('releaseDate') else None,
            explicit=album.get('explicit', False),
            artist_id=str(album['artist']['id']),
            cover_url=self._get_cover_url(album.get('cover')),
            all_track_cover_jpg_url=self._get_cover_url(album.get('cover'), size=1280),
            upc=album.get('upc')
        )

    def get_playlist_info(self, playlist_id: str) -> PlaylistInfo:
        playlist = self.api.get_playlist(playlist_id)
        tracks = playlist.get('tracks', {}).get('items', [])

        return PlaylistInfo(
            name=playlist['title'],
            creator=playlist.get('creator', {}).get('name', 'Unknown'),
            tracks=[str(track['id']) for track in tracks],
            release_year=None,  # Playlists don't have release years
            explicit=any(track.get('explicit', False) for track in tracks),
            creator_id=str(playlist.get('creator', {}).get('id')),
            cover_url=self._get_cover_url(playlist.get('image'))
        )

    def get_track_download(self, track_id: str, codec: CodecEnum) -> TrackDownloadInfo:
        download_url = self.api.get_track_url(track_id)
        return TrackDownloadInfo(
            download_type=DownloadEnum.URL,
            file_url=download_url
        )

    def search(self, query_type: DownloadTypeEnum, query: str, limit: int = 20) -> List[SearchResult]:
        query_type_map = {
            DownloadTypeEnum.TRACK: 'tracks',
            DownloadTypeEnum.ALBUM: 'albums',
            DownloadTypeEnum.PLAYLIST: 'playlists',
            DownloadTypeEnum.ARTIST: 'artists'
        }

        results = self.api.search(query_type_map[query_type], query, limit)
        items = results.get('items', [])
        
        search_results = []
        for item in items:
            if query_type == DownloadTypeEnum.TRACK:
                result = self._parse_track_search_result(item)
            elif query_type == DownloadTypeEnum.ALBUM:
                result = self._parse_album_search_result(item)
            elif query_type == DownloadTypeEnum.PLAYLIST:
                result = self._parse_playlist_search_result(item)
            elif query_type == DownloadTypeEnum.ARTIST:
                result = self._parse_artist_search_result(item)
            else:
                continue
            
            search_results.append(result)
        
        return search_results

    def _get_cover_url(self, cover_id: str, size: int = 1280) -> Optional[str]:
        if not cover_id:
            return None
        return f"https://resources.tidal.com/images/{cover_id.replace('-', '/')}/{size}x{size}.jpg"

    def _parse_track_search_result(self, item: dict) -> SearchResult:
        return SearchResult(
            result_id=str(item['id']),
            name=item['title'],
            artists=[artist['name'] for artist in item.get('artists', [])],
            year=item.get('releaseDate', '').split('-')[0] if item.get('releaseDate') else None,
            explicit=item.get('explicit', False),
            duration=item.get('duration', 0),
            additional=[item.get('audioQuality', '')]
        )

    def _parse_album_search_result(self, item: dict) -> SearchResult:
        return SearchResult(
            result_id=str(item['id']),
            name=item['title'],
            artists=[item['artist']['name']],
             year=item.get('releaseDate', '').split('-')[0] if item.get('releaseDate') else None,
            explicit=item.get('explicit', False),
            additional=[]
        )

    def _parse_playlist_search_result(self, item: dict) -> SearchResult:
        return SearchResult(
            result_id=str(item['id']),
            name=item['title'],
            artists=[item['creator']['name']],
            year=None,
            explicit=item.get('explicit', False),
            additional=[]
        )

    def _parse_artist_search_result(self, item: dict) -> SearchResult:
        return SearchResult(
            result_id=str(item['id']),
            name=item['name'],
            artists=[],
            year=None,
            explicit=False,
            additional=[]
        )
