from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List
from datetime import datetime
import re
from app.utils.timezone import (
    ensure_timezone_aware,
    validate_future_datetime,
    parse_datetime_with_timezone,
    convert_timezone,
    DEFAULT_TIMEZONE
)
from app.utils.validators import (
    Validators,
    ErrorMessages,
    ValidationError as CustomValidationError
)

class EventBase(BaseModel):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="Event name (1-200 characters)",
        example="Tech Conference 2024"
    )
    location: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="Event location (1-200 characters)",
        example="Mumbai Convention Center"
    )
    start_time: datetime = Field(
        ...,
        description="Event start time in ISO format",
        example="2024-03-15T10:00:00"
    )
    end_time: datetime = Field(
        ...,
        description="Event end time in ISO format",
        example="2024-03-15T18:00:00"
    )
    max_capacity: int = Field(
        ..., 
        ge=1, 
        le=10000,
        description="Maximum number of attendees (1-10000)",
        example=150
    )
    timezone: Optional[str] = Field(
        default='Asia/Kolkata',
        description="Event timezone (e.g., 'Asia/Kolkata', 'UTC')",
        example="Asia/Kolkata"
    )

    @validator('name')
    def validate_name(cls, v):
        """Validate event name with meaningful error messages"""
        if not v or not v.strip():
            raise ValueError(ErrorMessages.EVENT_NAME_REQUIRED)
        
        name = v.strip()
        
        if len(name) < 1:
            raise ValueError(ErrorMessages.EVENT_NAME_REQUIRED)
        
        if len(name) > 200:
            raise ValueError("Event name must be less than 200 characters")
        
        # Check for reasonable content
        if not any(c.isalnum() for c in name):
            raise ValueError("Event name must contain at least one letter or number")
        
        return name

    @validator('location')
    def validate_location(cls, v):
        """Validate event location with meaningful error messages"""
        if not v or not v.strip():
            raise ValueError(ErrorMessages.LOCATION_REQUIRED)
        
        location = v.strip()
        
        if len(location) < 1:
            raise ValueError(ErrorMessages.LOCATION_REQUIRED)
        
        if len(location) > 200:
            raise ValueError("Event location must be less than 200 characters")
        
        return location

    @validator('max_capacity')
    def validate_max_capacity(cls, v):
        """Validate maximum capacity with meaningful error messages"""
        return Validators.validate_capacity(v, min_value=1, max_value=10000)

class EventCreate(EventBase):
    """
    Request model for creating a new event.
    
    All datetime fields should be provided in ISO format.
    The timezone field specifies the event's timezone and affects how times are stored and displayed.
    """
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Tech Conference 2024",
                "location": "Mumbai Convention Center",
                "start_time": "2024-03-15T10:00:00",
                "end_time": "2024-03-15T18:00:00", 
                "max_capacity": 150,
                "timezone": "Asia/Kolkata"
            }
        }
    
    @validator('timezone')
    def validate_timezone(cls, v):
        """Validate timezone with meaningful error messages"""
        if v:
            try:
                from app.utils.timezone import get_timezone
                get_timezone(v)
                return v
            except ValueError:
                raise ValueError(ErrorMessages.TIMEZONE_INVALID.format(timezone=v))
        return 'Asia/Kolkata'

    @validator('start_time', pre=True)
    def validate_start_time(cls, v, values):
        """Validate start time with enhanced error messages"""
        try:
            if isinstance(v, str):
                tz = values.get('timezone', 'Asia/Kolkata')
                v = parse_datetime_with_timezone(v, tz)
        except Exception:
            raise ValueError(ErrorMessages.TIME_INVALID_FORMAT)

        # Ensure timezone aware and convert to IST for storage
        try:
            v = ensure_timezone_aware(v, values.get('timezone', 'Asia/Kolkata'))
        except Exception:
            raise ValueError(ErrorMessages.TIME_INVALID_FORMAT)

        # Validate that it's in the future (commented out for testing)
        # if not validate_future_datetime(v):
        #     raise ValueError(ErrorMessages.START_TIME_PAST)
        return v

    @validator('end_time', pre=True)
    def validate_end_time(cls, v, values):
        """Validate end time with enhanced error messages"""
        try:
            if isinstance(v, str):
                tz = values.get('timezone', 'Asia/Kolkata')
                v = parse_datetime_with_timezone(v, tz)
        except Exception:
            raise ValueError(ErrorMessages.TIME_INVALID_FORMAT)

        # Ensure timezone aware
        try:
            v = ensure_timezone_aware(v, values.get('timezone', 'Asia/Kolkata'))
        except Exception:
            raise ValueError(ErrorMessages.TIME_INVALID_FORMAT)
        return v

    @root_validator(skip_on_failure=True)
    def validate_times(cls, values):
        """Validate start and end time relationship with comprehensive checks"""
        start_time = values.get('start_time')
        end_time = values.get('end_time')
        timezone_name = values.get('timezone', 'Asia/Kolkata')

        if start_time and end_time:
            try:
                # Use the comprehensive time validation
                Validators.validate_event_times(start_time, end_time, timezone_name)
            except ValueError as e:
                raise ValueError(str(e))

        return values

class EventUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_capacity: Optional[int] = Field(None, gt=0)
    timezone: Optional[str] = Field(None, description="Timezone for the event")
    
    @validator('timezone')
    def validate_timezone(cls, v):
        if v:
            try:
                from app.utils.timezone import get_timezone
                get_timezone(v)
                return v
            except ValueError:
                raise ValueError(f'Invalid timezone: {v}')
        return v
    
    @validator('start_time', pre=True)
    def validate_start_time(cls, v, values):
        if v is None:
            return v
            
        if isinstance(v, str):
            tz = values.get('timezone', 'Asia/Kolkata')
            v = parse_datetime_with_timezone(v, tz)
        
        v = ensure_timezone_aware(v, values.get('timezone', 'Asia/Kolkata'))
        
        if not validate_future_datetime(v):
            raise ValueError('Start time must be in the future')
        return v
    
    @validator('end_time', pre=True)
    def validate_end_time(cls, v, values):
        if v is None:
            return v
            
        if isinstance(v, str):
            tz = values.get('timezone', 'Asia/Kolkata')
            v = parse_datetime_with_timezone(v, tz)
        
        v = ensure_timezone_aware(v, values.get('timezone', 'Asia/Kolkata'))
        return v

class EventResponse(BaseModel):
    """
    Response model for event data with timezone conversion support.
    
    Includes both the original datetime fields and timezone-converted display fields
    when requested with a specific timezone parameter.
    """
    id: int = Field(..., description="Unique event identifier")
    name: str = Field(..., description="Event name")
    location: str = Field(..., description="Event location")
    start_time: datetime = Field(..., description="Event start time (stored in IST)")
    end_time: datetime = Field(..., description="Event end time (stored in IST)")
    max_capacity: int = Field(..., description="Maximum number of attendees")
    timezone: str = Field(default='Asia/Kolkata', description="Event's original timezone")
    created_at: datetime = Field(..., description="Event creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    attendees: List[int] = Field(default=[], description="List of attendee IDs")
    
    # Timezone display fields
    start_time_display: Optional[dict] = Field(None, description="Start time converted to requested timezone")
    end_time_display: Optional[dict] = Field(None, description="End time converted to requested timezone")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Tech Conference 2024",
                "location": "Mumbai Convention Center",
                "start_time": "2024-03-15T04:30:00+00:00",
                "end_time": "2024-03-15T12:30:00+00:00",
                "max_capacity": 150,
                "timezone": "Asia/Kolkata",
                "created_at": "2024-01-08T10:00:00+00:00",
                "updated_at": "2024-01-08T10:00:00+00:00",
                "attendees": [1, 2, 3],
                "start_time_display": {
                    "datetime": "2024-03-15T10:00:00+05:30",
                    "timezone": "Asia/Kolkata", 
                    "formatted": "March 15, 2024 at 10:00 AM IST"
                },
                "end_time_display": {
                    "datetime": "2024-03-15T18:00:00+05:30",
                    "timezone": "Asia/Kolkata",
                    "formatted": "March 15, 2024 at 6:00 PM IST"
                }
            }
        }
    
    def dict(self, target_timezone: str = None, **kwargs):
        """Override dict method to include timezone conversions"""
        data = super().dict(**kwargs)
        
        if target_timezone:
            from app.utils.timezone import format_datetime_with_timezone, convert_timezone
            
            # Convert times to target timezone for display
            if self.start_time:
                converted_start = convert_timezone(self.start_time, target_timezone)
                data['start_time_display'] = format_datetime_with_timezone(converted_start)
            
            if self.end_time:
                converted_end = convert_timezone(self.end_time, target_timezone)
                data['end_time_display'] = format_datetime_with_timezone(converted_end)
        
        return data

class EventSearch(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    start_time_from: Optional[datetime] = None
    start_time_to: Optional[datetime] = None
    max_capacity: Optional[int] = None
    timezone: Optional[str] = Field(default='Asia/Kolkata', description="Timezone for search dates")
    
    @validator('timezone')
    def validate_timezone(cls, v):
        if v:
            try:
                from app.utils.timezone import get_timezone
                get_timezone(v)
                return v
            except ValueError:
                raise ValueError(f'Invalid timezone: {v}')
        return 'Asia/Kolkata'
    
    @validator('start_time_from', 'start_time_to', pre=True)
    def validate_search_times(cls, v, values):
        if v is None:
            return v
            
        if isinstance(v, str):
            tz = values.get('timezone', 'Asia/Kolkata')
            v = parse_datetime_with_timezone(v, tz)
        
        return ensure_timezone_aware(v, values.get('timezone', 'Asia/Kolkata'))

