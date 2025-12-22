#!/usr/bin/env python3
"""
Script to display NFL bet win/loss statistics
"""
import os
import argparse
from dotenv import load_dotenv
from database import Database

# Load environment variables
load_dotenv()

def display_nfl_stats(min_ev=None):
    """Display comprehensive NFL betting statistics
    
    Args:
        min_ev (float, optional): Minimum EV percentage to filter by
    """
    
    print("\n" + "="*60)
    if min_ev is not None:
        print(f"NFL BETTING PERFORMANCE REPORT (EV >= {min_ev}%)")
    else:
        print("NFL BETTING PERFORMANCE REPORT (ALL BETS)")
    print("="*60 + "\n")
    
    with Database() as db:
        # Overall NFL stats
        print("OVERALL NFL STATISTICS")
        print("-"*60)
        stats = db.get_nfl_win_loss_stats(min_ev=min_ev)
        
        if stats and stats['total_bets'] > 0:
            print(f"Total Bets Graded:    {stats['total_bets']}")
            print(f"Wins:                 {stats['wins']}")
            print(f"Losses:               {stats['losses']}")
            print(f"Win Rate:             {stats['win_rate']}%")
            print(f"Average EV (All):     {stats['total_ev']:.2f}%")
            if stats['avg_ev_won']:
                print(f"Average EV (Wins):    {stats['avg_ev_won']:.2f}%")
            if stats['avg_ev_lost']:
                print(f"Average EV (Losses):  {stats['avg_ev_lost']:.2f}%")
            if stats['first_bet_date']:
                print(f"Date Range:           {stats['first_bet_date']} to {stats['last_bet_date']}")
        else:
            if min_ev is not None:
                print(f"No graded NFL bets found with EV >= {min_ev}%.")
            else:
                print("No graded NFL bets found in database.")
            return
        
        # Stats by bookmaker
        print("\n" + "-"*60)
        print("PERFORMANCE BY BOOKMAKER")
        print("-"*60)
        bookmaker_stats = db.get_nfl_win_loss_by_bookmaker(min_ev=min_ev)
        
        if bookmaker_stats:
            print(f"{'Bookmaker':<15} {'Bets':>6} {'Wins':>6} {'Losses':>6} {'Win%':>7} {'Avg EV':>8}")
            print("-"*60)
            for row in bookmaker_stats:
                print(f"{row['bookmaker']:<15} {row['total_bets']:>6} {row['wins']:>6} "
                      f"{row['losses']:>6} {row['win_rate']:>6}% {row['avg_ev']:>7.2f}%")
        
        # Stats by market
        print("\n" + "-"*60)
        print("PERFORMANCE BY MARKET TYPE")
        print("-"*60)
        market_stats = db.get_nfl_win_loss_by_market(min_ev=min_ev)
        
        if market_stats:
            print(f"{'Market':<30} {'Bets':>6} {'Wins':>6} {'Losses':>6} {'Win%':>7} {'Avg EV':>8}")
            print("-"*60)
            for row in market_stats[:15]:  # Show top 15 markets
                market_name = row['market'].replace('player_', '')
                print(f"{market_name:<30} {row['total_bets']:>6} {row['wins']:>6} "
                      f"{row['losses']:>6} {row['win_rate']:>6}% {row['avg_ev']:>7.2f}%")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    if not os.getenv('DATABASE_URL'):
        print("ERROR: DATABASE_URL environment variable is not set!")
        print("Please set it in your .env file")
        exit(1)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Display NFL betting performance statistics'
    )
    parser.add_argument(
        '--min-ev',
        type=float,
        default=None,
        help='Minimum EV percentage to filter by (e.g., --min-ev 5 for EV >= 5%%)'
    )
    args = parser.parse_args()
    
    display_nfl_stats(min_ev=args.min_ev)

