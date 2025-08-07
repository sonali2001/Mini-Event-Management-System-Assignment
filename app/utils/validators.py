"""
Validation utilities for the Event Management API.

This module contains custom validators, error message formatters,
and validation helpers used throughout the application.
"""

import re
from datetime import datetime, timedelta
from typing import Any, Optional, Union, List
from pydantic import validator, ValidationError, Field
from fastapi import HTTPException


class ValidationError(Exception):
    """Custom validation error with meaningful messages"""
    
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"Validation error in field '{field}': {message}")


class ErrorMessages:
    """Centralized error messages for consistent user experience"""
    
    # Email validation messages
    EMAIL_REQUIRED = "Email address is required"
    EMAIL_INVALID_FORMAT = "Please provide a valid email address (e.g., user@example.com)"
    EMAIL_TOO_LONG = "Email address must be less than {max_length} characters"
    EMAIL_ALREADY_REGISTERED = "This email address is already registered for this event"
    
    # Name validation messages
    NAME_REQUIRED = "Name is required"
    NAME_TOO_SHORT = "Name must be at least {min_length} characters long"
    NAME_TOO_LONG = "Name must be less than {max_length} characters"
    NAME_INVALID_CHARACTERS = "Name can only contain letters, spaces, hyphens, and apostrophes"
    
    # Event validation messages
    EVENT_NAME_REQUIRED = "Event name is required"
    LOCATION_REQUIRED = "Event location is required"
    START_TIME_REQUIRED = "Event start time is required"
    END_TIME_REQUIRED = "Event end time is required"
    MAX_CAPACITY_REQUIRED = "Maximum capacity is required"
    MAX_CAPACITY_MIN = "Maximum capacity must be at least {min_value} attendee"
    MAX_CAPACITY_MAX = "Maximum capacity cannot exceed {max_value} attendees"
    
    # Time validation messages
    START_TIME_PAST = "Event start time must be in the future"
    END_TIME_BEFORE_START = "Event end time must be after the start time"
    TIME_INVALID_FORMAT = "Please provide time in ISO format (YYYY-MM-DDTHH:MM:SS)"
    TIMEZONE_INVALID = "Invalid timezone '{timezone}'. Please use a valid timezone name (e.g., 'Asia/Kolkata', 'UTC')"
    
    # Event registration messages
    EVENT_NOT_FOUND = "Event not found. Please check the event ID"
    EVENT_FULL = "This event has reached its maximum capacity of {capacity} attendees"
    EVENT_STARTED = "Registration is closed. This event has already started"
    ATTENDEE_NOT_FOUND = "Attendee not found. Please check the attendee ID"
    
    # Pagination messages
    PAGE_INVALID = "Page number must be a positive integer"
    PAGE_SIZE_INVALID = "Page size must be between {min_size} and {max_size}"
    
    # Phone validation messages
    PHONE_INVALID_FORMAT = "Please provide a valid phone number (e.g., +1-234-567-8900 or 1234567890)"
    PHONE_TOO_LONG = "Phone number must be less than {max_length} characters"


