"""
Timezone utilities for Event Management API
Handles timezone conversions with IST as the default storage timezone
"""

from datetime import datetime, timezone
from typing import Optional, Union
import pytz
from zoneinfo import ZoneInfo

# Default timezone for the application (India Standard Time)
DEFAULT_TIMEZONE = pytz.timezone('Asia/Kolkata')
UTC = pytz.UTC

# Common timezone mappings
TIMEZONE_MAPPINGS = {
    'IST': 'Asia/Kolkata',
    'UTC': 'UTC',
    'EST': 'America/New_York',
    'PST': 'America/Los_Angeles',
    'GMT': 'Europe/London',
    'CET': 'Europe/Paris',
    'JST': 'Asia/Tokyo',
    'AEST': 'Australia/Sydney',
}

def get_timezone(tz_name: str) -> pytz.BaseTzInfo:
    """
    Get timezone object from timezone name or abbreviation
    
    Args:
        tz_name: Timezone name (e.g., 'Asia/Kolkata', 'IST', 'UTC')
        
    Returns:
        pytz timezone object
        
    Raises:
        ValueError: If timezone is not recognized
    """
    if tz_name in TIMEZONE_MAPPINGS:
        tz_name = TIMEZONE_MAPPINGS[tz_name]
    
    try:
        return pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        raise ValueError(f"Unknown timezone: {tz_name}")

def now_in_timezone(tz_name: str = 'Asia/Kolkata') -> datetime:
    """
    Get current time in specified timezone
    
    Args:
        tz_name: Timezone name (default: IST)
        
    Returns:
        Current datetime in specified timezone
    """
    tz = get_timezone(tz_name)
    return datetime.now(tz)

def utc_now() -> datetime:
    """Get current UTC time with timezone info"""
    return datetime.now(UTC)

def ist_now() -> datetime:
    """Get current IST time with timezone info"""
    return datetime.now(DEFAULT_TIMEZONE)

def ensure_timezone_aware(dt: datetime, default_tz: str = 'Asia/Kolkata') -> datetime:
    """
    Ensure datetime is timezone-aware
    
    Args:
        dt: Datetime object (may be naive or aware)
        default_tz: Default timezone to assume for naive datetimes
        
    Returns:
        Timezone-aware datetime
    """
    if dt.tzinfo is None:
        # Naive datetime - assume it's in the default timezone
        tz = get_timezone(default_tz)
        return tz.localize(dt)
    return dt

def convert_timezone(dt: datetime, target_tz: str, source_tz: str = None) -> datetime:
    """
    Convert datetime from one timezone to another
    
    Args:
        dt: Datetime to convert
        target_tz: Target timezone name
        source_tz: Source timezone (if dt is naive)
        
    Returns:
        Datetime converted to target timezone
    """
    # Ensure the datetime is timezone-aware
    if dt.tzinfo is None:
        if source_tz is None:
            raise ValueError("source_tz must be provided for naive datetime")
        dt = ensure_timezone_aware(dt, source_tz)
    
    target_timezone = get_timezone(target_tz)
    return dt.astimezone(target_timezone)

def to_utc(dt: datetime, source_tz: str = None) -> datetime:
    """
    Convert datetime to UTC
    
    Args:
        dt: Datetime to convert
        source_tz: Source timezone (if dt is naive)
        
    Returns:
        Datetime in UTC
    """
    return convert_timezone(dt, 'UTC', source_tz)

def to_ist(dt: datetime) -> datetime:
    """
    Convert datetime to IST
    
    Args:
        dt: Timezone-aware datetime
        
    Returns:
        Datetime in IST
    """
    return convert_timezone(dt, 'Asia/Kolkata')

def format_datetime_with_timezone(dt: datetime, target_tz: str = None) -> dict:
    """
    Format datetime with timezone information
    
    Args:
        dt: Timezone-aware datetime
        target_tz: Target timezone for display (if different from dt's timezone)
        
    Returns:
        Dictionary with formatted datetime and timezone info
    """
    if target_tz:
        dt = convert_timezone(dt, target_tz)
    
    return {
        'datetime': dt.isoformat(),
        'timezone': str(dt.tzinfo),
        'timezone_name': dt.tzinfo.zone if hasattr(dt.tzinfo, 'zone') else str(dt.tzinfo),
        'utc_offset': dt.strftime('%z'),
        'timestamp': int(dt.timestamp())
    }

def parse_datetime_with_timezone(
    dt_str: str, 
    tz_name: str = None,
    format_str: str = None
) -> datetime:
    """
    Parse datetime string with timezone information
    
    Args:
        dt_str: Datetime string
        tz_name: Timezone name (if not in datetime string)
        format_str: Custom format string
        
    Returns:
        Timezone-aware datetime
    """
    if format_str:
        dt = datetime.strptime(dt_str, format_str)
        if tz_name:
            return ensure_timezone_aware(dt, tz_name)
        return dt
    
    # Try to parse ISO format first
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt
    except ValueError:
        pass
    
    # If no timezone in string, assume default timezone
    try:
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None and tz_name:
            return ensure_timezone_aware(dt, tz_name)
        return dt
    except ValueError:
        raise ValueError(f"Unable to parse datetime: {dt_str}")



def validate_future_datetime(dt: datetime, tz_name: str = 'Asia/Kolkata') -> bool:
    """
    Validate that datetime is in the future in the specified timezone
    
    Args:
        dt: Datetime to validate
        tz_name: Timezone for comparison
        
    Returns:
        True if datetime is in the future
    """
    current_time = now_in_timezone(tz_name)
    
    # If dt is naive, assume it's in the same timezone
    if dt.tzinfo is None:
        dt = ensure_timezone_aware(dt, tz_name)
    else:
        # Convert to the comparison timezone
        dt = convert_timezone(dt, tz_name)
        current_time = current_time.replace(tzinfo=dt.tzinfo)
    
    return dt > current_time 