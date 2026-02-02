# app/exceptions.py
"""
Custom exception classes for the API.
Provides consistent error handling with actionable messages.
"""
from fastapi import HTTPException
from typing import Optional, Dict, Any


class BaseAPIException(HTTPException):
    """Base exception for all API errors."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.context = context or {}


class ResourceNotFoundError(BaseAPIException):
    """Resource not found (404)."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Any,
        message: Optional[str] = None
    ):
        detail = message or f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(
            status_code=404,
            detail=detail,
            error_code="RESOURCE_NOT_FOUND",
            context={"resource_type": resource_type, "resource_id": str(resource_id)}
        )


class ValidationError(BaseAPIException):
    """Validation error (422)."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            status_code=422,
            detail=message,
            error_code="VALIDATION_ERROR",
            context={"field": field} if field else {}
        )


class DuplicateResourceError(BaseAPIException):
    """Resource already exists (409)."""
    
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            status_code=409,
            detail=f"{resource_type} with identifier '{identifier}' already exists",
            error_code="DUPLICATE_RESOURCE",
            context={"resource_type": resource_type, "identifier": identifier}
        )


class ExternalServiceError(BaseAPIException):
    """External service error (502)."""
    
    def __init__(self, service_name: str, message: Optional[str] = None):
        detail = message or f"Error communicating with {service_name}"
        super().__init__(
            status_code=502,
            detail=detail,
            error_code="EXTERNAL_SERVICE_ERROR",
            context={"service": service_name}
        )


class AIServiceError(ExternalServiceError):
    """AI service (OpenAI/ElevenLabs) error."""
    
    def __init__(self, service_name: str = "AI Service", message: Optional[str] = None):
        super().__init__(service_name=service_name, message=message)
        self.error_code = "AI_SERVICE_ERROR"


class DatabaseError(BaseAPIException):
    """Database operation error (500)."""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            status_code=500,
            detail=message,
            error_code="DATABASE_ERROR"
        )


class ConfigurationError(BaseAPIException):
    """Configuration/setup error (500)."""
    
    def __init__(self, message: str):
        super().__init__(
            status_code=500,
            detail=message,
            error_code="CONFIGURATION_ERROR"
        )


class RateLimitError(BaseAPIException):
    """Rate limit exceeded (429)."""
    
    def __init__(self, retry_after: Optional[int] = None):
        detail = "Rate limit exceeded. Please slow down your requests."
        if retry_after:
            detail += f" Retry after {retry_after} seconds."
        super().__init__(
            status_code=429,
            detail=detail,
            error_code="RATE_LIMIT_EXCEEDED",
            context={"retry_after": retry_after} if retry_after else {}
        )
