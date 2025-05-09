# Football Data Ingestion System

This directory contains the enhanced football data ingestion system for MatchWise.

## Overview

The ingestion system processes football data from various sources including:

- Clubs and teams
- Players and squads
- Fixtures and results
- Competitions and seasons

## Key Components

- **team_mapper_builder.py**: Builds a comprehensive mapping of team names and variants
- **enhanced_ingestion.py**: Main ingestion script for processing football data
- **parsers/**: Modular parsers for different data types and formats
- **run_full_ingestion.sh**: One-click script to run the complete ingestion process

## Usage

### Full Data Ingestion

To run a complete data ingestion process:

```bash
./run_full_ingestion.sh
```

This will:

1. Build/update the team name mapping
2. Process all data repositories
3. Update the database with new/changed data

### Partial Updates

Process only specific leagues:

```bash
python -m scripts.enhanced_ingestion --league eng-england
```

Force reprocessing of all files regardless of timestamps:

```bash
python -m scripts.enhanced_ingestion --force
```

Use parallel processing for faster ingestion:

```bash
python -m scripts.enhanced_ingestion --parallel --threads 4
```

### API Integration

The ingestion system can also be triggered via API endpoints:

```
POST /api/v1/ingestion/run
GET /api/v1/ingestion/status
```

## Data Structure

The raw data is structured in directories by:

- League/country (e.g., eng-england, es-espana)
- Season (e.g., 2023-24)
- Content type (fixtures, clubs, squads)

## Monitoring

Ingestion logs are saved to:

- **enhanced_ingestion.log**: Detailed processing logs
- **IngestionAudit** database table: Historical record of processed files

## Extending

To add support for new data formats:

1. Create a parser in the `parsers/` directory
2. Add the new parser to the processing logic in enhanced_ingestion.py

# Football Predictor Data Ingestion

This directory contains scripts for loading and managing football fixture data in the MatchWise prediction system.

## Available Scripts

### 1. Load Real Fixtures

The most important script for setting up real fixture data is:

```bash
./load_real_fixtures.sh
```

This script:

1. Creates the database tables if they don't exist
2. Loads fixtures from the raw data files in the `/data/raw` directory
3. Updates fixture dates to ensure they use the current year
4. Ensures all the fixtures are properly linked to teams, clubs, and competitions

### 2. Update Fixture Dates

If you want to manually update fixture dates to the current year:

```bash
python update_fixture_dates.py
```

This ensures that all fixtures are shown with dates in the current year, making them relevant for upcoming predictions.

### 3. Check Fixtures

To verify that fixtures are properly loaded:

```bash
python check_fixtures.py
```

This will show a summary of fixtures in the database and their status.

## Data Sources

The fixture data comes from open-source repositories containing historical and upcoming matches. The primary source is the raw data in:

```
football-predictor/backend/data/raw
```

This includes fixtures from:

- English Premier League
- Spanish La Liga
- German Bundesliga
- Italian Serie A
- French Ligue 1
- Champions League
- Europa League

## Adding New Fixtures

To add new fixtures manually, you can:

1. Add text files to the appropriate league folder in the raw data directory
2. Run the load_real_fixtures.sh script to load them

## Database Structure

Fixtures are stored in the `fixtures` table with relationships to:

- `teams` - Home and away teams
- `clubs` - The clubs that the teams belong to
- `competitions` - The competition/league the fixture is part of
- `seasons` - The season within the competition

## Troubleshooting

If you encounter errors when loading fixtures:

1. Ensure your PostgreSQL database is running
2. Check that the DATABASE_URL environment variable is set correctly
3. Verify that the data files exist in the correct locations
4. Check the database tables to ensure they're created correctly

For database connection issues, the default connection string is:

```
postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor
```

You can override this by setting the DATABASE_URL environment variable.
