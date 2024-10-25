class Error(Exception):
    pass


class FFmpegError(Error):

    message = None
    details = None
    stdout = None

    def __init__(self, message, details, stdout):
        super().__init__(message)
        self.message = message
        self.details = details
        self.stdout = stdout

    def __str__(self) -> str:
        return_str = f"{self.message}"
        if self.details:
            return_str += f"\n{self.details}"
        return_str = super().__str__()
        if self.stdout:
            return_str += f"\n{self.stderr.decode()}"
        return return_str


class FFmpegProbeError(FFmpegError):
    pass
