#!/usr/bin/env python3
"""
Simple test script to verify the POST /events endpoint works
"""

import asyncio
import httpx
from datetime import datetime, timedelta
import json

async def test_create_event():
    """Test creating a new event"""
    
    # Test data for creating an event
    event_data = {
        "name": "Test Conference 2025",
        "location": "San Francisco Convention Center",
        "start_time": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "end_time": (datetime.utcnow() + timedelta(days=30, hours=8)).isoformat(),
        "max_capacity": 500
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Test POST /api/v1/events
            response = await client.post(
                "http://localhost:8000/api/v1/events/",
                json=event_data,
                timeout=10.0
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 200:
                print("✅ Event created successfully!")
                return response.json()
            else:
                print("❌ Failed to create event")
                return None
                
        except Exception as e:
            print(f"❌ Error occurred: {e}")
            return None

async def test_get_events():
    """Test getting all events"""
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://localhost:8000/api/v1/events/",
                timeout=10.0
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 200:
                print("✅ Retrieved events successfully!")
                return response.json()
            else:
                print("❌ Failed to retrieve events")
                return None
                
        except Exception as e:
            print(f"❌ Error occurred: {e}")
            return None

async def main():
    print("Testing Event Management API")
    print("=" * 40)
    
    print("\n1. Testing POST /api/v1/events/")
    event = await test_create_event()
    
    print("\n2. Testing GET /api/v1/events/")
    events = await test_get_events()
    
    if event:
        print(f"\n3. Testing GET /api/v1/events/{event['id']}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"http://localhost:8000/api/v1/events/{event['id']}",
                    timeout=10.0
                )
                print(f"Status Code: {response.status_code}")
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            except Exception as e:
                print(f"❌ Error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 