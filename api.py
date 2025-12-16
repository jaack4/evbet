import os
from datetime import datetime
from typing import Optional, List
from enum import Enum
from fastapi import FastAPI, HTTPException, Query, Security, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from database import Database

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="EV Betting API",
    description="API for retrieving Expected Value (EV) betting opportunities",
    version="1.0.0"
)

# API Key Security
API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify the API key from request headers"""
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured")
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Configure CORS - Update with your website domain
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# Enum for bookmaker filtering
class Bookmaker(str, Enum):
    prizepicks = "prizepicks"
    underdog = "underdog"

# Pydantic models for response
class EVBet(BaseModel):
    id: int
    bookmaker: str
    market: str
    player: str
    outcome: str
    betting_line: float
    sharp_mean: float
    std_dev: Optional[float] = None
    implied_means: Optional[dict] = None
    sample_size: Optional[int] = None
    mean_diff: float
    ev_percent: float
    price: float
    true_prob: float
    created_at: datetime
    sport_title: str
    home_team: str
    away_team: str
    commence_time: datetime

    class Config:
        from_attributes = True

class BetStatistics(BaseModel):
    total_bets: int
    active_bets: int
    avg_ev_percent: Optional[float] = None
    max_ev_percent: Optional[float] = None
    oldest_bet: Optional[datetime] = None
    newest_bet: Optional[datetime] = None

@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "EV Betting API",
        "version": "1.0.0",
        "endpoints": {
            "/bets": "Get active EV bets",
            "/bets/stats": "Get betting statistics",
            "/health": "Health check"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        with Database() as db:
            with db.conn.cursor() as cur:
                cur.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.get("/bets", response_model=List[EVBet])
def get_active_bets(
    api_key: str = Depends(verify_api_key),
    bookmaker: Optional[Bookmaker] = Query(
        None, 
        description="Filter by bookmaker (prizepicks or underdog)"
    ),
    sport: Optional[str] = Query(
        None,
        description="Filter by sport (e.g., 'NFL', 'NBA')"
    ),
    min_ev: Optional[float] = Query(
        None,
        description="Minimum EV percentage",
        ge=0
    ),
    max_ev: Optional[float] = Query(
        None,
        description="Maximum EV percentage"
    ),
    player: Optional[str] = Query(
        None,
        description="Filter by player name (partial match)"
    ),
    market: Optional[str] = Query(
        None,
        description="Filter by market type (e.g., 'player_pass_yds')"
    ),
    limit: int = Query(
        100,
        description="Maximum number of results to return",
        ge=1,
        le=500
    )
):
    """
    Get active EV bets with optional filtering
    
    - **bookmaker**: Filter by specific bookmaker (prizepicks or underdog)
    - **sport**: Filter by sport title
    - **min_ev**: Minimum EV percentage threshold
    - **max_ev**: Maximum EV percentage threshold
    - **player**: Filter by player name (case-insensitive partial match)
    - **market**: Filter by market type
    - **limit**: Maximum number of results (default: 100, max: 500)
    """
    try:
        with Database() as db:
            with db.conn.cursor() as cur:
                # Build dynamic query with filters
                query = """
                    SELECT eb.*, g.sport_title
                    FROM ev_bets eb
                    JOIN games g ON eb.game_id = g.id
                    WHERE eb.is_active = TRUE
                """
                params = []
                
                # Add bookmaker filter
                if bookmaker:
                    query += " AND eb.bookmaker = %s"
                    params.append(bookmaker.value)
                
                # Add sport filter
                if sport:
                    query += " AND UPPER(g.sport_title) LIKE UPPER(%s)"
                    params.append(f"%{sport}%")
                
                # Add minimum EV filter
                if min_ev is not None:
                    query += " AND eb.ev_percent >= %s"
                    params.append(min_ev)
                
                # Add maximum EV filter
                if max_ev is not None:
                    query += " AND eb.ev_percent <= %s"
                    params.append(max_ev)
                
                # Add player filter
                if player:
                    query += " AND UPPER(eb.player) LIKE UPPER(%s)"
                    params.append(f"%{player}%")
                
                # Add market filter
                if market:
                    query += " AND eb.market = %s"
                    params.append(market)
                
                # Add ordering and limit
                query += " ORDER BY eb.ev_percent DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                results = cur.fetchall()
                
                # Convert to list of dictionaries
                bets = []
                for row in results:
                    bet = dict(row)
                    if bet.get('implied_means') and isinstance(bet['implied_means'], list):
                        bet['implied_means'] = {
                            item['bookmaker']: item['implied_mean'] 
                            for item in bet['implied_means']
                        }
                    bets.append(bet)
                
                return bets
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/bets/by-bookmaker/{bookmaker}", response_model=List[EVBet])
def get_bets_by_bookmaker(
    bookmaker: Bookmaker,
    api_key: str = Depends(verify_api_key),
    limit: int = Query(
        100,
        description="Maximum number of results to return",
        ge=1,
        le=500
    )
):
    """
    Get active EV bets for a specific bookmaker
    
    - **bookmaker**: prizepicks or underdog
    - **limit**: Maximum number of results (default: 100, max: 500)
    """
    try:
        with Database() as db:
            with db.conn.cursor() as cur:
                cur.execute("""
                    SELECT eb.*, g.sport_title
                    FROM ev_bets eb
                    JOIN games g ON eb.game_id = g.id
                    WHERE eb.is_active = TRUE AND eb.bookmaker = %s
                    ORDER BY eb.ev_percent DESC
                    LIMIT %s
                """, (bookmaker.value, limit))
                
                results = cur.fetchall()
                bets = []
                for row in results:
                    bet = dict(row)
                    
                    if bet.get('implied_means') and isinstance(bet['implied_means'], list):
                        bet['implied_means'] = {
                            item['bookmaker']: item['implied_mean'] 
                            for item in bet['implied_means']
                        }
                    bets.append(bet)
                return bets
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/bets/stats", response_model=BetStatistics)
def get_bet_statistics(api_key: str = Depends(verify_api_key)):
    """
    Get statistics about stored bets
    
    Returns aggregate statistics including:
    - Total number of bets
    - Number of active bets
    - Average EV percentage
    - Maximum EV percentage
    - Timestamp of oldest and newest bets
    """
    try:
        with Database() as db:
            stats = db.get_bet_statistics()
            return BetStatistics(**stats)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/bets/bookmakers")
def get_available_bookmakers(api_key: str = Depends(verify_api_key)):
    """
    Get list of available bookmakers in the database
    """
    try:
        with Database() as db:
            with db.conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT bookmaker, COUNT(*) as bet_count
                    FROM ev_bets
                    WHERE is_active = TRUE
                    GROUP BY bookmaker
                    ORDER BY bet_count DESC
                """)
                results = cur.fetchall()
                bookmakers = [dict(row) for row in results]
                return {"bookmakers": bookmakers}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/bets/markets")
def get_available_markets(api_key: str = Depends(verify_api_key)):
    """
    Get list of available markets in the database
    """
    try:
        with Database() as db:
            with db.conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT market, COUNT(*) as bet_count
                    FROM ev_bets
                    WHERE is_active = TRUE
                    GROUP BY market
                    ORDER BY bet_count DESC
                """)
                results = cur.fetchall()
                markets = [dict(row) for row in results]
                return {"markets": markets}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("ERROR: DATABASE_URL environment variable is not set!")
        print("Please set it in your .env file")
        exit(1)
    
    # Run the API server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )






