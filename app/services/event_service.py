from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from fastapi import HTTPException
import datetime
from app.db_models.event import Event
from app.db_models.attendee import Attendee
from app.request_models.events import EventCreate, EventUpdate, EventResponse, EventSearch
from app.utils.error_handlers import (
    ResourceNotFoundError,
    ConflictError,
    BusinessLogicError,
    ValidationError as APIValidationError
)
from app.utils.validators import ErrorMessages
from app.utils.timezone import (
    ensure_timezone_aware,
    convert_timezone,
    to_ist,
    ist_now,
    format_datetime_with_timezone
)



async def create_event(
    session: AsyncSession,
    event_create: EventCreate
) -> EventResponse:
    """Create a new event with timezone handling"""
    try:
        # Ensure times are timezone-aware and convert to IST for storage
        start_time_ist = to_ist(event_create.start_time)
        end_time_ist = to_ist(event_create.end_time)
        
        # Validate times again after conversion
        if end_time_ist <= start_time_ist:
            raise HTTPException(
                status_code=400,
                detail="End time must be after start time"
            )
        
        event = Event(
            name=event_create.name,
            location=event_create.location,
            start_time=start_time_ist,
            end_time=end_time_ist,
            max_capacity=event_create.max_capacity,
            timezone=event_create.timezone or 'Asia/Kolkata'
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        
        # Create response model manually to avoid async relationship issues
        response_data = {
            "id": event.id,
            "name": event.name,
            "location": event.location,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "max_capacity": event.max_capacity,
            "timezone": event.timezone,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
            "attendees": []  # Empty for new event
        }
        return EventResponse(**response_data)
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Event creation failed: {str(e)}"
        )

async def get_event(
    session: AsyncSession,
    event_id: int,
    target_timezone: str = None
) -> EventResponse:
    """Get event by ID with optional timezone conversion"""
    result = await session.execute(
        select(Event).where(Event.id == event_id)
    )
    event = result.scalars().first()
    if not event:
        raise ResourceNotFoundError("Event", event_id)
    
    # Create response model manually to avoid async relationship issues
    response_data = {
        "id": event.id,
        "name": event.name,
        "location": event.location,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "max_capacity": event.max_capacity,
        "timezone": event.timezone,
        "created_at": event.created_at,
        "updated_at": event.updated_at,
        "attendees": []  # Will be populated separately if needed
    }
    event_response = EventResponse(**response_data)
    
    # Add timezone conversion if requested and different from stored timezone
    if target_timezone and target_timezone != event.timezone:
        try:
            # Convert the main time fields to the requested timezone
            converted_start = convert_timezone(event.start_time, target_timezone, 'Asia/Kolkata')
            converted_end = convert_timezone(event.end_time, target_timezone, 'Asia/Kolkata')
            
            # Update the main time fields with converted times
            event_response.start_time = converted_start.replace(tzinfo=None)  # Store as naive
            event_response.end_time = converted_end.replace(tzinfo=None)  # Store as naive
            
            # Also provide detailed display information
            event_response.start_time_display = format_datetime_with_timezone(converted_start)
            event_response.end_time_display = format_datetime_with_timezone(converted_end)
        except Exception:
            # If timezone conversion fails, skip the display fields
            pass
    
    return event_response

async def get_all_events(
    session: AsyncSession,
    search_params: Optional[EventSearch] = None,
    target_timezone: str = None
) -> List[EventResponse]:
    """Get list of events with optional timezone conversion"""
    query = select(Event)
    
    if search_params:
        if search_params.name:
            query = query.where(Event.name.ilike(f"%{search_params.name}%"))
        if search_params.location:
            query = query.where(Event.location.ilike(f"%{search_params.location}%"))
        if search_params.start_time_from:
            # Convert search time to IST for comparison
            search_time_ist = to_ist(search_params.start_time_from)
            query = query.where(Event.start_time >= search_time_ist)
        if search_params.start_time_to:
            # Convert search time to IST for comparison
            search_time_ist = to_ist(search_params.start_time_to)
            query = query.where(Event.start_time <= search_time_ist)
        if search_params.max_capacity:
            query = query.where(Event.max_capacity >= search_params.max_capacity)
    
    query = query.order_by(Event.created_at.desc())
    
    result = await session.execute(query)
    events = result.scalars().all()
    
    event_responses = []
    for event in events:
        # Create response model manually to avoid async relationship issues
        response_data = {
            "id": event.id,
            "name": event.name,
            "location": event.location,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "max_capacity": event.max_capacity,
            "timezone": event.timezone,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
            "attendees": []  # Will be populated separately if needed
        }
        event_response = EventResponse(**response_data)
        
        # Add timezone conversion if requested and different from stored timezone
        if target_timezone and target_timezone != event.timezone:
            try:
                # Convert the main time fields to the requested timezone
                converted_start = convert_timezone(event.start_time, target_timezone, 'Asia/Kolkata')
                converted_end = convert_timezone(event.end_time, target_timezone, 'Asia/Kolkata')
                
                # Update the main time fields with converted times
                event_response.start_time = converted_start.replace(tzinfo=None)  # Store as naive
                event_response.end_time = converted_end.replace(tzinfo=None)  # Store as naive
                
                # Also provide detailed display information
                event_response.start_time_display = format_datetime_with_timezone(converted_start)
                event_response.end_time_display = format_datetime_with_timezone(converted_end)
            except Exception:
                # If timezone conversion fails, skip the display fields
                pass
        
        event_responses.append(event_response)
    
    return event_responses

