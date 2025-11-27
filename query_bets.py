"""
Simple utility to query and display EV bets from the database
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from database import Database

load_dotenv()

def display_active_bets(limit=20):
    """Display the top active EV bets"""
    with Database() as db:
        bets = db.get_active_ev_bets(limit=limit)
        
        if not bets:
            print("No active EV bets found!")
            return
        
        print(f"\n{'='*100}")
        print(f"TOP {len(bets)} ACTIVE EV BETS")
        print(f"{'='*100}\n")
        
        for i, bet in enumerate(bets, 1):
            print(f"{i}. {bet['player']} - {bet['market']}")
            print(f"   Game: {bet['away_team']} @ {bet['home_team']} ({bet['sport_title']})")
            print(f"   Starts: {bet['commence_time']}")
            print(f"   Bookmaker: {bet['bookmaker']}")
            print(f"   Bet: {bet['outcome']} {bet['betting_line']}")
            print(f"   Price: {bet['price']:.2f} | True Prob: {bet['true_prob']:.1%}")
            print(f"   EV: {bet['ev_percent']:.2f}% | Sharp Mean: {bet['sharp_mean']:.1f}")
            print(f"   Line Diff: {bet['mean_diff']:.1f}")
            print(f"   Added: {bet['created_at']}")
            print()

def display_statistics():
    """Display overall betting statistics"""
    with Database() as db:
        stats = db.get_bet_statistics()
        
        print(f"\n{'='*100}")
        print(f"DATABASE STATISTICS")
        print(f"{'='*100}\n")
        
        print(f"Total Bets: {stats['total_bets']}")
        print(f"Active Bets: {stats['active_bets']}")
        
        if stats['avg_ev_percent']:
            print(f"Average EV: {stats['avg_ev_percent']:.2f}%")
            print(f"Max EV: {stats['max_ev_percent']:.2f}%")
        
        if stats['oldest_bet']:
            print(f"Oldest Bet: {stats['oldest_bet']}")
        if stats['newest_bet']:
            print(f"Newest Bet: {stats['newest_bet']}")
        
        print()

def main():
    """Main function"""
    if not os.getenv('DATABASE_URL'):
        print("ERROR: DATABASE_URL environment variable is not set!")
        return
    
    try:
        display_statistics()
        display_active_bets(limit=20)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

