# Event Management API

A comprehensive REST API for managing events and attendee registrations with advanced features including timezone support, pagination, input validation, and error handling.

## 🚀 Features

- **Event Management**: Create, read, and update events with advanced timezone support
- **Intelligent Timezone Handling**: Dynamic timezone conversion and event timezone updates that preserve absolute time
- **Attendee Registration**: Register attendees with duplicate prevention and capacity limits
- **Pagination**: Efficient pagination for large datasets with flexible page sizes
- **Real-time Timezone Conversion**: View events in any timezone with automatic time conversion
- **Event Updates**: Update events with smart timezone conversion that maintains absolute timing
- **Input Validation**: Comprehensive input validation with meaningful error messages
- **Async Architecture**: Built with FastAPI for high performance and scalability
- **API Documentation**: Interactive Swagger UI and ReDoc documentation
- **Comprehensive Testing**: Full test suite with unit and integration tests

## 🏗️ Architecture

- **FastAPI**: Modern Python web framework with automatic API documentation
- **SQLAlchemy**: Async ORM for database operations
- **PostgreSQL/SQLite**: Database support (PostgreSQL for production, SQLite for development)
- **Pydantic**: Data validation and serialization
- **Alembic**: Database migrations
- **Pytest**: Comprehensive testing framework

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- PostgreSQL (for production) or SQLite (for development)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd event_management
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=sqlite:///./event_management.db

# For PostgreSQL (production):
# DATABASE_URL=postgresql://username:password@localhost:5432/event_management

# Application Settings
ENV=development
DEBUG=True
```

### 5. Database Setup

```bash
# Initialize database with Alembic
alembic upgrade head
```

### 6. Run the Application

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Base URL**: http://localhost:8000
- **Interactive Documentation (Swagger)**: http://localhost:8000/docs
- **Alternative Documentation (ReDoc)**: http://localhost:8000/redoc

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app

# Run specific test file
pytest tests/test_event_service_unit.py

# Run async tests only
pytest -k "async"
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/events/` | List all upcoming events with pagination and filtering |
| POST | `/events/` | Create a new event with timezone support |
| PUT | `/events/{event_id}` | Update event with intelligent timezone handling |
| POST | `/events/{event_id}/register` | Register an attendee for an event |
| GET | `/events/{event_id}/attendees` | Get paginated list of event attendees |

## 🔧 Sample API Requests

### 1. Create an Event

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/events/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Conference 2025",
    "location": "Mumbai Convention Center",
    "start_time": "2025-06-15T10:00:00",
    "end_time": "2025-06-15T18:00:00",
    "max_capacity": 150,
    "timezone": "Asia/Kolkata"
  }'
```

**Response:**
```json
{
  "id": 1,
  "name": "Tech Conference 2025",
  "location": "Mumbai Convention Center",
  "start_time": "2025-06-15T10:00:00",
  "end_time": "2025-06-15T18:00:00",
  "max_capacity": 150,
  "timezone": "Asia/Kolkata",
  "created_at": "2025-08-07T15:14:25.422620",
  "updated_at": "2025-08-07T15:14:25.422620",
  "attendees": []
}
```

### 2. List All Upcoming Events

**cURL:**
```bash
curl -X GET "http://localhost:8000/api/v1/events/?upcoming_only=true&timezone=Asia/Kolkata"
```

**With Filtering:**
```bash
curl -X GET "http://localhost:8000/api/v1/events/?name=Tech&location=Mumbai&upcoming_only=true"
```

### 3. Register an Attendee for an Event

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/events/1/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com"
  }'

  curl -X POST "http://localhost:8000/api/v1/events/5/register" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User Two",
    "email": "different.email7@example.com"
  }'

  // {"detail":"This event has reached its maximum capacity of 500 attendees"}
  curl -X POST "http://localhost:8000/api/v1/events/4/register" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sonali",
    "email": "singhsonal2003@gmail.com"
  }'

//This email address is already registered for this event

  curl -X POST "http://localhost:8000/api/v1/events/5/register" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User One",
    "email": "different.email@example.com"
  }'

  curl -X GET "http://localhost:8000/api/v1/events/?name=Year-End%20Comedy%20Show&timezone=America/New_York&upcoming_only=false" \
  -H "accept: application/json" | python3 -c "
import sys, json
from datetime import datetime

data = json.load(sys.stdin)
if len(data) > 0:
    event = data[0]  # Get the first matching event
    print('🇺🇸 Event Viewed in US Eastern Timezone!')
    print('=' * 50)
    print(f'📅 Event ID: {event[\"id\"]}')
    print(f'📝 Name: {event[\"name\"]}')
    print(f'📍 Location: {event[\"location\"]}')
    print(f'🕐 Start Time: {event[\"start_time\"]} EST/EDT')
    print(f'🕐 End Time: {event[\"end_time\"]} EST/EDT')
    print(f'🌍 Displayed in: America/New_York timezone')
    print(f'🏠 Original Timezone: {event[\"timezone\"]}')
    print(f'👥 Capacity: {event[\"max_capacity\"]} attendees')
    print(f'✅ Current Registrations: {len(event[\"attendees\"])}')
    print()
    print('⏰ Time Conversion Summary:')
    print('   🇮🇳 Indian Time (IST):     Dec 10, 7:00 PM - Dec 20, 11:00 PM')
    print('   🇺🇸 US Eastern Time (EST): Dec 10, 8:30 AM - Dec 20, 12:30 PM')
    print('   ⏳ Time Difference: IST is 10.5 hours ahead of EST')
    print()
    print('🎭 Multi-day Comedy Event!')
    print('   • Indian attendees: Evening start, late night end')
    print('   • US East Coast attendees: Morning start, afternoon end')
    print('   • Duration: 10 days of comedy shows!')
else:
    print('❌ No events found matching the criteria')
"
```

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": null,
  "event_id": 1,
  "created_at": "2024-01-08T10:30:00+00:00",
  "updated_at": "2024-01-08T10:30:00+00:00"
}
```

### 4. Get Event Attendees with Pagination

**cURL:**
```bash
curl -X GET "http://localhost:8000/api/v1/events/4/attendees?page=1&page_size=20"
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": null,
      "event_id": 1,
      "created_at": "2024-01-08T10:30:00+00:00",
      "updated_at": "2024-01-08T10:30:00+00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "has_next": false,
  "has_prev": false
}
```

### 5. Get Supported Timezones

**cURL:**
```bash
curl -X GET "http://localhost:8000/api/v1/events/timezones"
```

### 6. Convert Event Times to Different Timezone

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/events/1/convert-timezone" \
  -H "Content-Type: application/json" \
  -d '{
    "timezone": "America/New_York"
  }'
```

