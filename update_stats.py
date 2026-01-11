"""
Script to update NBA and NFL stats CSV files with the most recent data.
This script maintains a rolling window of recent games, keeping file size under 100MB.
"""

import pandas as pd
import nflreadpy as nfl
import kagglehub
from kagglehub import KaggleDatasetAdapter
from datetime import datetime
import os

MAX_FILE_SIZE_KB = 100000  # Maximum file size in KB (100 MB)

def update_nba_stats(csv_path='stats/nba_stats.csv'):
    """
    Update NBA stats CSV with the most recent data from Kaggle.
    Maintains a rolling window of recent games, keeping file size under 100MB.
    """
    print("="*60)
    print("UPDATING NBA STATS")
    print("="*60)
    
    # Read existing CSV
    print(f"Reading existing NBA data from {csv_path}...")
    existing_df = pd.read_csv(csv_path, low_memory=False)
    
    # Convert gameDate to datetime for comparison
    existing_df['gameDate'] = pd.to_datetime(existing_df['gameDate'], format='ISO8601', utc=True, errors='coerce')
    
    # Get the most recent date in the existing file
    latest_date = existing_df['gameDate'].max()
    print(f"Latest date in existing file: {latest_date}")
    
    # Download the latest data from Kaggle
    print("Downloading latest NBA data from Kaggle...")
    new_df = kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        "eoinamoore/historical-nba-data-and-player-box-scores",
        "PlayerStatistics.csv",
        pandas_kwargs={'low_memory': False}
    )
    
    # Rename column to match existing file
    new_df = new_df.rename(columns={'gameDateTimeEst': 'gameDate'})
    
    # Convert gameDate to datetime
    new_df['gameDate'] = pd.to_datetime(new_df['gameDate'], format='ISO8601', utc=True, errors='coerce')
    
    # Filter for only new games (after the latest date in existing file)
    new_games = new_df[new_df['gameDate'] > latest_date]
    
    if len(new_games) == 0:
        print("No new games to add. File is up to date!")
        return 0
    
    print(f"Found {len(new_games)} new game records to add")
    print(f"Date range of new games: {new_games['gameDate'].min()} to {new_games['gameDate'].max()}")
    
    # Combine existing and new data
    combined_df = pd.concat([existing_df, new_games], ignore_index=True)
    
    # Sort by date (most recent first)
    combined_df = combined_df.sort_values('gameDate', ascending=False)
    
    # Keep only the most recent data that fits within the size limit
    max_bytes = MAX_FILE_SIZE_KB * 1024
    temp_path = csv_path + '.tmp'
    
    # Start with all data and progressively remove oldest rows until size fits
    for num_rows in range(len(combined_df), 0, -100):
        test_df = combined_df.head(num_rows)
        test_df.to_csv(temp_path, index=False)
        file_size = os.path.getsize(temp_path)
        
        if file_size <= max_bytes:
            # Found the right size
            final_df = test_df
            break
    else:
        # If even the header is too large, keep minimal rows
        final_df = combined_df.head(10)
    
    # Remove temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    # Write the final data
    final_df.to_csv(csv_path, index=False)
    
    final_size_kb = os.path.getsize(csv_path) / 1024
    date_range_start = final_df['gameDate'].min()
    date_range_end = final_df['gameDate'].max()
    
    print(f"✓ Successfully updated NBA stats!")
    print(f"  Added {len(new_games)} new records")
    print(f"  Keeping {len(final_df)} total records (most recent)")
    print(f"  Date range: {date_range_start} to {date_range_end}")
    print(f"  File size: {final_size_kb:.1f} KB / {MAX_FILE_SIZE_KB} KB")
    
    return len(new_games)


