-- Migration to add unique constraint to prevent duplicate bets
-- Run this on your existing database to add the constraint

-- First, remove any existing duplicates (keeps the most recent one)
DELETE FROM ev_bets a
USING ev_bets b
WHERE a.id < b.id
AND a.game_id = b.game_id
AND a.bookmaker = b.bookmaker
AND a.market = b.market
AND a.player = b.player
AND a.outcome = b.outcome
AND a.betting_line = b.betting_line;

-- Add the unique constraint
ALTER TABLE ev_bets 
ADD CONSTRAINT unique_bet_per_bookmaker 
UNIQUE (game_id, bookmaker, market, player, outcome, betting_line);

-- Verify the constraint was added
SELECT conname, contype, conrelid::regclass
FROM pg_constraint
WHERE conname = 'unique_bet_per_bookmaker';

