class DownloadError(Exception):
    """Raised when download fails"""
    pass

class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass

class InvalidURLError(Exception):
    """Raised when URL is
