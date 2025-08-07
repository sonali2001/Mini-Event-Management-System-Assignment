from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from fastapi import HTTPException
from app.db_models.attendee import Attendee
from app.request_models.attendees import AttendeeResponse
from app.request_models import PaginatedResponse


async def get_attendee(
    session: AsyncSession,
    attendee_id: int
) -> AttendeeResponse:
    """Get attendee by ID"""
    result = await session.execute(
        select(Attendee).where(Attendee.id == attendee_id)
    )
    attendee = result.scalars().first()
    if not attendee:
        raise HTTPException(
            status_code=404,
            detail=f"Attendee with ID {attendee_id} not found"
        )
    return AttendeeResponse.model_validate(attendee)


async def get_event_attendees(
    session: AsyncSession,
    event_id: int,
    page: int = 1,
    page_size: int = 10
) -> PaginatedResponse[AttendeeResponse]:
    """Get paginated list of attendees for a specific event"""
    # Build queries for event attendees
    query = select(Attendee).where(Attendee.event_id == event_id)
    count_query = select(func.count(Attendee.id)).where(Attendee.event_id == event_id)
    
    # Get total count
    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(Attendee.created_at).offset(offset).limit(page_size)
    
    # Execute query
    result = await session.execute(query)
    attendees = result.scalars().all()
    
    # Convert to response models
    attendee_responses = [AttendeeResponse.model_validate(attendee) for attendee in attendees]
    
    # Return paginated response
    return PaginatedResponse.create(
        items=attendee_responses,
        total=total,
        page=page,
        page_size=page_size
    )
