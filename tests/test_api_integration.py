import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from fastapi import status

from app.db_models.event import Event
from app.db_models.attendee import Attendee
from app.utils.timezone import to_ist


class TestEventAPIIntegration:
    """Integration tests for Event API endpoints"""

    @pytest.mark.asyncio
    async def test_create_event_success(self, async_client: AsyncClient):
        """Test successful event creation via API"""
        future_time = datetime.now() + timedelta(days=1)
        event_data = {
            "name": "API Test Event",
            "location": "API Test Location",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "max_capacity": 50,
            "timezone": "Asia/Kolkata"
        }
        
        response = await async_client.post("/events/", json=event_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "API Test Event"
        assert data["max_capacity"] == 50

    @pytest.mark.asyncio
    async def test_create_event_validation_errors(self, async_client: AsyncClient):
        """Test event creation with validation errors"""
        # Test with past start time
        past_time = datetime.now() - timedelta(hours=1)
        event_data = {
            "name": "Past Event",
            "location": "Test Location",
            "start_time": past_time.isoformat(),
            "end_time": (past_time + timedelta(hours=2)).isoformat(),
            "max_capacity": 50,
            "timezone": "Asia/Kolkata"
        }
        
        response = await async_client.post("/events/", json=event_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_events_pagination_and_filtering(self, async_client: AsyncClient, sample_event: Event):
        """Test get events with filtering and upcoming events only"""
        # Create additional events
        future_time = datetime.now() + timedelta(days=2)
        for i in range(5):
            event_data = {
                "name": f"Future Event {i}",
                "location": f"Location {i}",
                "start_time": (future_time + timedelta(hours=i)).isoformat(),
                "end_time": (future_time + timedelta(hours=i+2)).isoformat(),
                "max_capacity": 10 + i,
                "timezone": "Asia/Kolkata"
            }
            await async_client.post("/events/", json=event_data)
        
        # Test get all upcoming events
        response = await async_client.get("/events/?upcoming_only=true")
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) >= 1
        
        # Test filtering by name
        response = await async_client.get("/events/?name=Future Event 1")
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        # Should find the event with that name
        assert any("Future Event 1" in event["name"] for event in events)

    @pytest.mark.asyncio
    async def test_register_attendee_success(self, async_client: AsyncClient, sample_event: Event):
        """Test successful attendee registration"""
        registration_data = {
            "name": "API Test Attendee",
            "email": "api.test@example.com"
        }
        
        response = await async_client.post(
            f"/events/{sample_event.id}/register",
            json=registration_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "API Test Attendee"
        assert data["email"] == "api.test@example.com"
        assert data["event_id"] == sample_event.id

    @pytest.mark.asyncio
    async def test_register_attendee_duplicate_email(self, async_client: AsyncClient, sample_event: Event):
        """Test duplicate email registration prevention"""
        registration_data = {
            "name": "First User",
            "email": "duplicate@example.com"
        }
        
        # First registration should succeed
        response = await async_client.post(
            f"/events/{sample_event.id}/register",
            json=registration_data
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Second registration with same email should fail
        registration_data["name"] = "Second User"
        response = await async_client.post(
            f"/events/{sample_event.id}/register",
            json=registration_data
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_attendee_max_capacity(self, async_client: AsyncClient):
        """Test max capacity enforcement"""
        # Create event with capacity of 1
        future_time = datetime.now() + timedelta(days=1)
        event_data = {
            "name": "Small Capacity Event",
            "location": "Test Location",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "max_capacity": 1,
            "timezone": "Asia/Kolkata"
        }
        
        event_response = await async_client.post("/events/", json=event_data)
        event_id = event_response.json()["id"]
        
        # First registration should succeed
        registration_data = {
            "name": "First Attendee",
            "email": "first@example.com"
        }
        response = await async_client.post(f"/events/{event_id}/register", json=registration_data)
        assert response.status_code == status.HTTP_200_OK
        
        # Second registration should fail
        registration_data = {
            "name": "Second Attendee", 
            "email": "second@example.com"
        }
        response = await async_client.post(f"/events/{event_id}/register", json=registration_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "maximum capacity" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_event_attendees_pagination(self, async_client: AsyncClient, sample_event: Event):
        """Test paginated attendee listing"""
        # Register multiple attendees
        for i in range(15):
            registration_data = {
                "name": f"Attendee {i}",
                "email": f"attendee{i}@example.com"
            }
            await async_client.post(
                f"/events/{sample_event.id}/register",
                json=registration_data
            )
        
        # Test first page
        response = await async_client.get(f"/events/{sample_event.id}/attendees?page=1&page_size=10")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] >= 15
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["has_next"] is True
        assert data["has_prev"] is False
        
        # Test second page
        response = await async_client.get(f"/events/{sample_event.id}/attendees?page=2&page_size=10")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["page"] == 2
        assert data["has_prev"] is True

    @pytest.mark.asyncio
    async def test_attendee_registration_invalid_data(self, async_client: AsyncClient, sample_event: Event):
        """Test attendee registration with invalid data"""
        # Test with empty name
        registration_data = {
            "name": "",
            "email": "test@example.com"
        }
        response = await async_client.post(
            f"/events/{sample_event.id}/register",
            json=registration_data
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test with empty email
        registration_data = {
            "name": "Test User",
            "email": ""
        }
        response = await async_client.post(
            f"/events/{sample_event.id}/register",
            json=registration_data
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_event_not_found_errors(self, async_client: AsyncClient):
        """Test 404 errors for non-existent events"""
        # Test register for non-existent event
        registration_data = {
            "name": "Test User",
            "email": "test@example.com"
        }
        response = await async_client.post("/events/99999/register", json=registration_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test get attendees for non-existent event
        response = await async_client.get("/events/99999/attendees")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_timezone_support(self, async_client: AsyncClient):
        """Test timezone support in API"""
        # Test creating event with different timezone
        future_time = datetime.now() + timedelta(days=1)
        event_data = {
            "name": "NYC Event",
            "location": "New York",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "max_capacity": 50,
            "timezone": "America/New_York"
        }
        
        response = await async_client.post("/events/", json=event_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["timezone"] == "America/New_York"


class TestAttendeeAPIIntegration:
    """Integration tests for Attendee API endpoints"""

    @pytest.mark.asyncio
    async def test_create_standalone_attendee(self, async_client: AsyncClient):
        """Test creating standalone attendee"""
        attendee_data = {
            "name": "Standalone Attendee",
            "email": "standalone@example.com",
            "phone": "123-456-7890"
        }
        
        response = await async_client.post("/attendees/", json=attendee_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "Standalone Attendee"
        assert data["email"] == "standalone@example.com"
        assert data["phone"] == "123-456-7890"

    @pytest.mark.asyncio
    async def test_get_all_attendees_pagination(self, async_client: AsyncClient, sample_event: Event):
        """Test getting all attendees with pagination"""
        # Create multiple attendees
        for i in range(12):
            attendee_data = {
                "name": f"Global Attendee {i}",
                "email": f"global{i}@example.com"
            }
            await async_client.post("/attendees/", json=attendee_data)
        
        # Test pagination
        response = await async_client.get("/attendees/?page=1&page_size=5")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data["items"]) == 5
        assert data["total"] >= 12
        assert data["page"] == 1
        assert data["page_size"] == 5

    @pytest.mark.asyncio
    async def test_get_attendee_by_id(self, async_client: AsyncClient, sample_attendee: Attendee):
        """Test getting specific attendee by ID"""
        response = await async_client.get(f"/attendees/{sample_attendee.id}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == sample_attendee.id
        assert data["name"] == sample_attendee.name

    @pytest.mark.asyncio
    async def test_update_attendee(self, async_client: AsyncClient, sample_attendee: Attendee):
        """Test updating attendee"""
        update_data = {
            "name": "Updated Name",
            "email": "updated@example.com"
        }
        
        response = await async_client.put(f"/attendees/{sample_attendee.id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["email"] == "updated@example.com"

    @pytest.mark.asyncio
    async def test_delete_attendee(self, async_client: AsyncClient, sample_attendee: Attendee):
        """Test deleting attendee"""
        response = await async_client.delete(f"/attendees/{sample_attendee.id}")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify attendee is deleted
        response = await async_client.get(f"/attendees/{sample_attendee.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_attendee_validation_errors(self, async_client: AsyncClient):
        """Test attendee creation with validation errors"""
        # Test with invalid email
        attendee_data = {
            "name": "Test User",
            "email": "not-an-email"
        }
        
        response = await async_client.post("/attendees/", json=attendee_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_attendee_not_found_errors(self, async_client: AsyncClient):
        """Test 404 errors for non-existent attendees"""
        # Test get non-existent attendee
        response = await async_client.get("/attendees/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test update non-existent attendee
        update_data = {"name": "Test"}
        response = await async_client.put("/attendees/99999", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestEdgeCasesIntegration:
    """Integration tests for edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_concurrent_registrations(self, async_client: AsyncClient):
        """Test concurrent registrations for limited capacity event"""
        # Create event with limited capacity
        future_time = datetime.now() + timedelta(days=1)
        event_data = {
            "name": "Concurrent Test Event",
            "location": "Test Location",
            "start_time": future_time.isoformat(),
            "end_time": (future_time + timedelta(hours=2)).isoformat(),
            "max_capacity": 3,
            "timezone": "Asia/Kolkata"
        }
        
        event_response = await async_client.post("/events/", json=event_data)
        event_id = event_response.json()["id"]
        
        # Simulate concurrent registrations
        import asyncio
        
        async def register_attendee(i):
            registration_data = {
                "name": f"Concurrent User {i}",
                "email": f"concurrent{i}@example.com"
            }
            return await async_client.post(f"/events/{event_id}/register", json=registration_data)
        
        # Try to register 5 people for event with capacity 3
        responses = await asyncio.gather(
            *[register_attendee(i) for i in range(5)],
            return_exceptions=True
        )
        
        # Count successful registrations
        successful = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        failed = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code in [400, 409])
        
        # Should have exactly 3 successful and 2 failed
        assert successful == 3
        assert failed == 2

    @pytest.mark.asyncio
    async def test_boundary_values(self, async_client: AsyncClient):
        """Test boundary values for pagination"""
        # Test minimum page size
        response = await async_client.get("/attendees/?page=1&page_size=1")
        assert response.status_code == status.HTTP_200_OK
        
        # Test maximum page size
        response = await async_client.get("/attendees/?page=1&page_size=100")
        assert response.status_code == status.HTTP_200_OK
        
        # Test invalid page size (should be validated by FastAPI)
        response = await async_client.get("/attendees/?page=1&page_size=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, async_client: AsyncClient):
        """Test protection against SQL injection in search parameters"""
        # Try SQL injection in event name filter
        response = await async_client.get("/events/?name='; DROP TABLE events; --")
        # Should not crash and return normal response
        assert response.status_code in [200, 422]  # Either valid empty response or validation error

    @pytest.mark.asyncio
    async def test_large_data_handling(self, async_client: AsyncClient, sample_event: Event):
        """Test handling of large amounts of data"""
        # Register many attendees to test pagination with large datasets
        for i in range(50):
            registration_data = {
                "name": f"Bulk Attendee {i:03d}",
                "email": f"bulk{i:03d}@example.com"
            }
            response = await async_client.post(
                f"/events/{sample_event.id}/register",
                json=registration_data
            )
            # Some might fail due to capacity, that's ok
            assert response.status_code in [200, 400]
        
        # Test getting attendees with large page size
        response = await async_client.get(f"/events/{sample_event.id}/attendees?page=1&page_size=100")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "items" in data
        assert "total" in data 