import math
import pathlib
import shutil
import sys
import threading
from typing import Any, Dict, Optional

from tqdm import tqdm

TERM_SIZE_FALLBACK = 80
PATH_DISPLAY_RATIO = 1 / 3
ELLIPSIS = "..."

# Progress bar formats
PBAR_OPEN_FORMAT = "{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
PBAR_CLOSED_FORMAT = "{desc}: {n_fmt}/{total_fmt} [{elapsed}, {rate_fmt}]                                                                                    "

# Global lock for thread-safe progress bar updates
pbar_lock = threading.Lock()


def _get_term_size():
    """Get terminal width with fallback for non-terminal contexts."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return TERM_SIZE_FALLBACK


def _truncate_path(path, max_len=None):
    """
    Truncate a path while preserving the most meaningful parts for display.
    """
    if max_len is None:
        max_len = math.floor(_get_term_size() * PATH_DISPLAY_RATIO)

    path = pathlib.Path(path)
    path_str = str(path)

    if len(path_str) <= max_len:
        return path_str

    ellipsis_len = len(ELLIPSIS)
    parts = path.parts
    basename = parts[-1]

    if len(basename) <= max_len - ellipsis_len:
        available_space = max_len - ellipsis_len
        truncated_parts = []
        for part in parts[:-1]:
            if available_space - (len(part) + 1) >= 0:
                truncated_parts.append(part)
                available_space -= len(part) + 1
            else:
                break
        return f"{ELLIPSIS}{pathlib.Path(*truncated_parts, basename)}"

    return basename[: max(1, max_len - ellipsis_len)] + ELLIPSIS


def _format_path(path, max_len=None):
    """Format a path for display."""
    if max_len is None:
        max_len = math.floor(_get_term_size() * PATH_DISPLAY_RATIO)
    truncated_path = _truncate_path(path, max_len)
    return truncated_path


class MultiFileProgressBar:
    def __init__(self, total_files: int):
        self.total_files = total_files
        self.file_pbars: Dict[str, tqdm] = {}
        self.lock = threading.Lock()
        self.active_count = 0

    def get_file_pbar(self, input_file: str, file_size: int) -> tqdm:
        with self.lock:
            if input_file not in self.file_pbars:
                # Create progress bar at current position
                self.active_count += 1
                self.file_pbars[input_file] = tqdm(
                    desc=_format_path(input_file),
                    total=file_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    position=self.active_count - 1,
                    leave=False,  # Don't leave the progress bar
                    bar_format=PBAR_OPEN_FORMAT,
                    file=sys.stderr,
                )
            return self.file_pbars[input_file]

    def update(self, input_file: str, n: int):
        with self.lock:
            if input_file in self.file_pbars:
                self.file_pbars[input_file].update(n)

    def complete_file(self, input_file: str):
        """Complete a file's progress bar."""
        with self.lock:
            if input_file in self.file_pbars:
                pbar = self.file_pbars[input_file]

                # Ensure progress bar shows completion
                if pbar.n < pbar.total:
                    pbar.update(pbar.total - pbar.n)

                # Move cursor up to write completed bar
                sys.stderr.write("\033[s")  # Save cursor position
                sys.stderr.write("\033[%dA" % (self.active_count))  # Move to top

                # Change format and refresh to show completion
                pbar.bar_format = PBAR_CLOSED_FORMAT
                pbar.refresh()
                sys.stderr.write("\n")

                sys.stderr.write("\033[u")  # Restore cursor position

                # Close and remove progress bar
                pbar.close()
                del self.file_pbars[input_file]
                self.active_count -= 1

                # Refresh remaining bars
                for other_pbar in self.file_pbars.values():
                    if other_pbar.pos > pbar.pos:
                        other_pbar.pos -= 1
                    other_pbar.refresh()

    def close(self):
        with self.lock:
            # Complete any remaining progress bars
            for input_file in list(self.file_pbars.keys()):
                self.complete_file(input_file)


# Global progress bar instance
multi_file_pbar: Optional[MultiFileProgressBar] = None


def init_probe_progress(total_files: int):
    """Initialize progress tracking for probe phase."""
    init_multi_file_pbar(total_files)


def init_compression_progress(files_info: Dict[str, Any]):
    """Initialize progress tracking for compression phase."""
    init_multi_file_pbar(len(files_info))


def init_multi_file_pbar(total_files: int):
    """Initialize the global progress bar."""
    global multi_file_pbar
    multi_file_pbar = MultiFileProgressBar(total_files)


def get_file_pbar(input_file: str, file_size: int) -> tqdm:
    """Get a progress bar for a specific file."""
    global multi_file_pbar
    if multi_file_pbar is None:
        raise RuntimeError(
            "MultiFileProgressBar not initialized. Call init_multi_file_pbar first."
        )
    return multi_file_pbar.get_file_pbar(input_file, file_size)


def update_pbar(input_file: str, n: int):
    """Update progress for a specific file."""
    global multi_file_pbar
    if multi_file_pbar is None:
        raise RuntimeError(
            "MultiFileProgressBar not initialized. Call init_multi_file_pbar first."
        )
    multi_file_pbar.update(input_file, n)


def complete_pbar(input_file: str):
    """Complete a file's progress bar."""
    global multi_file_pbar
    if multi_file_pbar is not None:
        multi_file_pbar.complete_file(input_file)


def close_pbar():
    """Close and cleanup progress bars."""
    global multi_file_pbar
    if multi_file_pbar is not None:
        multi_file_pbar.close()
        multi_file_pbar = None
