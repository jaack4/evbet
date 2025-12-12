from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Game(Base):
    __tablename__ = "games"
    
    id = Column(String, primary_key=True)  # from odds API
    sport_key = Column(String, nullable=False)
    sport_title = Column(String, nullable=False)
    commence_time = Column(DateTime, nullable=False)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ev_bets = relationship("EVBet", back_populates="game", cascade="all, delete-orphan")

class EVBet(Base):
    __tablename__ = "ev_bets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    
    # Bet details
    bookmaker = Column(String, nullable=False)
    market = Column(String, nullable=False)
    player = Column(String, nullable=False)
    team = Column(String, nullable=True)
    outcome = Column(String, nullable=False)  # Over/Under
    
    # Odds information
    betting_line = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    
    # EV calculations
    sharp_mean = Column(Float, nullable=False)
    std_dev = Column(Float, nullable=True)
    implied_means = Column(JSON, nullable=True)  # Store array of means
    sample_size = Column(Integer, nullable=True)
    mean_diff = Column(Float, nullable=False)
    ev_percent = Column(Float, nullable=False)
    true_prob = Column(Float, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # To mark if bet is still valid
    
    # Relationships
    game = relationship("Game", back_populates="ev_bets")
    result = relationship("BetResult", back_populates="ev_bet", uselist=False)

class BetResult(Base):
    __tablename__ = "bet_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ev_bet_id = Column(Integer, ForeignKey("ev_bets.id"), unique=True)
    
    actual_value = Column(Float, nullable=True)  # Actual player stat
    won = Column(Boolean, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ev_bet = relationship("EVBet", back_populates="result")






