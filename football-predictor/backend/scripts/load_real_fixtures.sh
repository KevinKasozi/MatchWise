#!/bin/bash

# Script to load real fixtures into the database

# Ensure script stops on error
set -e

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$BACKEND_DIR")"

echo "Current directory: $(pwd)"
echo "Script directory: $SCRIPT_DIR"
echo "Backend directory: $BACKEND_DIR" 
echo "Project directory: $PROJECT_DIR"

# Activate virtual environment if it exists
if [ -d "$BACKEND_DIR/venv" ]; then
    echo "Activating virtual environment..."
    source "$BACKEND_DIR/venv/bin/activate"
fi

# Set the PYTHONPATH to include the backend directory
export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"

# Check if database URL is provided as an environment variable
if [ -z "$DATABASE_URL" ]; then
    echo "No DATABASE_URL provided, using default localhost connection"
    export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor"
fi

echo "Using database: $DATABASE_URL"

# First ensure database tables exist
echo "Ensuring database tables exist..."
python "$BACKEND_DIR/scripts/setup_db_and_fixtures.py"

# Run the real fixture parser
echo "Loading real fixtures from data files..."
python "$BACKEND_DIR/scripts/real_fixture_parser.py"

# Update fixture dates to ensure they're current
echo "Updating fixture dates to current year..."
python "$BACKEND_DIR/scripts/update_fixture_dates.py"

echo "Fixture loading complete!" 