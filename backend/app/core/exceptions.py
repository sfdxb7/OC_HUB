"""
Custom exceptions for the application.
"""
from typing import Any, Optional


class DCIAException(Exception):
    """Base exception for DCAI platform."""
    
    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        details: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


class RAGFlowError(DCIAException):
    """Error communicating with RAGFlow."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, "RAGFLOW_ERROR", details)


class LLMError(DCIAException):
    """Error from LLM provider."""
    
    def __init__(self, message: str, model: str = "", details: Optional[Any] = None):
        self.model = model
        super().__init__(message, "LLM_ERROR", details)


class ProcessingError(DCIAException):
    """Error during document processing."""
    
    def __init__(self, message: str, filename: str = "", details: Optional[Any] = None):
        self.filename = filename
        super().__init__(message, "PROCESSING_ERROR", details)


class ValidationError(DCIAException):
    """Data validation error."""
    
    def __init__(self, message: str, field: str = "", details: Optional[Any] = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR", details)


class NotFoundError(DCIAException):
    """Resource not found."""
    
    def __init__(self, resource: str, identifier: str = ""):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        super().__init__(message, "NOT_FOUND", {"resource": resource, "id": identifier})


class RateLimitError(DCIAException):
    """Rate limit exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message, "RATE_LIMIT", {"retry_after": retry_after})


class ExtractionError(DCIAException):
    """Error during intelligence extraction."""
    
    def __init__(self, message: str, report_id: str = "", details: Optional[Any] = None):
        self.report_id = report_id
        super().__init__(message, "EXTRACTION_ERROR", details)


class DatabaseError(DCIAException):
    """Database operation error."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, "DATABASE_ERROR", details)


class AuthenticationError(DCIAException):
    """Authentication error."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Any] = None):
        super().__init__(message, "AUTH_ERROR", details)
