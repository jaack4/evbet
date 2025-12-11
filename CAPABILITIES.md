# propEV Capabilities Document

## What This Application Can Do

### Core Functionality

#### 1. **Odds Collection & Analysis**
- ✅ Fetches live odds from The Odds API for NFL and NBA games
- ✅ Supports multiple bookmakers:
  - **Sharp Books** (for true probability): FanDuel, DraftKings, BetMGM
  - **Soft Books** (for betting opportunities): PrizePicks, Underdog
- ✅ Updates odds automatically every 15-30 minutes (configurable)
- ✅ Looks ahead 7 days for NFL and 2 days for NBA events

#### 2. **Statistical Analysis**
- ✅ Removes bookmaker vig using multiplicative devigging method
- ✅ Calculates "true" probabilities from sharp bookmaker odds
- ✅ Uses historical player statistics (standard deviation) for accurate probability models
- ✅ Employs normal distribution for probability calculations
- ✅ Backs out implied means from sharp book lines

#### 3. **Expected Value (EV) Calculation**
- ✅ Identifies positive EV betting opportunities
- ✅ Compares soft book odds against sharp book "true" probabilities
- ✅ Calculates EV percentage for each bet
- ✅ Filters out unrealistic bets (>75% EV likely data errors)
- ✅ Customizable EV threshold (default: 0% to show all positive EV)

#### 4. **Data Storage & Management**
- ✅ Stores all data in PostgreSQL database
- ✅ Tracks games: teams, commence time, sport
- ✅ Stores EV bets with full details:
  - Player, market, outcome, betting line
  - Sharp mean, mean difference
  - EV percentage, price, true probability
  - Active/inactive status
- ✅ Auto-deactivates old bets each update cycle
- ✅ Maintains historical bet records

#### 5. **REST API**
- ✅ FastAPI-based web service
- ✅ Multiple endpoints for querying bets:
  - `/bets` - Get all active bets with advanced filtering
  - `/bets/by-bookmaker/{bookmaker}` - Filter by bookmaker
  - `/bets/stats` - Get aggregate statistics
  - `/bets/bookmakers` - List available bookmakers
  - `/bets/markets` - List available markets
- ✅ Rich filtering options:
  - By bookmaker (PrizePicks or Underdog)
  - By sport (NFL or NBA)
  - By player name (partial match)
  - By market type (passing yards, points, etc.)
  - By EV range (min/max percentage)
  - Result limit control
- ✅ CORS-enabled for frontend integration
- ✅ Interactive Swagger UI documentation at `/docs`
- ✅ Health check endpoint at `/health`

#### 6. **Supported Markets**

**NFL Markets:**
- Player passing yards
- Player rushing yards
- Player receptions

**NBA Markets:**
- Player points
- Player rebounds
- Player assists

#### 7. **Deployment & Operations**
- ✅ Configured for Railway deployment
- ✅ Environment variable configuration (DATABASE_URL, API_KEY)
- ✅ Automatic database initialization
- ✅ Continuous background scheduling
- ✅ Error handling and logging
- ✅ Graceful startup and shutdown

### What You Can Query

#### Get All High-Value Bets
```bash
curl "http://localhost:8000/bets?min_ev=5.0"
```

#### Get PrizePicks-Specific Opportunities
```bash
curl "http://localhost:8000/bets?bookmaker=prizepicks&limit=50"
```

#### Find Bets for Specific Player
```bash
curl "http://localhost:8000/bets?player=mahomes"
```

#### Get NFL Passing Yards Bets
```bash
curl "http://localhost:8000/bets?sport=NFL&market=player_pass_yds"
```

#### View Statistics
```bash
curl "http://localhost:8000/bets/stats"
```

### Database Queries

The application provides a clean database schema you can query directly:

```sql
-- View all active bets
SELECT * FROM active_ev_bets ORDER BY ev_percent DESC;

-- Get average EV by market
SELECT market, AVG(ev_percent) as avg_ev, COUNT(*) as bet_count
FROM ev_bets 
WHERE is_active = TRUE
GROUP BY market;

-- Find top players by EV opportunity count
SELECT player, COUNT(*) as opportunity_count, AVG(ev_percent) as avg_ev
FROM ev_bets
WHERE is_active = TRUE
GROUP BY player
ORDER BY opportunity_count DESC;
```

