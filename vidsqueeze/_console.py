import sys


def _print_status(action: str, message: str, verbose: bool = True):
    """Print a status message to stderr."""
    print(f"{action}: {message}", file=sys.stderr, flush=True)


def print_error(message: str):
    """Print an error message to stderr."""
    print(f"Error: {message}", file=sys.stderr, flush=True)


def print_warning(message: str):
    """Print a warning message to stderr."""
    print(f"Warning: {message}", file=sys.stderr, flush=True)
