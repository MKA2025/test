import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

class TidalApi:
    API_URL = "https://api.tidal.com/v1/"
    AUTH_URL = "https://auth.tidal.com/v1/"

    def __init__(self, tv_token: str, tv_secret: str, mobile_token: Optional[str] = None, enable_mobile: bool = True):
        self.tv_token = tv_token
        self.tv_secret = tv_secret
        self.mobile_token = mobile_token
        self.enable_mobile = enable_mobile
        self.access_token = None
        self.user_id = None
        self.session = requests.Session()

    def _api_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
        url = urljoin(self.API_URL, endpoint)
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        response = self.session.request(method, url, params=params, json=data, headers=headers)
        
        if response.status_code == 401:
            raise Exception("Invalid or expired access token")
        elif response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} {response.text}")
        
        return response.json()

    def login(self):
        """Login to Tidal using TV token"""
        device_code = self._get_device_code()
        self.access_token = self._wait_for_device_auth(device_code)

    def _get_device_code(self) -> Dict[str, Any]:
        """Get device code for TV login"""
        response = self.session.post(
            f"{self.AUTH_URL}oauth2/device_authorization",
            data={
                "client_id": self.tv_token,
                "scope": "r_usr w_usr w_sub"
            }
        )
        if response.status_code == 200:
            return response.json()
        raise Exception("Failed to get device code")

    def _wait_for_device_auth(self, device_code: Dict[str, Any]) -> str:
        """Wait for user to authorize device"""
        interval = device_code.get('interval', 5)
        expires_in = device_code.get('expires_in', 300)
        device_code = device_code['device_code']
        
        print(f"Please visit: {device_code['verification_uri_complete']}")
        print("Waiting for authorization...")

        start_time = time.time()
        while time.time() - start_time < expires_in:
            response = self.session.post(
                f"{self.AUTH_URL}oauth2/token",
                data={
                    "client_id": self.tv_token,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data['access_token']
            time.sleep(interval)
        
        raise Exception("Authorization timeout")

    def search(self, query_type: str, query: str, limit: int = 20) -> List[Dict]:
        """Search for tracks, albums, artists or playlists"""
        params = {
            'query': query,
            'limit': limit,
            'offset': 0,
            'types': query_type
        }
        return self._api_request('GET', 'search', params=params).get('items', [])

    def get_track(self, track_id: str) -> Dict:
        """Get track metadata"""
        return self._api_request('GET', f'tracks/{track_id}')

    def get_album(self, album_id: str) -> Dict:
        """Get album metadata"""
        return self._api_request('GET', f'albums/{album_id}')

    def get_playlist(self, playlist_id: str) -> Dict:
        """Get playlist metadata"""
        return self._api_request('GET', f'playlists/{playlist_id}')

    def get_artist(self, artist_id: str) -> Dict:
        """Get artist metadata"""
        return self._api_request('GET', f'artists/{artist_id}')

    def get_track_url(self, track_id: str) -> str:
        """Get track download URL"""
        track_info = self.get_track(track_id)
        return track_info.get('playbackInfo', {}).get('url', '')

    def get_user_info(self) -> Dict:
        """Get user account info"""
        return self._api_request('GET', f'users/{self.user_id}')

    def get_subscription_info(self) -> Dict:
        """Get user subscription info"""
        return self._api_request('GET', 'subscriptions')

    def download_file(self, url: str, filename: str) -> str:
        """Download file from URL"""
        response = self.session.get(url ```python
        response.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(response.content)
        return filename

      def download_file(self, url: str, filename: str) -> str:
        """Download file from URL"""
        response = self.session.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return filename

    def get_album_tracks(self, album_id: str) -> List[Dict]:
        """Get tracks from an album"""
        return self._api_request('GET', f'albums/{album_id}/tracks').get('items', [])

    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """Get tracks from a playlist"""
        return self._api_request('GET', f'playlists/{playlist_id}/tracks').get('items', [])

    def get_artist_albums(self, artist_id: str, limit: int = 50) -> List[Dict]:
        """Get albums from an artist"""
        params = {'limit': limit}
        return self._api_request('GET', f'artists/{artist_id}/albums', params=params).get('items', [])

    def get_track_lyrics(self, track_id: str) -> Optional[Dict]:
        """Get lyrics for a track"""
        try:
            return self._api_request('GET', f'tracks/{track_id}/lyrics')
        except Exception:
            return None

    def get_track_contributors(self, track_id: str) -> List[Dict]:
        """Get contributors for a track"""
        return self._api_request('GET', f'tracks/{track_id}/contributors').get('items', [])

    def get_album_contributors(self, album_id: str) -> List[Dict]:
        """Get contributors for an album"""
        return self._api_request('GET', f'albums/{album_id}/contributors').get('items', [])

    def get_favorite_tracks(self, limit: int = 50) -> List[Dict]:
        """Get user's favorite tracks"""
        params = {'limit': limit}
        return self._api_request('GET', f'users/{self.user_id}/favorites/tracks', params=params).get('items', [])

    def get_favorite_albums(self, limit: int = 50) -> List[Dict]:
        """Get user's favorite albums"""
        params = {'limit': limit}
        return self._api_request('GET', f'users/{self.user_id}/favorites/albums', params=params).get('items', [])

    def get_favorite_playlists(self, limit: int = 50) -> List[Dict]:
        """Get user's favorite playlists"""
        params = {'limit': limit}
        return self._api_request('GET', f'users/{self.user_id}/favorites/playlists', params=params).get('items', [])

    def add_favorite_track(self, track_id: str) -> None:
        """Add a track to user's favorites"""
        self._api_request('POST', f'users/{self.user_id}/favorites/tracks', data={'trackId': track_id})

    def remove_favorite_track(self, track_id: str) -> None:
        """Remove a track from user's favorites"""
        self._api_request('DELETE', f'users/{self.user_id}/favorites/tracks/{track_id}')

    def add_favorite_album(self, album_id: str) -> None:
        """Add an album to user's favorites"""
        self._api_request('POST', f'users/{self.user_id}/favorites/albums', data={'albumId': album_id})

    def remove_favorite_album(self, album_id: str) -> None:
        """Remove an album from user's favorites"""
        self._api_request('DELETE', f'users/{self.user_id}/favorites/albums/{album_id}')

    def add_favorite_playlist(self, playlist_id: str) -> None:
        """Add a playlist to user's favorites"""
        self._api_request('POST', f'users/{self.user_id}/favorites/playlists', data={'playlistId': playlist_id})

    def remove_favorite_playlist(self, playlist_id: str) -> None:
        """Remove a playlist from user's favorites"""
        self._api_request('DELETE', f'users/{self.user_id}/favorites/playlists/{playlist_id}')
