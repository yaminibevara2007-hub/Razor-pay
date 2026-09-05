import logging
import re
import os

SENSITIVE_PATTERNS = [
    (re.compile(r'("?(?:password|token|secret|jwt|cvv|pin|otp)"?\s*[:=]\s*)"[^"]+"', re.IGNORECASE), r'\1"***REDACTED***"'),
    (re.compile(r'("?(?:password|token|secret|jwt|cvv|pin|otp)"?\s*[:=]\s*)[^\s,;}]+', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'\b(?:\d[ -]*?){13,19}\b'), r'***REDACTED_CARD_NUMBER***')
]

class SecurityFilter(logging.Filter):
    """Filter that sanitizes credentials, tokens, and payment card numbers from log records"""
    def filter(self, record):
        if isinstance(record.msg, str):
            for pattern, replacement in SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True

def setup_logger(app):
    """Configure secure application logger with sanitization filter"""
    log_level = logging.DEBUG if app.debug else logging.INFO
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.addFilter(SecurityFilter())
    
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
    
    return app.logger
