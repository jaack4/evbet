# Setup Summary

This document summarizes all the files created for your Railway deployment.

## Files Created

### Core Application Files
- `database.py` - PostgreSQL database operations
- `scheduler.py` - Main scheduler that runs continuously and updates bets
- `query_bets.py` - Utility to view EV bets from command line

### Database Files
- `schema.sql` - Database schema (tables, indexes, views)
- `init_db.py` - Script to initialize database

### Deployment Files
- `requirements.txt` - Python dependencies
- `Procfile` - Tells Railway how to run your app
- `railway.json` - Railway configuration
- `env.template` - Template for environment variables

### Documentation
- `README.md` - Complete project documentation
- `DEPLOYMENT.md` - Detailed deployment guide
- `QUICKSTART.md` - Quick start guide (10 minutes to deploy)
- `SETUP_SUMMARY.md` - This file

## What You Need to Do Next

### 1. Prepare Your Repository

Check that these files exist and have data:
```
stats/nfl_stats.csv
stats/nba_stats.csv
```

If these are in `.gitignore`, either:
- Remove them from `.gitignore` and commit them, OR
- Plan to upload them manually to Railway, OR  
- Modify the paths in `nfl_data.py` and `nba_data.py`

### 2. Push to GitHub

```bash
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

### 3. Deploy to Railway

**Quick Version:**
1. Go to https://railway.app/dashboard
2. New Project → Deploy from GitHub → Select your repo
3. Add Database → PostgreSQL
4. Set Variables → Add `API_KEY`
5. Run `railway run python init_db.py`

**Detailed Version:**
- Follow `QUICKSTART.md` for step-by-step instructions
- Follow `DEPLOYMENT.md` for in-depth guide

### 4. Verify Deployment

```bash
# Check logs
railway logs

# Initialize database (if not done)
railway run python init_db.py

# View bets
railway run python query_bets.py

# Connect to database
railway connect postgres
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Railway Platform                   │
│                                                      │
│  ┌────────────────┐         ┌──────────────────┐   │
│  │  Python Worker │────────▶│   PostgreSQL     │   │
│  │  (scheduler.py)│         │    Database      │   │
│  └────────────────┘         └──────────────────┘   │
│         │                                            │
│         │ Every 30 minutes                          │
│         ▼                                            │
│  ┌────────────────┐                                 │
│  │  The Odds API  │                                 │
│  └────────────────┘                                 │
└─────────────────────────────────────────────────────┘
```

### Flow:
1. `scheduler.py` runs continuously
2. Every 30 minutes, it:
   - Fetches upcoming NFL/NBA games
   - Gets odds from multiple bookmakers
   - Calculates true probabilities using stats
   - Finds +EV betting opportunities
   - Stores results in PostgreSQL
3. You can query bets anytime via `query_bets.py` or SQL

## Environment Variables Needed

### Required:
- `API_KEY` - Your Odds API key (get from https://the-odds-api.com)
- `DATABASE_URL` - PostgreSQL connection (auto-set by Railway)

### Optional:
None at this time, but you could add:
- `UPDATE_INTERVAL_MINUTES` - Override default 30-minute interval
- `EV_THRESHOLD` - Override default 0% threshold
- `ALERT_EMAIL` - For future email notifications

## Database Schema

### Tables:
1. **games** - Stores game information
2. **ev_bets** - Stores all EV betting opportunities

### Views:
1. **active_ev_bets** - Shows only active bets with game info

### Key Features:
- Automatic deactivation of old bets
- Indexes for fast queries
- Cascade delete (when game deleted, bets deleted)

## Resource Usage Estimates

### Railway (Free Tier: $5/month credit)
- PostgreSQL: ~$0.20/day = ~$6/month
- Python Worker: ~$0.02/day = ~$0.60/month
- **Total**: ~$6.60/month (exceeds free tier by ~$1.60)

### The Odds API
- Free tier: 500 requests/month
- Each game = 1 request
- Running every 30 minutes with 10 games = 480 requests/day
- **You'll need a paid plan** (Hobby: $10/month for 10K requests)

### Optimization Tips:
1. **Reduce frequency**: Run every hour instead of 30 minutes
2. **Limit markets**: Only query markets you use
3. **Fewer bookmakers**: Remove bookmakers you don't use
4. **Time windows**: Only query games in next 48 hours

## Testing Locally First

Before deploying to Railway, test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set up local PostgreSQL
# Create database: createdb evbet

# Create .env file
cp env.template .env
# Edit .env with your API_KEY and local DATABASE_URL

# Initialize database
python init_db.py

# Run scheduler (will run continuously)
python scheduler.py

# In another terminal, check results
python query_bets.py
```

## Troubleshooting Checklist

- [ ] `requirements.txt` exists with all dependencies
- [ ] `.env` is in `.gitignore` (yes, line 141)
- [ ] `env.template` exists for reference
- [ ] Stats files exist or are handled
- [ ] API_KEY is set in Railway
- [ ] DATABASE_URL is set by Railway
- [ ] Database initialized with `init_db.py`
- [ ] Logs show successful updates
- [ ] No rate limit errors from API

## Useful Commands

```bash
# Railway CLI commands
railway login                     # Login to Railway
railway init                      # Initialize project
railway link                      # Link to existing project
railway run python init_db.py    # Initialize database
railway run python query_bets.py # View bets
railway logs                      # View logs
railway connect postgres          # Connect to database
railway variables                 # View environment variables
railway variables set KEY=value   # Set variable
railway status                    # Check deployment status

# Local testing
python init_db.py                 # Initialize local database
python scheduler.py               # Run scheduler locally
python query_bets.py             # Query bets locally

# Database queries (in psql)
\dt                              # List tables
\d+ games                        # Describe games table
SELECT * FROM active_ev_bets LIMIT 10;
SELECT COUNT(*) FROM ev_bets WHERE is_active = TRUE;
```

## Next Steps After Deployment

1. **Monitor for 24 hours**
   - Check logs regularly
   - Verify bets are being found
   - Monitor API usage

2. **Optimize if needed**
   - Adjust update frequency
   - Modify EV threshold
   - Fine-tune markets

3. **Build additional features**
   - Web dashboard to view bets
   - Email/SMS notifications
   - Bet result tracking
   - Performance analytics

4. **Scale up**
   - Add more sports
   - Improve statistical models
   - Add correlation analysis
   - Build mobile app

## Support Resources

- **Railway**: https://docs.railway.app
- **The Odds API**: https://the-odds-api.com/liveapi/guides/v4/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Python Schedule**: https://schedule.readthedocs.io/

## Files You May Want to Customize

- `scheduler.py` - Update frequency, thresholds, bookmakers
- `get_data.py` - Markets, bookmakers, date ranges
- `Game.py` - EV calculation logic, devigging method
- `schema.sql` - Add custom tables/views

## Important Reminders

1. **This is a worker, not a web service** - It runs in the background continuously
2. **Stats files must be current** - Old data = inaccurate predictions
3. **API costs money beyond free tier** - Monitor your usage
4. **EV ≠ guaranteed profit** - Variance is real, manage your bankroll
5. **Laws vary by location** - Know your local gambling laws

---

**You're all set!** Follow the QUICKSTART.md guide to get deployed in 10 minutes.

Good luck finding those +EV bets!

