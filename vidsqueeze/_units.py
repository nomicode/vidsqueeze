import math
from typing import Union


def _get_appropriate_size_unit(bytes: float) -> tuple[float, str]:
    """Helper function to get appropriate unit for data size."""
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    if bytes == 0:
        return 0, "B"

    # Calculate appropriate unit
    unit_index = min(math.floor(math.log(abs(bytes), 1024)), len(units) - 1)
    value = bytes / (1024**unit_index)
    return value, units[unit_index]


def _get_appropriate_time_unit(seconds: float) -> tuple[float, str]:
    """Helper function to get appropriate unit for time."""
    units = [(1e-9, "ns"), (1e-6, "µs"), (1e-3, "ms"), (1, "s"), (60, "m"), (3600, "h")]

    if seconds == 0:
        return 0, "s"

    # Find appropriate unit
    for threshold, unit in reversed(units):
        if abs(seconds) >= threshold:
            return seconds / threshold, unit

    return seconds, "s"


def _format_data_volume(data_volume: Union[int, float]) -> str:
    """Format data volume to appropriate unit with 1 decimal place."""
    value, unit = _get_appropriate_size_unit(data_volume)
    return f"{value:.1f}{unit}"


def _format_time(time: Union[int, float]) -> str:
    """Format time to appropriate unit with 1 decimal place."""
    value, unit = _get_appropriate_time_unit(time)
    return f"{value:.1f}{unit}"


def _format_data_rate(data_rate: Union[int, float]) -> str:
    """Format data rate (bytes/second) to appropriate unit with 1 decimal place."""
    value, unit = _get_appropriate_size_unit(data_rate)
    return f"{value:.1f}{unit}/s"
