"""Security utilities for input validation and rate limiting"""

import logging
import re
from typing import Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class InputValidator:
    """Validates and sanitizes user inputs"""

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript URLs
        r'data:',                      # Data URLs
        r'vbscript:',                  # VBScript
        r'on\w+\s*=',                  # Event handlers
        r'<\w+[^>]*\bon\w+[^>]*>',    # HTML with event handlers
    ]

    # Suspicious keywords
    SUSPICIOUS_KEYWORDS = [
        'eval', 'exec', 'system', 'subprocess', 'os.', 'import os',
        'rm ', 'del ', 'format ', 'delete', 'drop table', 'union select'
    ]

    def __init__(self):
        self.dangerous_regex = re.compile('|'.join(self.DANGEROUS_PATTERNS), re.IGNORECASE)
        self.suspicious_regex = re.compile('|'.join(self.SUSPICIOUS_KEYWORDS), re.IGNORECASE)

    def validate_text(self, text: str, max_length: int = 10000) -> Tuple[bool, str]:
        """Validate and sanitize text input"""
        if not text or not isinstance(text, str):
            return False, "Invalid input: text must be a non-empty string"

        if len(text) > max_length:
            return False, f"Input too long: maximum {max_length} characters allowed"

        # Check for dangerous patterns
        if self.dangerous_regex.search(text):
            logger.warning("Dangerous pattern detected in input")
            return False, "Input contains potentially dangerous content"

        # Check for suspicious keywords
        if self.suspicious_regex.search(text):
            logger.warning("Suspicious keywords detected in input")
            return False, "Input contains suspicious content"

        return True, text.strip()

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """Validate URL for safety"""
        if not url or not isinstance(url, str):
            return False, "Invalid URL: must be a non-empty string"

        # Basic URL pattern
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        if not url_pattern.match(url):
            return False, "Invalid URL format"

        # Block localhost/private IPs in production
        if any(x in url for x in ['localhost', '127.0.0.1', '0.0.0.0', '10.', '192.168.', '172.']):
            logger.warning(f"Blocked private/localhost URL: {url}")
            return False, "Access to local/private resources is not allowed"

        return True, url

    def sanitize_markdown(self, text: str) -> str:
        """Sanitize markdown content to prevent formatting abuse"""
        # Remove excessive markdown formatting
        text = re.sub(r'\*{5,}', '****', text)  # Max 4 asterisks
        text = re.sub(r'`{5,}', '````', text)  # Max 4 backticks
        text = re.sub(r'#{10,}', '#########', text)  # Max 9 hashes

        # Limit line length
        lines = text.split('\n')
        sanitized_lines = []
        for line in lines:
            if len(line) > 200:  # Max line length
                line = line[:197] + "..."
            sanitized_lines.append(line)

        return '\n'.join(sanitized_lines)


class RateLimiter:
    """Rate limiting for API calls and user actions"""

    def __init__(self, requests_per_minute: int = 30, burst_limit: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.user_requests = defaultdict(lambda: deque(maxlen=burst_limit))
        self.blocked_users = set()

        logger.info(f"RateLimiter initialized: {requests_per_minute}/min, burst={burst_limit}")

    def is_allowed(self, user_id: int, action: str = "default") -> Tuple[bool, str]:
        """Check if user is allowed to perform action"""
        if user_id in self.blocked_users:
            return False, "User is temporarily blocked due to excessive usage"

        now = datetime.now()
        key = f"{user_id}:{action}"
        requests = self.user_requests[key]

        # Remove old requests outside the time window
        cutoff_time = now - timedelta(minutes=1)
        while requests and requests[0] < cutoff_time:
            requests.popleft()

        # Check burst limit
        if len(requests) >= self.burst_limit:
            self.blocked_users.add(user_id)
            logger.warning(f"User {user_id} blocked due to burst limit violation")
            return False, "Too many requests. Please slow down."

        # Check rate limit
        if len(requests) >= self.requests_per_minute:
            return False, f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute."

        # Add current request
        requests.append(now)
        return True, "OK"

    def unblock_user(self, user_id: int) -> None:
        """Unblock a user"""
        self.blocked_users.discard(user_id)
        logger.info(f"User {user_id} unblocked")

    def cleanup(self) -> None:
        """Clean up old request data"""
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=5)  # Keep 5 minutes of history

        for key in list(self.user_requests.keys()):
            requests = self.user_requests[key]
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            if not requests:
                del self.user_requests[key]

        logger.debug("Rate limiter cleanup completed")