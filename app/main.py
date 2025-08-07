from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError
from app.controllers.v1 import events_router
from app.utils.error_handlers import (
    validation_exception_handler,
    database_exception_handler,
    generic_exception_handler,
    APIError
)

# Define comprehensive API metadata
app = FastAPI(
    title="Event Management API",
    description="""
## Event Management System

A comprehensive API for managing events and attendee registrations with advanced features:

### Key Features

* **Event Management**: Create and manage events with timezone support
* **Attendee Registration**: Register attendees with duplicate prevention and capacity limits
* **Pagination**: Efficient pagination for large datasets
* **Timezone Support**: Full timezone awareness for global events
* **Validation**: Comprehensive input validation and error handling
* **Async Support**: Built with FastAPI for high performance

### Core Endpoints

* **Events**: Create, list, and manage events
* **Registration**: Register attendees for events with validation
* **Timezone**: Support for multiple timezones and conversion

### Edge Cases Handled

* Maximum capacity enforcement
* Duplicate email prevention
* Past event registration prevention
* Timezone conversion and validation
* Input sanitization and validation

### Technical Stack

* **FastAPI** - Modern Python web framework
* **SQLAlchemy** - Async ORM for database operations
* **PostgreSQL** - Primary database with async support
* **Pydantic** - Data validation and serialization
* **Pytest** - Comprehensive testing suite
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Event Management Team",
        "email": "support@eventmanagement.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.eventmanagement.com",
            "description": "Production server"
        }
    ],
    tags_metadata=[
        {
            "name": "events",
            "description": "Event management operations. Create, list, and manage events with timezone support.",
            "externalDocs": {
                "description": "Event management guide",
                "url": "https://docs.eventmanagement.com/events",
            },
        },
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers for comprehensive error handling
app.add_exception_handler(APIError, lambda request, exc: JSONResponse(
    status_code=exc.status_code,
    content={"detail": exc.message, "error_code": exc.error_code, "details": exc.details}
))
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, database_exception_handler)
app.add_exception_handler(OperationalError, database_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include versioned routes
app.include_router(events_router, prefix="/api/v1")

@app.get("/", 
         summary="API Root",
         description="Get API information and available endpoints",
         response_description="API welcome message with navigation links",
         tags=["root"])
async def root():
    """
    Welcome endpoint for the Event Management API.
    
    Returns basic API information and links to documentation.
    """
    return {
        "message": "Welcome to Event Management API",
        "version": "1.0.0",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "api_endpoints": {
            "events": "/api/v1/events"
        },
        "features": [
            "Event creation and management",
            "Attendee registration with validation",
            "Timezone support",
            "Pagination",
            "Comprehensive error handling"
        ]
    }
