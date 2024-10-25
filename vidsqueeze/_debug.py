import os
import sys
import time
from enum import Enum, auto
from typing import Any, Optional


class DebugCategory(Enum):
    """Categories for debug messages to allow filtering."""

    CLI = auto()
    VALIDATION = auto()
    FFMPEG = auto()
    PROGRESS = auto()
    SYSTEM = auto()


class Debug:
    """Debug logging system controlled by DEBUG environment variable."""

    def __init__(self):
        self._enabled = os.environ.get("DEBUG", "").lower() == "true"
        self._start_time = time.time()

    def _format_message(self, category: DebugCategory, message: Any) -> str:
        """Format debug message with timestamp and category."""
        elapsed = time.time() - self._start_time
        return f"[{elapsed:.3f}s] {category.name}: {message}"

    def log(self, category: DebugCategory, message: Any) -> None:
        """Log a debug message if debugging is enabled."""
        if self._enabled:
            print(self._format_message(category, message), file=sys.stderr, flush=True)

    def is_enabled(self) -> bool:
        """Check if debugging is enabled."""
        return self._enabled


# Global debug instance
debug = Debug()


def log_call(category: DebugCategory):
    """Decorator to log function calls with args and execution time."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not debug.is_enabled():
                return func(*args, **kwargs)

            # Log function entry
            debug.log(category, f"Entering {func.__name__}")
            debug.log(category, f"Args: {args}, Kwargs: {kwargs}")

            # Time the function
            start = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                debug.log(category, f"Completed {func.__name__} in {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start
                debug.log(
                    category, f"Failed {func.__name__} after {elapsed:.3f}s: {str(e)}"
                )
                raise

        return wrapper

    return decorator