### 7. Update Event with Timezone Change

**cURL:**
```bash
curl -X PUT "http://localhost:8000/api/v1/events/1" \
  -H "Content-Type: application/json" \
  -d '{
    "timezone": "America/New_York"
  }'
```

**Response:**
The system automatically converts the event times to maintain the same absolute moment:
```json
{
  "id": 1,
  "name": "Tech Conference 2025",
  "location": "Mumbai Convention Center",
  "start_time": "2025-06-14T23:30:00",
  "end_time": "2025-06-15T07:30:00",
  "max_capacity": 150,
  "timezone": "America/New_York",
  "created_at": "2025-08-07T15:14:25.422620",
  "updated_at": "2025-08-07T15:20:30.123456",
  "attendees": []
}
```





## 📝 Postman Collection

### Import Instructions

1. Open Postman
2. Click "Import" button
3. Copy and paste the following collection:

```json
{
  "info": {
    "name": "Event Management API",
    "description": "Comprehensive API for managing events and attendees",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000/api/v1",
      "type": "string"
    }
  ],
  "item": [
    {
      "name": "Events",
      "item": [
        {
          "name": "Create Event",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"name\": \"Tech Conference 2024\",\n  \"location\": \"Mumbai Convention Center\",\n  \"start_time\": \"2024-06-15T10:00:00\",\n  \"end_time\": \"2024-06-15T18:00:00\",\n  \"max_capacity\": 150,\n  \"timezone\": \"Asia/Kolkata\"\n}"
            },
            "url": {
              "raw": "{{base_url}}/events/",
              "host": ["{{base_url}}"],
              "path": ["events", ""]
            }
          }
        },
        {
          "name": "List Events",
          "request": {
            "method": "GET",
            "url": {
              "raw": "{{base_url}}/events/?upcoming_only=true&timezone=Asia/Kolkata",
              "host": ["{{base_url}}"],
              "path": ["events", ""],
              "query": [
                {
                  "key": "upcoming_only",
                  "value": "true"
                },
                {
                  "key": "timezone",
                  "value": "Asia/Kolkata"
                }
              ]
            }
          }
        },
        {
          "name": "Register Attendee",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"name\": \"John Doe\",\n  \"email\": \"john.doe@example.com\"\n}"
            },
            "url": {
              "raw": "{{base_url}}/events/1/register",
              "host": ["{{base_url}}"],
              "path": ["events", "1", "register"]
            }
          }
        },
        {
          "name": "Get Event Attendees",
          "request": {
            "method": "GET",
            "url": {
              "raw": "{{base_url}}/events/1/attendees?page=1&page_size=10",
              "host": ["{{base_url}}"],
              "path": ["events", "1", "attendees"],
              "query": [
                {
                  "key": "page",
                  "value": "1"
                },
                {
                  "key": "page_size",
                  "value": "10"
                }
              ]
            }
          }
        },
        {
          "name": "Update Event",
          "request": {
            "method": "PUT",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"timezone\": \"America/New_York\"\n}"
            },
            "url": {
              "raw": "{{base_url}}/events/1",
              "host": ["{{base_url}}"],
              "path": ["events", "1"]
            }
          }
        }
      ]
    }
  ]
}
```

