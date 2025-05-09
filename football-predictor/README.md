# MatchWise - Football Prediction System

MatchWise is a modern football prediction system that displays real fixture data and provides predictions for upcoming matches.

## Features

- **Real Fixtures**: Displays actual upcoming fixtures from major football leagues including Premier League, La Liga, Bundesliga, Serie A, and Ligue 1
- **Team Information**: Shows team information with proper team logos/badges
- **Competition Grouping**: Organizes fixtures by competition and date
- **Prediction System**: Analyze and predict match outcomes (coming soon)

## Project Structure

The project consists of two main parts:

1. **Backend** (FastAPI)
   - Database models for fixtures, teams, competitions, etc.
   - API endpoints for retrieving fixture data
   - Data ingestion scripts for loading fixtures from raw data files

2. **Frontend** (React with Vite)
   - Modern responsive UI for displaying fixtures
   - Integration with the backend API
   - Tabbed interface for viewing fixtures by date

## Setup Instructions

### Prerequisites

- Node.js (v16+)
- Python (v3.10+)
- PostgreSQL

### Backend Setup

1. Navigate to the backend directory:

```bash
cd football-predictor/backend
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up the database connection in .env file:

```
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/football_predictor
```

5. Load fixtures into the database:

```bash
cd scripts
./load_real_fixtures.sh
```

6. Start the backend server:

```bash
cd ..
uvicorn app.main:app --reload
```

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd football-predictor/frontend
```

2. Install dependencies:

```bash
npm install
```

3. Create a .env file with:

```
VITE_API_URL=http://localhost:8000/api/v1
```

4. Start the development server:

```bash
npm run dev
```

5. Open your browser and navigate to http://localhost:5173

## Using the Application

1. Navigate to the Fixtures page to see upcoming matches
2. View fixtures organized by date and competition
3. Each fixture shows the teams with their respective logos
4. Tabs allow you to view today's fixtures, tomorrow's fixtures, or upcoming fixtures

## Working with Real Fixture Data

The system uses real fixture data from various football leagues. This data is stored in text files in the `backend/data/raw` directory, organized by league and season.

### How Fixture Data Works

1. Raw data is stored in text files (e.g., `backend/data/raw/eng-england/2023-24/1-premierleague.txt`)
2. The `real_fixture_parser.py` script parses these files and loads them into the database
3. The `update_fixture_dates.py` script ensures all fixtures use dates in the current year
4. The API endpoints in `fixtures.py` retrieve this data with proper team and competition information
5. The frontend displays these fixtures in a user-friendly interface

### Updating Fixture Data

To update fixture data:

1. Add or modify text files in the `backend/data/raw` directory
2. Run the load script: `cd backend/scripts && ./load_real_fixtures.sh`

## Technologies Used

- **Backend**:
  - FastAPI
  - SQLAlchemy
  - PostgreSQL
  - Pydantic

- **Frontend**:
  - React
  - Vite
  - TailwindCSS
  - React Query
  - Headless UI

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. 