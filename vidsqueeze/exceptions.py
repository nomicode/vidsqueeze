class Error(Exception):
    pass


class FFmpegError(Error):
    pass


class FFmpegProbeError(FFmpegError):
    pass
