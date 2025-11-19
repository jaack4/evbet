import pandas as pd



class Game:
    def __init__(self, id, sport_key, sport_title, commence_time, home_team, away_team, bookmakers, markets, bookmaker_keys):
        self.id = id
        self.sport_key = sport_key
        self.sport_title = sport_title
        self.commence_time = commence_time
        self.home_team = home_team
        self.away_team = away_team
        self.bookmakers = bookmakers
        self.markets = markets
        self.bookmaker_keys = bookmaker_keys

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
        Update odds_df to add column for devigged price by adding price of
        over and under for same player and market
        """
        self.odds_df['implied_prob'] = 1 / self.odds_df['price']
        
        # Group by bookmaker, market, player, and line to find Over/Under pairs
        grouped = self.odds_df.groupby(['bookmaker', 'market', 'player', 'line'])
        
        # Calculate total implied probability for each pair
        self.odds_df['total_prob'] = grouped['implied_prob'].transform('sum')
        
        # Devig using multiplicative method: divide each implied prob by total
        self.odds_df['devigged_prob'] = self.odds_df['implied_prob'] / self.odds_df['total_prob']
        
        # Convert back to decimal odds
        self.odds_df['devigged_price'] = 1 / self.odds_df['devigged_prob']
        
        # Optional: clean up intermediate columns
        self.odds_df.drop(columns=['implied_prob', 'total_prob'], inplace=True)

        

    def __str__(self):
        return f"Game(id={self.id}, sport_key={self.sport_key}, sport_title={self.sport_title}, commence_time={self.commence_time}, home_team={self.home_team}, away_team={self.away_team}, bookmakers={self.bookmaker_keys}, markets={self.markets})"

