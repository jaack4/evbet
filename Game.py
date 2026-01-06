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
        self.odds_df['implied_prob'] = 1 / self.odds_df['price']
        
        grouped = self.odds_df.groupby(['bookmaker', 'market', 'player', 'line'])

        self.odds_df['total_prob'] = grouped['implied_prob'].transform('sum')
        self.odds_df['devigged_prob'] = self.odds_df['implied_prob'] / self.odds_df['total_prob']
        self.odds_df['devigged_price'] = 1 / self.odds_df['devigged_prob']
        self.odds_df.drop(columns=['implied_prob', 'total_prob'], inplace=True)
    
    def _adjust_odds_for_betting_books(self, books: list[str], price: float = 1.82) -> None:
        mask = self.odds_df['bookmaker'].isin(books)
        self.odds_df.loc[mask, 'price'] = price

    def _get_std_dev_batch(self, player_market_pairs: pd.DataFrame) -> dict:
        """
        Batch fetch std_dev for all unique player/market combinations.
        Returns dict mapping (player, market) -> (std, sample_size)
        """
        cache = {}
        unique_pairs = player_market_pairs[['player', 'market']].drop_duplicates()
        
        failed_lookups = []
        low_sample_size = []
        
        for _, row in unique_pairs.iterrows():
            key = (row['player'], row['market'])
            if key not in cache:
                std, sample_size = self.sport_data.get_std_dev(row['player'], row['market'])
                cache[key] = (std, sample_size)
                
                # Log issues
                if np.isnan(std) or std == 0:
                    failed_lookups.append(f"{row['player']} - {row['market']}")
                elif sample_size <= 1:
                    low_sample_size.append(f"{row['player']} - {row['market']} (n={sample_size})")
        
        if failed_lookups:
            print(f"WARNING: Failed to get valid std_dev for {len(failed_lookups)} player/market combinations:")
            for item in failed_lookups[:5]:  # Show first 5
                print(f"  - {item}")
            if len(failed_lookups) > 5:
                print(f"  ... and {len(failed_lookups) - 5} more")
        
        if low_sample_size:
            print(f"WARNING: Low sample size for {len(low_sample_size)} player/market combinations:")
            for item in low_sample_size[:5]:  # Show first 5
                print(f"  - {item}")
            if len(low_sample_size) > 5:
                print(f"  ... and {len(low_sample_size) - 5} more")
        
        return cache
    
    def _add_std_dev_to_dataframe(self, df: pd.DataFrame, std_cache: dict) -> pd.DataFrame:
        """
        Add std_dev and sample_size columns to dataframe using cached values.
        """
        df['_key'] = list(zip(df['player'], df['market']))
        df['std_dev'] = df['_key'].map(lambda k: std_cache.get(k, (np.nan, 0))[0])
        df['sample_size'] = df['_key'].map(lambda k: std_cache.get(k, (np.nan, 0))[1])
        df.drop(columns=['_key'], inplace=True)
        return df
    
    def _calculate_sharp_means(self, sharp_over_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate implied means from sharp book lines and aggregate per player/market.
        
        Uses the formula: μ = L - σ * Φ^(-1)(1 - p_over)
        where L is the line, σ is std dev, and p_over is the devigged probability
        """
        # Handle edge cases
        valid_std_mask = (sharp_over_df['std_dev'] > 0) & (~sharp_over_df['std_dev'].isna())
        prob_not_half_mask = sharp_over_df['devigged_prob'] != 0.5
        
        # Log edge cases with player names
        invalid_std_count = (~valid_std_mask).sum()
        prob_half_count = (~prob_not_half_mask).sum()
        
        if invalid_std_count > 0:
            invalid_players = sharp_over_df[~valid_std_mask][['player', 'market']].drop_duplicates()
            print(f"INFO: {invalid_std_count} sharp lines using fallback (line value) due to invalid std_dev")
            print(f"      Players affected:")
            for _, row in invalid_players.head(10).iterrows():
                print(f"        - {row['player']} ({row['market']})")
            if len(invalid_players) > 10:
                print(f"        ... and {len(invalid_players) - 10} more")
        
        if prob_half_count > 0:
            print(f"INFO: {prob_half_count} sharp lines at exactly 50% probability (using line value)")
        
        # Default to line value
        sharp_over_df['implied_mean'] = sharp_over_df['line']
        
        # Calculate z-scores and implied means where valid
        calc_mask = valid_std_mask & prob_not_half_mask
        calculated_count = calc_mask.sum()
        
        if calc_mask.any():
            z_scores = stats.norm.ppf(1 - sharp_over_df.loc[calc_mask, 'devigged_prob'].values)
            sharp_over_df.loc[calc_mask, 'implied_mean'] = (
                sharp_over_df.loc[calc_mask, 'line'].values - 
                (sharp_over_df.loc[calc_mask, 'std_dev'].values * z_scores)
            )
            print(f"INFO: Calculated implied means for {calculated_count} sharp lines using Normal distribution")
        
        # Aggregate sharp means per player/market with bookmaker details
        sharp_agg = sharp_over_df.groupby(['player', 'market']).agg(
            sharp_mean=('implied_mean', 'mean'),
            implied_means_list=('implied_mean', list),
            bookmakers_list=('bookmaker', list)
        ).reset_index()
        
        # Create implied_means column with bookmaker info
        sharp_agg['implied_means'] = sharp_agg.apply(
            lambda row: [{'bookmaker': b, 'implied_mean': m} 
                        for b, m in zip(row['bookmakers_list'], row['implied_means_list'])],
            axis=1
        )
        sharp_agg.drop(columns=['implied_means_list', 'bookmakers_list'], inplace=True)
        
        return sharp_agg
    
    def _calculate_true_probabilities(self, merged: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate true probabilities using normal distribution or mean comparison.
        """
        valid_std = (merged['std_dev'] > 0) & (~merged['std_dev'].isna())
        merged['true_prob'] = np.nan
        
        valid_count = valid_std.sum()
        invalid_count = (~valid_std).sum()
        
        # For valid std_dev: use normal distribution
        if valid_std.any():
            over_mask = valid_std & (merged['outcome'] == 'Over')
            under_mask = valid_std & (merged['outcome'] == 'Under')
            
            if over_mask.any():
                merged.loc[over_mask, 'true_prob'] = 1 - stats.norm.cdf(
                    merged.loc[over_mask, 'line'].values,
                    loc=merged.loc[over_mask, 'sharp_mean'].values,
                    scale=merged.loc[over_mask, 'std_dev'].values
                )
            
            if under_mask.any():
                merged.loc[under_mask, 'true_prob'] = stats.norm.cdf(
                    merged.loc[under_mask, 'line'].values,
                    loc=merged.loc[under_mask, 'sharp_mean'].values,
                    scale=merged.loc[under_mask, 'std_dev'].values
                )
            
            print(f"INFO: Calculated probabilities using Normal distribution for {valid_count} bets")
        
        # For invalid std_dev: use mean comparison
        invalid_std = ~valid_std
        if invalid_std.any():
            over_invalid = invalid_std & (merged['outcome'] == 'Over')
            under_invalid = invalid_std & (merged['outcome'] == 'Under')
            
            merged.loc[over_invalid, 'true_prob'] = (
                merged.loc[over_invalid, 'sharp_mean'] > merged.loc[over_invalid, 'line']
            ).astype(float)
            merged.loc[under_invalid, 'true_prob'] = (
                merged.loc[under_invalid, 'sharp_mean'] < merged.loc[under_invalid, 'line']
            ).astype(float)
            
            print(f"WARNING: Using mean comparison fallback for {invalid_count} bets (no valid std_dev)")
            invalid_players = merged[invalid_std][['player', 'market', 'bookmaker']].drop_duplicates()
            print(f"         Players affected:")
            for _, row in invalid_players.head(10).iterrows():
                print(f"           - {row['player']} ({row['market']}) on {row['bookmaker']}")
            if len(invalid_players) > 10:
                print(f"           ... and {len(invalid_players) - 10} more")
        
        return merged
    
    def _format_results(self, merged: pd.DataFrame, threshold: float) -> pd.DataFrame:
        """
        Calculate EV, filter by threshold and sample size, and format output.
        """
        # Calculate EV percentage (vectorized)
        merged['ev_percent'] = ((merged['true_prob'] * merged['price']) - 1) * 100
        merged['mean_diff'] = merged['line'] - merged['sharp_mean']
        
        total_bets = len(merged)
        above_threshold = (merged['ev_percent'] >= threshold).sum()
        
        # Identify bets filtered by low sample size
        low_sample_mask = (merged['sample_size'] <= 1)
        low_sample = low_sample_mask.sum()
        
        # Filter by threshold and sample size
        result_df = merged[
            (merged['ev_percent'] >= threshold) & 
            (merged['sample_size'] > 1)
        ].copy()
        
        final_count = len(result_df)
        
        # Log filtering summary
        print(f"INFO: Filtering summary:")
        print(f"  - Total bets evaluated: {total_bets}")
        print(f"  - Bets meeting EV threshold (>={threshold}%): {above_threshold}")
        print(f"  - Bets filtered due to low sample size (<=1): {low_sample}")
        
        # Show which players had low sample size
        if low_sample > 0:
            low_sample_players = merged[low_sample_mask][['player', 'market', 'sample_size']].drop_duplicates()
            print(f"      Players with low sample size:")
            for _, row in low_sample_players.head(10).iterrows():
                print(f"        - {row['player']} ({row['market']}) n={row['sample_size']}")
            if len(low_sample_players) > 10:
                print(f"        ... and {len(low_sample_players) - 10} more")
        
        print(f"  - Final EV bets: {final_count}")
        
        if final_count == 0:
            below_threshold = total_bets - above_threshold
            if below_threshold > 0:
                print(f"INFO: {below_threshold} bets were below EV threshold")
            if low_sample > 0:
                print(f"INFO: Consider lowering sample size requirement if too many bets are filtered")
            return pd.DataFrame()
        
        # Add game metadata
        result_df['sport_key'] = self.sport_key
        result_df['home_team'] = self.home_team
        result_df['away_team'] = self.away_team
        result_df['commence_time'] = self.commence_time
        
        # Select and rename columns to match expected output format
        result_df = result_df.rename(columns={'line': 'betting_line'})
        result_df = result_df[[
            'bookmaker', 'sport_key', 'market', 'player', 'outcome',
            'betting_line', 'sharp_mean', 'implied_means', 'std_dev', 
            'sample_size', 'mean_diff', 'ev_percent', 'price', 'true_prob',
            'home_team', 'away_team', 'commence_time'
        ]]
        
        # Sort by EV
        result_df = result_df.sort_values('ev_percent', ascending=False)
        
        return result_df

    def find_plus_ev(self, betting_books: list[str], sharp_books: list[str], threshold: float=0.0) -> pd.DataFrame:
        """
        Find positive expected value (EV) bets using vectorized operations.
        
        @param betting_books: Bookmakers user is betting on
        @param sharp_books: Bookmakers to use for sharp odds (their lines used as true mean)
        @param threshold: Minimum EV percentage to include in results (default 0.0)
        @return: DataFrame with plus EV bets sorted by EV percentage
        """
        print(f"\n{'='*60}")
        print(f"Finding EV bets for {self.home_team} vs {self.away_team}")
        print(f"Betting books: {betting_books}")
        print(f"Sharp books: {sharp_books}")
        print(f"EV threshold: {threshold}%")
        print(f"{'='*60}")
        
        # Filter dataframes
        sharp_df = self.odds_df[self.odds_df['bookmaker'].isin(sharp_books)].copy()
        betting_df = self.odds_df[self.odds_df['bookmaker'].isin(betting_books)].copy()
        
        print(f"INFO: Found {len(betting_df)} betting lines and {len(sharp_df)} sharp lines")
        
        if betting_df.empty:
            print("WARNING: No betting lines found for specified betting books")
            return pd.DataFrame()
        
        if sharp_df.empty:
            print("WARNING: No sharp lines found for specified sharp books")
            return pd.DataFrame()
        
        # Get only 'Over' outcomes from sharp books for mean calculation
        sharp_over_df = sharp_df[sharp_df['outcome'] == 'Over'].copy()
        
        print(f"INFO: Found {len(sharp_over_df)} sharp 'Over' lines for mean calculation")
        
        if sharp_over_df.empty:
            print("WARNING: No 'Over' outcomes found in sharp books")
            return pd.DataFrame()
        
        # Pre-fetch all std_dev values at once (cached lookup)
        print("\nFetching standard deviations...")
        std_cache = self._get_std_dev_batch(betting_df)
        
        # Add std_dev and sample_size to both dataframes
        betting_df = self._add_std_dev_to_dataframe(betting_df, std_cache)
        sharp_over_df = self._add_std_dev_to_dataframe(sharp_over_df, std_cache)
        
        # Calculate sharp means from sharp book lines
        print("\nCalculating sharp means...")
        sharp_agg = self._calculate_sharp_means(sharp_over_df)
        
        print(f"INFO: Calculated sharp means for {len(sharp_agg)} unique player/market combinations")
        
        # Merge betting bets with aggregated sharp data
        merged = betting_df.merge(sharp_agg, on=['player', 'market'], how='inner')
        
        unmatched = len(betting_df) - len(merged)
        if unmatched > 0:
            print(f"WARNING: {unmatched} betting lines had no matching sharp data and were excluded")
        
        if merged.empty:
            print("WARNING: No betting lines matched with sharp data")
            return pd.DataFrame()
        
        print(f"INFO: {len(merged)} betting lines matched with sharp data")
        
        # Calculate true probabilities
        print("\nCalculating true probabilities...")
        merged = self._calculate_true_probabilities(merged)
        
        # Format results and filter by threshold
        print("\nFiltering and formatting results...")
        result_df = self._format_results(merged, threshold)
        
        print(f"{'='*60}\n")
        
        return result_df
    

        

    def __str__(self):
        return f"Game(id={self.id}, sport_key={self.sport_key}, sport_title={self.sport_title}, commence_time={self.commence_time}, home_team={self.home_team}, away_team={self.away_team}, bookmakers={self.bookmaker_keys}, markets={self.markets})"




