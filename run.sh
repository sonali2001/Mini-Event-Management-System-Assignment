#!/bin/bash

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize database migrations
echo "Initializing database migrations..."
alembic upgrade head

# Start the FastAPI server
echo "Starting FastAPI server..."
uvicorn app.main:app --reload
