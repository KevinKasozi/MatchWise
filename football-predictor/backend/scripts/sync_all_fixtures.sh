#!/bin/bash

# Script to synchronize ALL fixtures from raw data files

# Exit on error
set -e

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

echo "================================================"
echo "    FIXTURE SYNCHRONIZATION FROM RAW DATA"
echo "================================================"
echo "Current directory: $(pwd)"
echo "Script directory: $SCRIPT_DIR"
echo "Backend directory: $BACKEND_DIR"

# Activate virtual environment if it exists
if [ -d "$BACKEND_DIR/venv" ]; then
    echo "Activating virtual environment..."
    source "$BACKEND_DIR/venv/bin/activate"
fi

# Set the PYTHONPATH to include the backend directory
export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"

# Check if database URL is provided as an environment variable
if [ -z "$DATABASE_URL" ]; then
    echo "No DATABASE_URL provided, using default local connection"
    export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor"
fi

echo "Using database connection: $DATABASE_URL"

# Create log file
LOG_FILE="$SCRIPT_DIR/sync_all_fixtures_run.log"
echo "Logging to: $LOG_FILE"

echo "===== Starting complete fixture data refresh at $(date) =====" > "$LOG_FILE"

# Run the fixture sync script
echo "Running sync_all_fixtures_from_raw_data.py..."
python "$SCRIPT_DIR/sync_all_fixtures_from_raw_data.py" 2>&1 | tee -a "$LOG_FILE"

SYNC_STATUS=${PIPESTATUS[0]}
if [ $SYNC_STATUS -eq 0 ]; then
    echo "===== Fixture data refresh completed successfully at $(date) =====" >> "$LOG_FILE"
    echo "✅ SUCCESS: Fixture data synchronization completed."
else
    echo "===== Fixture data refresh FAILED at $(date) =====" >> "$LOG_FILE"
    echo "❌ ERROR: Fixture data synchronization failed with code $SYNC_STATUS."
fi

echo "Done! Check $LOG_FILE for detailed logs."
echo "================================================" 