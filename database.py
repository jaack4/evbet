import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime

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
    
    def insert_ev_bets(self, ev_bets_df, game_id):
        """
        Insert EV bets from a DataFrame as active bets.
        All bets are inserted as active (is_active = TRUE).
        
        Args:
            ev_bets_df (pd.DataFrame): DataFrame containing EV bets
            game_id (str): The game ID to associate bets with
        """
        if len(ev_bets_df) == 0:
            print(f"No EV bets to insert for game {game_id}")
            return
        
        with self.conn.cursor() as cur:
            inserted_count = 0
            for _, bet in ev_bets_df.iterrows():
                try:
                    # Insert the new bet as active
                    cur.execute("""
                        INSERT INTO ev_bets 
                        (game_id, bookmaker, market, player, outcome, betting_line, 
                         sharp_mean, mean_diff, ev_percent, price, true_prob)
                        VALUES 
                        (%(game_id)s, %(bookmaker)s, %(market)s, %(player)s, 
                         %(outcome)s, %(betting_line)s, %(sharp_mean)s, %(mean_diff)s, 
                         %(ev_percent)s, %(price)s, %(true_prob)s)
                    """, {
                        'game_id': game_id,
                        'bookmaker': bet['bookmaker'],
                        'market': bet['market'],
                        'player': bet['player'],
                        'outcome': bet['outcome'],
                        'betting_line': float(bet['betting_line']),
                        'sharp_mean': float(bet['sharp_mean']),
                        'mean_diff': float(bet['mean_diff']),
                        'ev_percent': float(bet['ev_percent']),
                        'price': float(bet['price']),
                        'true_prob': float(bet['true_prob'])
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
    
    def get_active_ev_bets(self, limit=100):
        """
        Get active EV bets sorted by EV percentage
        
        Args:
            limit (int): Maximum number of bets to return
            
        Returns:
            list: List of active EV bets
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT eb.*, g.home_team, g.away_team, g.commence_time, g.sport_title
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
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

