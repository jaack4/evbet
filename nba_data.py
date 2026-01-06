import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt

ODDS_API_TO_NBA_STATS_MAP = {
    'player_points': 'points',
    'player_rebounds': 'reboundsTotal',
    'player_assists': 'assists',
    'player_threes': 'threePointersMade',
    'player_blocks': 'blocks',
    'player_steals': 'steals',
    'player_turnovers': 'turnovers'
}

class NBAData:
    def __init__(self, file='stats/nba_stats.csv'):
        self.games = []
        # Only load columns we need
        columns_needed = ['firstName', 'lastName'] + list(ODDS_API_TO_NBA_STATS_MAP.values())
        self.stats = pd.read_csv(file, usecols=columns_needed, low_memory=False)
        
        # Create combined name column for faster lookups
        self.stats['full_name'] = self.stats['firstName'] + ' ' + self.stats['lastName']
        self.stats.set_index('full_name', inplace=True, drop=False)
        self.stats.sort_index(inplace=True)
        
        # Cache for std_dev lookups
        self._std_cache = {}

    def get_stats_for_all_games(self, player: str, stat: str) -> tuple[list[int|float], int]:
        try:
            # Use index-based lookup (O(log n) vs O(n) for filter)
            current_stats = self.stats.loc[player]
            stat_name = ODDS_API_TO_NBA_STATS_MAP[stat]
            # Handle single row vs multiple rows
            if isinstance(current_stats, pd.Series):
                stat_values = np.array([current_stats[stat_name]])
            else:
                stat_values = current_stats[stat_name].values
            stat_values = stat_values[~np.isnan(stat_values)]
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
    
    def find_ev_all_games(self, betting_books: list[str], sharp_books: list[str], threshold: float=0.03) -> pd.DataFrame:
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
        values = self.stats[ODDS_API_TO_NBA_STATS_MAP[stat]].values
        #remove 0 values
        values = values[values != 0]
        plt.hist(values, bins)
        plt.show()

        



