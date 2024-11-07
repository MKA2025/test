from collections import defaultdict
import time
from typing import Dict, Tuple

class RateLimiter:
    def __init__(self, max_requests: int = 5, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[int, list] = defaultdict(list)

    def can_proceed(self, user_id: int) -> Tuple[bool, float]:
        """Check if user can proceed with request"""
        current_time = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests
        user_requests = [req_time for req_time in user_requests 
                        if current_time - req_time < self.time_window]
        self.requests[user_id] = user_requests

        if len(user_requests) >= self.max_requests:
            wait_time = user_requests[0] + self.time_window - current_time
            return False, wait_time

        self.requests[user_id].append(current_time)
        return True, 0

    def reset_user(self, user_id: int):
        """Reset rate limit for a user"""
        if user_id in self.requests:
            del self.requests[user_id]
