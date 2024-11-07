from typing import Dict, Any
import asyncio
from tidal_api import TidalAPI

async def download_from_tidal(url: str, token: str, format: str = 'stereo') -> Dict[str, Any]:
    try:
        api = TidalAPI(token)
        
        # Extract track/album ID from URL
        media_id = extract_tidal_id(url)
        
        # Get track info
        track_info = await api.get_track_info(media_id)
        
        # Check available formats
        formats = await api.get_available_formats(media_id)
        
        # Select quality based on format
        if format == 'atmos' and 'Dol by Atmos' in formats:
            selected_format = 'Dolby Atmos'
        elif format == '360' and '360 Audio' in formats:
            selected_format = '360 Audio'
        else:
            selected_format = 'Stereo'
        
        # Download the track
        file_path = await api.download_track(media_id, selected_format)
        
        return {
            'success': True,
            'title': track_info['title'],
            'duration': track_info['duration'],
            'file_path': file_path,
            'artist': track_info['artist']
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
``` 5. **service_handlers/qobuz_handler.py**
```python
from typing import Dict, Any
from qobuz_api import QobuzAPI

async def download_from_qobuz(url: str, token: str) -> Dict[str, Any]:
    try:
        api = QobuzAPI(token)
        
        # Extract track/album ID from URL
        media_id = extract_qobuz_id(url)
        
        # Get track info
        track_info = await api.get_track_info(media_id)
        
        # Download the track
        file_path = await api.download_track(media_id)
        
        return {
            'success': True,
            'title': track_info['title'],
            'duration': track_info['duration'],
            'file_path': file_path,
            'artist': track_info['artist']
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
