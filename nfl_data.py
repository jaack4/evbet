import pandas as pd
import numpy as np
import nflreadpy as nfl
import json
import os

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

class NFLData:
    def __init__(self, file='stats/nfl_stats.csv'):
        self.games = []
        # Only load columns we actually need to compute EV, not the full CSV
        columns_needed = ['player_display_name'] + list(ODDS_API_TO_NFL_STATS_MAP.values())
        self.stats = pd.read_csv(
            file,
            usecols=columns_needed,   # <- huge memory savings
            low_memory=False
        )



    def get_stats_for_all_games(self, player: str, stat: str) -> list[int|float]:
        current_stats = self.stats[self.stats['player_display_name'] == player]
        stat_name = ODDS_API_TO_NFL_STATS_MAP[stat]
        stat_values = current_stats[stat_name].values
        return stat_values

    def get_std_dev(self, player: str, stat: str) -> float:
        stat_values = self.get_stats_for_all_games(player, stat)
        return np.std(stat_values)
    
    def get_mean(self, player: str, stat: str) -> float:
        stat_values = self.get_stats_for_all_games(player, stat)
        return np.mean(stat_values)
    
    def find_ev_all_games(self, betting_books: list[str], sharp_books: list[str], threshold: float=0.03) -> pd.DataFrame:
        ev = []
        for game in self.games:
            game_ev = game.find_plus_ev(betting_books, sharp_books, threshold)
            ev.append(game_ev)
        return pd.concat(ev).sort_values('ev_percent', ascending=False)

        



