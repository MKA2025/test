from urllib.parse import urlparse, parse_qs
import re
from typing import Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)

class URLParsingError(Exception):
    """Custom exception for URL parsing errors"""
    pass

class URLParser:
    # Service URL patterns
    URL_PATTERNS = {
        'tidal': {
            'domains': ['tidal.com', 'listen.tidal.com'],
            'patterns': {
                'track': r'/track/(\d+)',
                'album': r'/album/(\d+)',
                'playlist': r'/playlist/([a-zA-Z0-9-]+)',
                'artist': r'/artist/(\d+)'
            }
        },
        'qobuz': {
            'domains': ['qobuz.com', 'play.qobuz.com', 'open.qobuz.com'],
            'patterns': {
                'track': r'/track/(\d+)',
                'album': r'/album/(\d+)',
                'playlist': r'/playlist/(\d+)',
                'artist': r'/artist/(\d+)'
            }
        },
        'deezer': {
            'domains': ['deezer.com', 'deezer.page.link'],
            'patterns': {
                'track': r'/track/(\d+)',
                'album': r'/album/(\d+)',
                'playlist': r'/playlist/(\d+)',
                'artist': r'/artist/(\d+)'
            }
        }
    }

    # Short URL patterns
    SHORT_URL_PATTERNS = {
        'tidal': r't.co/([a-zA-Z0-9]+)',
        'qobuz': r'qbz.fm/([a-zA-Z0-9]+)',
        'deezer': r'deezer.page.link/([a-zA-Z0-9]+)'
    }

    @staticmethod
    def parse_url(url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse music service URLs and return service, media type, and media ID.
        
        Args:
            url (str): The URL to parse
            
        Returns:
            Tuple[Optional[str], Optional[str], Optional[str]]: 
            (service_name, media_type, media_id) or (None, None, None) if parsing fails
            
        Raises:
            URLParsingError: If URL is invalid or unsupported
        """
        try:
            # Clean and validate URL
            cleaned_url = URLParser._clean_url(url)
            if not cleaned_url:
                raise URLParsingError("Invalid URL format")

            # Handle short URLs
            if URLParser._is_short_url(cleaned_url):
                expanded_url = URLParser._expand_short_url(cleaned_url)
                if expanded_url:
                    cleaned_url = expanded_url

            # Parse URL
            parsed_url = urlparse(cleaned_url)
            
            # Get service name
            service = URLParser._identify_service(parsed_url.netloc)
            if not service:
                raise URLParsingError(f"Unsupported service domain: {parsed_url.netloc}")

            # Get media type and ID
            media_type, media_id = URLParser._extract_media_info(service, parsed_url.path)
            if not media_type or not media_id:
                raise URLParsingError(f"Could not extract media information from path: {parsed_url.path}")

            return service, media_type, media_id

        except URLParsingError as e:
            logger.warning(f"URL parsing error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while parsing URL: {str(e)}", exc_info=True)
            raise URLParsingError(f"Failed to parse URL: {str(e)}")

    @staticmethod
    def _clean_url(url: str) -> Optional[str]:
        """Clean and validate URL format"""
        if not url:
            return None
            
        # Remove leading/trailing whitespace
        url = url.strip()
        
        # Add https:// if protocol is missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Basic URL format validation
        try:
            result = urlparse(url)
            return url if all([result.scheme, result.netloc]) else None
        except Exception:
            return None

    @staticmethod
    def _identify_service(domain: str) -> Optional[str]:
        """Identify music service from domain"""
        domain = domain.lower()
        for service, config in URLParser.URL_PATTERNS.items():
            if any(d in domain for d in config['domains']):
                return service
        return None

    @staticmethod
    def _extract_media_info(service: str, path: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract media type and ID from URL path"""
        patterns = URLParser.URL_PATTERNS[service]['patterns']
        
        for media_type, pattern in patterns.items():
            match = re.search(pattern, path)
            if match:
                return media_type, match.group(1)
                
        return None, None

    @staticmethod
    def _is_short_url(url: str) -> bool:
        """Check if URL is a short URL format"""
        for pattern in URLParser.SHORT_URL_PATTERNS.values():
            if re.search(pattern, url):
                return True
        return False

    @staticmethod
    def _expand_short_url(url: str) -> Optional[str]:
        """Expand short URL to full URL"""
        import requests
        
        try:
            response = requests.head(url, allow_redirects=True, timeout=5)
            return response.url if response.status_code == 200 else None
        except Exception as e:
            logger.warning(f"Failed to expand short URL: {str(e)}")
            return None

    @staticmethod
    def get_url_info(url: str) -> Dict[str, str]:
        """
        Get detailed information about a music URL
        
        Args:
            url (str): The URL to analyze
            
        Returns:
            Dict[str, str]: Dictionary containing URL information
        """
        try:
            service, media_type, media_id = URLParser.parse_url(url)
            
            return {
                'service': service,
                'media_type': media_type,
                'media_id': media_id,
                'is_valid': True,
                'error': None
            }
        except URLParsingError as e:
            return {
                'service': None,
                'media_type': None,
                'media_id': None,
                'is_valid': False,
                'error': str(e)
            }

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate if URL is supported
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if URL is valid and supported, False otherwise
        """
        try:
            service, media_type, media_id = URLParser.parse_url(url)
            return all([service, media_type, media_id])
        except URLParsingError:
            return False

def parse_url(url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Convenience function to parse URLs without instantiating URLParser
    
    Args:
        url (str): URL to parse
        
    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]: 
        (service_name, media_type, media_id)
    """
    return URLParser.parse_url(url)

def validate_url(url: str) -> bool:
    """
    Convenience function to validate URLs without instantiating URLParser
    
    Args:
        url (strdef validate_url(url: str) -> bool:
    """
    Convenience function to validate URLs without instantiating URLParser
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if URL is valid and supported, False otherwise
    """
    return URLParser.validate_url(url)

def get_url_info(url: str) -> Dict[str, str]:
    """
    Convenience function to get detailed URL info without instantiating URLParser
    
    Args:
        url (str): URL to analyze
        
    Returns:
        Dict[str, str]: Dictionary containing URL information
    """
    return URLParser.get_url_info(url)

# Example usage
if __name__ == "__main__":
    test_urls = [
        "https://tidal.com/browse/track/12345678",
        "https://listen.tidal.com/album/87654321",
        "https://play.qobuz.com/track/98765432",
        "https://www.deezer.com/en/album/12345678",
        "https://t.co/abcd1234",
        "https://invalid-url.com/track/12345"
    ]

    for url in test_urls:
        print(f"\nTesting URL: {url}")
        try:
            service, media_type, media_id = parse_url(url)
            print(f"Service: {service}")
            print(f"Media Type: {media_type}")
            print(f"Media ID: {media_id}")
        except URLParsingError as e:
            print(f"Error: {str(e)}")

        print(f"Is Valid: {validate_url(url)}")
        print("Detailed Info:", get_url_info(url))
