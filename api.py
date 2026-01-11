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
API_KEY = os.getenv("MY_API_KEY")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

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
    betr = "betr_us_dfs"
    pick6 = "pick6"

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

class HistoricalBet(BaseModel):
    # All existing EVBet fields
    id: int
    bookmaker: str
    market: str
    player: str
    outcome: str
    betting_line: float
    sharp_mean: float
    ev_percent: float
    price: float
    true_prob: float
    sport_title: str
    home_team: str
    away_team: str
    commence_time: datetime
    created_at: datetime
    
    # Historical outcome fields
    win: bool
    actual_value: Optional[float] = None
    prediction_diff: Optional[float] = None  # actual_value - sharp_mean
    
    class Config:
        from_attributes = True

class PaginatedHistoricalBets(BaseModel):
    bets: List[HistoricalBet]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class HitRateBreakdown(BaseModel):
    category: str  # e.g., "prizepicks", "NFL", "player_pass_yds"
    total_bets: int
    wins: int
    losses: int
    hit_rate: float  # percentage

class HitRateStatistics(BaseModel):
    overall: HitRateBreakdown
    by_bookmaker: List[HitRateBreakdown]
    by_sport: List[HitRateBreakdown]
    by_market: List[HitRateBreakdown]

@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "EV Betting API",
        "version": "1.0.0",
        "endpoints": {
            "/bets": "Get active EV bets",
            "/bets/stats": "Get betting statistics",
            "/bets/historical": "Get historical (completed) bets with pagination",
            "/bets/hitrate": "Get comprehensive hit rate statistics",
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
        description="Filter by bookmaker (prizepicks, underdog, betr, or pick6)"
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
    
    - **bookmaker**: Filter by specific bookmaker (prizepicks, underdog, betr, or pick6)
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
    
    - **bookmaker**: prizepicks, underdog, betr, or pick6
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

@app.get("/bets/historical", response_model=PaginatedHistoricalBets)
def get_historical_bets(
    api_key: str = Depends(verify_api_key),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    bookmaker: Optional[Bookmaker] = Query(None, description="Filter by bookmaker"),
    sport: Optional[str] = Query(None, description="Filter by sport"),
    market: Optional[str] = Query(None, description="Filter by market"),
    win: Optional[bool] = Query(None, description="Filter by outcome (true=wins, false=losses)")
):
    """
    Get historical (completed) bets with pagination
    
    - Historical bets are those where win IS NOT NULL
    - Returns bet details plus outcome information
    - Supports filtering by bookmaker, sport, market, and win/loss
    """
    try:
        with Database() as db:
            with db.conn.cursor() as cur:
                # Build count query
                count_query = """
                    SELECT COUNT(*)
                    FROM ev_bets eb
                    JOIN games g ON eb.game_id = g.id
                    WHERE eb.win IS NOT NULL
                """
                count_params = []
                
                # Build main query
                main_query = """
                    SELECT 
                        eb.id,
                        eb.bookmaker,
                        eb.market,
                        eb.player,
                        eb.outcome,
                        eb.betting_line,
                        eb.sharp_mean,
                        eb.ev_percent,
                        eb.price,
                        eb.true_prob,
                        eb.home_team,
                        eb.away_team,
                        eb.commence_time,
                        eb.created_at,
                        eb.win,
                        eb.actual_value,
                        (eb.actual_value - eb.sharp_mean) as prediction_diff,
                        g.sport_title
                    FROM ev_bets eb
                    JOIN games g ON eb.game_id = g.id
                    WHERE eb.win IS NOT NULL
                """
                main_params = []
                
                # Add bookmaker filter
                if bookmaker:
                    filter_clause = " AND eb.bookmaker = %s"
                    count_query += filter_clause
                    main_query += filter_clause
                    count_params.append(bookmaker.value)
                    main_params.append(bookmaker.value)
                
                # Add sport filter
                if sport:
                    filter_clause = " AND UPPER(g.sport_title) LIKE UPPER(%s)"
                    count_query += filter_clause
                    main_query += filter_clause
                    sport_param = f"%{sport}%"
                    count_params.append(sport_param)
                    main_params.append(sport_param)
                
                # Add market filter
                if market:
                    filter_clause = " AND eb.market = %s"
                    count_query += filter_clause
                    main_query += filter_clause
                    count_params.append(market)
                    main_params.append(market)
                
                # Add win filter
                if win is not None:
                    filter_clause = " AND eb.win = %s"
                    count_query += filter_clause
                    main_query += filter_clause
                    count_params.append(win)
                    main_params.append(win)
                
                # Get total count
                cur.execute(count_query, count_params)
                total_count = cur.fetchone()[0]
                
                # Calculate pagination
                total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
                offset = (page - 1) * page_size
                
                # Add ordering and pagination to main query
                main_query += " ORDER BY eb.commence_time DESC LIMIT %s OFFSET %s"
                main_params.extend([page_size, offset])
                
                # Execute main query
                cur.execute(main_query, main_params)
                results = cur.fetchall()
                
                # Convert to list of dictionaries
                bets = [dict(row) for row in results]
                
                return PaginatedHistoricalBets(
                    bets=bets,
                    total_count=total_count,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages
                )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/bets/hitrate", response_model=HitRateStatistics)
def get_hitrate_statistics(
    api_key: str = Depends(verify_api_key),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering")
):
    """
    Get comprehensive hit rate statistics
    
    - Overall hit rate across all completed bets
    - Breakdown by bookmaker (prizepicks, underdog, etc.)
    - Breakdown by sport (NFL, NBA)
    - Breakdown by market (player_pass_yds, player_points, etc.)
    - Optional date range filtering
    """
    try:
        with Database() as db:
            with db.conn.cursor() as cur:
                # Build base WHERE clause with date filtering
                base_where = "WHERE eb.win IS NOT NULL"
                date_params = []
                
                if start_date:
                    base_where += " AND eb.commence_time >= %s"
                    date_params.append(start_date)
                
                if end_date:
                    base_where += " AND eb.commence_time <= %s"
                    date_params.append(end_date)
                
                # Query 1: Overall hit rate
                overall_query = f"""
                    SELECT 
                        COUNT(*) as total_bets,
                        SUM(CASE WHEN win = TRUE THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN win = FALSE THEN 1 ELSE 0 END) as losses
                    FROM ev_bets eb
                    {base_where}
                """
                cur.execute(overall_query, date_params)
                overall_result = cur.fetchone()
                
                overall_total = overall_result['total_bets'] or 0
                overall_wins = overall_result['wins'] or 0
                overall_losses = overall_result['losses'] or 0
                overall_hit_rate = (overall_wins / overall_total * 100) if overall_total > 0 else 0.0
                
                overall = HitRateBreakdown(
                    category="Overall",
                    total_bets=overall_total,
                    wins=overall_wins,
                    losses=overall_losses,
                    hit_rate=round(overall_hit_rate, 2)
                )
                
                # Query 2: By bookmaker
                bookmaker_query = f"""
                    SELECT 
                        bookmaker as category,
                        COUNT(*) as total_bets,
                        SUM(CASE WHEN win = TRUE THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN win = FALSE THEN 1 ELSE 0 END) as losses
                    FROM ev_bets eb
                    {base_where}
                    GROUP BY bookmaker
                    ORDER BY total_bets DESC
                """
                cur.execute(bookmaker_query, date_params)
                bookmaker_results = cur.fetchall()
                
                by_bookmaker = []
                for row in bookmaker_results:
                    total = row['total_bets'] or 0
                    wins = row['wins'] or 0
                    losses = row['losses'] or 0
                    hit_rate = (wins / total * 100) if total > 0 else 0.0
                    
                    by_bookmaker.append(HitRateBreakdown(
                        category=row['category'],
                        total_bets=total,
                        wins=wins,
                        losses=losses,
                        hit_rate=round(hit_rate, 2)
                    ))
                
                # Query 3: By sport
                sport_query = f"""
                    SELECT 
                        g.sport_title as category,
                        COUNT(*) as total_bets,
                        SUM(CASE WHEN eb.win = TRUE THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN eb.win = FALSE THEN 1 ELSE 0 END) as losses
                    FROM ev_bets eb
                    JOIN games g ON eb.game_id = g.id
                    {base_where}
                    GROUP BY g.sport_title
                    ORDER BY total_bets DESC
                """
                cur.execute(sport_query, date_params)
                sport_results = cur.fetchall()
                
                by_sport = []
                for row in sport_results:
                    total = row['total_bets'] or 0
                    wins = row['wins'] or 0
                    losses = row['losses'] or 0
                    hit_rate = (wins / total * 100) if total > 0 else 0.0
                    
                    by_sport.append(HitRateBreakdown(
                        category=row['category'],
                        total_bets=total,
                        wins=wins,
                        losses=losses,
                        hit_rate=round(hit_rate, 2)
                    ))
                
                # Query 4: By market
                market_query = f"""
                    SELECT 
                        market as category,
                        COUNT(*) as total_bets,
                        SUM(CASE WHEN win = TRUE THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN win = FALSE THEN 1 ELSE 0 END) as losses
                    FROM ev_bets eb
                    {base_where}
                    GROUP BY market
                    ORDER BY total_bets DESC
                """
                cur.execute(market_query, date_params)
                market_results = cur.fetchall()
                
                by_market = []
                for row in market_results:
                    total = row['total_bets'] or 0
                    wins = row['wins'] or 0
                    losses = row['losses'] or 0
                    hit_rate = (wins / total * 100) if total > 0 else 0.0
                    
                    by_market.append(HitRateBreakdown(
                        category=row['category'],
                        total_bets=total,
                        wins=wins,
                        losses=losses,
                        hit_rate=round(hit_rate, 2)
                    ))
                
                return HitRateStatistics(
                    overall=overall,
                    by_bookmaker=by_bookmaker,
                    by_sport=by_sport,
                    by_market=by_market
                )
    
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






