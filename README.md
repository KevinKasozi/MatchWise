# MatchWise

**MatchWise** is an open-source football data platform for ingesting, normalizing, and predicting football match outcomes. It is designed for researchers, data scientists, and developers who want to work with comprehensive, structured football data from global leagues and competitions.

---

## 🚀 Features
- **Automated Data Ingestion:** Robust scripts to parse, normalize, and ingest raw football data (fixtures, clubs, squads, results) from open data sources.
- **Team Name Normalization:** Advanced mapping to unify team/club names across inconsistent datasets.
- **Modern Backend:** Python, FastAPI, SQLAlchemy, and Alembic for scalable APIs and database management.
- **Frontend:** Built with Vite and React for a fast, modern user experience.
- **Extensible Parsers:** Modular ingestion pipeline supports new data formats and competitions.
- **Validation & Auditing:** Scripts to check data completeness, consistency, and assignment.
- **Open Source:** MIT licensed, easy to contribute and extend.

---

## 📁 Project Structure

```
MatchWise/
  alembic/                  # Database migrations
  football-predictor/       # Main backend and data pipeline
    backend/
      app/                  # FastAPI app, models, schemas
      data/                 # Raw and processed football data
      scripts/              # Ingestion, validation, and utility scripts
      ml/                   # Machine learning models (future)
    frontend/               # Vite + React frontend
  node_modules/             # Frontend dependencies
  ...
  README.md                 # This file
```

---

## ⚙️ Setup & Installation

### 1. **Clone the Repository**
```bash
git clone https://github.com/KevinKasozi/MatchWise.git
cd MatchWise
```

### 2. **Backend Setup**
- Python 3.10+
- PostgreSQL (or compatible DB)
- Install dependencies:
  ```bash
  cd football-predictor/backend
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```
- Configure your database in `.env` or `app/core/config.py`.
- Run migrations:
  ```bash
  alembic upgrade head
  ```

### 3. **Frontend Setup**
- Node.js 18+
- Install dependencies:
  ```bash
  cd ../../frontend
  npm install
  npm run dev
  ```

---

## 🏗️ Data Ingestion Pipeline

1. **Build Team Name Mapper**
   ```bash
   python -m scripts.team_mapper_builder --use-db
   ```
2. **Run Full Ingestion**
   ```bash
   python -m scripts.enhanced_ingestion --force --parallel --threads 4
   # or
   ./scripts/run_full_ingestion.sh
   ```
3. **Validate Data**
   ```bash
   python -m scripts.verify_team_assignments
   ```

- All raw data is in `backend/data/raw/` (organized by country/league/season).
- Ingestion scripts handle normalization, upserts, and logging.
- See `scripts/README_INGESTION.md` for advanced usage.

---

## 🧩 Key Components
- **`app/models/models.py`**: SQLAlchemy models for clubs, teams, fixtures, results, etc.
- **`scripts/enhanced_ingestion.py`**: Main ingestion script (batch, parallel, robust).
- **`scripts/team_mapper_builder.py`**: Builds the team name normalization map.
- **`frontend/`**: Vite + React app for data exploration and prediction UI.

---

## 🛡️ Validation & Auditing
- **`scripts/verify_team_assignments.py`**: Checks for misassigned teams/fixtures.
- **Audit logs**: All ingestion actions are logged for traceability.

---

## 🤝 Contributing
1. Fork the repo and create a feature branch.
2. Follow code style and add tests where possible.
3. Submit a pull request with a clear description.
4. All contributions are welcome—data, code, docs, or ideas!

---

## 📄 License
MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements
- [OpenFootball](https://github.com/openfootball) for raw data sources.
- The Python, FastAPI, SQLAlchemy, Vite, and React communities.

---

## 📬 Contact
For questions, suggestions, or collaborations, open an issue or contact the maintainer via GitHub. 