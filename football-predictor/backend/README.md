# MatchWise Backend

The backend for the MatchWise football prediction system, built with FastAPI, SQLAlchemy, and scikit-learn.

## Overview

This backend provides:
- RESTful API for football data
- Enhanced data ingestion from OpenFootball sources
- Database models for football entities
- Machine learning predictions for match outcomes
- Authentication and authorization

## Tech Stack

- FastAPI (web framework)
- SQLAlchemy (ORM)
- PostgreSQL (database)
- scikit-learn (machine learning)
- Alembic (database migrations)
- Pydantic (data validation)

## Directory Structure

```
backend/
├── alembic/                # Database migrations
├── app/                    # Application code
│   ├── api/                # API endpoints
│   │   └── endpoints/      # Individual endpoint modules
│   ├── core/               # Core functionality
│   ├── ingestion/          # Data ingestion code
│   ├── models/             # Database models
│   │   └── models.py       # SQLAlchemy models
│   └── schemas/            # Pydantic schemas
├── data/                   # Data files
├── ml/                     # Machine learning code
└── scripts/                # Utility scripts
    ├── parsers/            # Data parsers
    ├── enhanced_ingestion.py  # Enhanced data ingestion
    ├── team_mapper_builder.py # Team name normalization
    └── run_full_ingestion.sh  # Full ingestion script
```

## Getting Started

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000, with interactive documentation at http://localhost:8000/docs.

## Enhanced Data Ingestion

The backend includes a comprehensive data ingestion system for OpenFootball data:

### Key Components

- **team_mapper_builder.py**: Creates a comprehensive mapping of team names and variants
- **enhanced_ingestion.py**: Main ingestion script with support for parallel processing
- **parsers/**: Modular parsers for different data formats
- **run_full_ingestion.sh**: One-click script to run the complete ingestion process

### Running Data Ingestion

Run full ingestion (recommended):
```bash
./scripts/run_full_ingestion.sh
```

For more control, use the Python script directly:
```bash
# Process all data
python -m scripts.enhanced_ingestion

# Force reprocessing of all files
python -m scripts.enhanced_ingestion --force

# Process only specific leagues
python -m scripts.enhanced_ingestion --league eng-england

# Use parallel processing
python -m scripts.enhanced_ingestion --parallel --threads 4
```

## API Endpoints

- **/api/v1/clubs/** - Club information
- **/api/v1/teams/** - Team data
- **/api/v1/fixtures/** - Match fixtures and results
- **/api/v1/players/** - Player information
- **/api/v1/predictions/** - Match predictions
- **/api/v1/ingestion/** - Data ingestion control and status

## Database Models

The database schema includes the following main entities:
- **Club** - Football clubs with metadata
- **Team** - Teams (club or national)
- **Player** - Player information
- **Fixture** - Match fixtures
- **MatchResult** - Match outcomes
- **Competition** - Leagues and tournaments
- **Season** - Competition seasons
- **Prediction** - ML-generated predictions

## Machine Learning

The prediction system uses:
- Historical match data for training
- Team performance metrics
- Home/away advantage factors
- Recent form analysis

Models are stored in the `ml/` directory, with prediction logic in `ml/predict.py`.

## Development

### Code Quality

This project uses:
- black for code formatting
- flake8 for linting
- mypy for type checking
- pytest for testing

### Running Tests

```bash
pytest
```

### Environment Variables

Key environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Security key for JWT
- `ALGORITHM`: JWT algorithm
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration
- `DATA_PATH`: Path to football data 