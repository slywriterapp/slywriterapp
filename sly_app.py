# sly_app.py

import os
import sys
import json
import config
import typing_engine as engine
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tab_humanizer import HumanizerTab
from tab_account import AccountTab
from tab_typing import TypingTab
from tab_hotkeys import HotkeysTab
from tab_stats import StatsTab
from auth import get_saved_user
from utils import Tooltip
import keyboard
import threading
from PIL import Image, ImageTk
import tkinter as tk  # <-- for classic Tk widgets!

from sly_splash import show_splash_screen
from sly_theme import apply_app_theme, force_theme_refresh
from sly_config import (
    load_config, save_config, BUILTIN_PROFILES,
    add_profile, delete_profile, save_profile, reset_typing_settings,
    on_profile_change, on_setting_change
)
from sly_hotkeys import (
    register_hotkeys, set_start_hotkey, set_stop_hotkey, set_pause_hotkey,
    reset_hotkeys, validate_and_set_hotkey
)

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

class TypingApp(tb.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.iconbitmap("slywriter_logo.ico")
        self.user = None

        # Load and immediately clean up your profiles
        self.cfg = load_config()
        self._clean_profiles()

        saved_dark = self.cfg.get("settings", {}).get("dark_mode", False)
        self.tb_style = tb.Style()
        self.tb_style.theme_use("darkly" if saved_dark else "flatly")

        self.withdraw()
        # Show splash then post-setup
        self.after(10, lambda: show_splash_screen(self, self._post_splash_setup))

    def _clean_profiles(self):
        """
        Keep only the three hyphenated profiles: Default, Speed-Type, Ultra-Slow.
        Rename any old variants to the correct names.
        """
        valid = {"Default", "Speed-Type", "Ultra-Slow"}
        old_to_new = {
            "Speed": "Speed-Type",
            "SpeedType": "Speed-Type",
            "SpeedTyping": "Speed-Type",
            "UltraSlow": "Ultra-Slow"
        }

        cleaned = []
        for p in self.cfg.get("profiles", []):
            name = old_to_new.get(p, p)
            if name in valid and name not in cleaned:
                cleaned.append(name)

        # Ensure all three exist
        for name in valid:
            if name not in cleaned:
                cleaned.append(name)

        self.cfg["profiles"] = cleaned

        # Fix active_profile if missing
        active = self.cfg.get("active_profile")
        active = old_to_new.get(active, active)
        if active not in cleaned:
            active = "Default"
        self.cfg["active_profile"] = active

        save_config(self.cfg)

    def _post_splash_setup(self):
        self.setup_ui()
        self.apply_theme()  # Will now style the top bar too!
        force_theme_refresh(self)

        on_profile_change(self)
        self.deiconify()

        # If already logged in, restore account tab
        saved_user = get_saved_user()
        if saved_user:
            self.user = saved_user
            self.on_login(saved_user)
            self.account_tab.update_for_login(saved_user)

    def setup_ui(self):
        self.title("SlyWriter")
        self.geometry("720x680")

        # -- Use classic Tk Frame for the TOP BAR so bg can be set safely!
        self.top = tk.Frame(self)
        self.top.pack(fill='x', padx=10, pady=5)

        # --- Profile selector: Use tk.Frame too so bg can be set!
        self.prof_frame = tk.Frame(self.top)
        self.prof_frame.pack(side='right')

        tb.Label(self.prof_frame, text="Profile:").pack(side='left')

        self.active_profile = tb.StringVar(value=self.cfg["active_profile"])
        self.prof_box = tb.Combobox(
            self.prof_frame,
            values=self.cfg["profiles"],
            textvariable=self.active_profile,
            state='readonly',
            width=15
        )
        self.prof_box.pack(side='left')
        Tooltip(self.prof_box, "Select typing profile")
        self.prof_box.bind("<<ComboboxSelected>>", lambda e: self._on_profile_change())

        for txt, cmd, tip in [
            ('+', self._add_profile, "Add profile"),
            ('–', self._delete_profile, "Delete profile"),
            ('💾', self._save_profile, "Save profile")
        ]:
            b = tb.Button(self.prof_frame, text=txt, width=2, command=cmd)
            b.pack(side='left', padx=2)
            Tooltip(b, tip)

        # --- Help & Dark mode toggles (these can remain ttkbootstrap) ---
        help_btn = tb.Button(self.top, text='?', width=2, command=self.show_help)
        help_btn.pack(side='right')
        Tooltip(help_btn, "Show usage guide")

        self.dark_var = tb.BooleanVar(value=self.cfg['settings'].get('dark_mode', False))
        dark_chk = tb.Checkbutton(
            self.top, text="Dark Mode", variable=self.dark_var,
            command=lambda: self.toggle_dark(self.dark_var.get())
        )
        dark_chk.pack(side='left', padx=5)
        Tooltip(dark_chk, "Toggle dark mode")

        # --- Notebook tabs ---
        self.notebook = tb.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        self.tabs = {}
        for name in ['Account', 'Typing', 'Hotkeys', 'Diagnostics', 'Humanizer']:
            f = tb.Frame(self.notebook)
            self.notebook.add(f, text=name)
            self.tabs[name] = f

        self.account_tab   = AccountTab(self.tabs['Account'], self); self.account_tab.pack(fill='both', expand=True)
        self.typing_tab    = TypingTab(self.tabs['Typing'], self);    self.typing_tab.pack(fill='both', expand=True)
        self.hotkeys_tab   = HotkeysTab(self.tabs['Hotkeys'], self);   self.hotkeys_tab.pack(fill='both', expand=True)
        self.stats_tab     = StatsTab(self.tabs['Diagnostics'], self); self.stats_tab.pack(fill='both', expand=True)
        self.humanizer_tab = HumanizerTab(self.tabs['Humanizer'], self);self.humanizer_tab.pack(fill='both', expand=True)
        engine.set_stats_tab_reference(self.stats_tab)

        engine.set_account_tab_reference(self.account_tab)

        # Lock down all but Account until login
        for name, frame in self.tabs.items():
            if name != 'Account':
                self.notebook.tab(frame, state='disabled')

        register_hotkeys(self)

    # ─── Profile handlers ───────────────────
    def _add_profile(self):
        add_profile(self)
        self._refresh_profiles_dropdown()

    def _delete_profile(self):
        delete_profile(self)
        self._refresh_profiles_dropdown()

    def _save_profile(self):
        save_profile(self)

    def _refresh_profiles_dropdown(self):
        val = self.active_profile.get()
        self.prof_box['values'] = self.cfg['profiles']
        if val in self.cfg['profiles']:
            self.active_profile.set(val)
        else:
            self.active_profile.set('Default')
        self._on_profile_change()

    def _on_profile_change(self):
        # persist & apply
        self.cfg['active_profile'] = self.active_profile.get()
        save_config(self.cfg)
        on_profile_change(self)

    # ─── Login/Logout ──────────────────────
    def on_login(self, user_info):
        self.user = user_info
        for name, frame in self.tabs.items():
            if name != 'Account':
                self.notebook.tab(frame, state='normal')
        self.notebook.select(self.tabs['Typing'])

    def on_logout(self):
        self.user = None
        for name, frame in self.tabs.items():
            self.notebook.tab(frame, state='disabled')
        self.notebook.select(self.tabs['Account'])

    # ─── Hotkeys & Settings ─────────────────
    def set_start_hotkey(self, hk):     set_start_hotkey(self, hk)
    def set_stop_hotkey(self, hk):      set_stop_hotkey(self, hk)
    def set_pause_hotkey(self, hk):     set_pause_hotkey(self, hk)
    def _validate_and_set_hotkey(self, hk, k): validate_and_set_hotkey(self, hk, k)
    def reset_hotkeys(self):            reset_hotkeys(self)
    def reset_typing_settings(self):    reset_typing_settings(self)
    def on_setting_change(self):        on_setting_change(self)
    def on_profile_change(self, _=None):on_profile_change(self)

    # ─── Theme toggling ────────────────────
    def toggle_dark(self, is_dark):
        self.cfg['settings']['dark_mode'] = is_dark
        theme = "darkly" if is_dark else "flatly"
        self.tb_style.theme_use(theme)
        self.apply_theme()
        save_config(self.cfg)

    def apply_theme(self):
        # Set classic bar colors
        is_dark = self.cfg['settings'].get('dark_mode', False)
        top_bg = "#21252B" if is_dark else "#ededed"
        prof_bg = "#2e323a" if is_dark else "#f8f8f8"

        self.top.configure(bg=top_bg)
        self.prof_frame.configure(bg=top_bg)

        # Make sure Combobox is readable
        fg = "#f0f0f0" if is_dark else "#1a1a1a"
        style = self.tb_style
        style.configure("TCombobox", fieldbackground=prof_bg, foreground=fg)
        style.map("TCombobox",
            fieldbackground=[('readonly', prof_bg)],
            foreground=[('readonly', fg)]
        )
        # All other normal theming
        apply_app_theme(self)

    def force_theme_refresh(self):
        force_theme_refresh(self)

    # ─── Help popup ────────────────────────
    def show_help(self):
        tb.messagebox.showinfo(
            'Help',
            "1. Paste or load text in the Typing tab.\n"
            "2. Configure settings and profiles.\n"
            "3. Press Start, Pause or Stop (or use hotkeys).\n"
            "4. Export logs or schedule tasks."
        )
