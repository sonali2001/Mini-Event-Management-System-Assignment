from .events import EventCreate, EventUpdate, EventResponse
from .attendees import AttendeeResponse
from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Pagination parameters for API endpoints"""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=10, ge=1, le=100, description="Number of items per page (max 100)")

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model"""
    items: List[T]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")

    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int):
        """Helper method to create paginated response"""
        total_pages = (total + page_size - 1) // page_size  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )

__all__ = [
    'EventCreate', 'EventUpdate', 'EventResponse',
    'AttendeeResponse'
]
