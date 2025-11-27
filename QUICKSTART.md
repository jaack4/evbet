# Quick Start Guide

Get your EV betting application running on Railway in under 10 minutes.

## Before You Start

You'll need:
1. A Railway account (free): https://railway.app
2. An Odds API key (500 free requests/month): https://the-odds-api.com
3. Git installed locally

## Step 1: Clone and Test Locally (Optional)

```bash
# Clone your repository
git clone <your-repo-url>
cd evbet

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp env.template .env

# Edit .env and add your API key
# You can skip DATABASE_URL for now
```

**Important Note**: Your `stats/nfl_stats.csv` and `stats/nba_stats.csv` files are in `.gitignore`. 
Make sure these files exist and contain player statistics, or update `.gitignore` to commit them.

## Step 2: Deploy to Railway

### Using Railway Dashboard (Easiest)

1. **Create Project**
   - Go to https://railway.app/dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your repository
   - Select your `evbet` repository

2. **Add PostgreSQL**
   - In your project, click "+ New"
   - Select "Database" → "PostgreSQL"
   - Wait for it to deploy

3. **Set Environment Variables**
   - Click on your Python service (not the database)
   - Go to "Variables" tab
   - Click "+ New Variable"
   - Add: `API_KEY` = `your_odds_api_key`
   - The `DATABASE_URL` is automatically set by Railway

4. **Deploy**
   - Railway automatically deploys when you push to GitHub
   - Or click "Deploy" in the dashboard

### Using Railway CLI (Alternative)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to a new project
railway link

# Add PostgreSQL
# (Do this in the Railway dashboard: New → Database → PostgreSQL)

# Set environment variables
railway variables set API_KEY=your_odds_api_key

# Deploy
railway up
```

## Step 3: Initialize Database

**Option A: Via Railway CLI**
```bash
railway run python init_db.py
```

**Option B: Via Railway Dashboard**
1. Go to your service in Railway dashboard
2. Click "Settings" → "Deploy Triggers"
3. Temporarily change "Start Command" to: `python init_db.py`
4. Wait for deployment to complete
5. Change it back to: `python scheduler.py`

## Step 4: Verify It's Working

### Check Logs
1. Go to Railway dashboard
2. Click on your service
3. View "Deployments" tab
4. Click latest deployment to see logs

You should see:
```
Starting EV Bet Update...
Found X NFL events
Found Y NBA events
Database Statistics: ...
```

### Check Database
```bash
# Connect to database
railway connect postgres

# View tables
\dt

# Check for bets
SELECT COUNT(*) FROM ev_bets;
SELECT * FROM active_ev_bets LIMIT 5;

# Exit
\q
```

## Step 5: Query Your Bets

```bash
# View top EV bets
railway run python query_bets.py
```

Or connect with a database GUI:
- Get connection URL from Railway dashboard
- Use pgAdmin, DBeaver, or TablePlus
- Run SQL queries directly

## Common Issues

### "Stats file not found"
Your `stats/nfl_stats.csv` and `stats/nba_stats.csv` are in `.gitignore`.
Either:
1. Remove them from `.gitignore` and commit them
2. Upload them manually to Railway
3. Update the file paths in `nfl_data.py` and `nba_data.py`

### "API rate limit exceeded"
The free tier has 500 requests/month. Each game queried counts as 1 request.
- Reduce update frequency in `scheduler.py`
- Limit markets to only what you need
- Query fewer bookmakers

### "No EV bets found"
This is normal! EV opportunities are not always available.
- Try lowering the threshold (change `0` to `-0.02` in `scheduler.py`)
- Check that your stats files have current player data
- Verify markets match between API and your stats

### Database connection failed
- Verify PostgreSQL is running in Railway dashboard
- Check that `DATABASE_URL` is set in environment variables
- Make sure you ran `init_db.py`

## Next Steps

### 1. Customize Your Settings

Edit `scheduler.py`:
```python
# Change update frequency
schedule.every(60).minutes.do(update_ev_bets)  # Every hour

# Change EV threshold
ev_bets = game.find_plus_ev(..., threshold=0.03)  # 3% minimum

# Change bet retention
db.deactivate_old_bets(hours=48)  # Keep for 48 hours
```

### 2. Monitor Your Bets

**View in terminal:**
```bash
railway run python query_bets.py
```

**View in database:**
```bash
railway connect postgres
```

```sql
-- Top 10 EV bets
SELECT player, market, outcome, betting_line, ev_percent, bookmaker
FROM active_ev_bets 
ORDER BY ev_percent DESC 
LIMIT 10;

-- Upcoming game bets
SELECT * FROM active_ev_bets 
WHERE commence_time > NOW() 
ORDER BY commence_time, ev_percent DESC;

-- Stats by bookmaker
SELECT bookmaker, COUNT(*), AVG(ev_percent) 
FROM ev_bets 
WHERE is_active = TRUE 
GROUP BY bookmaker;
```

### 3. Add More Features

Consider building:
- Web dashboard (Flask/FastAPI)
- Email alerts for high-EV bets
- Bet tracking and results
- Historical performance analysis
- Mobile app integration

## Cost Estimate

**Railway Free Tier:**
- $5 credit/month
- PostgreSQL: ~$0.20/day (~$6/month)
- Worker: ~$0.02/day (~$0.60/month)

**The Odds API:**
- Free: 500 requests/month
- Hobby: $10/month for 10,000 requests

**Total Cost:**
- Free tier: May exceed Railway free credit after ~20 days
- Recommended: ~$7-10/month for Railway + API

## Support

- Railway Docs: https://docs.railway.app
- The Odds API Docs: https://the-odds-api.com/liveapi/guides/v4/
- Railway Discord: https://discord.gg/railway

## Important Notes

**Gambling Responsibly:**
This tool is for educational purposes. Positive EV doesn't guarantee profit in the short term due to variance. Always:
- Bet within your means
- Understand the risks
- Be aware of laws in your jurisdiction
- Track your results

**Data Accuracy:**
- Stats files must be current
- Historical variance may not predict future performance
- Odds can move quickly
- Some markets may have limited data

Enjoy finding those +EV bets!

