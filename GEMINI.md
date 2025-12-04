# propEV - Expected Value Betting Tool

## Project Overview
`propEV` is a Python-based application designed to identify positive expected value (EV) betting opportunities in NFL and NBA player props. It scrapes odds from "The Odds API", calculates "true" probabilities by removing the vigorish (vig) from sharp bookmakers (FanDuel, DraftKings), and compares these against soft bookmakers (PrizePicks, Underdog) to find profitable discrepancies.

The system runs on a continuous schedule to update odds and stores potential bets in a PostgreSQL database, which can be queried directly or accessed via a FastAPI-based REST API.

## Architecture
The project consists of three main subsystems:
1.  **Data Collection & Logic Engine:** Fetches odds, calculates EV, and determines bet viability.
2.  **Scheduler:** Orchestrates the periodic data fetching and database updates.
3.  **API:** Exposes the stored betting opportunities via a RESTful interface.

### Key Files & Directories
*   **`Game.py`**: Core logic for EV calculation, devigging odds, and comparing bookmakers.
*   **`scheduler.py`**: The main entry point for the background worker. Runs the `update_ev_bets` job periodically.
*   **`api.py`**: A FastAPI application serving the collected bets and statistics.
*   **`get_data.py`**: Handles interactions with "The Odds API".
*   **`nba_data.py` / `nfl_data.py`**: Sport-specific logic and stats handling.
*   **`database.py`**: Manages PostgreSQL connections and operations.
*   **`schema.sql`**: Defines the database structure (`games`, `ev_bets`, `active_ev_bets`).
*   **`stats/`**: Directory containing CSV files (`nba_stats.csv`, `nfl_stats.csv`) with historical player data used for standard deviation calculations.

## Setup & Configuration

### Dependencies
Managed via `requirements.txt`. Key libraries include:
*   `fastapi`, `uvicorn`: API server.
*   `pandas`, `numpy`, `scipy`: Data analysis and probability calculations.
*   `psycopg2-binary`: PostgreSQL adapter.
*   `schedule`: Task scheduling.
*   `nflreadpy`: NFL data fetching.

### Environment Variables
The application requires a `.env` file with the following keys:
*   `API_KEY`: Your key from "The Odds API".
*   `DATABASE_URL`: Connection string for the PostgreSQL database.

## Building and Running

### 1. Database Initialization
Before running the app, initialize the database schema:
```bash
python init_db.py
```

### 2. Running the Scheduler (Background Worker)
To start the continuous data collection process:
```bash
python scheduler.py
```
*Note: This process runs indefinitely, fetching new data every 30 minutes (configurable).*

### 3. Running the API
To start the web server:
```bash
python api.py
```
The API will be available at `http://0.0.0.0:8000`.
*   **Docs:** `http://localhost:8000/docs` (Swagger UI)
*   **Health Check:** `http://localhost:8000/health`

### 4. Testing
*   **API Tests:** Run `python test_api.py` to verify endpoints.
*   **Unit Tests:** (If available) typically run via `pytest` or similar, though specific test commands are not explicitly defined in `README.md`.

## Development Conventions
*   **Code Style:** Standard Python PEP 8.
*   **Database:** Uses raw SQL via `psycopg2` for most operations; the schema includes views for convenient querying (`active_ev_bets`).
*   **Deployment:** Configured for **Railway** using `Procfile` and `railway.json`.
*   **Stats Files:** The `stats/` directory contains critical CSVs that are often ignored by git (`.gitignore`). Ensure these are present for the application to function correctly.
