"""
Custom exceptions for Kimi Authentication Bridge
"""


class KimiAuthError(Exception):
    """Base exception for Kimi authentication errors"""
    pass


class KimiNotAuthenticatedError(KimiAuthError):
    """Raised when user is not authenticated with Kimi CLI"""
    
    def __init__(self, message="Not authenticated. Please run 'kimi login' first."):
        super().__init__(message)


class KimiTokenExpiredError(KimiAuthError):
    """Raised when the access token has expired"""
    
    def __init__(self, message="Token expired. Please run 'kimi login' again."):
        super().__init__(message)


class KimiCLINotFoundError(KimiAuthError):
    """Raised when Kimi CLI is not installed"""
    
    def __init__(self, message="Kimi CLI not found. Please install: pip install kimi-cli"):
        super().__init__(message)


class KimiCredentialsNotFoundError(KimiAuthError):
    """Raised when credentials file is not found"""
    
    def __init__(self, path: str):
        super().__init__(f"Credentials file not found: {path}")


class KimiInvalidCredentialsError(KimiAuthError):
    """Raised when credentials file is invalid or corrupted"""
    
    def __init__(self, message="Invalid or corrupted credentials file"):
        super().__init__(message)
