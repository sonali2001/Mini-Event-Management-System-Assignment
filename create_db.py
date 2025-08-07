#!/usr/bin/env python3
"""
Simple script to create the SQLite database from our models.
This bypasses the Alembic migration issues with SQLite.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.database.base import Base
from app.db_models.event import Event
from app.db_models.attendee import Attendee

async def create_database():
    """Create the database and all tables"""
    # Create async engine for SQLite
    engine = create_async_engine("sqlite+aiosqlite:///./event_management.db", echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database created successfully!")
    print("📁 Database file: event_management.db")
    
    # Close the engine
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_database()) 