import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import pandas as pd
from datetime import datetime
import json

class Database:
    def __init__(self):
        """Initialize database connection"""
        self.conn = psycopg2.connect(
            os.getenv('DATABASE_URL'),
            cursor_factory=RealDictCursor
        )
    
    def insert_game(self, game_data):
        """
        Insert a game into the database
        
        Args:
            game_data (dict): Dictionary containing game information
                - id, sport_key, sport_title, commence_time, home_team, away_team
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO games (id, sport_key, sport_title, commence_time, home_team, away_team)
                VALUES (%(id)s, %(sport_key)s, %(sport_title)s, %(commence_time)s, %(home_team)s, %(away_team)s)
                ON CONFLICT (id) DO UPDATE SET
                    commence_time = EXCLUDED.commence_time,
                    home_team = EXCLUDED.home_team,
                    away_team = EXCLUDED.away_team,
                    updated_at = CURRENT_TIMESTAMP
            """, game_data)
            self.conn.commit()
    
    def deactivate_all_bets(self):
        """
        Deactivate all currently active bets.
        Called at the start of each update cycle to ensure only the most recent bets are active.
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE ev_bets 
                SET is_active = FALSE 
                WHERE is_active = TRUE
            """)
            rows_affected = cur.rowcount
            self.conn.commit()
            if rows_affected > 0:
                print(f"Deactivated {rows_affected} previously active bets")
    
    def deactivate_bets_for_sport(self, sport_title):
        """
        Deactivate all currently active bets for a specific sport.
        This allows multiple scheduler instances to run concurrently without interfering.
        
        Args:
            sport_title (str): The sport title (e.g., 'NFL', 'NBA')
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE ev_bets 
                SET is_active = FALSE 
                WHERE is_active = TRUE
                AND game_id IN (
                    SELECT id FROM games WHERE sport_title = %s
                )
            """, (sport_title,))
            rows_affected = cur.rowcount
            self.conn.commit()
            if rows_affected > 0:
                print(f"Deactivated {rows_affected} previously active {sport_title} bets")
    
    def insert_ev_bets(self, ev_bets_df, game_id):
        """
        Insert EV bets from a DataFrame as active bets.
        All bets are inserted as active (is_active = TRUE).
        Only inserts bets if the game has not yet commenced.
        
        Args:
            ev_bets_df (pd.DataFrame): DataFrame containing EV bets
            game_id (str): The game ID to associate bets with
        """
        if len(ev_bets_df) == 0:
            print(f"No EV bets to insert for game {game_id}")
            return
        
        # Get game information for denormalization
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT home_team, away_team, commence_time 
                FROM games 
                WHERE id = %s
            """, (game_id,))
            game_info = cur.fetchone()
            
            if not game_info:
                print(f"Warning: Game {game_id} not found in database. Cannot insert bets.")
                return
            
            # Check if game has already commenced
            if game_info['commence_time'] <= datetime.now(game_info['commence_time'].tzinfo):
                print(f"Warning: Game {game_id} has already commenced. Skipping bet insertion to prevent invalid bets.")
                return
        
        with self.conn.cursor() as cur:
            inserted_count = 0
            for _, bet in ev_bets_df.iterrows():
                try:
                    # Insert the new bet as active with denormalized game data
                    # If duplicate exists, update the bet with new values
                    cur.execute("""
                        INSERT INTO ev_bets 
                        (game_id, bookmaker, market, player, outcome, betting_line, 
                         sharp_mean, std_dev, implied_means, sample_size, mean_diff, 
                         ev_percent, price, true_prob, home_team, away_team, commence_time)
                        VALUES 
                        (%(game_id)s, %(bookmaker)s, %(market)s, %(player)s, 
                         %(outcome)s, %(betting_line)s, %(sharp_mean)s, %(std_dev)s,
                         %(implied_means)s, %(sample_size)s, %(mean_diff)s, 
                         %(ev_percent)s, %(price)s, %(true_prob)s, %(home_team)s,
                         %(away_team)s, %(commence_time)s)
                        ON CONFLICT (game_id, bookmaker, market, player, outcome, betting_line)
                        DO UPDATE SET
                            sharp_mean = EXCLUDED.sharp_mean,
                            std_dev = EXCLUDED.std_dev,
                            implied_means = EXCLUDED.implied_means,
                            sample_size = EXCLUDED.sample_size,
                            mean_diff = EXCLUDED.mean_diff,
                            ev_percent = EXCLUDED.ev_percent,
                            price = EXCLUDED.price,
                            true_prob = EXCLUDED.true_prob,
                            is_active = TRUE,
                            created_at = CURRENT_TIMESTAMP
                    """, {
                        'game_id': game_id,
                        'bookmaker': bet['bookmaker'],
                        'market': bet['market'],
                        'player': bet['player'],
                        'outcome': bet['outcome'],
                        'betting_line': float(bet['betting_line']),
                        'sharp_mean': float(bet['sharp_mean']),
                        'std_dev': float(bet['std_dev']) if 'std_dev' in bet and bet['std_dev'] is not None else None,
                        'implied_means': Json(bet['implied_means']) if 'implied_means' in bet and bet['implied_means'] is not None else None,
                        'sample_size': int(bet['sample_size']) if 'sample_size' in bet and bet['sample_size'] is not None else None,
                        'mean_diff': float(bet['mean_diff']),
                        'ev_percent': float(bet['ev_percent']),
                        'price': float(bet['price']),
                        'true_prob': float(bet['true_prob']),
                        'home_team': game_info['home_team'],
                        'away_team': game_info['away_team'],
                        'commence_time': game_info['commence_time']
                    })
                    inserted_count += 1
                except Exception as e:
                    print(f"Error inserting bet for {bet.get('player', 'unknown')}: {e}")
                    continue
            
            self.conn.commit()
            print(f"Inserted {inserted_count} EV bets for game {game_id}")
    
    def deactivate_old_bets(self, hours=24):
        """
        Mark bets older than X hours as inactive
        
        Args:
            hours (int): Number of hours after which to deactivate bets
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE ev_bets 
                SET is_active = FALSE 
                WHERE created_at < NOW() - INTERVAL '%s hours' 
                AND is_active = TRUE
            """ % hours)
            rows_affected = cur.rowcount
            self.conn.commit()
            print(f"Deactivated {rows_affected} old bets (older than {hours} hours)")
    
    def deactivate_commenced_bets(self):
        """
        Mark bets for games that have already started as inactive
        This keeps active_ev_bets relevant by only showing upcoming games
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE ev_bets 
                SET is_active = FALSE 
                WHERE game_id IN (
                    SELECT id FROM games WHERE commence_time < NOW()
                )
                AND is_active = TRUE
            """)
            rows_affected = cur.rowcount
            self.conn.commit()
            if rows_affected > 0:
                print(f"Deactivated {rows_affected} bets for commenced games")
    
    def get_active_ev_bets(self, limit=400):
        """
        Get active EV bets sorted by EV percentage
        
        Args:
            limit (int): Maximum number of bets to return
            
        Returns:
            list: List of active EV bets
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT eb.*, g.sport_title
                FROM ev_bets eb
                JOIN games g ON eb.game_id = g.id
                WHERE eb.is_active = TRUE
                ORDER BY eb.ev_percent DESC
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
    
    def get_bet_statistics(self):
        """Get statistics about stored bets"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_bets,
                    COUNT(CASE WHEN is_active THEN 1 END) as active_bets,
                    AVG(ev_percent) as avg_ev_percent,
                    MAX(ev_percent) as max_ev_percent,
                    MIN(created_at) as oldest_bet,
                    MAX(created_at) as newest_bet
                FROM ev_bets
            """)
            return cur.fetchone()
    
    def get_nfl_win_loss_stats(self, min_ev=None, min_mean_diff=None):
        """
        Get win/loss statistics for NFL bets
        
        Args:
            min_ev (float, optional): Minimum EV percentage to filter by
            min_mean_diff (float, optional): Minimum absolute mean difference to filter by
        
        Returns:
            dict: Dictionary containing win/loss stats including:
                - total_bets: Total number of NFL bets with results
                - wins: Number of winning bets
                - losses: Number of losing bets
                - win_rate: Win percentage
                - avg_ev_won: Average EV% of winning bets
                - avg_ev_lost: Average EV% of losing bets
                - total_ev: Average EV% of all graded bets
        """
        with self.conn.cursor() as cur:
            filters = []
            params = []
            
            if min_ev is not None:
                filters.append("eb.ev_percent >= %s")
                params.append(min_ev)
            
            if min_mean_diff is not None:
                filters.append("ABS(eb.mean_diff) >= %s")
                params.append(min_mean_diff)
            
            filter_clause = "AND " + " AND ".join(filters) if filters else ""
            params = tuple(params)
            
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total_bets,
                    COUNT(CASE WHEN eb.win = TRUE THEN 1 END) as wins,
                    COUNT(CASE WHEN eb.win = FALSE THEN 1 END) as losses,
                    ROUND(
                        COUNT(CASE WHEN eb.win = TRUE THEN 1 END)::numeric / 
                        NULLIF(COUNT(*), 0) * 100, 
                        2
                    ) as win_rate,
                    AVG(CASE WHEN eb.win = TRUE THEN eb.ev_percent END) as avg_ev_won,
                    AVG(CASE WHEN eb.win = FALSE THEN eb.ev_percent END) as avg_ev_lost,
                    AVG(eb.ev_percent) as total_ev,
                    MIN(eb.commence_time) as first_bet_date,
                    MAX(eb.commence_time) as last_bet_date
                FROM ev_bets eb
                JOIN games g ON eb.game_id = g.id
                WHERE g.sport_title = 'NFL'
                AND eb.win IS NOT NULL
                {filter_clause}
            """, params)
            return cur.fetchone()
    
    def get_nfl_win_loss_by_bookmaker(self, min_ev=None, min_mean_diff=None):
        """
        Get win/loss statistics for NFL bets grouped by bookmaker
        
        Args:
            min_ev (float, optional): Minimum EV percentage to filter by
            min_mean_diff (float, optional): Minimum absolute mean difference to filter by
        
        Returns:
            list: List of dictionaries with stats per bookmaker
        """
        with self.conn.cursor() as cur:
            filters = []
            params = []
            
            if min_ev is not None:
                filters.append("eb.ev_percent >= %s")
                params.append(min_ev)
            
            if min_mean_diff is not None:
                filters.append("ABS(eb.mean_diff) >= %s")
                params.append(min_mean_diff)
            
            filter_clause = "AND " + " AND ".join(filters) if filters else ""
            params = tuple(params)
            
            cur.execute(f"""
                SELECT 
                    eb.bookmaker,
                    COUNT(*) as total_bets,
                    COUNT(CASE WHEN eb.win = TRUE THEN 1 END) as wins,
                    COUNT(CASE WHEN eb.win = FALSE THEN 1 END) as losses,
                    ROUND(
                        COUNT(CASE WHEN eb.win = TRUE THEN 1 END)::numeric / 
                        NULLIF(COUNT(*), 0) * 100, 
                        2
                    ) as win_rate,
                    AVG(eb.ev_percent) as avg_ev
                FROM ev_bets eb
                JOIN games g ON eb.game_id = g.id
                WHERE g.sport_title = 'NFL'
                AND eb.win IS NOT NULL
                {filter_clause}
                GROUP BY eb.bookmaker
                ORDER BY total_bets DESC
            """, params)
            return cur.fetchall()
    
    def get_nfl_win_loss_by_market(self, min_ev=None, min_mean_diff=None):
        """
        Get win/loss statistics for NFL bets grouped by market type
        
        Args:
            min_ev (float, optional): Minimum EV percentage to filter by
            min_mean_diff (float, optional): Minimum absolute mean difference to filter by
        
        Returns:
            list: List of dictionaries with stats per market
        """
        with self.conn.cursor() as cur:
            filters = []
            params = []
            
            if min_ev is not None:
                filters.append("eb.ev_percent >= %s")
                params.append(min_ev)
            
            if min_mean_diff is not None:
                filters.append("ABS(eb.mean_diff) >= %s")
                params.append(min_mean_diff)
            
            filter_clause = "AND " + " AND ".join(filters) if filters else ""
            params = tuple(params)
            
            cur.execute(f"""
                SELECT 
                    eb.market,
                    COUNT(*) as total_bets,
                    COUNT(CASE WHEN eb.win = TRUE THEN 1 END) as wins,
                    COUNT(CASE WHEN eb.win = FALSE THEN 1 END) as losses,
                    ROUND(
                        COUNT(CASE WHEN eb.win = TRUE THEN 1 END)::numeric / 
                        NULLIF(COUNT(*), 0) * 100, 
                        2
                    ) as win_rate,
                    AVG(eb.ev_percent) as avg_ev
                FROM ev_bets eb
                JOIN games g ON eb.game_id = g.id
                WHERE g.sport_title = 'NFL'
                AND eb.win IS NOT NULL
                {filter_clause}
                GROUP BY eb.market
                ORDER BY total_bets DESC
            """, params)
            return cur.fetchall()
    
    def get_nba_win_loss_stats(self, min_ev=None, min_mean_diff=None):
        """
        Get win/loss statistics for NBA bets
        
        Args:
            min_ev (float, optional): Minimum EV percentage to filter by
            min_mean_diff (float, optional): Minimum absolute mean difference to filter by
        
        Returns:
            dict: Dictionary containing win/loss stats including:
                - total_bets: Total number of NBA bets with results
                - wins: Number of winning bets
                - losses: Number of losing bets
                - win_rate: Win percentage
                - avg_ev_won: Average EV% of winning bets
                - avg_ev_lost: Average EV% of losing bets
                - total_ev: Average EV% of all graded bets
        """
        with self.conn.cursor() as cur:
            filters = []
            params = []
            
            if min_ev is not None:
                filters.append("eb.ev_percent >= %s")
                params.append(min_ev)
            
            if min_mean_diff is not None:
                filters.append("ABS(eb.mean_diff) >= %s")
                params.append(min_mean_diff)
            
            filter_clause = "AND " + " AND ".join(filters) if filters else ""
            params = tuple(params)
            
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total_bets,
                    COUNT(CASE WHEN eb.win = TRUE THEN 1 END) as wins,
                    COUNT(CASE WHEN eb.win = FALSE THEN 1 END) as losses,
                    ROUND(
                        COUNT(CASE WHEN eb.win = TRUE THEN 1 END)::numeric / 
                        NULLIF(COUNT(*), 0) * 100, 
                        2
                    ) as win_rate,
                    AVG(CASE WHEN eb.win = TRUE THEN eb.ev_percent END) as avg_ev_won,
                    AVG(CASE WHEN eb.win = FALSE THEN eb.ev_percent END) as avg_ev_lost,
                    AVG(eb.ev_percent) as total_ev,
                    MIN(eb.commence_time) as first_bet_date,
                    MAX(eb.commence_time) as last_bet_date
                FROM ev_bets eb
                JOIN games g ON eb.game_id = g.id
                WHERE g.sport_title = 'NBA'
                AND eb.win IS NOT NULL
                {filter_clause}
            """, params)
            return cur.fetchone()
    
    def get_nba_win_loss_by_bookmaker(self, min_ev=None, min_mean_diff=None):
        """
        Get win/loss statistics for NBA bets grouped by bookmaker
        
        Args:
            min_ev (float, optional): Minimum EV percentage to filter by
            min_mean_diff (float, optional): Minimum absolute mean difference to filter by
        
        Returns:
            list: List of dictionaries with stats per bookmaker
        """
        with self.conn.cursor() as cur:
            filters = []
            params = []
            
            if min_ev is not None:
                filters.append("eb.ev_percent >= %s")
                params.append(min_ev)
            
            if min_mean_diff is not None:
                filters.append("ABS(eb.mean_diff) >= %s")
                params.append(min_mean_diff)
            
            filter_clause = "AND " + " AND ".join(filters) if filters else ""
            params = tuple(params)
            
            cur.execute(f"""
                SELECT 
                    eb.bookmaker,
                    COUNT(*) as total_bets,
                    COUNT(CASE WHEN eb.win = TRUE THEN 1 END) as wins,
                    COUNT(CASE WHEN eb.win = FALSE THEN 1 END) as losses,
                    ROUND(
                        COUNT(CASE WHEN eb.win = TRUE THEN 1 END)::numeric / 
                        NULLIF(COUNT(*), 0) * 100, 
                        2
                    ) as win_rate,
                    AVG(eb.ev_percent) as avg_ev
                FROM ev_bets eb
                JOIN games g ON eb.game_id = g.id
                WHERE g.sport_title = 'NBA'
                AND eb.win IS NOT NULL
                {filter_clause}
                GROUP BY eb.bookmaker
                ORDER BY total_bets DESC
            """, params)
            return cur.fetchall()
    
    def get_nba_win_loss_by_market(self, min_ev=None, min_mean_diff=None):
        """
        Get win/loss statistics for NBA bets grouped by market type
        
        Args:
            min_ev (float, optional): Minimum EV percentage to filter by
            min_mean_diff (float, optional): Minimum absolute mean difference to filter by
        
        Returns:
            list: List of dictionaries with stats per market
        """
        with self.conn.cursor() as cur:
            filters = []
            params = []
            
            if min_ev is not None:
                filters.append("eb.ev_percent >= %s")
                params.append(min_ev)
            
            if min_mean_diff is not None:
                filters.append("ABS(eb.mean_diff) >= %s")
                params.append(min_mean_diff)
            
            filter_clause = "AND " + " AND ".join(filters) if filters else ""
            params = tuple(params)
            
            cur.execute(f"""
                SELECT 
                    eb.market,
                    COUNT(*) as total_bets,
                    COUNT(CASE WHEN eb.win = TRUE THEN 1 END) as wins,
                    COUNT(CASE WHEN eb.win = FALSE THEN 1 END) as losses,
                    ROUND(
                        COUNT(CASE WHEN eb.win = TRUE THEN 1 END)::numeric / 
                        NULLIF(COUNT(*), 0) * 100, 
                        2
                    ) as win_rate,
                    AVG(eb.ev_percent) as avg_ev
                FROM ev_bets eb
                JOIN games g ON eb.game_id = g.id
                WHERE g.sport_title = 'NBA'
                AND eb.win IS NOT NULL
                {filter_clause}
                GROUP BY eb.market
                ORDER BY total_bets DESC
            """, params)
            return cur.fetchall()
    
    def remove_invalid_bets(self):
        """
        Remove bets where created_at is after commence_time
        These are invalid as bets should be placed before the game starts
        
        Returns:
            int: Number of bets deleted
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                DELETE FROM ev_bets
                WHERE created_at > commence_time
            """)
            self.conn.commit()
            return cur.rowcount
    
    def get_invalid_bets_count(self):
        """
        Count bets where created_at is after commence_time
        
        Returns:
            int: Number of invalid bets
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as count
                FROM ev_bets
                WHERE created_at > commence_time
            """)
            return cur.fetchone()['count']
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

