"""
Upload service for handling file upload operations and exceptions
"""


class UploadError(Exception):
    """Base exception for upload-related errors"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class FileValidationError(UploadError):
    """Exception raised when file validation fails (invalid format, corrupted file)"""
    def __init__(self, message: str, mime_type: str = None, details: dict = None):
        self.mime_type = mime_type
        super().__init__(message, details)


class FileSizeLimitError(UploadError):
    """Exception raised when file exceeds size limit"""
    def __init__(self, message: str, file_size: int = None, max_size: int = None, details: dict = None):
        self.file_size = file_size
        self.max_size = max_size
        super().__init__(message, details)


class FileConversionError(UploadError):
    """Exception raised when FFmpeg conversion fails"""
    def __init__(self, message: str, ffmpeg_output: str = None, details: dict = None):
        self.ffmpeg_output = ffmpeg_output
        super().__init__(message, details)


class DuplicateEpisodeError(UploadError):
    """Exception raised when episode with same title already exists"""
    def __init__(self, message: str, existing_episode_id: int = None, details: dict = None):
        self.existing_episode_id = existing_episode_id
        self.message = message
        self.details = details or {}
        Exception.__init__(self, message)


