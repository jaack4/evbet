#!/usr/bin/env python3
"""
Non-interactive script to reset and refill all bet results
Usage: python refill_all_bets.py [--seasons 2024 2025] [--sport nfl|nba|both] [--no-reset]
"""
import os
import argparse
from dotenv import load_dotenv
from database import Database
from get_stats import fill_nfl_bet_results, fill_nba_bet_results
from datetime import datetime

# Load environment variables
load_dotenv()

def reset_bet_results(sport=None):
    """
    Reset win and actual_value for bets so they can be refilled
    
    Args:
        sport (str, optional): 'nfl', 'nba', or None for both
        
    Returns:
        int: Number of bets reset
    """
    
    with Database() as db:
        with db.conn.cursor() as cur:
            # Build query based on sport filter
            if sport == 'nfl':
                where_clause = """
                    WHERE win IS NOT NULL 
                    AND game_id IN (SELECT id FROM games WHERE sport_key LIKE '%americanfootball_nfl%')
                """
            elif sport == 'nba':
                where_clause = """
                    WHERE win IS NOT NULL 
                    AND game_id IN (SELECT id FROM games WHERE sport_key LIKE '%basketball_nba%')
                """
            else:
                where_clause = "WHERE win IS NOT NULL"
            
            # Reset bet results
            cur.execute(f"""
                UPDATE ev_bets
                SET win = NULL, actual_value = NULL
                {where_clause}
            """)
            
            db.conn.commit()
            rows_updated = cur.rowcount
            
            sport_str = sport.upper() if sport else "all"
            print(f"Reset {rows_updated} {sport_str} bet results")
            return rows_updated

def main():
    """Main function to reset and refill bet results"""
    
    parser = argparse.ArgumentParser(
        description='Reset and refill all bet results with corrected timezone logic'
    )
    parser.add_argument(
        '--seasons',
        type=int,
        nargs='+',
        default=[datetime.now().year],
        help='Seasons to load data for (default: current year)'
    )
    parser.add_argument(
        '--sport',
        type=str,
        choices=['nfl', 'nba', 'both'],
        default='both',
        help='Which sport to process: nfl, nba, or both (default: both)'
    )
    parser.add_argument(
        '--no-reset',
        action='store_true',
        help='Skip reset step and only fill NULL bets'
    )
    
    args = parser.parse_args()
    
    if not os.getenv('DATABASE_URL'):
        print("ERROR: DATABASE_URL environment variable is not set!")
        exit(1)
    
    print("\n" + "="*60)
    print("REFILL BET RESULTS")
    print("="*60)
    print(f"Seasons: {args.seasons}")
    print(f"Sport: {args.sport}")
    print(f"Reset first: {not args.no_reset}")
    print("="*60 + "\n")
    
    reset_count = 0
    
    # Reset results if requested
    if not args.no_reset:
        print("Step 1: Resetting bet results...")
        sport_filter = args.sport if args.sport != 'both' else None
        reset_count = reset_bet_results(sport=sport_filter)
        print()
    else:
        print("Skipping reset step (only filling NULL bets)...\n")
    
    # Refill results
    nfl_results = {'updated': 0, 'not_found': 0, 'errors': 0}
    nba_results = {'updated': 0, 'not_found': 0, 'errors': 0}
    
    if args.sport in ['nfl', 'both']:
        print("="*60)
        print("FILLING NFL BET RESULTS")
        print("="*60)
        nfl_results = fill_nfl_bet_results(args.seasons)
        print()
    
    if args.sport in ['nba', 'both']:
        print("="*60)
        print("FILLING NBA BET RESULTS")
        print("="*60)
        nba_results = fill_nba_bet_results(args.seasons)
        print()
    
    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    if reset_count > 0:
        print(f"Total bets reset:           {reset_count}")
    print(f"\nNFL:")
    print(f"  Updated:                  {nfl_results['updated']}")
    print(f"  Not found:                {nfl_results['not_found']}")
    print(f"  Errors:                   {nfl_results['errors']}")
    print(f"\nNBA:")
    print(f"  Updated:                  {nba_results['updated']}")
    print(f"  Not found:                {nba_results['not_found']}")
    print(f"  Errors:                   {nba_results['errors']}")
    print(f"\nTotal updated:              {nfl_results['updated'] + nba_results['updated']}")
    print(f"Total not found:            {nfl_results['not_found'] + nba_results['not_found']}")
    print(f"Total errors:               {nfl_results['errors'] + nba_results['errors']}")
    
    if reset_count > 0:
        still_null = reset_count - (nfl_results['updated'] + nba_results['updated'])
        if still_null > 0:
            print(f"\nBets still NULL:            {still_null}")
            print("These may be from different seasons or future games.")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()

