# Deployment Guide for Railway

This guide will help you deploy your EV betting application to Railway with PostgreSQL.

## Prerequisites

1. A Railway account (sign up at https://railway.app)
2. Your Odds API key from The Odds API
3. Git installed on your machine

## Step-by-Step Deployment

### 1. Prepare Your Local Environment

First, make sure you have a `.env` file locally for testing:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```
API_KEY=your_actual_odds_api_key
```

### 2. Install Railway CLI (Optional but Recommended)

```bash
npm i -g @railway/cli
railway login
```

### 3. Create a New Railway Project

**Option A: Using Railway Dashboard (Recommended for First Time)**

1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account and select your repository
5. Railway will automatically detect your Python app

**Option B: Using Railway CLI**

```bash
# In your project directory
railway init
railway link
```

### 4. Add PostgreSQL Database

1. In your Railway project dashboard, click "New" 
2. Select "Database" → "PostgreSQL"
3. Railway will automatically create a `DATABASE_URL` environment variable

### 5. Set Environment Variables

In Railway Dashboard:
1. Click on your service
2. Go to "Variables" tab
3. Add the following variable:
   - `API_KEY`: Your Odds API key

The `DATABASE_URL` is automatically set by Railway when you add PostgreSQL.

### 6. Initialize the Database

After your first deployment, you need to run the database initialization:

**Option A: Using Railway CLI**
```bash
railway run python init_db.py
```

**Option B: Temporarily modify scheduler.py**

Add this at the top of the `if __name__ == "__main__":` block:
```python
from init_db import init_database
init_database()
```

Then remove it after the first successful run.

### 7. Deploy

**If using GitHub:**
- Simply push your code to GitHub
- Railway will automatically deploy on each push to your main branch

**If using Railway CLI:**
```bash
railway up
```

### 8. Monitor Your Deployment

1. Go to your Railway dashboard
2. Click on your service
3. View logs in the "Deployments" tab
4. You should see the scheduler running and updating bets every 30 minutes

## Verify Deployment

You can verify your deployment is working by:

1. Checking the logs in Railway dashboard
2. Connecting to your PostgreSQL database and running:

```sql
-- Check if tables exist
\dt

-- View active bets
SELECT * FROM active_ev_bets LIMIT 10;

-- Get statistics
SELECT COUNT(*) as total_bets FROM ev_bets;
SELECT COUNT(*) as active_bets FROM ev_bets WHERE is_active = TRUE;
```

## Connect to Railway PostgreSQL Database

**Using Railway CLI:**
```bash
railway connect postgres
```

**Using psql directly:**
```bash
# Get the DATABASE_URL from Railway dashboard
psql "your_database_url_here"
```

**Using DBeaver, pgAdmin, or other GUI tools:**
- Get the connection details from Railway dashboard
- Host, Port, Database, User, and Password are in the DATABASE_URL

## Troubleshooting

### API Rate Limits
The Odds API has rate limits. Monitor your usage in the logs. You may want to:
- Adjust the schedule interval (currently 30 minutes)
- Reduce the number of bookmakers queried
- Limit markets to only what you need

### Database Connection Issues
If you see connection errors:
1. Verify `DATABASE_URL` is set in Railway variables
2. Make sure your PostgreSQL database is running
3. Check that `psycopg2-binary` is in requirements.txt

### Stats Files Missing
If you see errors about `stats/nfl_stats.csv` or `stats/nba_stats.csv`:
1. Make sure these files exist in your repository
2. Ensure the `stats/` directory is not in `.gitignore`
3. Update the file paths in `nfl_data.py` and `nba_data.py` if needed

### Memory Issues
If Railway runs out of memory:
1. Process fewer games at once
2. Upgrade your Railway plan
3. Optimize the data processing

## Customization

### Adjust Schedule
Edit `scheduler.py` line with `schedule.every(30).minutes.do(update_ev_bets)` to change frequency:

```python
schedule.every(15).minutes.do(update_ev_bets)  # Every 15 minutes
schedule.every(1).hours.do(update_ev_bets)     # Every hour
schedule.every().day.at("10:00").do(update_ev_bets)  # Daily at 10 AM
```

### Change EV Threshold
In `scheduler.py`, modify the threshold parameter in `find_plus_ev()`:

```python
ev_bets = game.find_plus_ev(
    ['underdog', 'prizepicks'], 
    ['fanduel', 'draftkings'], 
    0.03  # Change to 3% minimum EV
)
```

### Adjust Bet Retention
In `scheduler.py`, change how long bets stay active:

```python
db.deactivate_old_bets(hours=48)  # Keep bets active for 48 hours
```

## Next Steps

Consider adding:
1. **Web Dashboard**: Create a Flask/FastAPI app to view bets
2. **Notifications**: Send alerts for high-EV bets via email/SMS
3. **Analytics**: Track historical performance
4. **Multiple Sports**: Extend to more sports beyond NFL/NBA
5. **Bet Tracking**: Track which bets you placed and their outcomes

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- The Odds API Docs: https://the-odds-api.com/liveapi/guides/v4/

