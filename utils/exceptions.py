class DownloadError(Exception):
    """Raised when download fails"""
    def __init__(self, message="Download failed", details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)

class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    def __init__(self, message="Rate limit exceeded", retry_after=None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    def __init__(self, message="Authentication failed", service=None):
        self.message = message
        self.service = service
        super().__init__(self.message)

class InvalidURLError(Exception):
    """Raised when URL is invalid or not supported"""
    def __init__(self, message="Invalid or unsupported URL", url=None):
        self.message = message
        self.url = url
        super().__init__(self.message)

class QualityNotAvailableError(Exception):
    """Raised when requested quality is not available"""
    def __init__(self, message="Requested quality not available", available_qualities=None):
        self.message = message
        self.available_qualities = available_qualities
        super().__init__(self.message)

class FileSizeLimitError(Exception):
    """Raised when file size exceeds limit"""
    def __init__(self, message="File size exceeds limit", size=None, limit=None):
        self.message = message
        self.size = size
        self.limit = limit
        super().__init__(self.message)

class DatabaseError(Exception):
    """Raised when database operation fails"""
    def __init__(self, message="Database operation failed", operation=None):
        self.message = message
        self.operation = operation
        super().__init__(self.message)

class UserNotAuthorizedError(Exception):
    """Raised when user is not authorized"""
    def __init__(self, message="User not authorized", user_id=None):
        self.message = message
        self.user_id = user_id
        super().__init__(self.message)

class ServiceUnavailableError(Exception):
    """Raised when music service is unavailable"""
    def __init__(self, message="Service unavailable", service=None):
        self.message = message
        self.service = service
        super().__init__(self.message)

class ConversionError(Exception):
    """Raised when audio conversion fails"""
    def __init__(self, message="Audio conversion failed", source_format=None, target_format=None):
        self.message = message
        self.source_format = source_format
        self.target_format = target_format
        super().__init__(self.message)

class MetadataError(Exception):
    """Raised when handling audio metadata fails"""
    def __init__(self, message="Metadata operation failed", details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)

class NetworkError(Exception):
    """Raised when network-related operations fail"""
    def __init__(self, message="Network operation failed", details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)

class QueueError(Exception):
    """Raised when queue-related operations fail"""
    def __init__(self, message="Queue operation failed", queue_size=None):
        self.message = message
        self.queue_size = queue_size
        super().__init__(self.message)

class CacheError(Exception):
    """Raised when cache-related operations fail"""
    def __init__(self, message="Cache operation failed", operation=None):
        self.message = message
        self.operation = operation
        super().__init__(self.message)

class ConfigError(Exception):
    """Raised when configuration-related issues occur"""
    def __init__(self, message="Configuration error", parameter=None):
        self.message = message
        self.parameter = parameter
        super().__init__(self.message)

class APIError(Exception):
    """Raised when API-related operations fail"""
    def __init__(self, message="API operation failed", service=None, status_code=None):
        self.message = message
        self.service = service
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(Exception):
    """Raised when validation fails"""
    def __init__(self, message="Validation failed", field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)
