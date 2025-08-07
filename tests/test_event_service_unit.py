import pytest
import uuid
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.services.event_service import (
    create_event, 
    get_event, 
    get_all_events, 
    add_attendee,
    update_event
)
from app.request_models.events import EventCreate, EventUpdate
from app.db_models.event import Event
from app.db_models.attendee import Attendee
from app.utils.timezone import ensure_timezone_aware, to_ist
from app.utils.error_handlers import (
    ResourceNotFoundError,
    ConflictError,
    BusinessLogicError
)
from app.database.base import Base

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


class TestEventService:
    """Unit tests for event service functions"""
    
    async def get_test_session(self) -> AsyncSession:
        """Create a fresh test session with clean tables"""
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        session = TestSessionLocal()
        return session
    
    async def cleanup_test_session(self, session: AsyncSession):
        """Clean up test session and drop tables"""
        await session.close()
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @pytest.mark.asyncio
    async def test_create_event_success(self):
        """Test successful event creation"""
        session = await self.get_test_session()
        try:
            # Create timezone-aware datetimes
            future_time = datetime.now() + timedelta(days=1)
            start_time_aware = ensure_timezone_aware(future_time, 'Asia/Kolkata')
            end_time_aware = ensure_timezone_aware(future_time + timedelta(hours=2), 'Asia/Kolkata')
            
            event_data = EventCreate(
                name="Test Event",
                location="Test Location",
                start_time=start_time_aware,
                end_time=end_time_aware,
                max_capacity=50,
                timezone="Asia/Kolkata"
            )
            
            result = await create_event(session, event_data)
            
            assert result.name == "Test Event"
            assert result.location == "Test Location"
            assert result.max_capacity == 50
            assert result.timezone == "Asia/Kolkata"
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_create_event_end_time_before_start_time(self):
        """Test event creation with end time before start time - should fail at validation"""
        future_time = datetime.now() + timedelta(days=1)
        
        # This should fail at Pydantic validation level, not service level
        with pytest.raises(Exception):  # Could be ValidationError or ValueError
            event_data = EventCreate(
                name="Invalid Event",
                location="Test Location",
                start_time=ensure_timezone_aware(future_time, 'Asia/Kolkata'),
                end_time=ensure_timezone_aware(future_time - timedelta(hours=1), 'Asia/Kolkata'),  # End before start
                max_capacity=50,
                timezone="Asia/Kolkata"
            )

    @pytest.mark.asyncio
    async def test_get_event_success(self):
        """Test successful event retrieval"""
        session = await self.get_test_session()
        try:
            # First create an event
            future_time = datetime.now() + timedelta(days=1)
            event_data = EventCreate(
                name="Test Event for Get",
                location="Test Location",
                start_time=ensure_timezone_aware(future_time, 'Asia/Kolkata'),
                end_time=ensure_timezone_aware(future_time + timedelta(hours=2), 'Asia/Kolkata'),
                max_capacity=50,
                timezone="Asia/Kolkata"
            )
            
            created_event = await create_event(session, event_data)
            
            # Now retrieve it
            result = await get_event(session, created_event.id)
            
            assert result.id == created_event.id
            assert result.name == "Test Event for Get"
            assert result.location == "Test Location"
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_get_event_not_found(self):
        """Test event retrieval with non-existent ID"""
        session = await self.get_test_session()
        try:
            with pytest.raises(ResourceNotFoundError):
                await get_event(session, 99999)
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_get_all_events(self):
        """Test retrieving all events"""
        session = await self.get_test_session()
        try:
            # Create a test event first
            future_time = datetime.now() + timedelta(days=1)
            event_data = EventCreate(
                name="Test Event for List",
                location="Test Location",
                start_time=ensure_timezone_aware(future_time, 'Asia/Kolkata'),
                end_time=ensure_timezone_aware(future_time + timedelta(hours=2), 'Asia/Kolkata'),
                max_capacity=50,
                timezone="Asia/Kolkata"
            )
            
            created_event = await create_event(session, event_data)
            
            # Now get all events
            results = await get_all_events(session)
            
            assert len(results) >= 1
            assert any(event.id == created_event.id for event in results)
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_add_attendee_success(self):
        """Test successful attendee registration"""
        session = await self.get_test_session()
        try:
            # Create a test event first
            future_time = datetime.now() + timedelta(days=1)
            event_data = EventCreate(
                name="Test Event for Attendee",
                location="Test Location",
                start_time=ensure_timezone_aware(future_time, 'Asia/Kolkata'),
                end_time=ensure_timezone_aware(future_time + timedelta(hours=2), 'Asia/Kolkata'),
                max_capacity=50,
                timezone="Asia/Kolkata"
            )
            
            created_event = await create_event(session, event_data)
            
            # Generate unique email to avoid conflicts
            unique_email = f"jane-{uuid.uuid4()}@example.com"
            
            attendee_id = await add_attendee(
                session,
                created_event.id,
                "Jane Doe",
                unique_email
            )
            
            assert isinstance(attendee_id, int)
            assert attendee_id > 0
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_add_attendee_duplicate_email(self):
        """Test duplicate email registration prevention"""
        session = await self.get_test_session()
        try:
            # Create a test event first
            future_time = datetime.now() + timedelta(days=1)
            event_data = EventCreate(
                name="Test Event for Duplicate",
                location="Test Location",
                start_time=ensure_timezone_aware(future_time, 'Asia/Kolkata'),
                end_time=ensure_timezone_aware(future_time + timedelta(hours=2), 'Asia/Kolkata'),
                max_capacity=50,
                timezone="Asia/Kolkata"
            )
            
            created_event = await create_event(session, event_data)
            
            # Add first attendee
            unique_email = f"duplicate-{uuid.uuid4()}@example.com"
            await add_attendee(
                session,
                created_event.id,
                "John Doe",
                unique_email
            )
            
            # Try to add second attendee with same email
            with pytest.raises(ConflictError):
                await add_attendee(
                    session,
                    created_event.id,
                    "Jane Doe", 
                    unique_email
                )
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_add_attendee_nonexistent_event(self):
        """Test registration for non-existent event"""
        session = await self.get_test_session()
        try:
            unique_email = f"test-{uuid.uuid4()}@example.com"
            with pytest.raises(ResourceNotFoundError):
                await add_attendee(session, 99999, "Test User", unique_email)
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_update_event_success(self):
        """Test successful event update"""
        session = await self.get_test_session()
        try:
            # Create a test event first
            future_time = datetime.now() + timedelta(days=1)
            event_data = EventCreate(
                name="Test Event for Update",
                location="Original Location",
                start_time=ensure_timezone_aware(future_time, 'Asia/Kolkata'),
                end_time=ensure_timezone_aware(future_time + timedelta(hours=2), 'Asia/Kolkata'),
                max_capacity=50,
                timezone="Asia/Kolkata"
            )
            
            created_event = await create_event(session, event_data)
            
            # Create update data
            update_data = EventUpdate(
                name="Updated Event Name",
                location="Updated Location"
            )
            
            result = await update_event(session, created_event.id, update_data)
            
            assert result.name == "Updated Event Name"
            assert result.location == "Updated Location"
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_update_event_not_found(self):
        """Test update of non-existent event"""
        session = await self.get_test_session()
        try:
            update_data = EventUpdate(name="Test")
            with pytest.raises(Exception):  # Could be HTTPException or ResourceNotFoundError
                await update_event(session, 99999, update_data)
        finally:
            await self.cleanup_test_session(session) 