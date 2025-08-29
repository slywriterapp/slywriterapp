# feature_spotlight.py - Feature Discovery and Spotlight System

import tkinter as tk
from tkinter import ttk
import json
import os
import random
import time
from datetime import datetime, timedelta
import threading

class FeatureSpotlight:
    """Manages feature discovery, tips, and spotlight system"""
    
    def __init__(self, app):
        self.app = app
        self.usage_file = os.path.join(os.path.dirname(__file__), 'feature_usage.json')
        self.spotlight_active = False
        self.last_tip_time = 0
        self.tip_interval = 300  # 5 minutes between tips
        
        # Load usage data
        self.usage_data = self.load_usage_data()
        
        # Initialize tracking
        self.start_usage_tracking()
        
        # Schedule periodic tips
        self.schedule_next_tip()
    
    def load_usage_data(self):
        """Load feature usage tracking data"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[SPOTLIGHT] Error loading usage data: {e}")
        
        # Default usage data structure
        return {
            'features': {},  # feature_name: {'count': 0, 'last_used': timestamp, 'discovered': False}
            'tips_shown': [],  # List of tip IDs already shown
            'spotlight_dismissed': [],  # List of dismissed spotlights
            'last_tip_time': 0,
            'total_app_launches': 0,
            'first_launch': time.time()
        }
    
    def save_usage_data(self):
        """Save usage data to file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            print(f"[SPOTLIGHT] Error saving usage data: {e}")
    
    def track_feature_usage(self, feature_name):
        """Track when a feature is used"""
        if feature_name not in self.usage_data['features']:
            self.usage_data['features'][feature_name] = {
                'count': 0,
                'last_used': 0,
                'discovered': False
            }
        
        self.usage_data['features'][feature_name]['count'] += 1
        self.usage_data['features'][feature_name]['last_used'] = time.time()
        self.usage_data['features'][feature_name]['discovered'] = True
        
        self.save_usage_data()
        print(f"[SPOTLIGHT] Tracked usage of feature: {feature_name}")
    
    def get_unused_features(self):
        """Get list of features that haven't been used much"""
        all_features = self.get_all_features()
        unused_features = []
        
        for feature in all_features:
            feature_data = self.usage_data['features'].get(feature['id'], {'count': 0})
            
            # Consider unused if used less than 3 times or never used
            if feature_data['count'] < 3:
                unused_features.append(feature)
        
        return unused_features
    
    def get_all_features(self):
        """Get all trackable features with their metadata"""
        return [
            {
                'id': 'ai_humanizer',
                'name': 'AI Humanizer',
                'description': 'Transform your text to bypass AI detection with advanced humanization',
                'location': 'AI Hub tab',
                'tip': 'The AI Humanizer can make your text sound more natural and bypass AI detectors!',
                'icon': '🤖',
                'priority': 'high'
            },
            {
                'id': 'advanced_pauses',
                'name': 'Advanced Pause Patterns',
                'description': 'Realistic pauses at punctuation and sentence breaks',
                'location': 'Typing tab → Advanced Settings',
                'tip': 'Enable advanced pauses to make your typing look more human-like with realistic breaks!',
                'icon': '⏸️',
                'priority': 'medium'
            },
            {
                'id': 'typing_profiles',
                'name': 'Typing Profiles',
                'description': 'Save and switch between different typing configurations',
                'location': 'Typing tab → Profile dropdown',
                'tip': 'Create multiple typing profiles for different scenarios (essays, emails, etc.)!',
                'icon': '👤',
                'priority': 'medium'
            },
            {
                'id': 'global_hotkeys',
                'name': 'Global Hotkeys',
                'description': 'Control typing with keyboard shortcuts from anywhere',
                'location': 'Settings tab → Hotkeys',
                'tip': 'Set up global hotkeys to start/stop typing without switching windows!',
                'icon': '⌨️',
                'priority': 'high'
            },
            {
                'id': 'typing_stats',
                'name': 'Detailed Statistics',
                'description': 'View comprehensive typing analytics and performance metrics',
                'location': 'Stats tab',
                'tip': 'Check your typing statistics to see your WPM trends and session history!',
                'icon': '📊',
                'priority': 'low'
            },
            {
                'id': 'text_preview',
                'name': 'Live Text Preview',
                'description': 'See exactly what will be typed before starting',
                'location': 'Typing tab → Preview panel',
                'tip': 'Use the live preview to see exactly how your text will look before typing!',
                'icon': '👁️',
                'priority': 'medium'
            },
            {
                'id': 'typo_correction',
                'name': 'Automatic Typo Correction',
                'description': 'Simulate realistic typos and corrections while typing',
                'location': 'Typing tab → Advanced Settings',
                'tip': 'Enable typo correction to make your automated typing look even more realistic!',
                'icon': '✏️',
                'priority': 'medium'
            },
            {
                'id': 'essay_mode',
                'name': 'Essay Generation Mode',
                'description': 'Generate full essays with AI assistance',
                'location': 'AI Hub tab → Essay Mode',
                'tip': 'Try Essay Mode to generate complete academic papers with proper formatting!',
                'icon': '📝',
                'priority': 'high'
            },
            {
                'id': 'learning_system',
                'name': 'Interactive Learning',
                'description': 'Improve your skills with personalized lessons',
                'location': 'Learn tab',
                'tip': 'The Learn tab has interactive tutorials to help you master advanced features!',
                'icon': '🎓',
                'priority': 'medium'
            },
            {
                'id': 'notification_system',
                'name': 'Notifications & Updates',
                'description': 'Stay updated with new features and discount codes',
                'location': 'Bell icon (top-right)',
                'tip': 'Click the bell icon to see the latest updates and exclusive discount codes!',
                'icon': '🔔',
                'priority': 'low'
            }
        ]
    
    def should_show_tip(self):
        """Determine if a tip should be shown now"""
        current_time = time.time()
        
        # Don't show tips too frequently
        if current_time - self.usage_data.get('last_tip_time', 0) < self.tip_interval:
            return False
        
        # Show tips more often for new users
        app_age_days = (current_time - self.usage_data.get('first_launch', current_time)) / 86400
        
        if app_age_days < 1:  # First day - show tips more often
            return random.random() < 0.3  # 30% chance
        elif app_age_days < 7:  # First week
            return random.random() < 0.15  # 15% chance
        else:  # After first week
            return random.random() < 0.08  # 8% chance
        
    def get_best_tip(self):
        """Get the best tip to show based on unused features"""
        unused_features = self.get_unused_features()
        
        if not unused_features:
            return None
        
        # Filter out already shown tips and permanently dismissed tips
        shown_tips = set(self.usage_data.get('tips_shown', []))
        dismissed_tips = set(self.usage_data.get('tips_dismissed', []))
        available_tips = [f for f in unused_features 
                         if f['id'] not in shown_tips and f['id'] not in dismissed_tips]
        
        if not available_tips:
            # Reset shown tips if we've shown them all
            self.usage_data['tips_shown'] = []
            available_tips = unused_features
        
        # Prioritize high-priority features
        high_priority = [f for f in available_tips if f['priority'] == 'high']
        if high_priority:
            return random.choice(high_priority)
        
        medium_priority = [f for f in available_tips if f['priority'] == 'medium']
        if medium_priority:
            return random.choice(medium_priority)
        
        return random.choice(available_tips) if available_tips else None
    
    def show_tip(self, feature=None):
        """Show a 'Did you know?' tip"""
        if self.spotlight_active:
            return
        
        if not feature:
            feature = self.get_best_tip()
        
        if not feature:
            return
        
        self.spotlight_active = True
        self.create_tip_popup(feature)
        
        # Mark tip as shown
        if feature['id'] not in self.usage_data.get('tips_shown', []):
            self.usage_data.setdefault('tips_shown', []).append(feature['id'])
        
        self.usage_data['last_tip_time'] = time.time()
        self.save_usage_data()
    
    def create_tip_popup(self, feature):
        """Create animated tip popup"""
        # Create popup window
        popup = tk.Toplevel(self.app)
        popup.title("💡 Did You Know?")
        popup.geometry("450x300")
        popup.configure(bg='#1A1B3E')
        popup.transient(self.app)
        popup.grab_set()
        
        # Position in bottom-right corner
        popup.geometry("+%d+%d" % (self.app.winfo_screenwidth() - 470, 
                                 self.app.winfo_screenheight() - 350))
        
        # Make popup semi-transparent and modern
        popup.attributes('-alpha', 0.0)  # Start invisible for animation
        
        # Header with icon and title
        header_frame = tk.Frame(popup, bg='#1A1B3E')
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        # Icon and "Did You Know?" title
        title_frame = tk.Frame(header_frame, bg='#1A1B3E')
        title_frame.pack(fill='x')
        
        tk.Label(title_frame, text="💡", font=('Segoe UI', 24), 
                bg='#1A1B3E', fg='#FFF').pack(side='left')
        
        tk.Label(title_frame, text="Did You Know?", 
                font=('Segoe UI', 16, 'bold'),
                bg='#1A1B3E', fg='#FFFFFF').pack(side='left', padx=(10, 0))
        
        # Close button
        close_btn = tk.Button(title_frame, text="✕", 
                            font=('Segoe UI', 12, 'bold'),
                            fg='#FFFFFF', bg='#1A1B3E', 
                            bd=0, cursor='hand2',
                            command=lambda: self.dismiss_popup(popup))
        close_btn.pack(side='right')
        
        # Feature content
        content_frame = tk.Frame(popup, bg='#2D2F5A', relief='flat', bd=0)
        content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))
        
        # Feature icon and name
        feature_header = tk.Frame(content_frame, bg='#2D2F5A')
        feature_header.pack(fill='x', padx=15, pady=(15, 10))
        
        tk.Label(feature_header, text=feature['icon'], 
                font=('Segoe UI', 20), bg='#2D2F5A').pack(side='left')
        
        tk.Label(feature_header, text=feature['name'],
                font=('Segoe UI', 14, 'bold'),
                fg='#FFFFFF', bg='#2D2F5A').pack(side='left', padx=(10, 0))
        
        # Feature description
        desc_label = tk.Label(content_frame, text=feature['tip'],
                            font=('Segoe UI', 11),
                            fg='#B4B4B8', bg='#2D2F5A',
                            wraplength=400, justify='left')
        desc_label.pack(padx=15, pady=(0, 10), anchor='w')
        
        # Location info
        location_label = tk.Label(content_frame, 
                                text=f"📍 Find it: {feature['location']}",
                                font=('Segoe UI', 9),
                                fg='#8B5CF6', bg='#2D2F5A')
        location_label.pack(padx=15, pady=(0, 10), anchor='w')
        
        # Action buttons
        button_frame = tk.Frame(content_frame, bg='#2D2F5A')
        button_frame.pack(fill='x', padx=15, pady=(5, 15))
        
        # "Show me" button
        show_btn = tk.Button(button_frame, text="Show Me!",
                           font=('Segoe UI', 10, 'bold'),
                           fg='#FFFFFF', bg='#8B5CF6',
                           bd=0, pady=8, padx=20,
                           cursor='hand2',
                           command=lambda: self.navigate_to_feature(feature, popup))
        show_btn.pack(side='left')
        
        # "Maybe later" button
        later_btn = tk.Button(button_frame, text="Maybe Later",
                            font=('Segoe UI', 10),
                            fg='#B4B4B8', bg='#2D2F5A',
                            bd=0, pady=8, padx=20,
                            cursor='hand2',
                            command=lambda: self.dismiss_popup(popup))
        later_btn.pack(side='right')
        
        # Debug: Add "Don't show again" for this feature (small text)
        debug_frame = tk.Frame(content_frame, bg='#2D2F5A')
        debug_frame.pack(fill='x', padx=15, pady=(0, 5))
        
        dont_show_btn = tk.Button(debug_frame, text="Don't show this tip again",
                                font=('Segoe UI', 8),
                                fg='#6B7280', bg='#2D2F5A',
                                bd=0, cursor='hand2',
                                command=lambda: self.dismiss_tip_permanently(feature, popup))
        dont_show_btn.pack(anchor='e')
        
        # Animate popup appearance
        self.animate_popup_in(popup)
        
        # Auto-dismiss after 15 seconds
        popup.after(15000, lambda: self.dismiss_popup(popup))
    
    def animate_popup_in(self, popup):
        """Animate popup sliding in"""
        def fade_in(alpha=0.0):
            if alpha < 0.95:
                popup.attributes('-alpha', alpha)
                popup.after(50, lambda: fade_in(alpha + 0.1))
            else:
                popup.attributes('-alpha', 0.95)
        
        fade_in()
    
    def navigate_to_feature(self, feature, popup):
        """Navigate to the feature location"""
        self.dismiss_popup(popup)
        
        # Track that user showed interest
        self.track_feature_usage(f"{feature['id']}_navigation")
        
        # Navigate based on feature location
        if 'AI Hub' in feature['location']:
            self.app.switch_to_tab('AI Hub')
        elif 'Typing' in feature['location']:
            self.app.switch_to_tab('Typing')
        elif 'Settings' in feature['location']:
            self.app.switch_to_tab('Settings')
        elif 'Stats' in feature['location']:
            self.app.switch_to_tab('Stats')
        elif 'Learn' in feature['location']:
            self.app.switch_to_tab('Learn')
        elif 'Bell icon' in feature['location']:
            # Show notifications
            if hasattr(self.app, 'header'):
                self.app.header.show_notifications()
        
        # Show success notification
        self.app.show_notification("✨ Feature highlighted! Check it out.")
    
    def dismiss_popup(self, popup):
        """Dismiss the tip popup"""
        self.spotlight_active = False
        
        def fade_out(alpha=0.95):
            if alpha > 0.0:
                popup.attributes('-alpha', alpha)
                popup.after(30, lambda: fade_out(alpha - 0.1))
            else:
                popup.destroy()
        
        fade_out()
    
    def dismiss_tip_permanently(self, feature, popup):
        """Permanently dismiss a tip for this feature"""
        # Add to dismissed list
        if 'tips_dismissed' not in self.usage_data:
            self.usage_data['tips_dismissed'] = []
        
        if feature['id'] not in self.usage_data['tips_dismissed']:
            self.usage_data['tips_dismissed'].append(feature['id'])
            self.save_usage_data()
            print(f"[SPOTLIGHT] Permanently dismissed tip for {feature['name']}")
        
        self.dismiss_popup(popup)
    
    def schedule_next_tip(self):
        """Schedule the next tip to appear"""
        # Random delay between 5-15 minutes
        delay = random.randint(300, 900) * 1000  # Convert to milliseconds
        
        def show_random_tip():
            if self.should_show_tip():
                self.show_tip()
            # Schedule next tip
            self.schedule_next_tip()
        
        self.app.after(delay, show_random_tip)
    
    def start_usage_tracking(self):
        """Start tracking app usage"""
        self.usage_data['total_app_launches'] += 1
        self.save_usage_data()
    
    def show_feature_spotlight(self, feature_id):
        """Show spotlight for a specific feature (can be called manually)"""
        feature = next((f for f in self.get_all_features() if f['id'] == feature_id), None)
        if feature:
            self.show_tip(feature)
    
    def get_discovery_stats(self):
        """Get statistics about feature discovery"""
        all_features = self.get_all_features()
        total_features = len(all_features)
        discovered_features = len([f for f in all_features 
                                 if self.usage_data['features'].get(f['id'], {}).get('discovered', False)])
        
        return {
            'total_features': total_features,
            'discovered_features': discovered_features,
            'discovery_percentage': (discovered_features / total_features) * 100 if total_features > 0 else 0,
            'unused_features': len(self.get_unused_features())
        }