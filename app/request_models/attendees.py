from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re
from app.utils.validators import (
    Validators,
    ErrorMessages,
    ValidationError as CustomValidationError
)

class AttendeeBase(BaseModel):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Attendee's full name (1-100 characters)",
        example="John Doe"
    )
    email: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Valid email address (1-100 characters)",
        example="john.doe@example.com"
    )

    @validator('name')
    def validate_name(cls, v):
        """Validate name with comprehensive error messages"""
        return Validators.validate_name(v, min_length=1, max_length=100)

    @validator('email')
    def validate_email(cls, v):
        """Validate email with comprehensive error messages"""
        return Validators.validate_email(v)



class AttendeeRegistration(BaseModel):
    """
    For event registration - only name and email required.
    
    This model is used when registering an attendee for a specific event.
    Email validation ensures proper format and is case-insensitive.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Attendee's full name")
    email: str = Field(..., min_length=1, max_length=100, description="Attendee's email address")

    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com"
            }
        }

    @validator('name')
    def validate_name(cls, v):
        """Validate name for event registration"""
        return Validators.validate_name(v, min_length=1, max_length=100)

    @validator('email')
    def validate_email(cls, v):
        """Validate email for event registration"""
        return Validators.validate_email(v)

class AttendeeResponse(AttendeeBase):
    """
    Response model for attendee data.
    
    Contains complete attendee information including registration details
    and association with events if applicable.
    """
    id: int = Field(..., description="Unique attendee identifier")
    event_id: Optional[int] = Field(None, description="Associated event ID if registered")
    phone: Optional[str] = Field(None, description="Attendee's phone number")
    created_at: datetime = Field(..., description="Registration timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+91-9876543210",
                "event_id": 1,
                "created_at": "2024-01-08T10:00:00+00:00",
                "updated_at": "2024-01-08T10:00:00+00:00"
            }
        }


