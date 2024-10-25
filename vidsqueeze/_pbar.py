import math
import pathlib
import shutil
import threading

from tqdm import tqdm

TERM_SIZE_FALLBACK = 80
PATH_DISPLAY_RATIO = 1 / 3
ELLIPSIS = "..."

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
    """
    Format a path for display.
    """
    if max_len is None:
        max_len = math.floor(_get_term_size() * PATH_DISPLAY_RATIO)
    truncated_path = _truncate_path(path, max_len)
    return truncated_path


class MultiFileProgressBar:
    def __init__(self, total_files, total_size):
        self.overall_pbar = tqdm(
            desc="Overall Progress",
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            position=0,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
        )
        self.file_pbars = {}
        self.total_files = total_files
        self.lock = threading.Lock()

    def get_file_pbar(self, input_file, file_size):
        with self.lock:
            if input_file not in self.file_pbars:
                self.file_pbars[input_file] = tqdm(
                    desc=_format_path(input_file),
                    total=file_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    position=len(self.file_pbars) + 1,
                    leave=True,
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
                )
            return self.file_pbars[input_file]

    def update(self, input_file, n):
        with self.lock:
            self.overall_pbar.update(n)
            self.file_pbars[input_file].update(n)

    def close(self):
        with self.lock:
            self.overall_pbar.close()
            for pbar in self.file_pbars.values():
                pbar.close()


multi_file_pbar = None


def init_multi_file_pbar(total_files, total_size):
    global multi_file_pbar
    multi_file_pbar = MultiFileProgressBar(total_files, total_size)


def get_file_pbar(input_file, file_size):
    global multi_file_pbar
    if multi_file_pbar is None:
        raise RuntimeError(
            "MultiFileProgressBar not initialized. Call init_multi_file_pbar first."
        )
    return multi_file_pbar.get_file_pbar(input_file, file_size)


def update_pbar(input_file, n):
    global multi_file_pbar
    if multi_file_pbar is None:
        raise RuntimeError(
            "MultiFileProgressBar not initialized. Call init_multi_file_pbar first."
        )
    multi_file_pbar.update(input_file, n)


def close_pbar():
    global multi_file_pbar
    if multi_file_pbar is not None:
        multi_file_pbar.close()
        multi_file_pbar = None
