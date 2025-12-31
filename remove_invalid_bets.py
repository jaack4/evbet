#!/usr/bin/env python3
"""
Script to remove bets where created_at is after commence_time
(These are invalid as bets should be placed before the game starts)
"""
import os
import argparse
from dotenv import load_dotenv
from database import Database

# Load environment variables
load_dotenv()

def find_invalid_bets():
    """
    Find bets where created_at > commence_time
    
    Returns:
        list: List of invalid bet records
    """
    with Database() as db:
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    eb.id,
                    eb.player,
                    eb.market,
                    eb.betting_line,
                    eb.outcome,
                    eb.bookmaker,
                    eb.created_at,
                    eb.commence_time,
                    g.sport_title,
                    eb.home_team,
                    eb.away_team
                FROM ev_bets eb
                JOIN games g ON eb.game_id = g.id
                WHERE eb.created_at > eb.commence_time
                ORDER BY eb.created_at DESC
            """)
            return cur.fetchall()

def remove_invalid_bets(dry_run=True):
    """
    Remove bets where created_at > commence_time
    
    Args:
        dry_run (bool): If True, only show what would be deleted without actually deleting
        
    Returns:
        int: Number of bets that were (or would be) deleted
    """
    
    print("\n" + "="*70)
    print("REMOVE INVALID BETS (created_at > commence_time)")
    print("="*70 + "\n")
    
    # Find invalid bets
    invalid_bets = find_invalid_bets()
    
    if not invalid_bets:
        print("No invalid bets found. All bets were created before their game commenced.")
        return 0
    
    print(f"Found {len(invalid_bets)} invalid bets:\n")
    
    # Group by sport for summary
    sport_counts = {}
    bookmaker_counts = {}
    
    for bet in invalid_bets:
        sport = bet['sport_title']
        bookmaker = bet['bookmaker']
        
        sport_counts[sport] = sport_counts.get(sport, 0) + 1
        bookmaker_counts[bookmaker] = bookmaker_counts.get(bookmaker, 0) + 1
    
    # Show summary by sport
    print("Breakdown by Sport:")
    for sport, count in sorted(sport_counts.items()):
        print(f"  {sport}: {count} bets")
    
    print("\nBreakdown by Bookmaker:")
    for bookmaker, count in sorted(bookmaker_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {bookmaker}: {count} bets")
    
    # Show first 20 examples
    print("\nFirst 20 examples:")
    print("-"*70)
    print(f"{'ID':<8} {'Sport':<6} {'Player':<20} {'Market':<18} {'Created':<12} {'Commence':<12}")
    print("-"*70)
    
    for bet in invalid_bets[:20]:
        created_date = bet['created_at'].strftime('%Y-%m-%d %H:%M') if bet['created_at'] else 'N/A'
        commence_date = bet['commence_time'].strftime('%Y-%m-%d %H:%M') if bet['commence_time'] else 'N/A'
        
        print(f"{bet['id']:<8} {bet['sport_title']:<6} {bet['player'][:20]:<20} "
              f"{bet['market'][:18]:<18} {created_date:<12} {commence_date:<12}")
    
    if len(invalid_bets) > 20:
        print(f"... and {len(invalid_bets) - 20} more")
    
    print("\n" + "="*70)
    
    if dry_run:
        print("\nDRY RUN MODE - No bets were actually deleted.")
        print("Run with --confirm to actually delete these bets.")
        return len(invalid_bets)
    
    # Actually delete the bets
    print("\nDeleting invalid bets...")
    
    with Database() as db:
        with db.conn.cursor() as cur:
            cur.execute("""
                DELETE FROM ev_bets
                WHERE created_at > commence_time
            """)
            db.conn.commit()
            rows_deleted = cur.rowcount
    
    print(f"✓ Deleted {rows_deleted} invalid bets")
    return rows_deleted

def main():
    """Main function"""
    
    parser = argparse.ArgumentParser(
        description='Remove bets where created_at is after commence_time'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Actually delete the bets (default is dry-run mode)'
    )
    
    args = parser.parse_args()
    
    if not os.getenv('DATABASE_URL'):
        print("ERROR: DATABASE_URL environment variable is not set!")
        exit(1)
    
    # Run the removal (dry run by default)
    count = remove_invalid_bets(dry_run=not args.confirm)
    
    if count > 0 and not args.confirm:
        print(f"\nTo delete these {count} bets, run:")
        print("  python remove_invalid_bets.py --confirm")
    
    print()

if __name__ == "__main__":
    main()




