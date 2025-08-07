import pytest
import uuid
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.services.attendee_service import (
    get_attendee,
    get_event_attendees
)
from app.db_models.event import Event
from app.db_models.attendee import Attendee
from app.request_models.attendees import AttendeeResponse
from app.request_models import PaginatedResponse
from app.utils.timezone import ensure_timezone_aware, to_ist
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


class TestAttendeeService:
    """Unit tests for attendee service functions"""
    
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
    
    async def create_test_event(self, session: AsyncSession) -> Event:
        """Helper method to create a test event"""
        future_time = datetime.now() + timedelta(days=1)
        event = Event(
            name="Test Event",
            location="Test Location",
            start_time=to_ist(ensure_timezone_aware(future_time, 'Asia/Kolkata')),
            end_time=to_ist(ensure_timezone_aware(future_time + timedelta(hours=2), 'Asia/Kolkata')),
            max_capacity=50,
            timezone="Asia/Kolkata"
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event
    
    async def create_test_attendee(self, session: AsyncSession, event_id: int, name: str = None, email: str = None) -> Attendee:
        """Helper method to create a test attendee"""
        attendee = Attendee(
            name=name or "Test Attendee",
            email=email or f"test-{uuid.uuid4()}@example.com",
            event_id=event_id
        )
        session.add(attendee)
        await session.commit()
        await session.refresh(attendee)
        return attendee

    @pytest.mark.asyncio
    async def test_get_attendee_success(self):
        """Test successful attendee retrieval by ID"""
        session = await self.get_test_session()
        try:
            # Create test event and attendee
            event = await self.create_test_event(session)
            attendee = await self.create_test_attendee(session, event.id, "John Doe", "john@example.com")
            
            # Test getting the attendee
            result = await get_attendee(session, attendee.id)
            
            assert isinstance(result, AttendeeResponse)
            assert result.id == attendee.id
            assert result.name == "John Doe"
            assert result.email == "john@example.com"
            assert result.event_id == event.id
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_get_attendee_not_found(self):
        """Test attendee retrieval with non-existent ID"""
        session = await self.get_test_session()
        try:
            with pytest.raises(HTTPException) as exc:
                await get_attendee(session, 99999)
            assert exc.value.status_code == 404
            assert "not found" in str(exc.value.detail)
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_get_event_attendees_success(self):
        """Test successful retrieval of event attendees with pagination"""
        session = await self.get_test_session()
        try:
            # Create test event
            event = await self.create_test_event(session)
            
            # Create multiple attendees
            attendees = []
            names = ["Alice Johnson", "Bob Smith", "Carol Davis", "David Wilson", "Emma Brown"]
            for i in range(5):
                attendee = await self.create_test_attendee(
                    session, 
                    event.id, 
                    names[i], 
                    f"attendee{i+1}@example.com"
                )
                attendees.append(attendee)
            
            # Test getting event attendees (page 1, size 3)
            result = await get_event_attendees(session, event.id, page=1, page_size=3)
            
            assert isinstance(result, PaginatedResponse)
            assert result.total == 5
            assert result.page == 1
            assert result.page_size == 3
            assert len(result.items) == 3
            assert result.total_pages == 2
            assert result.has_next == True
            assert result.has_prev == False
            
            # Verify attendee data
            for item in result.items:
                assert isinstance(item, AttendeeResponse)
                assert item.event_id == event.id
                assert item.name in names  # Should be one of our test names
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_get_event_attendees_pagination(self):
        """Test pagination functionality for event attendees"""
        session = await self.get_test_session()
        try:
            # Create test event
            event = await self.create_test_event(session)
            
            # Create 7 attendees
            names = ["Alice Brown", "Bob Johnson", "Carol Smith", "David Davis", "Emma Wilson", "Frank Miller", "Grace Taylor"]
            for i in range(7):
                await self.create_test_attendee(
                    session, 
                    event.id, 
                    names[i], 
                    f"user{i+1}@example.com"
                )
            
            # Test page 1 (first 3)
            page1 = await get_event_attendees(session, event.id, page=1, page_size=3)
            assert len(page1.items) == 3
            assert page1.page == 1
            assert page1.total == 7
            assert page1.has_next == True
            assert page1.has_prev == False
            
            # Test page 2 (next 3)
            page2 = await get_event_attendees(session, event.id, page=2, page_size=3)
            assert len(page2.items) == 3
            assert page2.page == 2
            assert page2.total == 7
            assert page2.has_next == True
            assert page2.has_prev == True
            
            # Test page 3 (last 1)
            page3 = await get_event_attendees(session, event.id, page=3, page_size=3)
            assert len(page3.items) == 1
            assert page3.page == 3
            assert page3.total == 7
            assert page3.has_next == False
            assert page3.has_prev == True
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_get_event_attendees_empty_event(self):
        """Test getting attendees for an event with no attendees"""
        session = await self.get_test_session()
        try:
            # Create test event without attendees
            event = await self.create_test_event(session)
            
            # Test getting attendees for empty event
            result = await get_event_attendees(session, event.id)
            
            assert isinstance(result, PaginatedResponse)
            assert result.total == 0
            assert result.page == 1
            assert result.page_size == 10
            assert len(result.items) == 0
            assert result.total_pages == 0
            assert result.has_next == False
            assert result.has_prev == False
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_get_event_attendees_nonexistent_event(self):
        """Test getting attendees for a non-existent event"""
        session = await self.get_test_session()
        try:
            # Test getting attendees for non-existent event
            result = await get_event_attendees(session, 99999)
            
            # Should return empty result, not error
            assert isinstance(result, PaginatedResponse)
            assert result.total == 0
            assert len(result.items) == 0
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_get_event_attendees_custom_page_size(self):
        """Test custom page size for event attendees"""
        session = await self.get_test_session()
        try:
            # Create test event
            event = await self.create_test_event(session)
            
            # Create 10 attendees
            names = ["Alice Adams", "Bob Brown", "Carol Clark", "David Davis", "Emma Evans", 
                    "Frank Ford", "Grace Green", "Henry Hall", "Ivy Irving", "Jack Johnson"]
            for i in range(10):
                await self.create_test_attendee(
                    session, 
                    event.id, 
                    names[i], 
                    f"person{i+1}@example.com"
                )
            
            # Test with custom page size
            result = await get_event_attendees(session, event.id, page=1, page_size=4)
            
            assert result.total == 10
            assert result.page_size == 4
            assert len(result.items) == 4
            assert result.total_pages == 3
            assert result.has_next == True
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_get_event_attendees_ordering(self):
        """Test that attendees are ordered by created_at"""
        session = await self.get_test_session()
        try:
            # Create test event
            event = await self.create_test_event(session)
            
            # Create attendees with slight delays to ensure different created_at times
            first_attendee = await self.create_test_attendee(session, event.id, "First", "first@example.com")
            
            # Small delay to ensure different timestamps
            import asyncio
            await asyncio.sleep(0.001)
            
            second_attendee = await self.create_test_attendee(session, event.id, "Second", "second@example.com")
            
            # Get attendees
            result = await get_event_attendees(session, event.id, page=1, page_size=10)
            
            assert len(result.items) == 2
            # Should be ordered by created_at (first attendee first)
            assert result.items[0].name == "First"
            assert result.items[1].name == "Second"
        finally:
            await self.cleanup_test_session(session)

    @pytest.mark.asyncio
    async def test_attendee_response_validation(self):
        """Test that AttendeeResponse model validation works correctly"""
        session = await self.get_test_session()
        try:
            # Create test event and attendee
            event = await self.create_test_event(session)
            attendee = await self.create_test_attendee(
                session, 
                event.id, 
                "Validation Test", 
                "validation@example.com"
            )
            
            # Get attendee and verify response structure
            result = await get_attendee(session, attendee.id)
            
            # Check all expected fields are present
            assert hasattr(result, 'id')
            assert hasattr(result, 'name')
            assert hasattr(result, 'email')
            assert hasattr(result, 'event_id')
            assert hasattr(result, 'created_at')
            assert hasattr(result, 'updated_at')
            
            # Check field types and values
            assert isinstance(result.id, int)
            assert isinstance(result.name, str)
            assert isinstance(result.email, str)
            assert isinstance(result.event_id, int)
            assert result.name == "Validation Test"
            assert result.email == "validation@example.com"
            assert result.event_id == event.id
        finally:
            await self.cleanup_test_session(session)
