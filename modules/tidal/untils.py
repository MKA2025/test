from typing import Dict, Any, Optional, List
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

class TidalUtils:
    @staticmethod
    def parse_tidal_url(url: str) -> Dict[str, str]:
        """
        Parse Tidal URL to extract media type and ID
        
        Args:
            url: Tidal URL (track, album, playlist, mix)
            
        Returns:
            Dictionary containing media type and ID
            
        Example URLs:
            - https://tidal.com/browse/track/123456789
            - https://tidal.com/album/123456789
            - https://tidal.com/playlist/123456789
            - https://tidal.com/mix/123456789
        """
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            
            # Handle different URL formats
            if 'browse' in path_parts:
                path_parts.remove('browse')
                
            if len(path_parts) < 2:
                raise ValueError("Invalid Tidal URL format")
                
            media_type = path_parts[0].lower()  # track, album, playlist, mix
            media_id = path_parts[1]
            
            valid_types = ['track', 'album', 'playlist', 'mix', 'video']
            if media_type not in valid_types:
                raise ValueError(f"Invalid media type. Must be one of: {', '.join(valid_types)}")
                
            return {
                'type': media_type,
                'id': media_id
            }
        except Exception as e:
            raise ValueError(f"Failed to parse Tidal URL: {str(e)}")

    @staticmethod
    def format_file_name(track_info: Dict[str, Any], template: str = None) -> str:
        """
        Format track filename based on template
        
        Args:
            track_info: Track metadata dictionary
            template: Optional filename template
            
        Returns:
            Formatted filename string
            
        Default template: {track_number}. {artist} - {title}
        """
        if not template:
            template = "{track_number}. {artist} - {title}"
            
        # Get basic track info
        track_data = {
            'track_number': str(track_info.get('trackNumber', '')).zfill(2),
            'title': track_info.get('title', ''),
            'artist': track_info.get('artist', {}).get('name', ''),
            'album': track_info.get('album', {}).get('title', ''),
            'year': track_info.get('releaseDate', '')[:4] if track_info.get('releaseDate') else ''
        }
        
        # Add quality info if available
        quality_info = TidalUtils.get_quality_info(track_info)
        track_data.update(quality_info)
        
        # Sanitize filename
        filename = template.format(**track_data)
        filename = TidalUtils.sanitize_filename(filename)
        
        return filename

    @staticmethod
    def get_quality_info(track_info: Dict[str, Any]) -> Dict[str, str]:
        """
        Get quality information from track metadata
        
        Args:
            track_info: Track metadata dictionary
            
        Returns:
            Dictionary containing quality information
        """
        quality_info = {
            'quality': '',
            'bit_depth': '',
            'sample_rate': '',
            'bitrate': ''
        }
        
        # Get audio quality
        audio_quality = track_info.get('audioQuality', '').upper()
        audio_modes = track_info.get('audioModes', [])
        
        if 'DOLBY_ATMOS' in audio_modes:
            quality_info['quality'] = 'Dolby Atmos'
        elif 'SONY_360RA' in audio_modes:
            quality_info['quality'] = 'Sony 360 Reality Audio'
        elif audio_quality == 'HI_RES':
            quality_info['quality'] = 'MQA'
            quality_info['bit_depth'] = '24'
            quality_info['sample_rate'] = '96'
        elif audio_quality == 'LOSSLESS':
            quality_info['quality'] = 'FLAC'
            quality_info['bit_depth'] = '16'
            quality_info['sample_rate'] = '44.1'
        elif audio_quality == 'HIGH':
            quality_info['quality'] = 'AAC'
            quality_info['bitrate'] = '320'
        elif audio_quality == 'LOW':
            quality_info['quality'] = 'AAC'
            quality_info['bitrate'] = '96'
            
        return quality_info

    @staticmethod
    def get_cover_url(cover_id: str, size: int = 1280) -> Optional[str]:
        """
        Generate cover artwork URL
        
        Args:
            cover_id: Cover artwork ID
            size: Desired image size (default 1280)
            
        Returns:
            Cover artwork URL string
            
        Supported sizes: 80, 160, 320, 480, 640, 1080, 1280
        """
        if not cover_id:
            return None
            
        valid_sizes = [80, 160, 320, 480, 640, 1080, 1280]
        if size not in valid_sizes:
            size = min(valid_sizes, key=lambda x: abs(x - size))
            
        cover_id = cover_id.replace('-', '/')
        return f"https://resources.tidal.com/images/{cover_id}/{size}x{size}.jpg"

    @staticmethod
    def format_duration(duration: int) -> str:
        """
        Format duration in seconds to MM:SS format
        
        Args:
            duration: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        minutes = duration // 60
        seconds = duration % 60
        return f"{minutes}:{seconds:02d}"

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Remove invalid characters from filename
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        # Remove trailing spaces and periods
        filename = filename.strip('. ')
        
        # Limit length
        if len(filename.encode('utf-8')) > 255:
            while len(filename.encode('utf-8')) > 251:
                filename = filename[:-1]
            filename = filename.strip('. ')
            
        return filename

    @staticmethod
    def parse_release_date(date_str: str) -> Optional[datetime]:
        """
        Parse release date string to datetime object
        
        Args:
            date_str: Date string from Tidal API
            
        Returns:
            datetime object or None if parsing fails
        """
        if not date_str:
            return None
            
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y')
            except ValueError:
                return None

        @staticmethod
    def format_contributors(contributors: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Format track/album contributors
        
        Args:
            contributors: List of contributor dictionaries
            
        Returns:
            Dictionary mapping role to list of contributor names
        """
        formatted = {}
        for contributor in contributors:
            role = contributor.get('role', 'Unknown')
            name = contributor.get('name', '')
            if role not in formatted:
                formatted[role] = []
            formatted[role].append(name)
        return formatted

    @staticmethod
    def format_track_info(track: Dict[str, Any]) -> str:
        """
        Format track information for display
        
        Args:
            track: Track metadata dictionary
            
        Returns:
            Formatted track information string
        """
        info = []
        info.append(f"Title: {track.get('title', 'Unknown')}")
        info.append(f"Artist: {track.get('artist', {}).get('name', 'Unknown')}")
        info.append(f"Album: {track.get('album', {}).get('title', 'Unknown')}")
        info.append(f"Duration: {TidalUtils.format_duration(track.get('duration', 0))}")
        
        quality_info = TidalUtils.get_quality_info(track)
        info.append(f"Quality: {quality_info['quality']}")
        if quality_info['bit_depth'] and quality_info['sample_rate']:
            info.append(f"Format: {quality_info['bit_depth']}bit / {quality_info['sample_rate']}kHz")
        elif quality_info['bitrate']:
            info.append(f"Bitrate: {quality_info['bitrate']}kbps")
        
        return "\n".join(info)
