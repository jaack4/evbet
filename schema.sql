-- Database schema for EV betting application

-- Table for storing games
CREATE TABLE IF NOT EXISTS games (
    id VARCHAR(255) PRIMARY KEY,
    sport_key VARCHAR(100) NOT NULL,
    sport_title VARCHAR(100) NOT NULL,
    commence_time TIMESTAMP NOT NULL,
    home_team VARCHAR(255) NOT NULL,
    away_team VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing EV bets
CREATE TABLE IF NOT EXISTS ev_bets (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(255) REFERENCES games(id) ON DELETE CASCADE,
    bookmaker VARCHAR(100) NOT NULL,
    market VARCHAR(100) NOT NULL,
    player VARCHAR(255) NOT NULL,
    outcome VARCHAR(10) NOT NULL,
    betting_line DECIMAL(10, 2) NOT NULL,
    sharp_mean DECIMAL(10, 2) NOT NULL,
    std_dev DECIMAL(10, 4),
    implied_means JSON,
    sample_size INTEGER,
    mean_diff DECIMAL(10, 2) NOT NULL,
    ev_percent DECIMAL(10, 4) NOT NULL,
    price DECIMAL(10, 4) NOT NULL,
    true_prob DECIMAL(10, 6) NOT NULL,
    home_team VARCHAR(255),
    away_team VARCHAR(255),
    commence_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    win BOOLEAN DEFAULT NULL,
    actual_value DECIMAL(10, 2) DEFAULT NULL,
    CONSTRAINT unique_bet_per_bookmaker UNIQUE (game_id, bookmaker, market, player, outcome, betting_line)
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_games_commence_time ON games(commence_time);
CREATE INDEX IF NOT EXISTS idx_games_sport_key ON games(sport_key);
CREATE INDEX IF NOT EXISTS idx_ev_bets_game_id ON ev_bets(game_id);
CREATE INDEX IF NOT EXISTS idx_ev_bets_created_at ON ev_bets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ev_bets_ev_percent ON ev_bets(ev_percent DESC);
CREATE INDEX IF NOT EXISTS idx_ev_bets_active ON ev_bets(is_active);
CREATE INDEX IF NOT EXISTS idx_ev_bets_player ON ev_bets(player);
CREATE INDEX IF NOT EXISTS idx_ev_bets_bookmaker ON ev_bets(bookmaker);
CREATE INDEX IF NOT EXISTS idx_ev_bets_commence_time ON ev_bets(commence_time);
CREATE INDEX IF NOT EXISTS idx_ev_bets_home_team ON ev_bets(home_team);
CREATE INDEX IF NOT EXISTS idx_ev_bets_away_team ON ev_bets(away_team);

-- Create a view for easy querying of active bets with game info
CREATE OR REPLACE VIEW active_ev_bets AS
SELECT 
    eb.id,
    eb.bookmaker,
    eb.market,
    eb.player,
    eb.outcome,
    eb.betting_line,
    eb.sharp_mean,
    eb.std_dev,
    eb.implied_means,
    eb.sample_size,
    eb.mean_diff,
    eb.ev_percent,
    eb.price,
    eb.true_prob,
    eb.created_at,
    eb.home_team,
    eb.away_team,
    eb.commence_time,
    g.sport_title
FROM ev_bets eb
JOIN games g ON eb.game_id = g.id
WHERE eb.is_active = TRUE
ORDER BY eb.ev_percent DESC;

