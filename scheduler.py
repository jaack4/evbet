import schedule
import time
import os
import sys
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from get_data import get_events, get_game, NFL, NBA, NFL_MARKETS, NBA_MARKETS
from nfl_data import NFLData
from nba_data import NBAData
from database import Database

# Load environment variables
load_dotenv()

def update_nfl_bets(db: Database):
    """Fetch and update NFL EV bets"""
    print(f"\n{'='*50}")
    print(f"[{datetime.now()}] Updating NFL bets...")
    print(f"{'='*50}\n")
    
    try:
        # Get NFL games for the next 7 days
        commence_time_to = (datetime.now() + timedelta(days=9)).isoformat(timespec='seconds') + 'Z'
        nfl_events = get_events(NFL, commence_time_to)
        
        if not nfl_events:
            print("No NFL events found")
            return
        
        print(f"Found {len(nfl_events)} NFL events")
        nfl_data = NFLData()
        
        total_ev_bets = 0
        
        for event in nfl_events:
            try:
                print(f"\nProcessing: {event['away_team']} @ {event['home_team']}")
                
                # Insert game into database
                game_data = {
                    'id': event['id'],
                    'sport_key': event['sport_key'],
                    'sport_title': event['sport_title'],
                    'commence_time': event['commence_time'],
                    'home_team': event['home_team'],
                    'away_team': event['away_team']
                }
                db.insert_game(game_data)
                
                # Get odds and calculate EV
                game = get_game(
                    NFL,
                    event['id'],
                    'us,us_dfs',
                    NFL_MARKETS,
                    'decimal',
                    'prizepicks,underdog,betr_us_dfs,pick6,fanduel,draftkings',
                    nfl_data
                )
                
                if game is None:
                    print(f"Failed to get game data for {event['id']}")
                    continue
                
                # Find EV bets (threshold of 0 to get all positive EV)
                ev_bets = game.find_plus_ev(
                    ['underdog', 'prizepicks', 'betr_us_dfs', 'pick6'], 
                    ['fanduel', 'draftkings'], 
                    -5
                )
                
                # Insert EV bets into database
                db.insert_ev_bets(ev_bets, event['id'])
                
                bet_count = len(ev_bets)
                total_ev_bets += bet_count
                print(f"Found {bet_count} EV bets")
                
            except Exception as e:
                print(f"Error processing event {event.get('id')}: {e}")
                continue
        
        print(f"\nNFL Update Complete: {total_ev_bets} total EV bets found")
        
    except Exception as e:
        print(f"Error in update_nfl_bets: {e}")

def update_nba_bets(db: Database):
    """Fetch and update NBA EV bets"""
    print(f"\n{'='*50}")
    print(f"[{datetime.now()}] Updating NBA bets...")
    print(f"{'='*50}\n")
    
    try:
        # Get NBA games for the next 7 days
        commence_time_to = (datetime.now() + timedelta(days=4)).isoformat(timespec='seconds') + 'Z'
        nba_events = get_events(NBA, commence_time_to)
        
        if not nba_events:
            print("No NBA events found")
            return
        
        print(f"Found {len(nba_events)} NBA events")
        nba_data = NBAData()
        
        total_ev_bets = 0
        
        for event in nba_events:
            try:
                print(f"\nProcessing: {event['away_team']} @ {event['home_team']}")
                
                # Insert game into database
                game_data = {
                    'id': event['id'],
                    'sport_key': event['sport_key'],
                    'sport_title': event['sport_title'],
                    'commence_time': event['commence_time'],
                    'home_team': event['home_team'],
                    'away_team': event['away_team']
                }
                db.insert_game(game_data)
                
                # Get odds and calculate EV
                game = get_game(
                    NBA,
                    event['id'],
                    'us,us_dfs',
                    NBA_MARKETS,
                    'decimal',
                    'prizepicks,underdog,betr_us_dfs,pick6,fanduel,draftkings',
                    nba_data
                )
                
                if game is None:
                    print(f"Failed to get game data for {event['id']}")
                    continue
                
                # Find EV bets
                ev_bets = game.find_plus_ev(
                    ['underdog', 'prizepicks', 'betr_us_dfs', 'pick6'], 
                    ['fanduel', 'draftkings'], 
                    -5
                )
                
                # Insert EV bets into database
                db.insert_ev_bets(ev_bets, event['id'])
                
                bet_count = len(ev_bets)
                total_ev_bets += bet_count
                print(f"Found {bet_count} EV bets")
                
            except Exception as e:
                print(f"Error processing event {event.get('id')}: {e}")
                continue
        
        print(f"\nNBA Update Complete: {total_ev_bets} total EV bets found")
        
    except Exception as e:
        print(f"Error in update_nba_bets: {e}")