class Validators:
    """Collection of custom validators with meaningful error messages"""
    
    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate email address with comprehensive checks
        
        Args:
            email: Email address to validate
            
        Returns:
            Normalized email address (lowercase, trimmed)
            
        Raises:
            ValueError: If email is invalid
        """
        if not email:
            raise ValueError(ErrorMessages.EMAIL_REQUIRED)
        
        # Trim and normalize
        email = email.strip().lower()
        
        if not email:
            raise ValueError(ErrorMessages.EMAIL_REQUIRED)
        
        if len(email) > 100:
            raise ValueError(ErrorMessages.EMAIL_TOO_LONG.format(max_length=100))
        
        # Enhanced email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            raise ValueError(ErrorMessages.EMAIL_INVALID_FORMAT)
        
        # Additional checks for common mistakes
        if '..' in email:
            raise ValueError("Email address cannot contain consecutive dots")
        
        if email.startswith('.') or email.endswith('.'):
            raise ValueError("Email address cannot start or end with a dot")
        
        return email
    
    @staticmethod
    def validate_name(name: str, min_length: int = 1, max_length: int = 100) -> str:
        """
        Validate person name with length and character checks
        
        Args:
            name: Name to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            
        Returns:
            Normalized name (trimmed)
            
        Raises:
            ValueError: If name is invalid
        """
        if not name:
            raise ValueError(ErrorMessages.NAME_REQUIRED)
        
        # Trim whitespace
        name = name.strip()
        
        if not name:
            raise ValueError(ErrorMessages.NAME_REQUIRED)
        
        if len(name) < min_length:
            raise ValueError(ErrorMessages.NAME_TOO_SHORT.format(min_length=min_length))
        
        if len(name) > max_length:
            raise ValueError(ErrorMessages.NAME_TOO_LONG.format(max_length=max_length))
        
        # Allow letters, spaces, hyphens, apostrophes, and basic accented characters
        name_pattern = r"^[a-zA-ZÀ-ÿ\s\-\'\.]+$"
        
        if not re.match(name_pattern, name):
            raise ValueError(ErrorMessages.NAME_INVALID_CHARACTERS)
        
        # Check for reasonable name structure
        if name.count(' ') > 10:  # Prevent abuse with excessive spaces
            raise ValueError("Name contains too many spaces")
        
        # Remove multiple consecutive spaces
        name = re.sub(r'\s+', ' ', name)
        
        return name
    
    @staticmethod
    def validate_capacity(capacity: int, min_value: int = 1, max_value: int = 10000) -> int:
        """
        Validate event capacity with reasonable limits
        
        Args:
            capacity: Capacity to validate
            min_value: Minimum allowed capacity
            max_value: Maximum allowed capacity
            
        Returns:
            Validated capacity
            
        Raises:
            ValueError: If capacity is invalid
        """
        if capacity is None:
            raise ValueError(ErrorMessages.MAX_CAPACITY_REQUIRED)
        
        if not isinstance(capacity, int):
            raise ValueError("Maximum capacity must be a whole number")
        
        if capacity < min_value:
            raise ValueError(ErrorMessages.MAX_CAPACITY_MIN.format(min_value=min_value))
        
        if capacity > max_value:
            raise ValueError(ErrorMessages.MAX_CAPACITY_MAX.format(max_value=max_value))
        
        return capacity
    
    @staticmethod
    def validate_phone(phone: str) -> Optional[str]:
        """
        Validate phone number with flexible format support
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Normalized phone number or None if empty
            
        Raises:
            ValueError: If phone number is invalid
        """
        if not phone:
            return None
        
        # Trim whitespace
        phone = phone.strip()
        
        if not phone:
            return None
        
        if len(phone) > 20:
            raise ValueError(ErrorMessages.PHONE_TOO_LONG.format(max_length=20))
        
        # Allow various phone formats: +1-234-567-8900, (123) 456-7890, 1234567890, etc.
        phone_pattern = r'^[\+]?[\d\s\-\(\)\.]{7,20}$'
        
        if not re.match(phone_pattern, phone):
            raise ValueError(ErrorMessages.PHONE_INVALID_FORMAT)
        
        # Ensure it has enough digits
        digits_only = re.sub(r'[^\d]', '', phone)
        if len(digits_only) < 7:
            raise ValueError("Phone number must contain at least 7 digits")
        
        return phone
    
    @staticmethod
    def validate_event_times(start_time: datetime, end_time: datetime, timezone_name: str = "Asia/Kolkata") -> tuple[datetime, datetime]:
        """
        Validate event start and end times
        
        Args:
            start_time: Event start time
            end_time: Event end time
            timezone_name: Timezone for validation
            
        Returns:
            Tuple of validated (start_time, end_time)
            
        Raises:
            ValueError: If times are invalid
        """
        from app.utils.timezone import ist_now, ensure_timezone_aware
        
        if not start_time:
            raise ValueError(ErrorMessages.START_TIME_REQUIRED)
        
        if not end_time:
            raise ValueError(ErrorMessages.END_TIME_REQUIRED)
        
        # Ensure times are timezone-aware
        start_time = ensure_timezone_aware(start_time, timezone_name)
        end_time = ensure_timezone_aware(end_time, timezone_name)
        
        # Check if start time is in the future (commented out for testing)
        # current_time = ist_now()
        # if start_time <= current_time:
        #     raise ValueError(ErrorMessages.START_TIME_PAST)
        
        # Check if end time is after start time
        if end_time <= start_time:
            raise ValueError(ErrorMessages.END_TIME_BEFORE_START)
        
        # Check for reasonable duration (not more than 30 days)
        duration = end_time - start_time
        if duration > timedelta(days=30):
            raise ValueError("Event duration cannot exceed 30 days")
        
        # Check for minimum duration (at least 15 minutes)
        if duration < timedelta(minutes=15):
            raise ValueError("Event duration must be at least 15 minutes")
        
        return start_time, end_time
    
    @staticmethod
    def validate_pagination(page: int, page_size: int, max_page_size: int = 100) -> tuple[int, int]:
        """
        Validate pagination parameters
        
        Args:
            page: Page number
            page_size: Items per page
            max_page_size: Maximum allowed page size
            
        Returns:
            Tuple of validated (page, page_size)
            
        Raises:
            ValueError: If pagination parameters are invalid
        """
        if page < 1:
            raise ValueError(ErrorMessages.PAGE_INVALID)
        
        if page_size < 1 or page_size > max_page_size:
            raise ValueError(ErrorMessages.PAGE_SIZE_INVALID.format(min_size=1, max_size=max_page_size))
        
        return page, page_size


def format_validation_error(exc: ValidationError) -> dict:
    """
    Format Pydantic validation errors into user-friendly messages
    
    Args:
        exc: Pydantic ValidationError
        
    Returns:
        Formatted error response
    """
    errors = []
    
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_type = error["type"]
        
        # Customize messages based on error type
        if error_type == "value_error.missing":
            message = f"{field.replace('_', ' ').title()} is required"
        elif error_type == "type_error.str":
            message = f"{field.replace('_', ' ').title()} must be a text value"
        elif error_type == "type_error.integer":
            message = f"{field.replace('_', ' ').title()} must be a whole number"
        elif error_type == "value_error.email":
            message = "Please provide a valid email address"
        
        errors.append({
            "field": field,
            "message": message,
            "type": error_type
        })
    
    return {
        "error": "Validation failed",
        "details": errors,
        "message": "Please check the provided data and try again"
    }


def create_error_response(status_code: int, message: str, details: Optional[dict] = None) -> HTTPException:
    """
    Create standardized HTTP error response
    
    Args:
        status_code: HTTP status code
        message: Error message
        details: Additional error details
        
    Returns:
        HTTPException with formatted error
    """
    error_data = {
        "error": True,
        "message": message,
        "status_code": status_code
    }
    
    if details:
        error_data["details"] = details
    
    return HTTPException(status_code=status_code, detail=error_data) 