import pandas as pd
import numpy as np
from scipy import stats
from nfl_data import NFLData
from nba_data import NBAData

class Game:
    def __init__(self, id, sport_key, sport_title, commence_time, home_team, away_team, bookmakers, markets, bookmaker_keys, sport_data: NFLData | NBAData = None):
        self.id = id
        self.sport_key = sport_key
        self.sport_title = sport_title
        self.commence_time = commence_time
        self.home_team = home_team
        self.away_team = away_team
        self.bookmakers = bookmakers
        self.markets = markets
        self.bookmaker_keys = bookmaker_keys
        self.sport_data = sport_data

        self.odds_df = self._odds_to_df(bookmakers)
        self._devig_odds()
        self._adjust_odds_for_betting_books(books=['prizepicks', 'underdog', 'betr_us_dfs', 'pick6'], price=1.82)
    
    def _odds_to_df(self, bookmakers):
        rows = []
        for bookmaker in bookmakers:
            for market in bookmaker['markets']:
                for outcome in market['outcomes']:
                    rows.append({
                        'bookmaker': bookmaker['key'],
                        'market': market['key'],
                        'player': outcome['description'],
                        'outcome': outcome['name'],
                        'line': outcome['point'],
                        'price': outcome['price'],
                        'last_update': market['last_update']
                    })
        return pd.DataFrame(rows)
    
    def _devig_odds(self):
        """
        Update odds_df to add column for devigged price and probability with multiplicative method
        """
        print(f'odds_df columns: {self.odds_df.columns.tolist()}')
        self.odds_df['implied_prob'] = 1 / self.odds_df['price']
        
        grouped = self.odds_df.groupby(['bookmaker', 'market', 'player', 'line'])

        self.odds_df['total_prob'] = grouped['implied_prob'].transform('sum')
        self.odds_df['devigged_prob'] = self.odds_df['implied_prob'] / self.odds_df['total_prob']
        self.odds_df['devigged_price'] = 1 / self.odds_df['devigged_prob']
        self.odds_df.drop(columns=['implied_prob', 'total_prob'], inplace=True)
    
    def _adjust_odds_for_betting_books(self, books: list[str], price: float = 1.82) -> None:
        mask = self.odds_df['bookmaker'].isin(books)
        self.odds_df.loc[mask, 'price'] = price
    
    
    def _calculate_true_mean_from_sharp(self, player: str, market: str, sharp_line: float, sharp_devigged_prob: float, std: float) -> float:
        """
        Back out the true mean from sharp book's line and probability using normal distribution.
        """
        try:
            if sharp_devigged_prob == 0.5:
                return np.float64(sharp_line)
            
            if std == 0 or np.isnan(std):
                print('STD Failed: Returning sharp line')
                return sharp_line
            
            # Back out the mean: μ = L - σ * Φ^(-1)(1 - p_over)
            # P(Over) = 1 - Φ((L - μ) / σ), solve for μ
            z_score = stats.norm.ppf(1 - sharp_devigged_prob)  # ppf is inverse CDF
            implied_mean = sharp_line - (std * z_score)
            
            return implied_mean

        except Exception as e:
            print(f"Error calculating implied mean for {player} {market}: {e}")
            return sharp_line  

    def _calculate_prob_with_sharp_mean(self, player: str, market: str, sharp_mean: float, betting_line: float, outcome: str, std: float) -> float:
        """
        Calculate the probability of an outcome using normal distribution.
        """
        try:
            
            if std == 0 or np.isnan(std):
                print(f'STD Failed: Returning based on mean for player: {player}, market: {market}')
                if outcome == 'Over':
                    return 1.0 if sharp_mean > betting_line else 0.0
                else:
                    return 1.0 if sharp_mean < betting_line else 0.0
            
            # Use normal distribution to calculate probability
            if outcome == 'Over':
                prob = 1 - stats.norm.cdf(betting_line, loc=sharp_mean, scale=std)
            else:  # Under
                prob = stats.norm.cdf(betting_line, loc=sharp_mean, scale=std)
            
            return prob
                
        except Exception as e:
            print(f"Error calculating probability for {player} {market}: {e}")
            return None

    def find_plus_ev(self, betting_books: list[str], sharp_books: list[str], threshold: float=0.0) -> pd.DataFrame:
        """
        @param betting_books: Bookmakers user is betting on
        @param sharp_books: List of bookmakers to use for sharp odds (their lines used as true mean)
        @param threshold: Threshold for plus EV, default of 0.03
        @return: DataFrame with plus EV bets
        """
        sharp_df = self.odds_df[self.odds_df['bookmaker'].isin(sharp_books)].copy()
        betting_df = self.odds_df[self.odds_df['bookmaker'].isin(betting_books)].copy()
        plus_ev_bets = []

        print(f"Finding plus EV bets {len(betting_df)} for {self.home_team} {self.away_team} {self.commence_time}")
        
        for _, bet in betting_df.iterrows():
            sharp_match_over = sharp_df[
                (sharp_df['player'] == bet['player']) & 
                (sharp_df['market'] == bet['market']) & 
                (sharp_df['outcome'] == 'Over')
            ]
            
            if sharp_match_over.empty:
                continue
            
            std, sample_size = self.sport_data.get_std_dev(bet['player'], bet['market'])

            implied_means = []
            implied_means_with_bookmaker = []
            for _, sharp_bet in sharp_match_over.iterrows():

                mean = self._calculate_true_mean_from_sharp(
                    bet['player'],
                    bet['market'],
                    sharp_bet['line'],
                    sharp_bet['devigged_prob'],
                    std
                )
                implied_means.append(mean)
                implied_means_with_bookmaker.append({
                    'bookmaker': sharp_bet['bookmaker'],
                    'implied_mean': mean
                })

            sharp_mean = np.mean(implied_means)

            print(f"player: {bet['player']}, market: {bet['market']}, sharp_mean: {sharp_mean}, implied_means: {implied_means}, num_sharp_books: {len(sharp_match_over)}")

            true_prob = self._calculate_prob_with_sharp_mean(
                bet['player'], 
                bet['market'], 
                sharp_mean,
                bet['line'], 
                bet['outcome'],
                std
            )
            
            if true_prob is None:
                print('True prob is None')
                continue
            
            ev_percent = ((true_prob * bet['price']) - 1) * 100
    
            if ev_percent >= threshold:
                plus_ev_bets.append({
                    'bookmaker': bet['bookmaker'],
                    'sport_key': self.sport_key,
                    'market': bet['market'],
                    'player': bet['player'],
                    'outcome': bet['outcome'],
                    'betting_line': bet['line'],
                    'sharp_mean': sharp_mean,
                    'implied_means': implied_means_with_bookmaker,
                    'std_dev': std,
                    'sample_size': sample_size,
                    'mean_diff': bet['line'] - sharp_mean,
                    'ev_percent': ev_percent,
                    'price': bet['price'],
                    'true_prob': true_prob,
                    'home_team': self.home_team,
                    'away_team': self.away_team,
                    'commence_time': self.commence_time
                })
        
        result_df = pd.DataFrame(plus_ev_bets)
        if len(result_df) > 0:
            result_df = result_df.sort_values('ev_percent', ascending=False)
            result_df = result_df[result_df['sample_size'] > 1]
        
        return result_df
    

        

    def __str__(self):
        return f"Game(id={self.id}, sport_key={self.sport_key}, sport_title={self.sport_title}, commence_time={self.commence_time}, home_team={self.home_team}, away_team={self.away_team}, bookmakers={self.bookmaker_keys}, markets={self.markets})"