def update_ev_bets(sport=None):
    """
    Main function to fetch and update EV bets
    
    Args:
        sport (str): 'nfl', 'nba', or None for both
    """
    sport_name = sport.upper() if sport else "ALL"
    print(f"\n{'#'*50}")
    print(f"# Starting {sport_name} EV Bet Update")
    print(f"# {datetime.now()}")
    print(f"{'#'*50}\n")
    
    try:
        with Database() as db:
            # Deactivate bets based on sport parameter
            if sport == 'nfl':
                db.deactivate_bets_for_sport('NFL')
                update_nfl_bets(db)
            elif sport == 'nba':
                db.deactivate_bets_for_sport('NBA')
                update_nba_bets(db)
            else:
                # Update both sports - deactivate all
                db.deactivate_all_bets()
                update_nfl_bets(db)
                update_nba_bets(db)
            
            # Print statistics
            stats = db.get_bet_statistics()
            print(f"\n{'='*50}")
            print(f"Database Statistics:")
            print(f"  Total Bets: {stats['total_bets']}")
            print(f"  Active Bets: {stats['active_bets']}")
            if stats['avg_ev_percent']:
                print(f"  Average EV: {stats['avg_ev_percent']:.2f}%")
                print(f"  Max EV: {stats['max_ev_percent']:.2f}%")
            print(f"{'='*50}\n")
        
        print(f"[{datetime.now()}] {sport_name} EV bet update completed successfully!\n")
        
    except Exception as e:
        print(f"Error in update_ev_bets: {e}")
        import traceback
        traceback.print_exc()

def check_and_initialize_database():
    """Check if database is initialized, and initialize if needed"""
    try:
        with Database() as db:
            # Try to query ev_bets table
            with db.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM ev_bets LIMIT 1")
        print("Database is already initialized.")
        return True
    except Exception as e:
        if "does not exist" in str(e):
            print("\n" + "="*50)
            print("Database not initialized. Initializing now...")
            print("="*50 + "\n")
            try:
                from init_db import init_database
                if init_database():
                    print("\nDatabase initialized successfully!")
                    return True
                else:
                    print("\nFailed to initialize database.")
                    return False
            except Exception as init_error:
                print(f"Error initializing database: {init_error}")
                return False
        else:
            print(f"Database connection error: {e}")
            return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='EV Bet Scheduler - Update NFL and/or NBA betting data'
    )
    parser.add_argument(
        '--sport',
        type=str,
        choices=['nfl', 'nba', 'both'],
        default='both',
        help='Which sport to update: nfl, nba, or both (default: both)'
    )
    args = parser.parse_args()
    
    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("ERROR: DATABASE_URL environment variable is not set!")
        print("Please set it in your .env file or Railway environment variables")
        exit(1)
    
    # Check if API_KEY is set
    if not os.getenv('API_KEY'):
        print("ERROR: API_KEY environment variable is not set!")
        print("Please set it in your .env file or Railway environment variables")
        exit(1)
    
    # Get update interval from environment variable (default to 15 minutes)
    update_interval = int(os.getenv('UPDATE_INTERVAL_MINUTES', '15'))
    
    # Determine which sport(s) to run
    sport_param = None if args.sport == 'both' else args.sport
    sport_display = args.sport.upper()
    
    print("="*50)
    print(f"EV Bet Scheduler Starting ({sport_display})...")
    print("="*50)
    
    # Check and initialize database if needed
    if not check_and_initialize_database():
        print("\nERROR: Could not initialize database. Exiting.")
        exit(1)
    
    # Run immediately on startup
    update_ev_bets(sport=sport_param)
    
    # Schedule to run at the specified interval
    schedule.every(update_interval).minutes.do(update_ev_bets, sport=sport_param)
    
    print(f"\nScheduler active ({sport_display}). Updates will run every {update_interval} minutes.")
    print("Press Ctrl+C to stop.\n")
    
    while True:
        schedule.run_pending()
        time.sleep(30)  # Check every minute