def update_nfl_stats(csv_path='stats/nfl_stats.csv'):
    """
    Update NFL stats CSV with the most recent data from nflreadpy.
    Maintains a rolling window of recent games, keeping file size under 100MB.
    """
    print("\n" + "="*60)
    print("UPDATING NFL STATS")
    print("="*60)
    
    # Read existing CSV
    print(f"Reading existing NFL data from {csv_path}...")
    existing_df = pd.read_csv(csv_path, low_memory=False)
    
    # Get the most recent season and week in the existing file
    latest_season = int(existing_df['season'].max())
    latest_week = int(existing_df[existing_df['season'] == latest_season]['week'].max())
    print(f"Latest data in existing file: Season {latest_season}, Week {latest_week}")
    
    # Determine which seasons to fetch

    seasons_to_fetch = [2025]

    
    print(f"Fetching data for seasons: {seasons_to_fetch}")
    
    # Load new data from nflreadpy
    print("Downloading latest NFL data from nflreadpy...")
    new_df = nfl.load_player_stats(seasons_to_fetch).to_pandas()
    
    # Filter for only data after what we have
    # Keep games from seasons after the latest, or same season but later weeks
    new_games = new_df[
        (new_df['season'] > latest_season) | 
        ((new_df['season'] == latest_season) & (new_df['week'] > latest_week))
    ]
    
    if len(new_games) == 0:
        print("No new games to add. File is up to date!")
        return 0
    
    print(f"Found {len(new_games)} new game records to add")
    latest_new_season = int(new_games['season'].max())
    latest_new_week = int(new_games[new_games['season'] == latest_new_season]['week'].max())
    print(f"Date range of new games: Season {new_games['season'].min()}, Week {new_games['week'].min()} "
          f"to Season {latest_new_season}, Week {latest_new_week}")
    
    # Combine existing and new data
    combined_df = pd.concat([existing_df, new_games], ignore_index=True)
    
    # Sort by season and week (most recent first)
    combined_df = combined_df.sort_values(['season', 'week'], ascending=False)
    
    # Keep only the most recent data that fits within the size limit
    max_bytes = MAX_FILE_SIZE_KB * 1024
    temp_path = csv_path + '.tmp'
    
    # Start with all data and progressively remove oldest rows until size fits
    for num_rows in range(len(combined_df), 0, -100):
        test_df = combined_df.head(num_rows)
        test_df.to_csv(temp_path, index=False)
        file_size = os.path.getsize(temp_path)
        
        if file_size <= max_bytes:
            # Found the right size
            final_df = test_df
            break
    else:
        # If even the header is too large, keep minimal rows
        final_df = combined_df.head(10)
    
    # Remove temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    # Write the final data
    final_df.to_csv(csv_path, index=False)
    
    final_size_kb = os.path.getsize(csv_path) / 1024
    final_season_max = int(final_df['season'].max())
    final_week_max = int(final_df[final_df['season'] == final_season_max]['week'].max())
    final_season_min = int(final_df['season'].min())
    final_week_min = int(final_df[final_df['season'] == final_season_min]['week'].min())
    
    print(f"✓ Successfully updated NFL stats!")
    print(f"  Added {len(new_games)} new records")
    print(f"  Keeping {len(final_df)} total records (most recent)")
    print(f"  Date range: Season {final_season_min}, Week {final_week_min} to Season {final_season_max}, Week {final_week_max}")
    print(f"  File size: {final_size_kb:.1f} KB / {MAX_FILE_SIZE_KB} KB")
    
    return len(new_games)


if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Update NBA and/or NFL stats CSV files with the most recent data'
    )
    parser.add_argument(
        '--sport',
        type=str,
        choices=['nfl', 'nba', 'both'],
        default='both',
        help='Which sport to update: nfl, nba, or both (default: both)'
    )
    args = parser.parse_args()
    
    print("\n" + "#"*60)
    print("# STATS FILE UPDATE SCRIPT")
    print(f"# {datetime.now()}")
    print("#"*60 + "\n")
    
    total_added = 0
    
    try:
        if args.sport in ['nba', 'both']:
            nba_added = update_nba_stats()
            total_added += nba_added
        
        if args.sport in ['nfl', 'both']:
            nfl_added = update_nfl_stats()
            total_added += nfl_added
        
        print("\n" + "="*60)
        print(f"UPDATE COMPLETE - {total_added} total new records added")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

