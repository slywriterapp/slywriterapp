import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import webbrowser
import datetime
import requests
from auth import get_saved_user

SERVER_URL = "https://slywriterapp.onrender.com"

class DashboardTab(tk.Frame):
    def __init__(self, parent, app):
        dark = app.cfg['settings'].get('dark_mode', False)
        bg = "#1a1a1a" if dark else "#f5f5f5"
        card_bg = "#2b2b2b" if dark else "#ffffff"
        text_color = "#ffffff" if dark else "#1a1a1a"
        secondary_color = "#aaaaaa" if dark else "#666666"

        super().__init__(parent, bg=bg)
        self.app = app
        self.bg = bg
        self.card_bg = card_bg
        self.text_color = text_color
        self.secondary_color = secondary_color

        self.user_data = None
        self.reset_date = None

        self.build_ui()
        self.start_auto_update()

    def build_ui(self):
        """Build modern dashboard UI"""
        # Main container with padding
        main_container = tk.Frame(self, bg=self.bg)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title_frame = tk.Frame(main_container, bg=self.bg)
        title_frame.pack(fill='x', pady=(0, 20))

        title_label = tk.Label(
            title_frame,
            text="📊 Dashboard",
            font=('Segoe UI', 20, 'bold'),
            fg=self.text_color,
            bg=self.bg
        )
        title_label.pack(side='left')

        # Stats Grid (2 columns)
        stats_grid = tk.Frame(main_container, bg=self.bg)
        stats_grid.pack(fill='both', expand=True)

        # Left column
        left_col = tk.Frame(stats_grid, bg=self.bg)
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Right column
        right_col = tk.Frame(stats_grid, bg=self.bg)
        right_col.pack(side='left', fill='both', expand=True, padx=(10, 0))

        # --- PLAN CARD ---
        self.plan_card = self.create_card(left_col, "Current Plan")
        self.plan_card.pack(fill='x', pady=(0, 15))

        self.plan_name_label = tk.Label(
            self.plan_card,
            text="Free",
            font=('Segoe UI', 24, 'bold'),
            fg="#8b5cf6",
            bg=self.card_bg
        )
        self.plan_name_label.pack(pady=(10, 5))

        self.plan_features_label = tk.Label(
            self.plan_card,
            text="Basic features",
            font=('Segoe UI', 10),
            fg=self.secondary_color,
            bg=self.card_bg
        )
        self.plan_features_label.pack(pady=(0, 15))

        # Upgrade button (hidden for Premium users)
        self.upgrade_btn = ttk.Button(
            self.plan_card,
            text="⬆️ Upgrade Plan",
            command=self.open_pricing_page,
            bootstyle="success"
        )
        self.upgrade_btn.pack(pady=(0, 10))

        # --- WORD USAGE CARD ---
        self.usage_card = self.create_card(left_col, "Word Usage")
        self.usage_card.pack(fill='x', pady=(0, 15))

        # Usage stats
        usage_stats_frame = tk.Frame(self.usage_card, bg=self.card_bg)
        usage_stats_frame.pack(fill='x', padx=15, pady=10)

        self.words_used_label = tk.Label(
            usage_stats_frame,
            text="0",
            font=('Segoe UI', 28, 'bold'),
            fg=self.text_color,
            bg=self.card_bg
        )
        self.words_used_label.pack()

        self.words_limit_label = tk.Label(
            usage_stats_frame,
            text="of 2,000 words",
            font=('Segoe UI', 11),
            fg=self.secondary_color,
            bg=self.card_bg
        )
        self.words_limit_label.pack(pady=(0, 10))

        # Progress bar
        self.usage_progress = ttk.Progressbar(
            usage_stats_frame,
            length=250,
            mode='determinate',
            bootstyle="success"
        )
        self.usage_progress.pack(pady=(5, 10))

        self.usage_percentage_label = tk.Label(
            usage_stats_frame,
            text="0% used",
            font=('Segoe UI', 10),
            fg=self.secondary_color,
            bg=self.card_bg
        )
        self.usage_percentage_label.pack()

        # --- RESET TIMER CARD ---
        self.reset_card = self.create_card(right_col, "Next Reset")
        self.reset_card.pack(fill='x', pady=(0, 15))

        self.reset_timer_label = tk.Label(
            self.reset_card,
            text="Calculating...",
            font=('Segoe UI', 20, 'bold'),
            fg="#10b981",
            bg=self.card_bg
        )
        self.reset_timer_label.pack(pady=(15, 5))

        self.reset_info_label = tk.Label(
            self.reset_card,
            text="Weekly reset",
            font=('Segoe UI', 10),
            fg=self.secondary_color,
            bg=self.card_bg
        )
        self.reset_info_label.pack(pady=(0, 15))

        # --- REFERRAL BONUSES CARD ---
        self.referral_card = self.create_card(right_col, "Referral Bonuses")
        self.referral_card.pack(fill='x', pady=(0, 15))

        self.referral_words_label = tk.Label(
            self.referral_card,
            text="+0 words",
            font=('Segoe UI', 20, 'bold'),
            fg="#f59e0b",
            bg=self.card_bg
        )
        self.referral_words_label.pack(pady=(15, 5))

        self.referral_count_label = tk.Label(
            self.referral_card,
            text="0 successful referrals",
            font=('Segoe UI', 10),
            fg=self.secondary_color,
            bg=self.card_bg
        )
        self.referral_count_label.pack(pady=(0, 15))

        # --- ACCOUNT INFO CARD ---
        self.account_card = self.create_card(right_col, "Account")
        self.account_card.pack(fill='x')

        self.account_email_label = tk.Label(
            self.account_card,
            text="Not signed in",
            font=('Segoe UI', 11),
            fg=self.text_color,
            bg=self.card_bg
        )
        self.account_email_label.pack(pady=(10, 5))

        self.account_status_label = tk.Label(
            self.account_card,
            text="✓ Active",
            font=('Segoe UI', 9),
            fg="#10b981",
            bg=self.card_bg
        )
        self.account_status_label.pack(pady=(0, 10))

    def create_card(self, parent, title):
        """Create a modern card widget"""
        card = tk.Frame(parent, bg=self.card_bg, relief='flat', bd=0)

        # Add subtle shadow effect with border
        if self.bg == "#f5f5f5":  # Light mode
            card.configure(highlightbackground="#e0e0e0", highlightthickness=1)
        else:  # Dark mode
            card.configure(highlightbackground="#3a3a3a", highlightthickness=1)

        # Card title
        title_label = tk.Label(
            card,
            text=title,
            font=('Segoe UI', 12, 'bold'),
            fg=self.text_color,
            bg=self.card_bg
        )
        title_label.pack(anchor='w', padx=15, pady=(12, 5))

        # Separator
        separator = tk.Frame(card, height=1, bg=self.secondary_color if self.bg == "#1a1a1a" else "#e0e0e0")
        separator.pack(fill='x', padx=15)

        return card

    def open_pricing_page(self):
        """Open pricing page in browser"""
        webbrowser.open("https://www.slywriter.ai/pricing")

    def start_auto_update(self):
        """Start auto-updating dashboard data"""
        self.update_dashboard_data()
        # Update every 5 seconds
        self.after(5000, self.start_auto_update)

    def update_dashboard_data(self):
        """Fetch and display dashboard data"""
        user = get_saved_user()
        if not user:
            self.show_logged_out_state()
            return

        self.account_email_label.configure(text=user.get('email', 'Unknown'))

        # Fetch usage data from server
        try:
            response = requests.post(
                f"{SERVER_URL}/billing/usage",
                headers={"Authorization": f"Bearer {user.get('token')}"},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                self.user_data = data
                self.update_ui_with_data(data)
            else:
                print(f"Failed to fetch dashboard data: {response.status_code}")
        except Exception as e:
            print(f"Error fetching dashboard data: {e}")

    def update_ui_with_data(self, data):
        """Update UI with fetched data"""
        # Plan info
        plan = data.get('plan', 'free').title()
        plan_emoji = {
            'Free': '🆓',
            'Pro': '⭐',
            'Premium': '👑',
            'Enterprise': '🏢'
        }

        self.plan_name_label.configure(text=f"{plan_emoji.get(plan, '')} {plan}")

        # Hide upgrade button for Premium/Enterprise users
        if plan.lower() in ['premium', 'enterprise']:
            self.upgrade_btn.pack_forget()
        else:
            self.upgrade_btn.pack(pady=(0, 10))

        # Plan features
        features_map = {
            'Free': 'Basic features • Limited words',
            'Pro': 'AI generation • Advanced features',
            'Premium': 'Everything • Priority support',
            'Enterprise': 'Custom solutions • Dedicated support'
        }
        self.plan_features_label.configure(text=features_map.get(plan, ''))

        # Word usage
        words_used = data.get('words_used', 0)
        total_limit = data.get('total_word_limit', 2000)
        base_limit = data.get('base_word_limit', 2000)
        referral_bonus = data.get('referral_bonus_words', 0)

        self.words_used_label.configure(text=f"{words_used:,}")
        self.words_limit_label.configure(text=f"of {total_limit:,} words")

        # Progress bar
        percentage = (words_used / total_limit * 100) if total_limit > 0 else 0
        self.usage_progress['value'] = min(percentage, 100)
        self.usage_percentage_label.configure(text=f"{percentage:.1f}% used")

        # Change progress bar color based on usage
        if percentage >= 90:
            self.usage_progress.configure(bootstyle="danger")
        elif percentage >= 70:
            self.usage_progress.configure(bootstyle="warning")
        else:
            self.usage_progress.configure(bootstyle="success")

        # Referral bonuses
        if referral_bonus > 0:
            self.referral_words_label.configure(text=f"+{referral_bonus:,} words")
            # We'd need to add referral count to the API response
            self.referral_count_label.configure(text="From referrals")
        else:
            self.referral_words_label.configure(text="+0 words")
            self.referral_count_label.configure(text="Invite friends to earn bonuses!")

        # Update reset timer
        self.update_reset_timer()

    def update_reset_timer(self):
        """Calculate and display time until next weekly reset"""
        if not self.reset_date:
            # Set reset date to next Monday at midnight
            now = datetime.datetime.now()
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7  # If today is Monday, reset next Monday
            self.reset_date = (now + datetime.timedelta(days=days_until_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        now = datetime.datetime.now()
        time_remaining = self.reset_date - now

        if time_remaining.total_seconds() <= 0:
            # Reset has occurred, set new reset date
            self.reset_date = self.reset_date + datetime.timedelta(days=7)
            time_remaining = self.reset_date - now

        days = time_remaining.days
        hours, remainder = divmod(time_remaining.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            timer_text = f"{days}d {hours}h"
        elif hours > 0:
            timer_text = f"{hours}h {minutes}m"
        else:
            timer_text = f"{minutes}m {seconds}s"

        self.reset_timer_label.configure(text=timer_text)

        # Update every second if less than 1 hour remaining
        if time_remaining.total_seconds() < 3600:
            self.after(1000, self.update_reset_timer)
        else:
            self.after(60000, self.update_reset_timer)  # Update every minute otherwise

    def show_logged_out_state(self):
        """Show dashboard in logged out state"""
        self.plan_name_label.configure(text="🔒 Not Signed In")
        self.plan_features_label.configure(text="Sign in to view your plan")
        self.words_used_label.configure(text="—")
        self.words_limit_label.configure(text="Sign in to track usage")
        self.usage_progress['value'] = 0
        self.usage_percentage_label.configure(text="")
        self.reset_timer_label.configure(text="—")
        self.reset_info_label.configure(text="Sign in to see reset timer")
        self.referral_words_label.configure(text="—")
        self.referral_count_label.configure(text="Sign in to earn bonuses")
        self.account_email_label.configure(text="Not signed in")
        self.account_status_label.configure(text="Sign in to continue")
        self.upgrade_btn.pack(pady=(0, 10))