async def update_event(
    session: AsyncSession,
    event_id: int,
    event_update: 'EventUpdate'
) -> EventResponse:
    """Update event details with intelligent timezone handling"""
    from app.request_models.events import EventUpdate
    
    result = await session.execute(
        select(Event).where(Event.id == event_id)
    )
    event = result.scalars().first()
    
    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Event with ID {event_id} not found"
        )
        
    try:
        # Store original timezone for comparison
        original_timezone = event.timezone
        new_timezone = event_update.timezone
        
        # If timezone is changing, we need to convert existing times
        timezone_changed = new_timezone and new_timezone != original_timezone
        
        if timezone_changed:
            # The approach: the stored times in the database are in IST
            # but they represent the local time in the event's original timezone
            # When we change timezone, we need to interpret those times as being
            # in the original timezone, then convert to the new timezone
            from app.utils.timezone import convert_timezone, ensure_timezone_aware
            
            print(f"🔄 Timezone changing from {original_timezone} to {new_timezone}")
            print(f"🕐 Original stored times: {event.start_time} to {event.end_time}")
            
            # The stored times are actually naive but represent the local time
            # in the original timezone. Make them timezone-aware in original timezone
            start_in_original_tz = ensure_timezone_aware(event.start_time, original_timezone)
            end_in_original_tz = ensure_timezone_aware(event.end_time, original_timezone)
            
            print(f"🌍 Times in original timezone: {start_in_original_tz} to {end_in_original_tz}")
            
            # Convert to the new timezone (keeping the same absolute moment)
            start_in_new_tz = convert_timezone(start_in_original_tz, new_timezone)
            end_in_new_tz = convert_timezone(end_in_original_tz, new_timezone)
            
            print(f"🌍 Times in new timezone: {start_in_new_tz} to {end_in_new_tz}")
            
            # Store the local time in the new timezone (naive) 
            # This maintains the absolute moment but adjusts the local time representation
            event.start_time = start_in_new_tz.replace(tzinfo=None)
            event.end_time = end_in_new_tz.replace(tzinfo=None)
            event.timezone = new_timezone
            
            print(f"🏪 Stored times (naive): {event.start_time} to {event.end_time}")
            print(f"✅ Timezone change complete")
        
        # Handle other field updates
        update_data = event_update.dict(exclude_unset=True, exclude={'timezone'})
        for key, value in update_data.items():
            if key in ['start_time', 'end_time'] and value is not None:
                # Convert new times to IST for storage
                if hasattr(value, 'tzinfo'):
                    value = to_ist(value)
                else:
                    # If naive, assume it's in the event's current timezone
                    current_tz = new_timezone if new_timezone else event.timezone
                    value = ensure_timezone_aware(value, current_tz)
                    value = to_ist(value)
            
            if hasattr(event, key) and value is not None:
                setattr(event, key, value)
                
        event.updated_at = ist_now()
        await session.commit()
        await session.refresh(event)
        
        # Create response model manually to avoid async relationship issues
        response_data = {
            "id": event.id,
            "name": event.name,
            "location": event.location,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "max_capacity": event.max_capacity,
            "timezone": event.timezone,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
            "attendees": []  # Will be populated separately if needed
        }
        return EventResponse(**response_data)
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Event update failed: {str(e)}"
        )



async def add_attendee(
    session: AsyncSession,
    event_id: int,
    name: str,
    email: str
) -> int:
    """Add attendee to event with comprehensive validation and return attendee ID"""
    from sqlalchemy import func
    
    # Get event with validation
    result = await session.execute(
        select(Event).where(Event.id == event_id)
    )
    event = result.scalars().first()
    
    if not event:
        raise ResourceNotFoundError("Event", event_id)
    
    # Check if event has already started
    current_time_ist = ist_now()
    # Make event start time timezone-aware for comparison
    from app.utils.timezone import ensure_timezone_aware
    event_start_aware = ensure_timezone_aware(event.start_time, 'Asia/Kolkata')
    if event_start_aware <= current_time_ist:
        raise BusinessLogicError(
            ErrorMessages.EVENT_STARTED,
            details={"event_start_time": event.start_time.isoformat()}
        )
    
    # Check for duplicate email registration (case-insensitive)
    duplicate_check = await session.execute(
        select(Attendee).where(
            Attendee.event_id == event_id,
            func.lower(Attendee.email) == email.lower()
        )
    )
    existing_attendee = duplicate_check.scalars().first()
    
    if existing_attendee:
        raise ConflictError(
            ErrorMessages.EMAIL_ALREADY_REGISTERED,
            resource="attendee",
            details={"email": email, "event_id": event_id}
        )
    
    # Check current attendance count against max capacity
    attendance_count = await session.execute(
        select(func.count(Attendee.id)).where(Attendee.event_id == event_id)
    )
    current_attendees = attendance_count.scalar() or 0
    
    if current_attendees >= event.max_capacity:
        raise BusinessLogicError(
            ErrorMessages.EVENT_FULL.format(capacity=event.max_capacity),
            details={
                "current_attendees": current_attendees,
                "max_capacity": event.max_capacity,
                "event_id": event_id
            }
        )
    
    # Validate input data
    if not name or not name.strip():
        raise APIValidationError(
            "Attendee name is required and cannot be empty",
            field="name"
        )
    
    if not email or not email.strip():
        raise APIValidationError(
            "Attendee email is required and cannot be empty",
            field="email"
        )
    
    try:
        # Create new attendee
        attendee = Attendee(
            name=name.strip(),
            email=email.lower().strip(),
            event_id=event_id
        )
        session.add(attendee)
        event.updated_at = ist_now()
        await session.commit()
        await session.refresh(attendee)
        return attendee.id
    except Exception as e:
        await session.rollback()
        # Log the actual error for debugging
        print(f"Database error in add_attendee: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to add attendee due to database error"
        )

