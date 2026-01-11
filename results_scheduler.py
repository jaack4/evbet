import schedule
import time
import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv
from get_stats import fill_nfl_bet_results, fill_nba_bet_results

# Load environment variables
load_dotenv()

def update_bet_results(sport=None):
    """
    Main function to update bet results based on actual game outcomes
    
    Args:
        sport (str): 'nfl', 'nba', or None for both
    """
    sport_name = sport.upper() if sport else "ALL"
    print(f"\n{'#'*50}")
    print(f"# Starting {sport_name} Bet Results Update")
    print(f"# {datetime.now()}")
    print(f"{'#'*50}\n")
    
    try:

        seasons = [2025,2026]


        print(f"Processing seasons: {seasons}\n")
        
        # Update results based on sport parameter
        if sport == 'nfl' or sport is None:
            print("\n" + "="*60)
            print("FILLING NFL BET RESULTS")
            print("="*60)
            nfl_results = fill_nfl_bet_results([2025])
            print(f"\nNFL Summary: {nfl_results['updated']} updated, "
                  f"{nfl_results['not_found']} not found, "
                  f"{nfl_results['errors']} errors")
        
        if sport == 'nba' or sport is None:
            print("\n" + "="*60)
            print("FILLING NBA BET RESULTS")
            print("="*60)
            nba_results = fill_nba_bet_results([2025,2026])
            print(f"\nNBA Summary: {nba_results['updated']} updated, "
                  f"{nba_results['not_found']} not found, "
                  f"{nba_results['errors']} errors")
        
        print(f"\n[{datetime.now()}] {sport_name} Bet results update completed successfully!\n")
        
    except Exception as e:
        print(f"Error in update_bet_results: {e}")
        import traceback
        traceback.print_exc()

def check_database_connection():
    """Check if database connection is working"""
    try:
        from database import Database
        with Database() as db:
            with db.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM ev_bets LIMIT 1")
        print("Database connection successful.")
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Bet Results Scheduler - Update bet results for NFL and/or NBA based on actual game outcomes'
    )
    parser.add_argument(
        '--sport',
        type=str,
        choices=['nfl', 'nba', 'both'],
        default='both',
        help='Which sport to update: nfl, nba, or both (default: both)'
    )
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run once and exit (no scheduling)'
    )
    args = parser.parse_args()
    
    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("ERROR: DATABASE_URL environment variable is not set!")
        print("Please set it in your .env file or Railway environment variables")
        exit(1)
    
    # Get update interval from environment variable (default to 60 minutes)
    update_interval = int(os.getenv('RESULTS_UPDATE_INTERVAL_MINUTES', '60'))
    
    # Determine which sport(s) to run
    sport_param = None if args.sport == 'both' else args.sport
    sport_display = args.sport.upper()
    
    print("="*50)
    print(f"Bet Results Scheduler Starting ({sport_display})...")
    print("="*50)
    
    # Check database connection
    if not check_database_connection():
        print("\nERROR: Could not connect to database. Exiting.")
        exit(1)
    
    # Run immediately on startup
    update_bet_results(sport=sport_param)
    
    # If run-once mode, exit after first run
    if args.run_once:
        print("\nRun-once mode: Exiting after single execution.")
        exit(0)
    
    # Schedule to run at the specified interval
    schedule.every(update_interval).minutes.do(update_bet_results, sport=sport_param)
    
    print(f"\nScheduler active ({sport_display}). Updates will run every {update_interval} minutes.")
    print("Press Ctrl+C to stop.\n")
    
    while True:
        schedule.run_pending()
        time.sleep(20)

