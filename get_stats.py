import nflreadpy as nfl
import pandas as pd
import kagglehub
from kagglehub import KaggleDatasetAdapter
from nfl_data import ODDS_API_TO_NFL_STATS_MAP, PLAYER_NAME_MAP
from nba_data import ODDS_API_TO_NBA_STATS_MAP
import numpy as np
from database import Database
from datetime import datetime


def get_nba_data(seasons: list[int]) -> pd.DataFrame:
    df = kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        "eoinamoore/historical-nba-data-and-player-box-scores",
        "PlayerStatistics.csv",
        pandas_kwargs={'low_memory': False}
    )
    
    # Convert gameDateTimeEst to datetime and extract the year
    df['gameDateTimeEst'] = pd.to_datetime(df['gameDateTimeEst'], format='ISO8601', utc=True, errors='coerce')
    df['season_year'] = df['gameDateTimeEst'].dt.year
    
    # Filter for specified seasons
    df = df[df['season_year'].isin(seasons)]
    return df

def get_nfl_data(seasons: list[int]) -> pd.DataFrame:
    df = nfl.load_player_stats(seasons)
    schedule = nfl.load_schedules(seasons)

    df = df.to_pandas()
    schedule = schedule.to_pandas()
    
    # Create schedule entries for home teams
    schedule_home = schedule[['season', 'week', 'game_type', 'home_team', 'away_team', 'gameday']].copy()
    schedule_home = schedule_home.rename(columns={
        'home_team': 'team',
        'away_team': 'opponent_team',
        'game_type': 'season_type'
    })
    
    # Create schedule entries for away teams
    schedule_away = schedule[['season', 'week', 'game_type', 'away_team', 'home_team', 'gameday']].copy()
    schedule_away = schedule_away.rename(columns={
        'away_team': 'team',
        'home_team': 'opponent_team',
        'game_type': 'season_type'
    })
    
    # Combine both perspectives
    schedule_combined = pd.concat([schedule_home, schedule_away], ignore_index=True)
    
    # Merge stats with schedule to add game dates
    df = df.merge(
        schedule_combined,
        on=['season', 'week', 'season_type', 'team', 'opponent_team'],
        how='left'
    )
    
    return df


# Reverse mapping from PLAYER_NAME_MAP to look up stats name from odds API name
PLAYER_NAME_MAP_REVERSE = {v: k for k, v in PLAYER_NAME_MAP.items()}


def fill_nfl_bet_results(seasons: list[int] = None) -> dict:
    """
    Update win and actual_value in ev_bets table for NFL bets based on actual game results.
    
    Args:
        seasons: List of seasons to load data for. Defaults to current year.
        
    Returns:
        dict with counts of updated, not_found, and error bets
    """
    if seasons is None:
        seasons = [datetime.now().year]
    
    # Load NFL stats data
    print(f"Loading NFL data for seasons: {seasons}")
    nfl_stats = get_nfl_data(seasons)
    
    # Convert gameday to date for matching
    nfl_stats['gameday'] = pd.to_datetime(nfl_stats['gameday']).dt.date
    
    results = {'updated': 0, 'not_found': 0, 'errors': 0, 'already_filled': 0}
    
    with Database() as db:
        # Get unfilled NFL bets where game has commenced
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT eb.id, eb.player, eb.market, eb.betting_line, eb.outcome,
                       eb.home_team, eb.away_team, eb.commence_time
                FROM ev_bets eb
                JOIN games g ON eb.game_id = g.id
                WHERE eb.win IS NULL
                  AND eb.commence_time < NOW()
                  AND g.sport_key LIKE '%americanfootball_nfl%'
            """)
            unfilled_bets = cur.fetchall()
        
        print(f"Found {len(unfilled_bets)} unfilled NFL bets to process")
        
        for bet in unfilled_bets:
            try:
                bet_id = bet['id']
                player_name = bet['player']
                market = bet['market']
                betting_line = float(bet['betting_line'])
                outcome = bet['outcome']
                commence_time = bet['commence_time']
                
                # Get the stat column name from market
                if market not in ODDS_API_TO_NFL_STATS_MAP:
                    print(f"  Unknown market '{market}' for bet {bet_id}")
                    results['errors'] += 1
                    continue
                
                stat_column = ODDS_API_TO_NFL_STATS_MAP[market]
                
                # Map player name if needed (odds API name -> stats name)
                stats_player_name = PLAYER_NAME_MAP.get(player_name, player_name)
                
                # Get game date from commence_time
                game_date = commence_time.date()
                
                # Find matching player stats for this game
                player_stats = nfl_stats[
                    (nfl_stats['player_display_name'] == stats_player_name) &
                    (nfl_stats['gameday'] == game_date)
                ]
                
                if player_stats.empty:
                    # Try without date matching (just player name) and print available dates
                    player_all = nfl_stats[nfl_stats['player_display_name'] == stats_player_name]
                    if player_all.empty:
                        print(f"  Player '{stats_player_name}' not found in stats (bet {bet_id})")
                    else:
                        available_dates = player_all['gameday'].unique()
                        print(f"  No stats for '{stats_player_name}' on {game_date}. Available: {available_dates[:5]}")
                    results['not_found'] += 1
                    continue
                
                # Get the actual stat value
                actual_value = player_stats[stat_column].iloc[0]
                
                # Handle NaN values
                if pd.isna(actual_value):
                    actual_value = 0.0
                else:
                    actual_value = float(actual_value)
                
                # Determine if bet won
                if outcome.lower() == 'over':
                    win = actual_value > betting_line
                elif outcome.lower() == 'under':
                    win = actual_value < betting_line
                else:
                    print(f"  Unknown outcome '{outcome}' for bet {bet_id}")
                    results['errors'] += 1
                    continue
                
                # Update the bet in the database
                with db.conn.cursor() as cur:
                    cur.execute("""
                        UPDATE ev_bets 
                        SET win = %s, actual_value = %s
                        WHERE id = %s
                    """, (win, actual_value, bet_id))
                
                db.conn.commit()
                results['updated'] += 1
                
                win_str = "WON" if win else "LOST"
                print(f"  Updated bet {bet_id}: {player_name} {outcome} {betting_line} {market} -> {actual_value} ({win_str})")
                
            except Exception as e:
                print(f"  Error processing bet {bet.get('id', 'unknown')}: {e}")
                results['errors'] += 1
                continue
    
    print(f"\nResults: {results['updated']} updated, {results['not_found']} not found, {results['errors']} errors")
    return results


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if not os.getenv('DATABASE_URL'):
        print("ERROR: DATABASE_URL environment variable is not set!")
        exit(1)
    
    # Run for current season
    fill_nfl_bet_results([2025])
