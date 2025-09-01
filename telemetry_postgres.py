"""
PostgreSQL-based telemetry system for SlyWriter beta testing
Upload this file to your Render server
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class TelemetryDatabase:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Initialize database tables
        self.init_database()
    
    def get_connection(self):
        """Get a database connection"""
        return psycopg2.connect(self.database_url)
    
    def init_database(self):
        """Create necessary tables if they don't exist"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # Create telemetry_events table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    event_type VARCHAR(100),
                    event_data JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create telemetry_sessions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    system_info JSONB,
                    session_duration INTEGER,
                    total_actions INTEGER,
                    total_errors INTEGER,
                    started_at TIMESTAMP,
                    last_activity TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create telemetry_errors table for quick error lookup
            cur.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_errors (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    error_message TEXT,
                    error_stack TEXT,
                    component VARCHAR(255),
                    severity VARCHAR(50),
                    context JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create telemetry_features table for feature usage
            cur.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_features (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    feature_name VARCHAR(255) NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings JSONB,
                    UNIQUE(user_id, feature_name)
                )
            """)
            
            # Create indexes for better performance
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_events_user_id ON telemetry_events(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_events_session_id ON telemetry_events(session_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_events_timestamp ON telemetry_events(timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_sessions_user_id ON telemetry_sessions(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_errors_user_id ON telemetry_errors(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_features_user_id ON telemetry_features(user_id)")
            
            conn.commit()
            logger.info("Database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
    
    def save_telemetry(self, data: Dict[str, Any]) -> bool:
        """Save telemetry data to PostgreSQL"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # Save session info
            cur.execute("""
                INSERT INTO telemetry_sessions (
                    user_id, session_id, system_info, session_duration,
                    total_actions, total_errors, started_at, last_activity
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_id) 
                DO UPDATE SET
                    session_duration = EXCLUDED.session_duration,
                    total_actions = EXCLUDED.total_actions,
                    total_errors = EXCLUDED.total_errors,
                    last_activity = EXCLUDED.last_activity
            """, (
                data['userId'],
                data['sessionId'],
                json.dumps(data.get('systemInfo', {})),
                data.get('sessionDuration', 0),
                len(data.get('actions', [])),
                len(data.get('errors', [])),
                datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')) if 'timestamp' in data else datetime.now(),
                datetime.now()
            ))
            
            # Save individual actions as events
            for action in data.get('actions', []):
                cur.execute("""
                    INSERT INTO telemetry_events (
                        user_id, session_id, event_type, event_data, timestamp
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    data['userId'],
                    data['sessionId'],
                    action.get('action', 'unknown'),
                    json.dumps(action),
                    datetime.fromisoformat(action['timestamp'].replace('Z', '+00:00')) if 'timestamp' in action else datetime.now()
                ))
            
            # Save errors
            for error in data.get('errors', []):
                cur.execute("""
                    INSERT INTO telemetry_errors (
                        user_id, session_id, error_message, error_stack,
                        component, severity, context, timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data['userId'],
                    data['sessionId'],
                    error.get('error', 'Unknown error'),
                    error.get('stack', ''),
                    error.get('component', 'unknown'),
                    error.get('severity', 'medium'),
                    json.dumps(error.get('context', {})),
                    datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00')) if 'timestamp' in error else datetime.now()
                ))
            
            # Update feature usage
            for feature in data.get('featureUsage', []):
                cur.execute("""
                    INSERT INTO telemetry_features (
                        user_id, feature_name, usage_count, last_used, settings
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, feature_name)
                    DO UPDATE SET
                        usage_count = telemetry_features.usage_count + EXCLUDED.usage_count,
                        last_used = EXCLUDED.last_used,
                        settings = EXCLUDED.settings
                """, (
                    data['userId'],
                    feature.get('feature', 'unknown'),
                    feature.get('usageCount', 1),
                    datetime.now(),
                    json.dumps(feature.get('settings', {}))
                ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving telemetry: {e}")
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get telemetry statistics"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get user and session counts
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT user_id) as total_users,
                    COUNT(DISTINCT session_id) as total_sessions,
                    COUNT(*) as total_events
                FROM telemetry_events
            """)
            basic_stats = cur.fetchone()
            
            # Get total actions and errors
            cur.execute("SELECT COUNT(*) as total_errors FROM telemetry_errors")
            error_count = cur.fetchone()
            
            # Get most used features
            cur.execute("""
                SELECT feature_name, SUM(usage_count) as total_usage
                FROM telemetry_features
                GROUP BY feature_name
                ORDER BY total_usage DESC
                LIMIT 10
            """)
            most_used_features = {row['feature_name']: row['total_usage'] for row in cur.fetchall()}
            
            # Get common errors
            cur.execute("""
                SELECT error_message, COUNT(*) as count
                FROM telemetry_errors
                GROUP BY error_message
                ORDER BY count DESC
                LIMIT 10
            """)
            common_errors = {row['error_message']: row['count'] for row in cur.fetchall()}
            
            # Get recent activity count
            cur.execute("""
                SELECT COUNT(*) as recent_events
                FROM telemetry_events
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            """)
            recent_activity = cur.fetchone()
            
            return {
                'total_users': basic_stats['total_users'],
                'total_sessions': basic_stats['total_sessions'],
                'total_actions': basic_stats['total_events'],
                'total_errors': error_count['total_errors'],
                'most_used_features': most_used_features,
                'common_errors': common_errors,
                'recent_events_24h': recent_activity['recent_events'],
                'data_points': basic_stats['total_events']
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                'error': str(e),
                'total_users': 0,
                'total_sessions': 0,
                'total_actions': 0,
                'total_errors': 0
            }
        finally:
            cur.close()
            conn.close()
    
    def get_recent_entries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent telemetry entries"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT 
                    s.user_id, s.session_id, s.system_info, 
                    s.session_duration, s.total_actions, s.total_errors,
                    s.started_at, s.last_activity,
                    COUNT(e.id) as event_count
                FROM telemetry_sessions s
                LEFT JOIN telemetry_events e ON s.session_id = e.session_id
                GROUP BY s.id, s.user_id, s.session_id, s.system_info, 
                         s.session_duration, s.total_actions, s.total_errors,
                         s.started_at, s.last_activity
                ORDER BY s.last_activity DESC
                LIMIT %s
            """, (limit,))
            
            entries = []
            for row in cur.fetchall():
                entries.append({
                    'userId': row['user_id'],
                    'sessionId': row['session_id'],
                    'systemInfo': row['system_info'],
                    'sessionDuration': row['session_duration'],
                    'actions': [],  # We don't load full actions for performance
                    'errors': [],
                    'timestamp': row['started_at'].isoformat() if row['started_at'] else '',
                    'received_at': row['last_activity'].isoformat() if row['last_activity'] else ''
                })
            
            return entries
            
        except Exception as e:
            logger.error(f"Error getting recent entries: {e}")
            return []
        finally:
            cur.close()
            conn.close()
    
    def export_all_data(self) -> List[Dict[str, Any]]:
        """Export all telemetry data"""
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Get all sessions with their events
            cur.execute("""
                SELECT * FROM telemetry_sessions
                ORDER BY created_at DESC
            """)
            sessions = cur.fetchall()
            
            export_data = []
            for session in sessions:
                # Get events for this session
                cur.execute("""
                    SELECT * FROM telemetry_events
                    WHERE session_id = %s
                    ORDER BY timestamp
                """, (session['session_id'],))
                events = cur.fetchall()
                
                # Get errors for this session
                cur.execute("""
                    SELECT * FROM telemetry_errors
                    WHERE session_id = %s
                    ORDER BY timestamp
                """, (session['session_id'],))
                errors = cur.fetchall()
                
                export_data.append({
                    'userId': session['user_id'],
                    'sessionId': session['session_id'],
                    'systemInfo': session['system_info'],
                    'sessionDuration': session['session_duration'],
                    'actions': [dict(e) for e in events],
                    'errors': [dict(e) for e in errors],
                    'timestamp': session['started_at'].isoformat() if session['started_at'] else '',
                    'received_at': session['created_at'].isoformat() if session['created_at'] else ''
                })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return []
        finally:
            cur.close()
            conn.close()
    
    def cleanup_old_data(self, days: int = 90):
        """Clean up old telemetry data"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # Delete old events
            cur.execute("""
                DELETE FROM telemetry_events
                WHERE timestamp < NOW() - INTERVAL '%s days'
            """, (days,))
            
            # Delete old errors
            cur.execute("""
                DELETE FROM telemetry_errors
                WHERE timestamp < NOW() - INTERVAL '%s days'
            """, (days,))
            
            # Delete old sessions
            cur.execute("""
                DELETE FROM telemetry_sessions
                WHERE created_at < NOW() - INTERVAL '%s days'
            """, (days,))
            
            conn.commit()
            logger.info(f"Cleaned up data older than {days} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()

# Initialize the database when module is imported
telemetry_db = TelemetryDatabase()