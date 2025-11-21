import pandas as pd
import numpy as np
from scipy import stats
from nfl_data import NFLData


class Game:
    def __init__(self, id, sport_key, sport_title, commence_time, home_team, away_team, bookmakers, markets, bookmaker_keys, nfl_data: NFLData = None):
        self.id = id
        self.sport_key = sport_key
        self.sport_title = sport_title
        self.commence_time = commence_time
        self.home_team = home_team
        self.away_team = away_team
        self.bookmakers = bookmakers
        self.markets = markets
        self.bookmaker_keys = bookmaker_keys
        self.nfl_data = nfl_data if nfl_data else NFLData()

        self.odds_df = self._odds_to_df(bookmakers)
        self._devig_odds()
    
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
        self.odds_df['implied_prob'] = 1 / self.odds_df['price']
        
        grouped = self.odds_df.groupby(['bookmaker', 'market', 'player', 'line'])

        self.odds_df['total_prob'] = grouped['implied_prob'].transform('sum')
        self.odds_df['devigged_prob'] = self.odds_df['implied_prob'] / self.odds_df['total_prob']
        self.odds_df['devigged_price'] = 1 / self.odds_df['devigged_prob']
        self.odds_df.drop(columns=['implied_prob', 'total_prob'], inplace=True)
    
    def _calculate_true_mean_from_sharp(self, player: str, market: str, sharp_line: float, sharp_devigged_prob: float) -> float:
        """
        Back out the true mean from sharp line and devigged probability
        @param player: Player name
        @param market: Market key
        @param sharp_line: Sharp book's line
        @param sharp_devigged_prob: Sharp book's devigged probability for OVER
        @return: Implied true mean
        """
        try:
            std = self.nfl_data.get_std_dev(player, market)
            
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
            return sharp_line  # Fallback to using line as mean

    def _calculate_prob_with_sharp_mean(self, player: str, market: str, sharp_mean: float, betting_line: float, outcome: str) -> float:
        """
        Calculate probability of hitting a betting line using sharp-implied mean and historical std dev
        @param player: Player name
        @param market: Market key (e.g., 'player_pass_yds')
        @param sharp_mean: Sharp book's implied mean (adjusted for non-50/50 odds)
        @param betting_line: Betting book's line to evaluate
        @param outcome: 'Over' or 'Under'
        @return: Probability between 0 and 1
        """
        try:
            std = self.nfl_data.get_std_dev(player, market)
            
            if std == 0 or np.isnan(std):
                # If no variance, return based on comparison to mean
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

    def find_plus_ev(self, betting_books: list[str], sharp_books: list[str], threshold: float=0.03) -> pd.DataFrame:
        """
        @param betting_books: Bookmakers user is betting on
        @param sharp_books: List of bookmakers to use for sharp odds (their lines used as true mean)
        @param threshold: Threshold for plus EV, default of 0.03
        @return: DataFrame with plus EV bets
        """
        sharp_df = self.odds_df[self.odds_df['bookmaker'].isin(sharp_books)].copy()
        betting_df = self.odds_df[self.odds_df['bookmaker'].isin(betting_books)].copy()
        plus_ev_bets = []

        for _, bet in betting_df.iterrows():
            # Find corresponding sharp book lines for same player/market (both Over and Under)
            sharp_match_over = sharp_df[
                (sharp_df['player'] == bet['player']) & 
                (sharp_df['market'] == bet['market']) & 
                (sharp_df['outcome'] == 'Over')
            ]
            
            if sharp_match_over.empty:
                continue
            
            # Get sharp line and devigged probability for Over
            sharp_line = sharp_match_over.iloc[0]['line']
            sharp_devigged_prob_over = sharp_match_over.iloc[0]['devigged_prob']

            print(f'player: {bet['player']}, market: {bet['market']}, sharp_line: {sharp_line}, sharp_devigged_prob_over: {sharp_devigged_prob_over}')
            
            # Calculate the true implied mean from sharp book's odds
            sharp_mean = self._calculate_true_mean_from_sharp(
                bet['player'],
                bet['market'],
                sharp_line,
                sharp_devigged_prob_over
            )
            
            # Calculate true probability using sharp-implied mean, historical std dev
            true_prob = self._calculate_prob_with_sharp_mean(
                bet['player'], 
                bet['market'], 
                sharp_mean,
                bet['line'], 
                bet['outcome']
            )
            
            if true_prob is None:
                continue
            
            # Calculate EV: (probability * decimal_odds) - 1
            ev = (true_prob * bet['price']) - 1
            
            # Only include if EV exceeds threshold
            if ev >= threshold:
                plus_ev_bets.append({
                    'bookmaker': bet['bookmaker'],
                    'market': bet['market'],
                    'player': bet['player'],
                    'outcome': bet['outcome'],
                    'betting_line': bet['line'],
                    'sharp_line': sharp_line,
                    'sharp_mean': sharp_mean,
                    'line_diff': bet['line'] - sharp_line,
                    'mean_diff': bet['line'] - sharp_mean,
                    'price': bet['price'],
                    'true_prob': true_prob,
                    'implied_prob': 1 / bet['price'],
                    'sharp_devigged_prob': sharp_devigged_prob_over if bet['outcome'] == 'Over' else (1 - sharp_devigged_prob_over),
                    'ev': ev,
                    'ev_percent': ev * 100
                })
        
        result_df = pd.DataFrame(plus_ev_bets)
        if len(result_df) > 0:
            result_df = result_df.sort_values('ev', ascending=False)
        
        return result_df
        

    def __str__(self):
        return f"Game(id={self.id}, sport_key={self.sport_key}, sport_title={self.sport_title}, commence_time={self.commence_time}, home_team={self.home_team}, away_team={self.away_team}, bookmakers={self.bookmaker_keys}, markets={self.markets})"




