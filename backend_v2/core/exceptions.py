"""Custom exceptions"""


class AppException(Exception):
    """Base application exception"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AppException):
    """Validation error"""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class AuthenticationError(AppException):
    """Authentication error"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(AppException):
    """Authorization error"""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403)


class NotFoundError(AppException):
    """Resource not found error"""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ConflictError(AppException):
    """Conflict error (e.g., duplicate resource)"""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


class ExtractionError(AppException):
    """OCR extraction error"""

    def __init__(self, message: str = "Failed to extract data from document"):
        super().__init__(message, status_code=422)


class ProcessingError(AppException):
    """Document processing error"""

    def __init__(self, message: str = "Failed to process document"):
        super().__init__(message, status_code=422)


class RateLimitError(AppException):
    """Rate limit exceeded error"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class ServiceUnavailableError(AppException):
    """Service unavailable error"""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(message, status_code=503)
