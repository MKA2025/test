import logging

logger = logging.getLogger(__name__)

class ErrorHandler:
    @staticmethod
    def handle_error(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                # You can add more specific error handling here
                return {"error": str(e)}
        return wrapper
