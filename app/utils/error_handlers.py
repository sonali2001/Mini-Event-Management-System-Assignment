"""
Error handling utilities for the Event Management API.

This module provides centralized error handling, exception handlers,
and response formatting for consistent error responses across the API.
"""

from typing import Union, Dict, Any, List
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from app.utils.validators import format_validation_error
import logging

# Configure logging
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception class for API errors"""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 400, 
        error_code: str = None,
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details or {}
        )
        if field:
            self.details["field"] = field


class BusinessLogicError(APIError):
    """Raised when business rules are violated"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details or {}
        )


class ResourceNotFoundError(APIError):
    """Raised when a requested resource is not found"""
    
    def __init__(self, resource: str, identifier: Union[str, int] = None):
        message = f"{resource} not found"
        if identifier:
            message += f" (ID: {identifier})"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier) if identifier else None}
        )


class ConflictError(APIError):
    """Raised when a resource conflict occurs"""
    
    def __init__(self, message: str, resource: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT_ERROR",
            details=details or {}
        )
        if resource:
            self.details["resource"] = resource


class AuthorizationError(APIError):
    """Raised when user lacks permission for an action"""
    
    def __init__(self, message: str = "Access denied", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            details=details or {}
        )


class TooManyRequestsError(APIError):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Too many requests", retry_after: int = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED"
        )
        if retry_after:
            self.details["retry_after"] = retry_after


def create_error_response(
    error: Union[APIError, HTTPException, Exception],
    request: Request = None
) -> JSONResponse:
    """
    Create a standardized error response
    
    Args:
        error: The error to format
        request: FastAPI request object (optional)
        
    Returns:
        JSONResponse with standardized error format
    """
    if isinstance(error, APIError):
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": True,
                "error_code": error.error_code,
                "message": error.message,
                "details": error.details,
                "timestamp": get_current_timestamp(),
                "path": str(request.url) if request else None
            }
        )
    
    elif isinstance(error, HTTPException):
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": True,
                "error_code": "HTTP_EXCEPTION",
                "message": error.detail if isinstance(error.detail, str) else str(error.detail),
                "details": error.detail if isinstance(error.detail, dict) else {},
                "timestamp": get_current_timestamp(),
                "path": str(request.url) if request else None
            }
        )
    
    else:
        # Log unexpected errors
        logger.exception(f"Unexpected error: {str(error)}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {},
                "timestamp": get_current_timestamp(),
                "path": str(request.url) if request else None
            }
        )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors with user-friendly messages
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError from Pydantic
        
    Returns:
        JSONResponse with formatted validation errors
    """
    errors = []
    
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        error_type = error["type"]
        message = error["msg"]
        
        # Customize error messages based on type
        if error_type == "value_error.missing":
            message = f"{field_path.replace('_', ' ').title()} is required"
        elif error_type == "type_error.str":
            message = f"{field_path.replace('_', ' ').title()} must be a text value"
        elif error_type == "type_error.integer":
            message = f"{field_path.replace('_', ' ').title()} must be a whole number"
        elif error_type == "value_error.number.not_gt":
            message = f"{field_path.replace('_', ' ').title()} must be greater than {error.get('ctx', {}).get('limit_value', 0)}"
        elif error_type == "value_error.number.not_ge":
            message = f"{field_path.replace('_', ' ').title()} must be at least {error.get('ctx', {}).get('limit_value', 0)}"
        elif error_type == "value_error.number.not_le":
            message = f"{field_path.replace('_', ' ').title()} must be at most {error.get('ctx', {}).get('limit_value', 'the maximum')}"
        elif error_type == "value_error.str.regex":
            message = f"{field_path.replace('_', ' ').title()} format is invalid"
        elif error_type == "value_error.email":
            message = "Please provide a valid email address"
        elif "datetime" in error_type:
            message = f"{field_path.replace('_', ' ').title()} must be a valid date and time"
        
        errors.append({
            "field": field_path,
            "message": message,
            "type": error_type,
            "input": error.get("input")
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "error_code": "VALIDATION_ERROR",
            "message": "The provided data is invalid. Please check the errors below and try again.",
            "details": {
                "validation_errors": errors,
                "error_count": len(errors)
            },
            "timestamp": get_current_timestamp(),
            "path": str(request.url)
        }
    )


async def database_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle database-related exceptions
    
    Args:
        request: FastAPI request object
        exc: Database exception
        
    Returns:
        JSONResponse with appropriate error message
    """
    if isinstance(exc, IntegrityError):
        # Handle constraint violations (like unique constraints)
        error_message = "A record with this information already exists"
        
        # Try to extract more specific information
        if "UNIQUE constraint failed" in str(exc.orig):
            if "email" in str(exc.orig):
                error_message = "This email address is already registered"
            elif "name" in str(exc.orig):
                error_message = "This name is already taken"
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": True,
                "error_code": "INTEGRITY_ERROR",
                "message": error_message,
                "details": {"constraint_violation": True},
                "timestamp": get_current_timestamp(),
                "path": str(request.url)
            }
        )
    
    elif isinstance(exc, OperationalError):
        logger.error(f"Database operational error: {str(exc)}")
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": True,
                "error_code": "DATABASE_ERROR",
                "message": "Database service is temporarily unavailable. Please try again later.",
                "details": {"service": "database"},
                "timestamp": get_current_timestamp(),
                "path": str(request.url)
            }
        )
    
    else:
        logger.exception(f"Unexpected database error: {str(exc)}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "error_code": "DATABASE_ERROR",
                "message": "A database error occurred. Please try again later.",
                "details": {},
                "timestamp": get_current_timestamp(),
                "path": str(request.url)
            }
        )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle any unexpected exceptions
    
    Args:
        request: FastAPI request object
        exc: Any exception
        
    Returns:
        JSONResponse with generic error message
    """
    logger.exception(f"Unexpected error: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {"exception_type": type(exc).__name__},
            "timestamp": get_current_timestamp(),
            "path": str(request.url)
        }
    )


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


def wrap_service_errors(func):
    """
    Decorator to wrap service functions and convert exceptions to API errors
    
    Args:
        func: Service function to wrap
        
    Returns:
        Wrapped function that raises API errors
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            # Convert ValueError to ValidationError
            raise ValidationError(str(e))
        except KeyError as e:
            # Convert KeyError to ResourceNotFoundError
            raise ResourceNotFoundError("Resource", str(e))
        except Exception as e:
            # Log and re-raise unexpected errors
            logger.exception(f"Service error in {func.__name__}: {str(e)}")
            raise APIError(
                message="A service error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return wrapper


def validate_pagination_params(page: int, page_size: int, max_page_size: int = 100) -> tuple[int, int]:
    """
    Validate pagination parameters with meaningful error messages
    
    Args:
        page: Page number
        page_size: Items per page
        max_page_size: Maximum allowed page size
        
    Returns:
        Validated (page, page_size) tuple
        
    Raises:
        ValidationError: If parameters are invalid
    """
    if page < 1:
        raise ValidationError(
            message="Page number must be a positive integer (starting from 1)",
            field="page"
        )
    
    if page_size < 1:
        raise ValidationError(
            message="Page size must be at least 1",
            field="page_size"
        )
    
    if page_size > max_page_size:
        raise ValidationError(
            message=f"Page size cannot exceed {max_page_size} items",
            field="page_size",
            details={"max_allowed": max_page_size}
        )
    
    return page, page_size 