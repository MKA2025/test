import aiohttp
import asyncio
import base64
import json
import time
from typing import Dict, Any, Optional
from utils.exceptions import AuthenticationError, ApiError, QualityNotAvailableError

class TidalApi:
    def __init__(self, tv_token: str, tv_secret: str, 
                 mobile_token: Optional[str] = None,
                 enable_mobile: bool = True):
        self.tv_token = tv_token
        self.tv_secret = tv_secret
        self.mobile_token = mobile_token
        self.enable_mobile = enable_mobile
        
        self.tv_session = None
        self.mobile_session = None
        self.access_token = None
        self.user_id = None
        
        self.api_base = "https://api.tidal.com/v1/"
        self.auth_base = "https://auth.tidal.com/v1/"

    async def login(self):
        """Login to Tidal using TV token"""
        try:
            # TV session login
            device_code = await self._get_device_code()
            self.access_token = await self._wait_for_device_auth(device_code)
            
            # Initialize sessions
            self.tv_session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            # Get user info
            user_info = await self.get_user_info()
            self.user_id = user_info['id']
            
            # Mobile session if enabled
            if self.enable_mobile and self.mobile_token:
                self.mobile_session = await self._create_mobile_session()
                
        except Exception as e:
            raise AuthenticationError(f"Failed to login: {str(e)}")

    async def _get_device_code(self) -> Dict[str, Any]:
        """Get device code for TV login"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.auth_base}oauth2/device_authorization",
                data={
                    "client_id": self.tv_token,
                    "scope": "r_usr w_usr w_sub"
                }
            ) as response:
                if response.status == 200:
                    return await response.json()
                raise AuthenticationError("Failed to get device code")

    async def _wait_for_device_auth(self, device_code: Dict[str, Any]) -> str:
        """Wait for user to authorize device"""
        interval = device_code.get('interval', 5)
        expires_in = device_code.get('expires_in', 300)
        device_code = device_code['device_code']
        
        print(f"Please visit: {device_code['verification_uri_complete']}")
        print("Waiting for authorization...")

        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            while time.time() - start_time < expires_in:
                try:
                    async with session.post(
                        f"{self.auth_base}oauth2/token",
                        data={
                            "client_id": self.tv_token,
                            "device_code": device_code,
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                        }
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data['access_token']
                except:
                    pass
                await asyncio.sleep(interval)
            
            raise AuthenticationError("Authorization timeout")

    async def _create_mobile_session(self) -> aiohttp.ClientSession:
        """Create mobile session for Atmos/Sony360"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.auth_base}oauth2/token",
                data={
                    "client_id": self.mobile_token,
                    "grant_type": "client_credentials"
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return aiohttp.ClientSession(
                        headers={"Authorization": f"Bearer {data['access_token']}"}
                    )
                raise AuthenticationError("Failed to create mobile session")

    async def get_user_info(self) -> Dict[str, Any]:
        """Get user account info"""
        async with self.tv_session.get(
            f"{self.api_base}users/{self.user_id}"
        ) as response:
            if response.status == 200:
                return await response.json()
            raise ApiError("Failed to get user info")

    async def get_track(self, track_id: str) -> Dict[str, Any]:
        """Get track metadata"""
        async with self.tv_session.get(
            f"{self.api_base}tracks/{track_id}"
        ) as response:
            if response.status == 200:
                return await response.json()
            raise ApiError(f"Failed to get track {track_id}")

    async def get_album(self, album_id: str) -> Dict[str, Any]:
        """Get album metadata and tracks"""
        # Get album info
        async with self.tv_session.get(
            f"{self.api_base}albums/{album_id}"
        ) as response:
            if response.status != 200:
                raise ApiError(f"Failed to get album {album_id}")
            album_data = await response.json()

        # Get album tracks
        async with self.tv_session.get(
            f"{self.api_base}albums/{album_id}/tracks"
        ) as response:
            if response.status == 200:
                tracks = await response.json()
                album_data['tracks'] = tracks
                return album_data
            raise ApiError(f"Failed to get album tracks for {album_id}")

    async def get_track_download_url(self, track_id: str, quality: str) -> str:
        """Get track download URL for specified quality"""
        quality_map = {
            'hifi': 'HI_RES',
            'mqa': 'HI_RES',
            'high': 'HIGH',
            'medium': 'LOW',
            'low': 'LOW'
        }
        
        params = {
            'soundQuality': quality_map.get(quality, 'HIGH'),
            'playbackmode': 'STREAM'
        }
        
        # Try mobile session first for Atmos/360
        if self.mobile_session and quality in ['dolby_atmos', 'sony_360']:
            session = self.mobile_session
        else:
            session = self.tv_session
            
        async with session.get(
            f"{self.api_base}tracks/{track_id}/playbackinfopostpaywall",
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                if 'manifest_url' in data:
                    return data['manifest_url']
                raise QualityNotAvailableError(f"Quality {quality} not available")
            raise ApiError("Failed to get download URL")

    async def download_file(self, url: str, filename: str) -> str:
        """Download file from URL"""
        async with self.tv_session.get(url) as response:
            if response.status == 200:
                filepath = f"downloads/{filename}.flac"
                with open(filepath, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break   
                      f
        async def download_file(self, url: str, filename: str) -> str:
        """Download file from URL"""
        async with self.tv_session.get(url) as response:
            if response.status == 200:
                filepath = f"downloads/{filename}.flac"
                with open(filepath, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                return filepath
            raise ApiError(f"Failed to download file: {url}")
