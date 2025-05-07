# Football Predictor

A full-stack football prediction system that ingests historical and current football data from OpenFootball, stores it in a relational database, and uses machine learning to make predictions via a modern frontend.

## Features

- Data ingestion from OpenFootball
- RESTful API with FastAPI
- Modern React frontend with Material-UI
- PostgreSQL database
- Machine learning predictions
- CI/CD with GitHub Actions

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- scikit-learn
- Python 3.11+

### Frontend
- React 18
- TypeScript
- Material-UI
- Vite
- React Query
- React Router

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Docker and Docker Compose (optional)

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/football-predictor.git
cd football-predictor
```

2. Create and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. Set up the frontend:
```bash
cd frontend
npm install
```

### Running the Application

1. Start the PostgreSQL database:
```bash
docker-compose up -d db
```

2. Run the backend:
```bash
cd backend
uvicorn app.main:app --reload
```

3. Run the frontend:
```bash
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Development

### Backend Development

- API endpoints are in `backend/app/api/endpoints/`
- Database models are in `backend/app/models/`
- Data ingestion logic is in `backend/app/ingestion/`
- ML pipeline is in `backend/ml/`

### Frontend Development

- Components are in `frontend/src/components/`
- Pages are in `frontend/src/pages/`
- API client is in `frontend/src/api/`
- Types are in `frontend/src/types/`

### Running Tests

Backend tests:
```bash
cd backend
pytest
```

Frontend tests:
```bash
cd frontend
npm test
```

### Code Quality

The project uses several tools to maintain code quality:

- Backend:
  - black for code formatting
  - flake8 for linting
  - mypy for type checking
  - bandit for security checks

- Frontend:
  - ESLint for linting
  - TypeScript for type checking
  - Prettier for code formatting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 