## Configuration Options

### Adjustable Parameters

1. **Update Frequency**: Change how often odds are refreshed (default: 15 minutes)
2. **EV Threshold**: Set minimum EV percentage to record (default: 0%)
3. **Bookmaker Selection**: Choose which sharp and soft books to compare
4. **Market Selection**: Pick which betting markets to analyze
5. **Look-Ahead Window**: Configure how far into future to fetch games (NFL: 7 days, NBA: 2 days)

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `API_KEY`: The Odds API key
- `UPDATE_INTERVAL_MINUTES`: How often to update (default: 15)

## Technical Capabilities

### Languages & Frameworks
- Python 3.10+
- FastAPI for REST API
- Pandas for data manipulation
- NumPy & SciPy for statistical calculations
- psycopg2 for PostgreSQL connectivity
- Schedule library for job scheduling

### Data Science
- Normal distribution probability modeling
- Multiplicative vig removal
- Standard deviation-based projections
- Implied probability calculations
- Expected value optimization

### Architecture
- Clean separation of concerns (data, logic, API, scheduling)
- Context-managed database connections
- RESTful API design
- Scheduled background workers
- Stateless API for easy scaling

## Limitations & Future Enhancements

### Current Limitations
- ❌ No real-time notifications for high-EV opportunities
- ❌ No bet tracking (placing bets, recording outcomes)
- ❌ No web dashboard/UI (only API)
- ❌ No historical performance analytics
- ❌ No machine learning models
- ❌ No correlation analysis for parlays
- ❌ No email/SMS alerts
- ❌ Limited to NFL and NBA
- ❌ Depends on The Odds API rate limits (500 requests/month free tier)

### Planned Enhancements
See README.md "Future Enhancements" section for the roadmap.

## Use Cases

### 1. Value Betting
Find and exploit pricing discrepancies between soft and sharp bookmakers.

### 2. Market Research
Analyze which markets consistently offer value on which platforms.

### 3. Player Props Analysis
Study how different bookmakers price the same player props.

### 4. Arbitrage Detection
Identify opportunities where bookmakers significantly disagree on player performance.

### 5. Portfolio Management
Build a diversified betting portfolio based on positive EV opportunities.

### 6. API Integration
Integrate with your own tools, dashboards, or automated betting systems.

## Support & Documentation

- **API Documentation**: `/docs` endpoint (Swagger UI)
- **Setup Guide**: README.md
- **Deployment Guide**: DEPLOYMENT.md
- **API Reference**: API_README.md
- **Quick Start**: QUICKSTART.md
- **This Document**: Overview of capabilities

## Questions This App Answers

1. **What bets have positive expected value right now?**
   - Query the API or database for active bets sorted by EV

2. **How much value is available on PrizePicks vs Underdog?**
   - Use the `/bets/bookmakers` endpoint to compare

3. **Which players have the most +EV opportunities?**
   - Query the database grouping by player

4. **What's the average EV I can expect to find?**
   - Use the `/bets/stats` endpoint

5. **Which markets are most profitable?**
   - Query by market and analyze average EV

6. **How reliable are the probabilities?**
   - Based on sharp book consensus (FanDuel + DraftKings) + historical stats

7. **When do bets become inactive?**
   - Automatically deactivated each update cycle to show only current odds

8. **Can I automate bet placement?**
   - Not currently, but API provides all data needed for integration

## Getting Help

If you need assistance:
1. Check the documentation files (README.md, API_README.md, etc.)
2. Review the `/docs` endpoint for API usage
3. Examine the logs for error messages
4. Verify environment variables are set correctly
5. Ensure database is initialized (`python init_db.py`)
6. Check The Odds API rate limits and quota

## Disclaimer

This tool provides information for educational purposes. Always gamble responsibly, verify all information independently, and be aware of laws in your jurisdiction. Past performance does not guarantee future results.
