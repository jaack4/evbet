"""
One-time script to trim existing large NBA and NFL stats CSV files down to 100MB each.
This keeps only the most recent data.
Run this once to prepare the files before using update_stats.py
"""

import pandas as pd
import os

MAX_FILE_SIZE_KB = 100000  # Maximum file size in KB (100 MB)

def trim_nba_stats(csv_path='stats/nba_stats.csv'):
    """
    Trim NBA stats CSV to keep only the most recent data (under 100MB).
    """
    print("="*60)
    print("TRIMMING NBA STATS TO 100MB")
    print("="*60)
    
    original_size = os.path.getsize(csv_path) / 1024 / 1024  # MB
    print(f"Original file size: {original_size:.1f} MB")
    
    # Read existing CSV
    print(f"Reading NBA data from {csv_path}...")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"Original record count: {len(df)}")
    
    # Convert gameDate to datetime for sorting
    df['gameDate'] = pd.to_datetime(df['gameDate'], format='ISO8601', utc=True, errors='coerce')
    
    # Sort by date (most recent first)
    df = df.sort_values('gameDate', ascending=False)
    
    # Keep only the most recent data that fits within the size limit
    max_bytes = MAX_FILE_SIZE_KB * 1024
    temp_path = csv_path + '.tmp'
    
    # Start with all data and progressively remove oldest rows until size fits
    print("Finding optimal number of records to fit in 100MB...")
    for num_rows in range(len(df), 0, -1000):  # Larger steps for bigger files
        test_df = df.head(num_rows)
        test_df.to_csv(temp_path, index=False)
        file_size = os.path.getsize(temp_path)
        
        if file_size <= max_bytes:
            # Found the right size
            final_df = test_df
            break
    else:
        # If even the header is too large, keep minimal rows
        final_df = df.head(10)
    
    # Remove temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    # Create backup of original file
    backup_path = csv_path + '.backup'
    print(f"Creating backup at {backup_path}...")
    os.rename(csv_path, backup_path)
    
    # Write the trimmed data
    final_df.to_csv(csv_path, index=False)
    
    final_size_mb = os.path.getsize(csv_path) / 1024 / 1024
    date_range_start = final_df['gameDate'].min()
    date_range_end = final_df['gameDate'].max()
    
    print(f"\n✓ Successfully trimmed NBA stats!")
    print(f"  Original: {len(df)} records ({original_size:.1f} MB)")
    print(f"  Final: {len(final_df)} records ({final_size_mb:.1f} MB)")
    print(f"  Date range: {date_range_start} to {date_range_end}")
    print(f"  Backup saved: {backup_path}")
    
    return len(final_df)


def trim_nfl_stats(csv_path='stats/nfl_stats.csv'):
    """
    Trim NFL stats CSV to keep only the most recent data (under 100MB).
    """
    print("\n" + "="*60)
    print("TRIMMING NFL STATS TO 100MB")
    print("="*60)
    
    original_size = os.path.getsize(csv_path) / 1024 / 1024  # MB
    print(f"Original file size: {original_size:.1f} MB")
    
    # Read existing CSV
    print(f"Reading NFL data from {csv_path}...")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"Original record count: {len(df)}")
    
    # Sort by season and week (most recent first)
    df = df.sort_values(['season', 'week'], ascending=False)
    
    # Keep only the most recent data that fits within the size limit
    max_bytes = MAX_FILE_SIZE_KB * 1024
    temp_path = csv_path + '.tmp'
    
    # Start with all data and progressively remove oldest rows until size fits
    print("Finding optimal number of records to fit in 100MB...")
    for num_rows in range(len(df), 0, -1000):  # Larger steps for bigger files
        test_df = df.head(num_rows)
        test_df.to_csv(temp_path, index=False)
        file_size = os.path.getsize(temp_path)
        
        if file_size <= max_bytes:
            # Found the right size
            final_df = test_df
            break
    else:
        # If even the header is too large, keep minimal rows
        final_df = df.head(10)
    
    # Remove temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    # Create backup of original file
    backup_path = csv_path + '.backup'
    print(f"Creating backup at {backup_path}...")
    os.rename(csv_path, backup_path)
    
    # Write the trimmed data
    final_df.to_csv(csv_path, index=False)
    
    final_size_mb = os.path.getsize(csv_path) / 1024 / 1024
    final_season_max = int(final_df['season'].max())
    final_week_max = int(final_df[final_df['season'] == final_season_max]['week'].max())
    final_season_min = int(final_df['season'].min())
    final_week_min = int(final_df[final_df['season'] == final_season_min]['week'].min())
    
    print(f"\n✓ Successfully trimmed NFL stats!")
    print(f"  Original: {len(df)} records ({original_size:.1f} MB)")
    print(f"  Final: {len(final_df)} records ({final_size_mb:.1f} MB)")
    print(f"  Date range: Season {final_season_min}, Week {final_week_min} to Season {final_season_max}, Week {final_week_max}")
    print(f"  Backup saved: {backup_path}")
    
    return len(final_df)


if __name__ == "__main__":
    import argparse
    from datetime import datetime
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Trim NBA and/or NFL stats CSV files to 100MB (one-time operation)'
    )
    parser.add_argument(
        '--sport',
        type=str,
        choices=['nfl', 'nba', 'both'],
        default='both',
        help='Which sport to trim: nfl, nba, or both (default: both)'
    )
    args = parser.parse_args()
    
    print("\n" + "#"*60)
    print("# STATS FILE TRIM SCRIPT (ONE-TIME)")
    print(f"# {datetime.now()}")
    print("#"*60)
    print("\nWARNING: This will create backups (.backup) and trim your files!")
    print("Press Ctrl+C within 5 seconds to cancel...")
    
    import time
    time.sleep(5)
    
    print("\nProceeding...\n")
    
    try:
        if args.sport in ['nba', 'both']:
            trim_nba_stats()
        
        if args.sport in ['nfl', 'both']:
            trim_nfl_stats()
        
        print("\n" + "="*60)
        print("TRIM COMPLETE!")
        print("="*60)
        print("\nYou can now use update_stats.py to keep these files updated.")
        print("Original files backed up with .backup extension.")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
