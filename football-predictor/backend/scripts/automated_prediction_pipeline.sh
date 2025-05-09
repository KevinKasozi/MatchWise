#!/bin/bash

# Automated Prediction Pipeline
# This script will:
# 1. Sync latest fixtures from raw data
# 2. Generate predictions for upcoming matches
# 3. Update the frontend with prediction data

# Set the base directory to the script's location
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$BASE_DIR/.."

echo "======= MatchWise Prediction Pipeline ======="
echo "Started at: $(date)"
echo "==========================================="

# Step 1: Sync fixtures from raw data
echo "Step 1: Syncing fixtures from raw data..."
python scripts/sync_all_fixtures_from_raw_data.py
if [ $? -ne 0 ]; then
    echo "Error: Failed to sync fixtures from raw data"
    exit 1
fi

# Step 2: Clean up fixture data
echo "Step 2: Cleaning up fixture data..."
python scripts/fix_duplicate_leagues.py
if [ $? -ne 0 ]; then
    echo "Error: Failed to clean up fixture data"
    exit 1
fi

# Step 3: Generate predictions
echo "Step 3: Generating predictions for upcoming matches..."
python scripts/generate_predictions.py
if [ $? -ne 0 ]; then
    echo "Warning: Failed to generate predictions, but continuing..."
fi

# Step 4: Update frontend with predictions
echo "Step 4: Updating frontend with prediction data..."
python scripts/update_predictions_frontend.py
if [ $? -ne 0 ]; then
    echo "Warning: Failed to update frontend with predictions"
fi

echo "==========================================="
echo "Prediction pipeline completed at: $(date)"
echo "===========================================" 