#!/bin/bash
# This script runs the full football data ingestion process

set -e  # Exit on any error

# Display banner
echo "====================================="
echo "  MatchWise Football Data Ingestion  "
echo "====================================="
echo ""

# Change to project root directory
cd "$(dirname "$0")/.."
PROJ_ROOT=$(pwd)

echo "Project root: $PROJ_ROOT"
echo "Starting data ingestion process..."

# 1. First build the team mapper
echo "Step 1: Building team name mapper..."
python -m scripts.team_mapper_builder --use-db

# Check if team mapper was created successfully
if [ ! -f "data/team_mapper.json" ]; then
    echo "Error: Failed to create team mapper."
    exit 1
fi

echo "Team mapper created successfully."

# 2. Run the enhanced ingestion script
echo "Step 2: Running enhanced data ingestion..."
python -m scripts.enhanced_ingestion --force

# 3. Display summary
echo "Data ingestion process completed!"
echo "To view detailed logs, check enhanced_ingestion.log"

echo "====================================="
echo "Done!" 