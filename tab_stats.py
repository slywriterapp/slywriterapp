# tab_stats.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import config
import typing_engine as engine
from datetime import datetime, timedelta
from collections import defaultdict
import re

class StatsTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.widgets = []
        # --- SESSION-BASED STATS (reset on app launch) ---
        self.session_words = 0
        self.session_sessions = 0
        self.session_wpm_sum = 0
        self.session_wpm_sessions = 0
        self.session_profile_counts = {}
        self.session_last_words = 0  # For display
        self.session_last_wpm = 0    # For display
        self.session_last_profile = "—"
        self.build_ui()
        self.update_stats(alltime_only=True)
        # Register to receive typing session completions
        engine.set_stats_tab_reference(self)

    def build_ui(self):
        # Summary frame at top
        self.summary_frame = tk.Frame(self)
        self.summary_frame.pack(fill='x', padx=10, pady=(10,0))
        self.widgets.append(self.summary_frame)

        self.lbl_sessions = tk.Label(self.summary_frame, font=('Segoe UI', 10, 'bold'))
        self.lbl_words = tk.Label(self.summary_frame, font=('Segoe UI', 10))
        self.lbl_session_words = tk.Label(self.summary_frame, font=('Segoe UI', 10))
        self.lbl_avg_wpm = tk.Label(self.summary_frame, font=('Segoe UI', 10))
        self.lbl_most_profile = tk.Label(self.summary_frame, font=('Segoe UI', 10))

        self.lbl_sessions.grid(row=0, column=0, sticky='w', padx=(0,20))
        self.lbl_words.grid(row=0, column=1, sticky='w', padx=(0,20))
        self.lbl_session_words.grid(row=0, column=2, sticky='w', padx=(0,20))
        self.lbl_avg_wpm.grid(row=0, column=3, sticky='w', padx=(0,20))
        self.lbl_most_profile.grid(row=0, column=4, sticky='w')

        # Usage Analytics section
        analytics_lbl = tk.Label(self, text='Usage Analytics', font=('Segoe UI', 12, 'bold'), anchor='w')
        analytics_lbl.pack(fill='x', padx=10, pady=(15, 5))
        self.widgets.append(analytics_lbl)
        
        # Analytics frame
        self.analytics_frame = tk.Frame(self)
        self.analytics_frame.pack(fill='x', padx=10, pady=(0, 10))
        self.widgets.append(self.analytics_frame)
        
        # Daily/Weekly insights
        self.lbl_today = tk.Label(self.analytics_frame, font=('Segoe UI', 9))
        self.lbl_week = tk.Label(self.analytics_frame, font=('Segoe UI', 9))
        self.lbl_peak_time = tk.Label(self.analytics_frame, font=('Segoe UI', 9))
        self.lbl_streak = tk.Label(self.analytics_frame, font=('Segoe UI', 9))
        
        self.lbl_today.grid(row=0, column=0, sticky='w', padx=(0,15))
        self.lbl_week.grid(row=0, column=1, sticky='w', padx=(0,15))
        self.lbl_peak_time.grid(row=1, column=0, sticky='w', padx=(0,15), pady=(5,0))
        self.lbl_streak.grid(row=1, column=1, sticky='w', padx=(0,15), pady=(5,0))
        
        # Show analytics button
        self.btn_analytics = ttk.Button(self.analytics_frame, text='Show Detailed Analytics', command=self.show_detailed_analytics)
        self.btn_analytics.grid(row=0, column=2, rowspan=2, padx=15)
        
        # Section header for diagnostics
        lbl = tk.Label(self, text='Typing Diagnostics', font=('Segoe UI', 12, 'bold'), anchor='w')
        lbl.pack(fill='x', padx=10, pady=(10, 0))
        self.widgets.append(lbl)

        # Log area
        frame = tk.Frame(self)
        frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.widgets.append(frame)

        self.txt = tk.Text(frame, height=13, wrap='none', font=('Consolas', 10))
        sb = ttk.Scrollbar(frame, orient='vertical', command=self.txt.yview)
        self.txt.configure(yscrollcommand=sb.set)
        self.txt.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=(5, 10))
        self.widgets.append(btn_frame)
        self.btn_export = ttk.Button(btn_frame, text='Export CSV', command=self.export_csv)
        self.btn_copy = ttk.Button(btn_frame, text='Copy to Clipboard', command=self.copy_to_clipboard)
        self.btn_export.pack(side='left', padx=5)
        self.btn_copy.pack(side='left', padx=5)

    def _get_user_log_file(self):
        """Get user-specific log file path"""
        try:
            # Try to get user info from the app
            if hasattr(self.app, 'user') and self.app.user:
                user_id = self.app.user.get('id', 'unknown')
                # Create user-specific log file name
                import os
                base_dir = os.path.dirname(config.LOG_FILE)
                user_log_file = os.path.join(base_dir, f"typing_log_{user_id}.txt")
                return user_log_file
            else:
                # No user logged in - return None to show no stats
                return None
        except Exception:
            # Fallback to None if there's any error
            return None

    def receive_session(self, words, wpm, profile):
        """Call this after each typing session to update session-based stats."""
        self.session_words += words
        self.session_sessions += 1
        if wpm > 0:
            self.session_wpm_sum += wpm
            self.session_wpm_sessions += 1
        if profile:
            self.session_profile_counts[profile] = self.session_profile_counts.get(profile, 0) + 1
            self.session_last_profile = profile
        self.session_last_words = words
        self.session_last_wpm = wpm
        self.update_stats()
    
    def analyze_usage_patterns(self):
        """Analyze usage patterns from user-specific log file"""
        # Get user-specific log file
        log_file = self._get_user_log_file()
        if not log_file:
            return {
                'today_words': 0,
                'week_words': 0,
                'peak_hour': 'N/A',
                'daily_streak': 0
            }
        
        try:
            with open(log_file, 'r', encoding='utf-8') as logf:
                lines = logf.readlines()
        except FileNotFoundError:
            return {
                'today_words': 0,
                'week_words': 0,
                'peak_hour': 'N/A',
                'daily_streak': 0
            }
        
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        daily_words = defaultdict(int)
        hourly_activity = defaultdict(int)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse timestamp from log entry [2025-01-08T14:30:45.123456]
            timestamp_match = re.match(r'\[(\d{4}-\d{2}-\d{2})T(\d{2}):', line)
            if not timestamp_match:
                continue
                
            date_str, hour_str = timestamp_match.groups()
            try:
                entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                hour = int(hour_str)
            except ValueError:
                continue
            
            # Extract word count from text
            parts = line.split('] ', 1)
            if len(parts) == 2:
                text = parts[1].split(' (profile=')[0].strip()
                word_count = len(text.split())
                
                daily_words[entry_date] += word_count
                hourly_activity[hour] += word_count
        
        # Calculate metrics
        today_words = daily_words[today]
        week_words = sum(daily_words[date] for date in daily_words if date >= week_ago)
        
        # Find peak hour
        peak_hour = max(hourly_activity, key=hourly_activity.get) if hourly_activity else 0
        peak_hour_str = f"{peak_hour:02d}:00-{peak_hour+1:02d}:00"
        
        # Calculate daily streak
        streak = 0
        current_date = today
        while current_date in daily_words and daily_words[current_date] > 0:
            streak += 1
            current_date -= timedelta(days=1)
        
        return {
            'today_words': today_words,
            'week_words': week_words,
            'peak_hour': peak_hour_str,
            'daily_streak': streak
        }
    
    def show_detailed_analytics(self):
        """Show a detailed analytics window"""
        analytics_window = tk.Toplevel(self)
        analytics_window.title("Detailed Usage Analytics")
        analytics_window.geometry("600x500")
        analytics_window.transient(self)
        
        # Apply theme colors to window
        dark = self.app.cfg['settings'].get('dark_mode', False)
        bg_color = config.DARK_BG if dark else config.LIGHT_BG
        fg_color = config.DARK_FG if dark else config.LIGHT_FG
        analytics_window.configure(bg=bg_color)
        
        # Configure ttk styling for this popup
        style = ttk.Style()
        
        # Style the ttk frames to match theme - NO MORE GRAY!
        style.configure("Analytics.TFrame",
                       background=bg_color,
                       borderwidth=0,
                       relief='flat')
        
        # Override any default frame styling
        style.configure("TFrame", 
                       background=bg_color,
                       borderwidth=0,
                       relief='flat')
        
        # Style the notebook tabs to match modern theme
        tab_bg = config.GRAY_600 if dark else config.GRAY_200
        tab_active = config.PRIMARY_BLUE
        tab_fg = config.DARK_FG if dark else config.LIGHT_FG
        
        style.configure("Analytics.TNotebook",
                       background=bg_color,
                       borderwidth=0,
                       tabposition="n")
        
        style.configure("Analytics.TNotebook.Tab",
                       background=tab_bg,
                       foreground=tab_fg,
                       padding=[16, 12],
                       borderwidth=0,
                       font=(config.FONT_PRIMARY, 10, 'bold'))
        
        style.map("Analytics.TNotebook.Tab",
                  background=[('selected', tab_active),
                             ('active', config.PRIMARY_BLUE_HOVER)],
                  foreground=[('selected', 'white'),
                             ('active', 'white')])
        
        # Make window non-resizable for clean layout
        analytics_window.resizable(False, False)
        
        # Create notebook for different analytics views
        notebook = ttk.Notebook(analytics_window, style="Analytics.TNotebook")
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Daily Activity Tab
        daily_frame = ttk.Frame(notebook, style="Analytics.TFrame")
        notebook.add(daily_frame, text="Daily Activity")
        
        # Weekly Summary Tab
        weekly_frame = ttk.Frame(notebook, style="Analytics.TFrame")
        notebook.add(weekly_frame, text="Weekly Summary")
        
        # Usage Chart Tab
        chart_frame = ttk.Frame(notebook, style="Analytics.TFrame")
        notebook.add(chart_frame, text="Usage Chart")
        
        self._populate_daily_analytics(daily_frame)
        self._populate_weekly_analytics(weekly_frame)
        self._populate_usage_chart(chart_frame)
    
    def _populate_daily_analytics(self, frame):
        """Populate daily analytics tab"""
        # Apply theme colors
        dark = self.app.cfg['settings'].get('dark_mode', False)
        bg_color = config.DARK_BG if dark else config.LIGHT_BG
        fg_color = config.DARK_FG if dark else config.LIGHT_FG
        
        # Get user-specific log file
        log_file = self._get_user_log_file()
        if not log_file:
            no_data_label = tk.Label(frame, text="Please log in to view your analytics.", font=('Segoe UI', 12), bg=bg_color, fg=fg_color)
            no_data_label.pack(pady=50)
            return
            
        try:
            with open(log_file, 'r', encoding='utf-8') as logf:
                lines = logf.readlines()
        except FileNotFoundError:
            no_data_label = tk.Label(frame, text="No usage data available yet.", font=('Segoe UI', 12), bg=bg_color, fg=fg_color)
            no_data_label.pack(pady=50)
            return
        
        # Process last 7 days
        daily_data = defaultdict(lambda: {'words': 0, 'sessions': 0})
        
        for line in lines:
            timestamp_match = re.match(r'\[(\d{4}-\d{2}-\d{2})', line)
            if not timestamp_match:
                continue
                
            date_str = timestamp_match.group(1)
            try:
                entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                continue
                
            if entry_date >= datetime.now().date() - timedelta(days=6):
                parts = line.split('] ', 1)
                if len(parts) == 2:
                    text = parts[1].split(' (profile=')[0].strip()
                    word_count = len(text.split())
                    daily_data[entry_date]['words'] += word_count
                    daily_data[entry_date]['sessions'] += 1
        
        # Display daily data
        title_label = tk.Label(frame, text="Last 7 Days Activity", font=('Segoe UI', 14, 'bold'), bg=bg_color, fg=fg_color)
        title_label.pack(pady=(10, 20))
        
        for i in range(7):
            date = datetime.now().date() - timedelta(days=i)
            data = daily_data[date]
            
            day_frame = tk.Frame(frame, bg=bg_color)
            day_frame.pack(fill='x', padx=20, pady=2)
            
            date_str = date.strftime("%A, %b %d")
            date_label = tk.Label(day_frame, text=f"{date_str}:", font=('Segoe UI', 10, 'bold'), width=20, anchor='w', bg=bg_color, fg=fg_color)
            date_label.pack(side='left')
            data_label = tk.Label(day_frame, text=f"{data['words']} words, {data['sessions']} sessions", font=('Segoe UI', 10), bg=bg_color, fg=fg_color)
            data_label.pack(side='left')
    
    def _populate_weekly_analytics(self, frame):
        """Populate weekly analytics tab"""
        # Apply theme colors
        dark = self.app.cfg['settings'].get('dark_mode', False)
        bg_color = config.DARK_BG if dark else config.LIGHT_BG
        fg_color = config.DARK_FG if dark else config.LIGHT_FG
        
        analytics = self.analyze_usage_patterns()
        
        title_label = tk.Label(frame, text="Weekly Summary", font=('Segoe UI', 14, 'bold'), bg=bg_color, fg=fg_color)
        title_label.pack(pady=(10, 20))
        
        # Summary stats
        stats_frame = tk.Frame(frame, bg=bg_color)
        stats_frame.pack(pady=10)
        
        stats = [
            ("Total words this week:", f"{analytics['week_words']:,}"),
            ("Daily streak:", f"{analytics['daily_streak']} days"),
            ("Peak activity time:", analytics['peak_hour']),
            ("Today's progress:", f"{analytics['today_words']:,} words")
        ]
        
        for i, (label, value) in enumerate(stats):
            row_frame = tk.Frame(stats_frame, bg=bg_color)
            row_frame.pack(fill='x', pady=5)
            label_widget = tk.Label(row_frame, text=label, font=('Segoe UI', 11), width=20, anchor='w', bg=bg_color, fg=fg_color)
            label_widget.pack(side='left')
            value_widget = tk.Label(row_frame, text=value, font=('Segoe UI', 11, 'bold'), fg=config.LIME_GREEN, bg=bg_color)
            value_widget.pack(side='left')
    
    def _populate_usage_chart(self, frame):
        """Populate usage chart tab with a proper coordinate plane graph"""
        # Apply theme colors
        dark = self.app.cfg['settings'].get('dark_mode', False)
        bg_color = config.DARK_BG if dark else config.LIGHT_BG
        fg_color = config.DARK_FG if dark else config.LIGHT_FG
        
        # Get user-specific log file
        log_file = self._get_user_log_file()
        if not log_file:
            no_data_label = tk.Label(frame, text="Please log in to view your usage chart.", font=('Segoe UI', 12), bg=bg_color, fg=fg_color)
            no_data_label.pack(pady=50)
            return
            
        try:
            with open(log_file, 'r', encoding='utf-8') as logf:
                lines = logf.readlines()
        except FileNotFoundError:
            no_data_label = tk.Label(frame, text="No usage data available yet.", font=('Segoe UI', 12), bg=bg_color, fg=fg_color)
            no_data_label.pack(pady=50)
            return
        
        title_label = tk.Label(frame, text="7-Day Usage Graph", font=('Segoe UI', 14, 'bold'), bg=bg_color, fg=fg_color)
        title_label.pack(pady=(10, 20))
        
        # Process last 7 days
        daily_words = defaultdict(int)
        
        for line in lines:
            timestamp_match = re.match(r'\[(\d{4}-\d{2}-\d{2})', line)
            if not timestamp_match:
                continue
                
            date_str = timestamp_match.group(1)
            try:
                entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                continue
                
            if entry_date >= datetime.now().date() - timedelta(days=6):
                parts = line.split('] ', 1)
                if len(parts) == 2:
                    text = parts[1].split(' (profile=')[0].strip()
                    word_count = len(text.split())
                    daily_words[entry_date] += word_count
        
        # Create graph canvas
        graph_frame = tk.Frame(frame, bg=bg_color)
        graph_frame.pack(pady=10, padx=20)
        
        canvas_bg = bg_color  # Use the same background as the frame
        canvas = tk.Canvas(graph_frame, width=500, height=300, bg=canvas_bg, highlightthickness=1, highlightbackground=fg_color)
        canvas.pack()
        
        # Graph dimensions
        margin = 50
        graph_width = 500 - 2 * margin
        graph_height = 300 - 2 * margin
        
        # Calculate data points
        dates = []
        values = []
        for i in range(7):
            date = datetime.now().date() - timedelta(days=6-i)
            dates.append(date)
            values.append(daily_words.get(date, 0))
        
        max_words = max(values) if values and max(values) > 0 else 100
        
        # Draw axes
        axis_color = '#000000' if not dark else '#ffffff'
        # Y-axis (left)
        canvas.create_line(margin, margin, margin, margin + graph_height, fill=axis_color, width=2)
        # X-axis (bottom)
        canvas.create_line(margin, margin + graph_height, margin + graph_width, margin + graph_height, fill=axis_color, width=2)
        
        # Draw grid lines and Y-axis labels
        for i in range(5):
            y = margin + (graph_height * i / 4)
            words_val = int(max_words * (4 - i) / 4)
            # Grid line
            canvas.create_line(margin, y, margin + graph_width, y, fill='#cccccc' if not dark else '#555555', width=1, dash=(2, 2))
            # Y-axis label
            canvas.create_text(margin - 10, y, text=str(words_val), fill=axis_color, anchor='e', font=('Segoe UI', 8))
        
        # Plot data points and lines
        points = []
        for i, (date, words) in enumerate(zip(dates, values)):
            x = margin + (graph_width * i / 6)
            y = margin + graph_height - (graph_height * words / max_words) if max_words > 0 else margin + graph_height
            points.append((x, y))
            
            # Draw data point
            canvas.create_oval(x-4, y-4, x+4, y+4, fill=config.LIME_GREEN, outline=config.LIME_GREEN, width=2)
            
            # X-axis labels (dates)
            date_str = date.strftime("%m/%d")
            canvas.create_text(x, margin + graph_height + 15, text=date_str, fill=axis_color, font=('Segoe UI', 8))
            
            # Value labels above points
            if words > 0:
                canvas.create_text(x, y - 15, text=str(words), fill=config.LIME_GREEN, font=('Segoe UI', 8, 'bold'))
        
        # Draw connecting lines
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            canvas.create_line(x1, y1, x2, y2, fill=config.LIME_GREEN, width=2)
        
        # Add axis labels
        canvas.create_text(margin + graph_width/2, margin + graph_height + 35, text="Days", fill=axis_color, font=('Segoe UI', 10, 'bold'))
        canvas.create_text(15, margin + graph_height/2, text="Words", fill=axis_color, font=('Segoe UI', 10, 'bold'), angle=90)
        
        # Chart legend
        legend_frame = tk.Frame(frame, bg=bg_color)
        legend_frame.pack(pady=10)
        
        legend_label = tk.Label(legend_frame, text="Daily word count over the last 7 days", font=('Segoe UI', 10, 'italic'), bg=bg_color, fg=fg_color)
        legend_label.pack()
        
        if max_words > 0:
            peak_label = tk.Label(legend_frame, text=f"Peak: {max(values):,} words", font=('Segoe UI', 9), fg=config.LIME_GREEN, bg=bg_color)
            peak_label.pack()

    def update_stats(self, alltime_only=False):
        # --- ALL-TIME STATS (from user-specific log) ---
        total_sessions = 0
        total_words = 0
        lines = []
        
        # Get user-specific log file
        log_file = self._get_user_log_file()
        if log_file:
            try:
                with open(log_file, 'r', encoding='utf-8') as logf:
                    lines = logf.readlines()
            except FileNotFoundError:
                lines = []
        total_sessions = len(lines)
        for line in lines:
            line = line.strip()
            parts = line.split('] ', 1)
            if len(parts) == 2:
                text = parts[1]
                entry_text = text.split(' (profile=')[0].strip()
                word_count = len(entry_text.split())
                total_words += word_count

        # --- SESSION-BASED STATS (for this app run) ---
        words_this_session = self.session_words
        avg_wpm = int(self.session_wpm_sum / self.session_wpm_sessions) if self.session_wpm_sessions else 0
        most_profile = max(self.session_profile_counts, key=self.session_profile_counts.get) if self.session_profile_counts else "—"

        # On initial app launch, force these to zero/"—" if no typing yet
        if alltime_only or (self.session_sessions == 0 and self.session_words == 0):
            words_this_session = 0
            avg_wpm = 0
            most_profile = "—"

        self.lbl_sessions.config(text=f"Total sessions: {total_sessions}")
        self.lbl_words.config(text=f"Total words: {total_words}")
        self.lbl_session_words.config(text=f"Words this session: {words_this_session}")
        self.lbl_avg_wpm.config(text=f"Avg. WPM: {avg_wpm}")
        self.lbl_most_profile.config(text=f"Most used profile: {most_profile}")
        
        # Update analytics display
        analytics = self.analyze_usage_patterns()
        self.lbl_today.config(text=f"Today: {analytics['today_words']:,} words")
        self.lbl_week.config(text=f"This week: {analytics['week_words']:,} words")
        self.lbl_peak_time.config(text=f"Peak time: {analytics['peak_hour']}")
        self.lbl_streak.config(text=f"Daily streak: {analytics['daily_streak']} days")

        # --- LOG DISPLAY ---
        last5 = lines[-5:] if len(lines) >= 5 else lines
        last5 = last5[::-1]
        self.txt.configure(state='normal')
        self.txt.delete('1.0', tk.END)
        self.txt.insert(tk.END, "Last 5 entries (most recent first):\n\n")
        for idx, line in enumerate(last5):
            if idx == 0:
                self.txt.insert(tk.END, line, 'highlight')
            else:
                self.txt.insert(tk.END, line)
        self.txt.configure(state='disabled')

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if not path:
            return
        
        log_file = self._get_user_log_file()
        if not log_file:
            messagebox.showwarning('Error', 'Please log in to export your data.')
            return
        
        try:
            with open(log_file, 'r', encoding='utf-8') as src, \
                 open(path, 'w', newline='', encoding='utf-8') as dst:
                writer = csv.writer(dst)
                writer.writerow(['timestamp', 'text'])
                for line in src:
                    parts = line.strip().split('] ', 1)
                    if len(parts) == 2:
                        writer.writerow([parts[0].lstrip('['), parts[1]])
            messagebox.showinfo('Exported', f'Log exported to {path}')
        except FileNotFoundError:
            messagebox.showwarning('Error', 'No log file to export.')

    def copy_to_clipboard(self):
        log_file = self._get_user_log_file()
        if not log_file:
            messagebox.showwarning('Error', 'Please log in to copy your data.')
            return
        
        try:
            with open(log_file, 'r', encoding='utf-8') as logf:
                text = logf.read()
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
            messagebox.showinfo('Copied', 'Log copied to clipboard.')
        except FileNotFoundError:
            messagebox.showwarning('Error', 'No log file to copy.')

    def set_theme(self, dark):
        bg = config.DARK_BG if dark else config.LIGHT_BG
        fg = config.DARK_FG if dark else config.LIGHT_FG
        entry_bg = config.DARK_ENTRY_BG if dark else "white"

        self.configure(bg=bg)
        self.summary_frame.configure(bg=bg)
        self.analytics_frame.configure(bg=bg)
        
        for lbl in (self.lbl_sessions, self.lbl_words, self.lbl_session_words, self.lbl_avg_wpm, self.lbl_most_profile):
            lbl.configure(bg=bg, fg=fg)
        
        for lbl in (self.lbl_today, self.lbl_week, self.lbl_peak_time, self.lbl_streak):
            lbl.configure(bg=bg, fg=fg)
        for widget in self.widgets:
            try:
                widget.configure(bg=bg)
            except:
                pass
        self.txt.configure(bg=entry_bg, fg=fg, insertbackground=fg)
        self.txt.tag_config('highlight', background='#30333a' if dark else '#D8E7FF')

# --- The following is the hook your typing engine should call! ---

def notify_typing_session(words, wpm, profile):
    """Global function for engine to call after each session."""
    # Find the first existing StatsTab instance and call receive_session.
    for widget in tk._default_root.winfo_children():
        if isinstance(widget, StatsTab):
            widget.receive_session(words, wpm, profile)
            break