## 🔍 Error Handling

The API provides comprehensive error handling with meaningful error messages:

### Validation Errors (422)
```json
{
  "error": true,
  "error_code": "VALIDATION_ERROR",
  "message": "The provided data is invalid. Please check the errors below and try again.",
  "details": {
    "validation_errors": [
      {
        "field": "email",
        "message": "Please provide a valid email address",
        "type": "value_error",
        "input": "invalid-email"
      }
    ],
    "error_count": 1
  },
  "timestamp": "2024-01-08T10:00:00Z",
  "path": "/api/v1/events/"
}
```

### Business Logic Errors (400)
```json
{
  "error": true,
  "error_code": "BUSINESS_LOGIC_ERROR",
  "message": "This event has reached its maximum capacity of 150 attendees",
  "details": {
    "current_attendees": 150,
    "max_capacity": 150,
    "event_id": 1
  },
  "timestamp": "2024-01-08T10:00:00Z",
  "path": "/api/v1/events/1/register"
}
```

### Conflict Errors (409)
```json
{
  "error": true,
  "error_code": "CONFLICT_ERROR",
  "message": "This email address is already registered for this event",
  "details": {
    "email": "john.doe@example.com",
    "event_id": 1,
    "resource": "attendee"
  },
  "timestamp": "2024-01-08T10:00:00Z",
  "path": "/api/v1/events/1/register"
}
```

## 🌍 Advanced Timezone Management

### Key Features

- **Storage**: All events are stored in IST (India Standard Time) for consistency
- **Input**: Events can be created in any timezone with automatic conversion
- **Display**: Events can be viewed in any timezone with real-time conversion
- **Validation**: Registration time validation uses the user's timezone
- **Smart Updates**: Changing an event's timezone preserves the absolute moment in time
- **Dynamic Conversion**: GET requests can specify any timezone for on-the-fly conversion
- **Intelligent Timezone Changes**: PUT requests automatically adjust times when timezone is updated

### Intelligent Timezone Updates

When you update an event's timezone using the PUT endpoint, the system:

1. **Preserves Absolute Time**: The actual moment of the event remains unchanged
2. **Converts Local Time**: Adjusts the displayed time to match the new timezone
3. **Maintains Consistency**: All attendees see the same absolute moment regardless of their timezone

**Example:**
- Original: 3:00 PM IST (Asia/Kolkata)
- Change to: America/New_York timezone
- Result: 5:30 AM EST (same absolute moment)

### Supported Timezones

Common timezone examples:
- `Asia/Kolkata` (IST)
- `UTC`
- `America/New_York` (EST/EDT)
- `America/Los_Angeles` (PST/PDT)
- `Europe/London` (GMT/BST)
- `Asia/Tokyo` (JST)
- `Australia/Sydney` (AEST/AEDT)

### Usage Examples

**Create event in New York timezone:**
```bash
curl -X POST "http://localhost:8000/api/v1/events/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NYC Tech Meetup",
    "description": "Technology networking event in New York",
    "location": "Manhattan Conference Center",
    "start_time": "2025-06-15T15:00:00",
    "end_time": "2025-06-15T18:00:00",
    "max_capacity": 100,
    "timezone": "America/New_York"
  }'
```

**View events in Tokyo timezone:**
```bash
curl -X GET "http://localhost:8000/api/v1/events/?timezone=Asia/Tokyo"
```

**Change event timezone (preserves absolute time):**
```bash
curl -X PUT "http://localhost:8000/api/v1/events/1" \
  -H "Content-Type: application/json" \
  -d '{
    "timezone": "Europe/London"
  }'
```



## 📊 Pagination

All list endpoints support pagination with the following parameters:

- `page`: Page number (1-based, default: 1)
- `page_size`: Items per page (1-100, default: 10)

### Pagination Response Format

```json
{
  "items": [...],
  "total": 150,
  "page": 2,
  "page_size": 10,
  "total_pages": 15,
  "has_next": true,
  "has_prev": true
}
```

## 🔒 Business Rules & Constraints

### Events
- Event name: 1-200 characters, must contain at least one alphanumeric character
- Location: 1-200 characters
- Start time: Must be in the future
- End time: Must be after start time
- Duration: Minimum 15 minutes, maximum 30 days
- Max capacity: 1-10,000 attendees

### Attendees
- Name: 1-100 characters, letters, spaces, hyphens, apostrophes allowed
- Email: Valid email format, case-insensitive, max 100 characters
- Phone: Optional, flexible format support
- No duplicate emails per event

