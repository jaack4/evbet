import nflreadpy as nfl
import pandas as pd
import kagglehub
from kagglehub import KaggleDatasetAdapter
from nfl_data import ODDS_API_TO_NFL_STATS_MAP
from nba_data import ODDS_API_TO_NBA_STATS_MAP
import numpy as np
from database import Database


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

    