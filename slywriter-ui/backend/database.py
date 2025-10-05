"""
Database models and connection for SlyWriter
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./slywriter.db")
logger.info(f"Using database: {DATABASE_URL.split('@')[0] if '@' in DATABASE_URL else DATABASE_URL}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)  # Indexed for fast email lookup
    google_id = Column(String, unique=True, nullable=True, index=True)
    username = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)  # Google profile picture URL
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_login = Column(DateTime, default=datetime.utcnow)
    
    # Plan and usage - WEEKLY tracking
    plan = Column(String, default="Free")  # Free, Pro, Premium

    # Weekly word tracking
    words_used_this_week = Column(Integer, default=0)
    week_start_date = Column(DateTime, default=datetime.utcnow)

    # AI generation tracking (weekly)
    ai_gen_used_this_week = Column(Integer, default=0)

    # Humanizer tracking (weekly)
    humanizer_used_this_week = Column(Integer, default=0)

    # Total lifetime stats
    total_words_typed = Column(Integer, default=0)
    total_ai_generations = Column(Integer, default=0)
    total_humanizer_uses = Column(Integer, default=0)
    
    # Stripe subscription data
    stripe_customer_id = Column(String, unique=True, nullable=True, index=True)  # Indexed for webhook lookups
    stripe_subscription_id = Column(String, unique=True, nullable=True, index=True)
    subscription_status = Column(String, nullable=True, index=True)  # active, canceled, past_due, etc.
    subscription_current_period_start = Column(DateTime, nullable=True)
    subscription_current_period_end = Column(DateTime, nullable=True)

    # Referral system
    referral_code = Column(String, unique=True, nullable=True)
    referred_by = Column(String, nullable=True)
    referral_bonus = Column(Integer, default=0)
    referral_count = Column(Integer, default=0)
    referral_tier_claimed = Column(Integer, default=0)  # Highest tier claimed

    # Premium from referrals
    premium_until = Column(DateTime, nullable=True)  # Premium expiration from referral rewards
    
    # Settings
    settings = Column(JSON, default={})
    profiles = Column(JSON, default={})
    hotkeys = Column(JSON, default={})
    theme = Column(String, default="dark")
    
    # Relationships
    sessions = relationship("TypingSession", back_populates="user")
    analytics = relationship("Analytics", back_populates="user")

class TypingSession(Base):
    __tablename__ = "typing_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # Indexed for user session queries
    started_at = Column(DateTime, default=datetime.utcnow, index=True)  # Indexed for time-based queries
    ended_at = Column(DateTime, nullable=True)
    
    # Session data
    words_typed = Column(Integer, default=0)
    characters_typed = Column(Integer, default=0)
    average_wpm = Column(Float, default=0)
    accuracy = Column(Float, default=100)
    profile_used = Column(String, default="default")
    
    # Text data
    input_text = Column(String)
    output_text = Column(String, nullable=True)
    typos_made = Column(Integer, default=0)
    pauses_taken = Column(Integer, default=0)
    
    # Features used
    ai_filler_used = Column(Boolean, default=False)
    ai_generated = Column(Boolean, default=False)  # Was text AI-generated?
    humanized = Column(Boolean, default=False)  # Was text humanized?
    preview_mode = Column(Boolean, default=False)
    premium_features_used = Column(JSON, default=[])
    
    # Relationship
    user = relationship("User", back_populates="sessions")

class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # Indexed for user analytics queries
    date = Column(DateTime, default=datetime.utcnow, index=True)  # Indexed for date-based queries
    
    # Daily statistics
    daily_words = Column(Integer, default=0)
    daily_characters = Column(Integer, default=0)
    daily_sessions = Column(Integer, default=0)
    daily_wpm_avg = Column(Float, default=0)
    daily_accuracy_avg = Column(Float, default=0)
    
    # Usage patterns
    peak_hour = Column(Integer, nullable=True)
    most_used_profile = Column(String, nullable=True)
    feature_usage = Column(JSON, default={})
    
    # Relationship
    user = relationship("User", back_populates="analytics")

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    is_builtin = Column(Boolean, default=False)
    
    # Settings
    min_delay = Column(Float, default=0.1)
    max_delay = Column(Float, default=0.3)
    typos_enabled = Column(Boolean, default=True)  # Changed to True for realistic typing
    typo_chance = Column(Float, default=0.03)  # Increased to 3% for more realistic typos
    pause_frequency = Column(Integer, default=5)
    pause_duration_min = Column(Float, default=1.5)
    pause_duration_max = Column(Float, default=3.0)
    
    # Premium settings
    ai_filler_enabled = Column(Boolean, default=False)
    micro_hesitations = Column(Boolean, default=False)
    zone_out_breaks = Column(Boolean, default=False)
    burst_variability = Column(Float, default=0)
    advanced_anti_detection = Column(Boolean, default=False)

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String)
    icon = Column(String)
    requirement_type = Column(String)  # words, sessions, wpm, streak, etc.
    requirement_value = Column(Integer)
    points = Column(Integer, default=10)

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    unlocked_at = Column(DateTime, default=datetime.utcnow)
    progress = Column(Float, default=0)

# Database initialization
def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Run migration to add profile_picture column if it doesn't exist
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("users")]

        if "profile_picture" not in columns:
            logger.info("Running migration: adding profile_picture column to users table...")
            with engine.connect() as conn:
                if "postgresql" in DATABASE_URL.lower():
                    conn.execute(text("ALTER TABLE users ADD COLUMN profile_picture VARCHAR"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN profile_picture TEXT"))
                conn.commit()
            logger.info("Migration successful: profile_picture column added")