### Registration Rules
- Cannot register for past events
- Cannot exceed event capacity
- Email uniqueness enforced per event
- Registration closes when event starts

## 📊 Database Schema

### Event Model
```python
- id: Integer (Primary Key)
- name: String (1-200 chars, required)
- description: Text (optional)
- location: String (1-200 chars, required) 
- start_time: DateTime (required, timezone-aware)
- end_time: DateTime (required, timezone-aware)
- max_capacity: Integer (1-10,000, required)
- timezone: String (IANA timezone, default: Asia/Kolkata)
- created_at: DateTime (auto-generated)
- updated_at: DateTime (auto-updated)
```

### Attendee Model
```python
- id: Integer (Primary Key)
- name: String (1-100 chars, required)
- email: String (valid email, required, unique per event)
- phone: String (optional, flexible format)
- event_id: Integer (Foreign Key to Event)
- created_at: DateTime (auto-generated)
- updated_at: DateTime (auto-updated)
```

### Relationships
- **Event → Attendees**: One-to-Many relationship
- **Unique Constraints**: Email per event (prevents duplicate registrations)
- **Indexes**: Optimized queries on event dates, email lookups, and attendee searches

## ⚙️ Configuration

### Environment Variables

```env
# Database
DATABASE_URL=sqlite:///./event_management.db

# Application
ENV=development
DEBUG=True
LOG_LEVEL=INFO

# Timezone
DEFAULT_TIMEZONE=Asia/Kolkata
```

### Development vs Production

**Development (SQLite):**
```env
DATABASE_URL=sqlite:///./event_management.db
```

**Production (PostgreSQL):**
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/event_management
```

## 🚀 Deployment

### Docker Deployment

1. Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. Build and run:
```bash
docker build -t event-management-api .
docker run -p 8000:8000 event-management-api
```

### Production Considerations

- Use PostgreSQL for the database
- Set up proper environment variables
- Configure logging
- Set up monitoring and health checks
- Use a reverse proxy (nginx)
- Enable HTTPS
- Set up database backups

## 🐛 Troubleshooting

### Common Issues

**1. Database Connection Error**
```bash
# Check database URL
echo $DATABASE_URL

# Reset database
alembic downgrade base
alembic upgrade head
```

**2. Module Import Errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**3. Port Already in Use**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8001
```

**4. Timezone Errors**
```bash
# Install/update timezone data
pip install --upgrade pytz
```

## 📞 Support

For issues and questions:

1. Check the API documentation at `/docs`
2. Review error messages in API responses
3. Check application logs
4. Verify environment configuration

## 🔄 API Versioning

Current API version: `v1`

All endpoints are prefixed with `/api/v1/`

## 📈 Performance Notes

- The API uses async/await for non-blocking operations
- Database queries are optimized with proper indexing
- Pagination prevents memory issues with large datasets
- Timezone conversions are cached where possible

## 🆕 Recent Enhancements

### Version 2.0 Features (Latest)

- **Advanced Timezone Management**: Intelligent timezone updates that preserve absolute time
- **Event Updates**: Full event update functionality with PUT endpoint
- **Enhanced Timezone Conversion**: Real-time timezone conversion on GET requests
- **Improved Error Handling**: More detailed error messages and validation
- **Comprehensive Testing**: Extended test suite covering all new features
- **Database Migration Support**: Alembic migrations for schema updates
- **Performance Optimizations**: Async operations and optimized queries

### What's New

1. **Smart Timezone Changes**: When you change an event's timezone, the system automatically adjusts the local time while preserving the absolute moment
2. **Dynamic Timezone Display**: View any event in any timezone without modifying the stored data
3. **Enhanced Event Management**: Update event details including name, location, capacity, and timezone
4. **Better Error Messages**: More informative error responses with detailed validation information
5. **Robust Testing**: Comprehensive test coverage including unit and integration tests

## 🧪 Testing Coverage

The API includes comprehensive testing:

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end API testing
- **Service Tests**: Business logic validation
- **Controller Tests**: Endpoint testing
- **Timezone Tests**: Timezone conversion validation
- **Error Handling Tests**: Error scenario coverage

**Run specific test categories:**
```bash
# Unit tests
pytest tests/test_*_unit.py

# Integration tests  
pytest tests/test_*_integration.py

# Service layer tests
pytest tests/test_*_service.py

# Controller tests
pytest tests/test_*_controller.py
```

## 🧩 Extension Points

The API is designed to be extensible:

- Add authentication/authorization
- Implement event categories  
- Add email notifications
- Create event analytics
- Add file upload for event images
- Implement event check-in/check-out
- Add recurring events support
- Implement event cancellation workflow
- Add attendee waitlist functionality