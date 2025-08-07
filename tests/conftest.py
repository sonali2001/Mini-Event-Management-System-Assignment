import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.db_models.event import Event
from app.db_models.attendee import Attendee

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture
async def db_session():
    """Create a clean database session for each test"""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    session = TestSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        
        # Clean up tables
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function") 
def client() -> TestClient:
    """Create test client - uses real database for now"""
    client = TestClient(app)
    yield client

@pytest.fixture
async def async_client(db_session):
    """Create async test client with database session override"""
    async def get_test_db():
        yield db_session
    
    app.dependency_overrides[get_db] = get_test_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
async def sample_event(db_session):
    """Create a sample event for testing"""
    from datetime import datetime, timedelta
    from app.utils.timezone import ensure_timezone_aware, to_ist
    
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)
    
    # Make timezone-aware before converting to IST
    start_time_aware = ensure_timezone_aware(start_time, 'Asia/Kolkata')
    end_time_aware = ensure_timezone_aware(end_time, 'Asia/Kolkata')
    
    event = Event(
        name="Test Event",
        location="Test Location",
        start_time=to_ist(start_time_aware),
        end_time=to_ist(end_time_aware),
        max_capacity=10,
        timezone="Asia/Kolkata"
    )
    
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)
    return event

@pytest.fixture
async def sample_attendee(db_session, sample_event):
    """Create a sample attendee for testing"""
    attendee = Attendee(
        name="John Doe",
        email="john@example.com",
        event_id=sample_event.id
    )
    
    db_session.add(attendee)
    await db_session.commit()
    await db_session.refresh(attendee)
    return attendee

# Configure pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 