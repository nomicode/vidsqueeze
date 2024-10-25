class FFmpegError(Exception):
    """Base class for FFmpeg-related errors."""

    pass


class FFmpegProbeError(FFmpegError):
    """Error occurred during FFprobe operation."""

    pass


class ValidationError(Exception):
    """Error occurred during file validation."""

    pass


class CompressionError(FFmpegError):
    """Error occurred during video compression."""

    pass
