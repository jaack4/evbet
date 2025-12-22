#!/usr/bin/env python3
"""
Script to display combined NFL and NBA bet win/loss statistics
"""
import os
import argparse
from dotenv import load_dotenv
from database import Database

# Load environment variables
load_dotenv()

def display_combined_stats(min_ev=None):
    """Display comprehensive betting statistics for both NFL and NBA
    
    Args:
        min_ev (float, optional): Minimum EV percentage to filter by
    """
    
    print("\n" + "="*70)
    if min_ev is not None:
        print(f"COMBINED BETTING PERFORMANCE REPORT (EV >= {min_ev}%)")
    else:
        print("COMBINED BETTING PERFORMANCE REPORT (ALL BETS)")
    print("="*70 + "\n")
    
    with Database() as db:
        # Get stats for both sports
        nfl_stats = db.get_nfl_win_loss_stats(min_ev=min_ev)
        nba_stats = db.get_nba_win_loss_stats(min_ev=min_ev)
        
        # Combined comparison table
        print("SPORT COMPARISON")
        print("-"*70)
        print(f"{'Sport':<10} {'Bets':>8} {'Wins':>8} {'Losses':>8} {'Win%':>8} {'Avg EV':>10}")
        print("-"*70)
        
        # NFL row
        if nfl_stats and nfl_stats['total_bets'] > 0:
            print(f"{'NFL':<10} {nfl_stats['total_bets']:>8} {nfl_stats['wins']:>8} "
                  f"{nfl_stats['losses']:>8} {nfl_stats['win_rate']:>7}% {nfl_stats['total_ev']:>9.2f}%")
        else:
            print(f"{'NFL':<10} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>10}")
        
        # NBA row
        if nba_stats and nba_stats['total_bets'] > 0:
            print(f"{'NBA':<10} {nba_stats['total_bets']:>8} {nba_stats['wins']:>8} "
                  f"{nba_stats['losses']:>8} {nba_stats['win_rate']:>7}% {nba_stats['total_ev']:>9.2f}%")
        else:
            print(f"{'NBA':<10} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>10}")
        
        # Combined totals
        if nfl_stats and nba_stats and nfl_stats['total_bets'] > 0 and nba_stats['total_bets'] > 0:
            total_bets = nfl_stats['total_bets'] + nba_stats['total_bets']
            total_wins = nfl_stats['wins'] + nba_stats['wins']
            total_losses = nfl_stats['losses'] + nba_stats['losses']
            combined_win_rate = round((total_wins / total_bets * 100), 2) if total_bets > 0 else 0
            
            # Weighted average EV
            combined_ev = (
                (nfl_stats['total_ev'] * nfl_stats['total_bets'] + 
                 nba_stats['total_ev'] * nba_stats['total_bets']) / total_bets
            )
            
            print("-"*70)
            print(f"{'COMBINED':<10} {total_bets:>8} {total_wins:>8} "
                  f"{total_losses:>8} {combined_win_rate:>7}% {combined_ev:>9.2f}%")
        
        print("\n" + "="*70 + "\n")
        
        # Detailed NFL stats
        if nfl_stats and nfl_stats['total_bets'] > 0:
            print("NFL DETAILED STATISTICS")
            print("-"*70)
            print(f"Total Bets:           {nfl_stats['total_bets']}")
            print(f"Win Rate:             {nfl_stats['win_rate']}%")
            if nfl_stats['avg_ev_won']:
                print(f"Average EV (Wins):    {nfl_stats['avg_ev_won']:.2f}%")
            if nfl_stats['avg_ev_lost']:
                print(f"Average EV (Losses):  {nfl_stats['avg_ev_lost']:.2f}%")
            print()
        
        # Detailed NBA stats
        if nba_stats and nba_stats['total_bets'] > 0:
            print("NBA DETAILED STATISTICS")
            print("-"*70)
            print(f"Total Bets:           {nba_stats['total_bets']}")
            print(f"Win Rate:             {nba_stats['win_rate']}%")
            if nba_stats['avg_ev_won']:
                print(f"Average EV (Wins):    {nba_stats['avg_ev_won']:.2f}%")
            if nba_stats['avg_ev_lost']:
                print(f"Average EV (Losses):  {nba_stats['avg_ev_lost']:.2f}%")
            print()
        
        # Top markets across both sports
        print("="*70)
        print("TOP PERFORMING MARKETS (COMBINED)")
        print("-"*70)
        
        # Get all markets from both sports
        nfl_markets = db.get_nfl_win_loss_by_market(min_ev=min_ev)
        nba_markets = db.get_nba_win_loss_by_market(min_ev=min_ev)
        
        # Combine and sort by win rate (minimum 10 bets)
        all_markets = []
        
        for market in nfl_markets:
            if market['total_bets'] >= 10:
                all_markets.append({
                    'sport': 'NFL',
                    'market': market['market'].replace('player_', ''),
                    'total_bets': market['total_bets'],
                    'win_rate': market['win_rate'],
                    'avg_ev': market['avg_ev']
                })
        
        for market in nba_markets:
            if market['total_bets'] >= 10:
                all_markets.append({
                    'sport': 'NBA',
                    'market': market['market'].replace('player_', ''),
                    'total_bets': market['total_bets'],
                    'win_rate': market['win_rate'],
                    'avg_ev': market['avg_ev']
                })
        
        # Sort by win rate
        all_markets.sort(key=lambda x: x['win_rate'], reverse=True)
        
        if all_markets:
            print(f"{'Market':<25} {'Sport':<6} {'Bets':>6} {'Win%':>7} {'Avg EV':>8}")
            print("-"*70)
            for market in all_markets[:20]:  # Top 20 markets
                print(f"{market['market']:<25} {market['sport']:<6} {market['total_bets']:>6} "
                      f"{market['win_rate']:>6}% {market['avg_ev']:>7.2f}%")
        
        print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    if not os.getenv('DATABASE_URL'):
        print("ERROR: DATABASE_URL environment variable is not set!")
        print("Please set it in your .env file")
        exit(1)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Display combined NFL and NBA betting performance statistics'
    )
    parser.add_argument(
        '--min-ev',
        type=float,
        default=None,
        help='Minimum EV percentage to filter by (e.g., --min-ev 5 for EV >= 5%%)'
    )
    args = parser.parse_args()
    
    display_combined_stats(min_ev=args.min_ev)

