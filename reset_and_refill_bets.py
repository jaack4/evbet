#!/usr/bin/env python3
"""
Script to reset and refill all bet results with corrected timezone logic
"""
import os
from dotenv import load_dotenv
from database import Database
from get_stats import fill_nfl_bet_results, fill_nba_bet_results
from datetime import datetime

# Load environment variables
load_dotenv()

def reset_all_bet_results():
    """Reset win and actual_value for all bets so they can be refilled"""
    
    print("\n" + "="*60)
    print("RESETTING ALL BET RESULTS")
    print("="*60 + "\n")
    
    with Database() as db:
        with db.conn.cursor() as cur:
            # Count how many bets currently have results
            cur.execute("""
                SELECT COUNT(*) as total
                FROM ev_bets
                WHERE win IS NOT NULL
            """)
            filled_count = cur.fetchone()['total']
            
            print(f"Found {filled_count} bets with results that will be reset")
            
            if filled_count == 0:
                print("No bets to reset.")
                return 0
            
            # Ask for confirmation
            print("\nThis will reset all win and actual_value fields to NULL.")
            response = input("Are you sure you want to continue? (yes/no): ")
            
            if response.lower() != 'yes':
                print("Reset cancelled.")
                return 0
            
            # Reset all bet results
            cur.execute("""
                UPDATE ev_bets
                SET win = NULL, actual_value = NULL
                WHERE win IS NOT NULL
            """)
            
            db.conn.commit()
            rows_updated = cur.rowcount
            
            print(f"\n✓ Reset {rows_updated} bet results")
            return rows_updated
    
def main():
    """Main function to reset and refill all bet results"""
    
    if not os.getenv('DATABASE_URL'):
        print("ERROR: DATABASE_URL environment variable is not set!")
        exit(1)
    
    print("\n" + "="*60)
    print("RESET AND REFILL BET RESULTS")
    print("This will reset all existing bet results and refill them")
    print("with the corrected timezone logic (-8 hours adjustment)")
    print("="*60)
    
    # Reset all results
    reset_count = reset_all_bet_results()
    
    if reset_count == 0:
        print("\nNo bets were reset. Exiting.")
        return
    
    # Determine which seasons to load
    current_year = datetime.now().year
    seasons = [current_year]
    
    print(f"\nWill load data for seasons: {seasons}")
    print("\nNote: If your bets span multiple seasons, you may need to run")
    print("the fill functions separately with different season parameters.")
    print()
    
    response = input("Continue with refilling? (yes/no): ")
    if response.lower() != 'yes':
        print("Refill cancelled. Bets remain reset (NULL values).")
        return
    
    # Refill NFL bets
    print("\n" + "="*60)
    print("REFILLING NFL BET RESULTS")
    print("="*60)
    nfl_results = fill_nfl_bet_results(seasons)
    
    # Refill NBA bets
    print("\n" + "="*60)
    print("REFILLING NBA BET RESULTS")
    print("="*60)
    nba_results = fill_nba_bet_results(seasons)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
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
    
    still_null = reset_count - (nfl_results['updated'] + nba_results['updated'])
    if still_null > 0:
        print(f"\nBets still NULL:            {still_null}")
        print("These may be from different seasons or future games.")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()

