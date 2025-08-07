import pytest
import uuid
from httpx import AsyncClient
from app.main import app
from app.request_models.events import EventCreate, EventUpdate
from app.request_models.attendees import AttendeeRegistration

@pytest.mark.asyncio
async def test_create_event():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/events/",
            json={
                "name": "Test Event",
                "location": "Test Location",
                            "start_time": "2025-12-05T18:48:00+05:30",
            "end_time": "2025-12-05T20:48:00+05:30",
                "max_capacity": 100,
                "timezone": "Asia/Kolkata"
            }
        )
        assert response.status_code == 200
        event = response.json()
        assert "id" in event
        assert event["name"] == "Test Event"

@pytest.mark.asyncio
async def test_add_remove_attendee():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create event
        response = await client.post(
            "/api/v1/events/",
            json={
                "name": "Test Event",
                "location": "Test Location",
                            "start_time": "2025-12-05T18:48:00+05:30",
            "end_time": "2025-12-05T20:48:00+05:30",
                "max_capacity": 100,
                "timezone": "Asia/Kolkata"
            }
        )
        event_id = response.json()["id"]
        
        # Register attendee (note: register endpoint, not create attendee)
        unique_email = f"test-{uuid.uuid4()}@example.com"
        response = await client.post(
            f"/api/v1/events/{event_id}/register",
            json={
                "name": "Test Attendee",
                "email": unique_email
            }
        )
        assert response.status_code == 200
        
        # Note: Remove attendee endpoint doesn't exist in current API
        # This test would need to be updated based on actual API design
        attendee_id = response.json()["id"]
        # response = await client.delete(
        #     f"/api/v1/events/{event_id}/attendees/{attendee_id}"
        # )
        # assert response.status_code == 200
