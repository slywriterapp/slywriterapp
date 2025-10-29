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
    
    # Text data - NOT STORED FOR PRIVACY
    # input_text = Column(String, nullable=True)  # REMOVED: We don't store user text
    # output_text = Column(String, nullable=True)  # REMOVED: We don't store user text
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

    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        # If using SQLite as fallback, it's okay to fail
        if "sqlite" in DATABASE_URL.lower():
            logger.warning("Using SQLite - database will reset on restart")
        raise

    # Create default profiles
    db = SessionLocal()
    try:
        # Check if profiles exist
        existing = db.query(Profile).filter_by(is_builtin=True).first()
        if not existing:
            default_profiles = [
                Profile(
                    name="Slow",
                    is_builtin=True,
                    min_delay=0.274,  # 30 WPM based on formula: 274ms min
                    max_delay=0.634,  # 30 WPM based on formula: 634ms max
                    typos_enabled=True,  # ON by default
                    typo_chance=0.05,  # 5% chance for slow typing
                    pause_frequency=5,
                    pause_duration_min=1.5,
                    pause_duration_max=3.5
                ),
                Profile(
                    name="Medium",
                    is_builtin=True,
                    min_delay=0.137,  # 60 WPM based on formula: 137ms min
                    max_delay=0.317,  # 60 WPM based on formula: 317ms max
                    typos_enabled=True,  # ON by default
                    typo_chance=0.03,  # 3% chance for medium typing
                    pause_frequency=7,
                    pause_duration_min=1.0,
                    pause_duration_max=2.5
                ),
                Profile(
                    name="Fast",
                    is_builtin=True,
                    min_delay=0.068,  # 120 WPM based on formula: 68ms min
                    max_delay=0.159,  # 120 WPM based on formula: 159ms max
                    typos_enabled=True,  # ON by default
                    typo_chance=0.02,  # 2% chance for fast typing
                    pause_frequency=10,
                    pause_duration_min=0.5,
                    pause_duration_max=1.5
                )
            ]
            
            for profile in default_profiles:
                db.add(profile)
            
            db.commit()
            logger.info("Default profiles created")
    except Exception as e:
        logger.error(f"Failed to create default profiles: {e}")
        db.rollback()
    finally:
        db.close()

# Helper functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, plan: str = "Free"):
    """Create new user"""
    from datetime import datetime, timedelta
    import secrets

    # Generate unique referral code
    referral_code = secrets.token_urlsafe(8)

    # Set week start to NOW (user's signup time) - not Monday
    week_start = datetime.utcnow()

    user = User(
        email=email,
        plan=plan,
        referral_code=referral_code,
        week_start_date=week_start,
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def check_weekly_reset(db: Session, user: User):
    """Check if user's weekly limits should reset - based on signup date, not Monday"""
    from datetime import datetime, timedelta

    if not user.week_start_date:
        # No week start date - set it to now
        user.week_start_date = datetime.utcnow()
        db.commit()
        return False

    days_since_week_start = (datetime.utcnow() - user.week_start_date).days

    if days_since_week_start >= 7:
        # Reset weekly counters - add exactly 7 days to maintain same day of week
        user.week_start_date = user.week_start_date + timedelta(days=7)
        user.words_used_this_week = 0
        user.ai_gen_used_this_week = 0
        user.humanizer_used_this_week = 0
        # NOTE: referral_bonus is NOT reset - it's permanent bonus words

        db.commit()
        return True

    return False

def get_user_limits(user: User):
    """Calculate user's limits - bonus words consumed first, then weekly allowance"""
    PLAN_LIMITS = {
        "Free": {"words": 500, "ai_gen": 3, "humanizer": 0},
        "Pro": {"words": 5000, "ai_gen": -1, "humanizer": 3},
        "Premium": {"words": -1, "ai_gen": -1, "humanizer": -1}
    }

    limits = PLAN_LIMITS.get(user.plan, PLAN_LIMITS["Free"])

    # Calculate words
    base_words = limits["words"]
    bonus_words = user.referral_bonus or 0

    if base_words == -1:
        # Unlimited plan
        total_words_available = -1
        words_remaining = "Unlimited"
        word_limit_display = "Unlimited"
    else:
        # Total available = bonus (consumed first) + (base - used_this_week)
        weekly_remaining = max(0, base_words - user.words_used_this_week)
        total_words_available = bonus_words + weekly_remaining
        words_remaining = total_words_available

        if bonus_words > 0:
            word_limit_display = f"{bonus_words:,} bonus + {weekly_remaining:,}/{base_words:,} weekly = {total_words_available:,} total"
        else:
            word_limit_display = f"{weekly_remaining:,}/{base_words:,} words this week"

    return {
        "word_limit": base_words,
        "word_limit_display": word_limit_display,
        "words_used": user.words_used_this_week,
        "words_remaining": words_remaining,
        "total_words_available": total_words_available,
        "base_word_limit": base_words,
        "bonus_words": bonus_words,
        "ai_gen_limit": limits["ai_gen"],
        "ai_gen_limit_display": "Unlimited" if limits["ai_gen"] == -1 else f"{limits['ai_gen']} uses/week",
        "ai_gen_uses": user.ai_gen_used_this_week,
        "ai_gen_remaining": "Unlimited" if limits["ai_gen"] == -1 else max(0, limits["ai_gen"] - user.ai_gen_used_this_week),
        "humanizer_limit": limits["humanizer"],
        "humanizer_limit_display": "Unlimited" if limits["humanizer"] == -1 else f"{limits['humanizer']} uses/week",
        "humanizer_uses": user.humanizer_used_this_week,
        "humanizer_remaining": "Unlimited" if limits["humanizer"] == -1 else max(0, limits["humanizer"] - user.humanizer_used_this_week),
        "week_start_date": user.week_start_date.isoformat() if user.week_start_date else None
    }

def track_word_usage(db: Session, user: User, words: int):
    """Track word usage - consumes bonus words first, then weekly allowance"""
    user.total_words_typed += words
    if user.referral_bonus and user.referral_bonus > 0:
        if words <= user.referral_bonus:
            user.referral_bonus -= words
        else:
            remaining_words = words - user.referral_bonus
            user.referral_bonus = 0
            user.words_used_this_week += remaining_words
    else:
        user.words_used_this_week += words
    db.commit()
    return user

def track_ai_generation(db: Session, user: User):
    """Track AI generation usage"""
    user.ai_gen_used_this_week += 1
    user.total_ai_generations += 1
    db.commit()
    return user

def track_humanizer_usage(db: Session, user: User):
    """Track humanizer usage"""
    user.humanizer_used_this_week += 1
    user.total_humanizer_uses += 1
    db.commit()
    return user

def create_typing_session(db: Session, user_id: int, session_data: dict):
    """Create a typing session record"""
    session = TypingSession(user_id=user_id, **session_data)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
