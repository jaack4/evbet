import pandas as pd
import numpy as np
import nflreadpy as nfl
import json
import os
import matplotlib.pyplot as plt

ODDS_API_TO_NFL_STATS_MAP = {
    'player_field_goals': 'fg_made',
    'player_pass_attempts': 'attempts',
    'player_pass_completions': 'completions',
    'player_pass_interceptions': 'passing_interceptions',
    'player_pass_tds': 'passing_tds',
    'player_pass_yds': 'passing_yards',
    'player_pats': 'pat_made',
    'player_receptions': 'receptions',
    'player_reception_tds': 'receiving_tds',
    'player_reception_yds': 'receiving_yards',
    'player_rush_attempts': 'carries',
    'player_rush_yds': 'rushing_yards',
    'player_rush_tds': 'rushing_tds',
    'player_solo_tackles': 'def_tackles_solo',
    'player_assists': 'def_tackle_assists'
}

PLAYER_NAME_MAP = {
    'Chris Godwin': 'Chris Godwin Jr.',
    'David Sills V': 'David Sills',
    'Michael Pittman Jr.': 'Michael Pittman',
    'AJ Brown': 'A.J. Brown',
    'Brian Robinson Jr.': 'Brian Robinson',
    'Brian Thomas Jr' : 'Brian Thomas Jr.',
    'Travis Etienne Jr.' : 'Travis Etienne'
}

class NFLData:
    def __init__(self, file='stats/nfl_stats.csv'):
        self.games = []
        # Only load columns we actually need to compute EV, not the full CSV
        columns_needed = ['player_display_name'] + list(ODDS_API_TO_NFL_STATS_MAP.values())
        self.stats = pd.read_csv(
            file,
            usecols=columns_needed, 
            low_memory=False
        )
        
        # Create index for fast player lookups
        self.stats.set_index('player_display_name', inplace=True, drop=False)
        self.stats.sort_index(inplace=True)
        
        # Cache for std_dev lookups
        self._std_cache = {}

    def get_stats_for_all_games(self, player: str, stat: str) -> tuple[list[int|float], int]:
        player_name = PLAYER_NAME_MAP.get(player, player)
        try:
            # Use index-based lookup (O(log n) vs O(n) for filter)
            current_stats = self.stats.loc[player_name]
            stat_name = ODDS_API_TO_NFL_STATS_MAP[stat]
            # Handle single row vs multiple rows
            if isinstance(current_stats, pd.Series):
                stat_values = np.array([current_stats[stat_name]])
            else:
                stat_values = current_stats[stat_name].values
            return stat_values, len(stat_values)
        except KeyError:
            return np.array([]), 0

    def get_std_dev(self, player: str, stat: str) -> tuple[float, int]:
        cache_key = (player, stat)
        if cache_key in self._std_cache:
            return self._std_cache[cache_key]
        
        stat_values, sample_size = self.get_stats_for_all_games(player, stat)
        result = (np.std(stat_values) if sample_size > 0 else np.nan, sample_size)
        self._std_cache[cache_key] = result
        return result
    
    def get_mean(self, player: str, stat: str) -> tuple[float, int]:
        stat_values, sample_size = self.get_stats_for_all_games(player, stat)
        return (np.mean(stat_values) if sample_size > 0 else np.nan, sample_size)
    
    def find_ev_all_games(self, betting_books: list[str], sharp_books: list[str], threshold: float=0.0) -> pd.DataFrame:
        ev = []
        for game in self.games:
            game_ev = game.find_plus_ev(betting_books, sharp_books, threshold)
            ev.append(game_ev)
        return pd.concat(ev).sort_values('ev_percent', ascending=False)

    def plot_stats_distribution(self, player: str, stat: str, bins: int = 100) -> None:
        stat_values = self.get_stats_for_all_games(player, stat)
        plt.hist(stat_values, bins)
        plt.show()

    def plot_all_stats_distribution(self, stat: str, bins: int = 100) -> None:
        values = self.stats[ODDS_API_TO_NFL_STATS_MAP[stat]].values
        #remove 0 values
        values = values[values != 0]
        plt.hist(values, bins)
        plt.show()

        



