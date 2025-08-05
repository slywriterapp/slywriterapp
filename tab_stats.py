# tab_stats.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import config
import typing_engine as engine

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

        # Section header
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

    def update_stats(self, alltime_only=False):
        # --- ALL-TIME STATS (from log) ---
        total_sessions = 0
        total_words = 0
        lines = []
        try:
            with open(config.LOG_FILE, 'r', encoding='utf-8') as logf:
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
        try:
            with open(config.LOG_FILE, 'r', encoding='utf-8') as src, \
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
        try:
            with open(config.LOG_FILE, 'r', encoding='utf-8') as logf:
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
        for lbl in (self.lbl_sessions, self.lbl_words, self.lbl_session_words, self.lbl_avg_wpm, self.lbl_most_profile):
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
