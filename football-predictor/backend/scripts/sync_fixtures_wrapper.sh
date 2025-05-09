#!/bin/bash
# Wrapper script for sync_fixtures.py that redirects to our new enhanced ingestion system
# This is for backwards compatibility only - use run_full_ingestion.sh for new code

echo "NOTE: sync_fixtures.py is deprecated. Using enhanced_ingestion.py instead."

# Get script directory
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Parse arguments
FORCE_FLAG=""
LEAGUE_FLAG=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --force)
      FORCE_FLAG="--force"
      shift
      ;;
    --league)
      LEAGUE_FLAG="--league $2"
      shift 2
      ;;
    *)
      # Unknown option
      shift
      ;;
  esac
done

# Run enhanced ingestion with same arguments
CMD="python -m scripts.enhanced_ingestion $FORCE_FLAG $LEAGUE_FLAG"
echo "Running: $CMD"
$CMD 