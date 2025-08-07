from fastapi import APIRouter, HTTPException, Depends, Query
from app.services import event_service, attendee_service
from app.request_models.events import EventCreate, EventResponse, EventSearch, EventUpdate
from app.request_models.attendees import AttendeeRegistration, AttendeeResponse
from app.request_models import PaginatedResponse
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from datetime import datetime
from app.utils.timezone import (
    convert_timezone,
    now_in_timezone
)

router = APIRouter(prefix="/events", tags=["events"])



@router.post("/", response_model=EventResponse)
async def create_event(
    event: EventCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new event with timezone support.
    Event times are stored in IST but can be provided in any timezone.
    """
    try:
        event_data = await event_service.create_event(db, event)
        return event_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[EventResponse])
async def get_all_events(
    db: AsyncSession = Depends(get_db),
    name: Optional[str] = Query(None, description="Filter events by name"),
    location: Optional[str] = Query(None, description="Filter events by location"),
    upcoming_only: bool = Query(True, description="Show only upcoming events"),
    timezone: Optional[str] = Query('Asia/Kolkata', description="Timezone for display (default: IST)")
):
    """
    List all events with optional filtering and timezone conversion.
    All events are stored in IST but can be displayed in any timezone.
    """
    try:
        # Build search parameters
        search_params = None
        if name or location:
            search_params = EventSearch(
                name=name,
                location=location,
                timezone=timezone
            )
        
        events = await event_service.get_all_events(db, search_params, timezone)
        
        # Filter for upcoming events if requested
        if upcoming_only:
            current_time = now_in_timezone(timezone)
            upcoming_events = []
            
            for event in events:
                # Convert event time to comparison timezone
                event_start_in_tz = convert_timezone(event.start_time, timezone, 'Asia/Kolkata')
                if event_start_in_tz > current_time:
                    upcoming_events.append(event)
            
            return upcoming_events
        
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an event with intelligent timezone handling.
    
    When timezone is changed, the system automatically converts the existing
    start and end times to maintain the same absolute moment in time.
    
    For example:
    - Event originally at 10:00 AM IST 
    - Change timezone to America/New_York
    - Times will be adjusted to represent the same moment in the new timezone
    """
    try:
        event = await event_service.update_event(db, event_id, event_update)
        return event
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{event_id}/register", response_model=AttendeeResponse)
async def register_attendee(
    event_id: int,
    attendee: AttendeeRegistration,
    db: AsyncSession = Depends(get_db),
    check_timezone: Optional[str] = Query('Asia/Kolkata', description="Timezone for time validation")
):
    """
    Register an attendee for a specific event. 
    Prevents overbooking and duplicate registrations.
    All validations are handled in the service layer.
    """
    try:
        # Register attendee (service handles all validation)
        attendee_id = await event_service.add_attendee(
            db,
            event_id,
            attendee.name,
            attendee.email
        )
        
        # Return the newly created attendee
        new_attendee = await attendee_service.get_attendee(db, attendee_id)
        return new_attendee
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{event_id}/attendees", response_model=PaginatedResponse[AttendeeResponse])
async def get_event_attendees(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """Returns paginated list of registered attendees for an event"""
    try:
        # Check if event exists
        event = await event_service.get_event(db, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Get paginated attendees for this event
        return await attendee_service.get_event_attendees(
            db, event_id, page=page, page_size=page_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






