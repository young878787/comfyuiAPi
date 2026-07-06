"""Domain layer exceptions."""


class DomainException(Exception):
    """Base exception for domain layer."""
    pass




class ImageGenerationError(DomainException):
    """Raised when image generation fails."""
    pass


class ImageNotFoundError(DomainException):
    """Raised when an image cannot be found."""
    pass


class InvalidParameterError(DomainException):
    """Raised when invalid parameters are provided."""
    pass


class APIError(DomainException):
    """Raised when external API calls fail."""
    pass
