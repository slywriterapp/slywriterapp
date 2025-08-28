"""
Database models and connection for SlyWriter
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime
import json
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./slywriter.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    google_id = Column(String, unique=True, nullable=True)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    
    # Plan and usage
    plan = Column(String, default="free")  # free, pro, premium, enterprise
    daily_limit = Column(Integer, default=4000)
    words_used_today = Column(Integer, default=0)
    total_words_typed = Column(Integer, default=0)
    usage_reset_date = Column(DateTime, default=datetime.utcnow)
    
    # Referral system
    referral_code = Column(String, unique=True)
    referred_by = Column(String, nullable=True)
    referral_bonus = Column(Integer, default=0)
    referral_count = Column(Integer, default=0)
    
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
    user_id = Column(Integer, ForeignKey("users.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
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
    preview_mode = Column(Boolean, default=False)
    premium_features_used = Column(JSON, default=[])
    
    # Relationship
    user = relationship("User", back_populates="sessions")

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.utcnow)
    
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
    Base.metadata.create_all(bind=engine)
    
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
                    min_delay=0.160,  # 60 WPM based on formula: 160ms min
                    max_delay=0.272,  # 60 WPM based on formula: 272ms max
                    typos_enabled=True,  # ON by default
                    typo_chance=0.025,  # 2.5% chance for medium typing
                    pause_frequency=10,
                    pause_duration_min=0.8,
                    pause_duration_max=2.0
                ),
                Profile(
                    name="Fast",
                    is_builtin=True,
                    min_delay=0.089,  # 120 WPM based on formula: 89ms min
                    max_delay=0.119,  # 120 WPM based on formula: 119ms max
                    typos_enabled=True,  # ON by default
                    typo_chance=0.015,  # 1.5% chance for fast typing
                    pause_frequency=18,
                    pause_duration_min=0.4,
                    pause_duration_max=1.2
                ),
                Profile(
                    name="Essay",
                    is_builtin=True,
                    min_delay=0.201,  # 45 WPM for thoughtful essay writing
                    max_delay=0.388,  # 45 WPM based on formula
                    typos_enabled=True,  # ON by default
                    typo_chance=0.03,  # 3% for essay writing
                    pause_frequency=8,
                    pause_duration_min=1.5,
                    pause_duration_max=3.0,
                    ai_filler_enabled=True,
                    micro_hesitations=True,
                    zone_out_breaks=True
                ),
                Profile(
                    name="Custom",
                    is_builtin=True,
                    min_delay=0.10,  # Will be calibrated from WPM test
                    max_delay=0.15,
                    typos_enabled=True,  # ON by default
                    typo_chance=0.03,  # 3% default for custom
                    pause_frequency=5
                )
            ]
            for profile in default_profiles:
                db.add(profile)
            
            # Add default achievements - focused on automation usage
            achievements = [
                Achievement(name="Automation Beginner", description="Complete your first automated typing session", 
                           icon="robot", requirement_type="sessions", requirement_value=1),
                Achievement(name="AI Assistant", description="Use AI to generate and type 1,000 words", 
                           icon="brain", requirement_type="ai_words", requirement_value=1000),
                Achievement(name="Productivity Master", description="Automate 50,000 words", 
                           icon="trending-up", requirement_type="words", requirement_value=50000),
                Achievement(name="Stealth Mode", description="Complete 10 sessions with humanizer enabled", 
                           icon="eye-off", requirement_type="humanized_sessions", requirement_value=10),
                Achievement(name="Content Creator", description="Generate and type 10 AI-enhanced documents", 
                           icon="file-text", requirement_type="ai_documents", requirement_value=10),
                Achievement(name="Learning Expert", description="Complete 20 AI-powered learning sessions", 
                           icon="graduation-cap", requirement_type="learning_sessions", requirement_value=20),
                Achievement(name="Efficiency King", description="Save 10 hours with automation", 
                           icon="clock", requirement_type="time_saved_hours", requirement_value=10),
            ]
            for achievement in achievements:
                db.add(achievement)
            
            db.commit()
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()