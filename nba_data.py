import pandas as pd
import numpy as np
import nflreadpy as nfl
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
        self.stats = pd.read_csv(file, low_memory=False)



    def get_stats_for_all_games(self, player: str, stat: str) -> tuple[list[int|float], int]:
        first_name = player[:player.find(' ')]
        last_name = player[player.find(' ') + 1:]
        current_stats = self.stats[(self.stats['firstName'] == first_name) & (self.stats['lastName'] == last_name)]
        stat_name = ODDS_API_TO_NBA_STATS_MAP[stat]
        stat_values = current_stats[stat_name].values
        stat_values = stat_values[~np.isnan(stat_values)]
        return stat_values, len(stat_values)

    def get_std_dev(self, player: str, stat: str) -> tuple[float, int]:
        stat_values, sample_size = self.get_stats_for_all_games(player, stat)
        return np.std(stat_values), sample_size
    
    def get_mean(self, player: str, stat: str) -> tuple[float, int]:
        stat_values, sample_size = self.get_stats_for_all_games(player, stat)
        return np.mean(stat_values), sample_size
    
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

        



