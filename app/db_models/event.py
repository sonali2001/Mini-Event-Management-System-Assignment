from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.base import Base
from ..utils.timezone import ist_now

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    start_time = Column(DateTime(timezone=True))  # Store with timezone info
    end_time = Column(DateTime(timezone=True))    # Store with timezone info
    max_capacity = Column(Integer)
    timezone = Column(String, default='Asia/Kolkata')  # Event's original timezone
    created_at = Column(DateTime(timezone=True), default=ist_now)
    updated_at = Column(DateTime(timezone=True), default=ist_now, onupdate=ist_now)

    # Relationships
    attendees = relationship("Attendee", back_populates="event")

#  {{ ... }}
