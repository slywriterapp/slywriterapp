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
from tab_overlay import OverlayTab
from tab_learn import LearnTab
from auth import get_saved_user
from utils import Tooltip
import keyboard
import threading
from PIL import Image, ImageTk
import tkinter as tk  # <-- for classic Tk widgets!

from sly_splash import show_splash_screen
from sly_theme import apply_app_theme, force_theme_refresh
from modern_notebook import apply_modern_notebook_style, TAB_ICONS
from sly_config import (
    load_config, save_config, BUILTIN_PROFILES,
    add_profile, delete_profile, save_profile, reset_typing_settings,
    on_profile_change, on_setting_change
)
from sly_hotkeys import (
    register_hotkeys, set_start_hotkey, set_stop_hotkey, set_pause_hotkey,
    set_overlay_hotkey, set_ai_generation_hotkey, reset_hotkeys, validate_and_set_hotkey
)

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

class TypingApp(tb.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.iconbitmap("slywriter_logo.ico")
        self.user = None
        
        # Modern window styling - wider for better proportions
        self.title("SlyWriter - AI-Powered Typing Assistant")
        self.geometry("980x780")  # Wider for better proportions 
        self.minsize(880, 700)    # Increased min width too
        
        # Center the window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

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

        # FORCE TTK REFRESH after all UI is created to fix startup checkbox issues
        self.after(100, lambda: self._force_startup_theme_refresh())

        # If already logged in, restore account tab and refresh premium
        saved_user = get_saved_user()
        if saved_user:
            self.user = saved_user
            self.on_login(saved_user)
            self.account_tab.update_for_login(saved_user)
            self.typing_tab.update_from_config()  # Ensure TypingTab picks up premium
            
            # Load usage data from server and update display
            self.account_tab.usage_mgr.load_usage()
            self.account_tab.usage_mgr.update_usage_display()
            self.update_idletasks()  # Force UI refresh

    def setup_ui(self):
        self.title("SlyWriter")
        self.geometry("980x780")  # Wider for better content display

        # -- Use classic Tk Frame for the TOP BAR so bg can be set safely!
        self.top = tk.Frame(self)
        self.top.pack(fill='x', padx=10, pady=5)
        
        # --- SlyWriter Logo and Title ---
        self.logo_frame = tk.Frame(self.top)
        self.logo_frame.pack(side='left')
        
        try:
            from PIL import Image, ImageTk
            # Load and resize logo
            logo_image = Image.open("slywriter_logo.png")
            logo_image = logo_image.resize((24, 24), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            
            logo_label = tk.Label(self.logo_frame, image=self.logo_photo)
            logo_label.pack(side='left', padx=(0, 8))
            
            title_label = tk.Label(
                self.logo_frame, 
                text="SlyWriter", 
                font=(config.FONT_PRIMARY, 12, 'bold'),
                fg=config.PRIMARY_BLUE
            )
            title_label.pack(side='left')
        except Exception as e:
            # Fallback if logo can't be loaded
            title_label = tk.Label(
                self.logo_frame, 
                text="🖊️ SlyWriter", 
                font=(config.FONT_PRIMARY, 12, 'bold'),
                fg=config.PRIMARY_BLUE
            )
            title_label.pack(side='left')

        # --- Profile selector: Use tk.Frame too so bg can be set!
        self.prof_frame = tk.Frame(self.top)
        self.prof_frame.pack(side='right')

        # Get initial modern theme colors - FIXED for light mode
        is_dark = self.cfg['settings'].get('dark_mode', False)
        top_bg = config.DARK_CARD_BG if is_dark else config.LIGHT_BG  # White in light mode
        prof_bg = config.DARK_ENTRY_BG if is_dark else config.LIGHT_CARD_BG  # Light gray in light mode
        profile_fg = config.DARK_FG if is_dark else config.LIGHT_FG
        
        self.profile_label = tk.Label(
            self.prof_frame, 
            text="Profile:", 
            bg=prof_bg, 
            fg=profile_fg,
            font=(config.FONT_PRIMARY, 10, 'bold')
        )
        self.profile_label.pack(side='left')

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
        self.dark_chk = tb.Checkbutton(
            self.top, text="Dark Mode", variable=self.dark_var,
            command=lambda: self.toggle_dark(self.dark_var.get())
        )
        self.dark_chk.pack(side='left', padx=5)
        Tooltip(self.dark_chk, "Toggle dark mode")

        # --- Modern Notebook tabs ---
        self.notebook = tb.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Apply modern notebook styling
        is_dark = self.cfg['settings'].get('dark_mode', False)
        apply_modern_notebook_style(self.notebook, is_dark)
        
        self.tabs = {}
        for name in ['Account', 'Typing', 'Hotkeys', 'Diagnostics', 'Humanizer', 'Overlay', 'Learn']:
            f = tb.Frame(self.notebook)
            # Add tab with icon
            icon = TAB_ICONS.get(name, "")
            display_name = f"{icon} {name}" if icon else name
            self.notebook.add(f, text=display_name)
            self.tabs[name] = f

        self.account_tab   = AccountTab(self.tabs['Account'], self); self.account_tab.pack(fill='both', expand=True)
        self.typing_tab    = TypingTab(self.tabs['Typing'], self);    self.typing_tab.pack(fill='both', expand=True)
        self.hotkeys_tab   = HotkeysTab(self.tabs['Hotkeys'], self);   self.hotkeys_tab.pack(fill='both', expand=True)
        self.stats_tab     = StatsTab(self.tabs['Diagnostics'], self); self.stats_tab.pack(fill='both', expand=True)
        self.humanizer_tab = HumanizerTab(self.tabs['Humanizer'], self);self.humanizer_tab.pack(fill='both', expand=True)
        self.overlay_tab   = OverlayTab(self.tabs['Overlay'], self); self.overlay_tab.pack(fill='both', expand=True)
        self.learn_tab     = LearnTab(self.tabs['Learn'], self); self.learn_tab.pack(fill='both', expand=True)
        engine.set_stats_tab_reference(self.stats_tab)
        engine.set_overlay_tab_reference(self.overlay_tab)

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
        # Whenever you login, always refresh premium in TypingTab
        self.typing_tab.update_from_config()

    def on_logout(self):
        self.user = None
        # Only disable tabs that require authentication, keep Account tab enabled
        tabs_to_disable = ['Typing', 'Diagnostics', 'Hotkeys', 'Humanizer']
        if hasattr(self, 'overlay_tab'):
            tabs_to_disable.append('Overlay')
        
        for name, frame in self.tabs.items():
            if name in tabs_to_disable:
                self.notebook.tab(frame, state='disabled')
            else:
                # Keep Account tab enabled so user can sign back in
                self.notebook.tab(frame, state='normal')
        
        self.notebook.select(self.tabs['Account'])
        self.typing_tab.update_from_config()  # Lock out premium on logout

    # ─── Hotkeys & Settings ─────────────────
    def set_start_hotkey(self, hk):     set_start_hotkey(self, hk)
    def set_stop_hotkey(self, hk):      set_stop_hotkey(self, hk)
    def set_pause_hotkey(self, hk):     set_pause_hotkey(self, hk)
    def set_overlay_hotkey(self, hk):   set_overlay_hotkey(self, hk)
    def set_ai_generation_hotkey(self, hk): set_ai_generation_hotkey(self, hk)
    def _validate_and_set_hotkey(self, hk, k): validate_and_set_hotkey(self, hk, k)
    def reset_hotkeys(self):            reset_hotkeys(self)
    def reset_typing_settings(self):    reset_typing_settings(self)
    def on_setting_change(self):        on_setting_change(self)
    def on_profile_change(self, _=None):on_profile_change(self)

    # ─── Theme toggling ────────────────────
    def toggle_dark(self, is_dark):
        self.cfg['settings']['dark_mode'] = is_dark
        
        # SEAMLESS THEME SWITCHING - Batch all updates to prevent flicker
        self.withdraw()  # Temporarily hide window
        
        try:
            # Apply basic TTK theme for standard widgets, but handle conflicts
            theme = "darkly" if is_dark else "flatly"
            try:
                # Only change theme if it's different from current
                if self.tb_style.theme.name != theme:
                    self.tb_style.theme_use(theme)
            except Exception as e:
                # If theme switching fails due to element conflicts, continue anyway
                # Our custom styling will handle the important elements
                pass
            
            # CRITICAL: Apply our custom theme AFTER ttkbootstrap theme to override it
            self.apply_theme()
            
            # DOUBLE FORCE: Apply global TTK theming again after everything else
            from modern_theme import apply_global_ttk_theme
            apply_global_ttk_theme(self, is_dark)
            
            # Force all updates to complete before showing window
            self.update_idletasks()
            
        finally:
            # Always show window again, even if there was an error
            self.deiconify()
            
        save_config(self.cfg)
        
        print(f"[THEME] Seamless switch to {'dark' if is_dark else 'light'} mode completed")

    def apply_theme(self):
        # Set modern 2025 colors - FIXED for light mode
        is_dark = self.cfg['settings'].get('dark_mode', False)
        
        # Apply global TTK theming first
        from modern_theme import apply_global_ttk_theme
        apply_global_ttk_theme(self, is_dark)
        
        # Apply modern app theming FIRST (this sets up the tab themes)
        apply_app_theme(self)
        
        # Then apply notebook styling
        apply_modern_notebook_style(self.notebook, is_dark)
        
        # Finally apply app-level styling
        top_bg = config.DARK_CARD_BG if is_dark else config.LIGHT_BG  # White in light mode
        prof_bg = config.DARK_ENTRY_BG if is_dark else config.LIGHT_CARD_BG  # Light gray in light mode

        self.top.configure(bg=top_bg)
        self.prof_frame.configure(bg=prof_bg)
        
        # Theme logo frame elements
        if hasattr(self, 'logo_frame'):
            self.logo_frame.configure(bg=top_bg)
            for child in self.logo_frame.winfo_children():
                if isinstance(child, tk.Label) and child.cget('text') != '':
                    child.configure(bg=top_bg, fg=config.PRIMARY_BLUE)
        
        # Modern typography and colors
        profile_fg = config.DARK_FG if is_dark else config.LIGHT_FG
        self.profile_label.configure(
            bg=prof_bg, 
            fg=profile_fg,
            font=(config.FONT_PRIMARY, 10, 'bold')
        )

        # Modern combobox styling - FIXED contrast
        fg = config.DARK_FG if is_dark else config.LIGHT_FG
        # Use darker background so white text is visible
        combo_bg = config.DARK_ENTRY_BG if is_dark else config.LIGHT_ENTRY_BG
        
        style = self.tb_style
        style.configure("TCombobox", 
                       fieldbackground=combo_bg,  # Darker background for contrast
                       foreground=fg,
                       borderwidth=1,
                       relief='flat',
                       font=(config.FONT_PRIMARY, 9),
                       selectbackground=config.PRIMARY_BLUE,
                       selectforeground="white")
        style.map("TCombobox",
            fieldbackground=[('readonly', combo_bg)],
            foreground=[('readonly', fg)],
            bordercolor=[('focus', config.PRIMARY_BLUE)],
            selectbackground=[('readonly', config.PRIMARY_BLUE)])

    def force_theme_refresh(self):
        force_theme_refresh(self)
    
    def _force_startup_theme_refresh(self):
        """Force TTK theme refresh after startup to fix checkbox styling issues"""
        is_dark = self.cfg['settings'].get('dark_mode', False)
        
        # Apply global TTK theming again
        from modern_theme import apply_global_ttk_theme
        apply_global_ttk_theme(self, is_dark)
        
        # Force update all widgets
        self.update_idletasks()
        
        print(f"[STARTUP] Forced TTK theme refresh for dark_mode={is_dark}")

    # ─── Help popup ────────────────────────
    def show_help(self):
        help_window = tk.Toplevel(self)
        help_window.title("SlyWriter Help")
        help_window.geometry("500x400")
        help_window.transient(self)
        help_window.grab_set()
        
        # Apply modern theme colors
        dark = self.cfg['settings'].get('dark_mode', False)
        bg_color = config.DARK_BG if dark else config.LIGHT_BG
        fg_color = config.DARK_FG if dark else config.LIGHT_FG
        help_window.configure(bg=bg_color)
        
        # Title
        title = tk.Label(help_window, 
                        text="🤖 SlyWriter - AI-Powered Typing Assistant",
                        font=(config.FONT_PRIMARY, 16, 'bold'),
                        bg=bg_color, fg=config.PRIMARY_BLUE)
        title.pack(pady=20)
        
        # Help content
        help_text = """
✨ Getting Started:

1. 📝 Sign in with your account in the Account tab
2. ⚙️  Configure typing settings and profiles  
3. 📄 Paste or load text in the Typing tab
4. 🚀 Press Start to begin AI-powered typing
5. ⏸️  Use Pause/Stop or global hotkeys for control

👑 Premium Features:
• Advanced AI anti-detection
• Realistic fake edits and pauses
• AI-generated filler text
• Enhanced human-like behavior

📊 Analytics:
• Track your usage patterns
• View detailed daily/weekly reports
• Export data for analysis

⌨️  Hotkeys:
• Configure global shortcuts in Hotkeys tab
• Control typing from anywhere
• Set custom key combinations

💡 Tips:
• Use Preview Mode to test without typing
• Adjust delays for natural speed
• Check Analytics for insights
        """
        
        content = tk.Label(help_window,
                          text=help_text,
                          font=(config.FONT_PRIMARY, 10),
                          bg=bg_color, fg=fg_color,
                          justify='left',
                          anchor='nw')
        content.pack(pady=10, padx=20, fill='both', expand=True)
        
        # Close button
        close_btn = tk.Button(help_window,
                             text="Got it!",
                             command=help_window.destroy,
                             bg=config.PRIMARY_BLUE,
                             fg="white",
                             font=(config.FONT_PRIMARY, 10, 'bold'),
                             relief="flat",
                             padx=20, pady=8,
                             cursor='hand2')
        close_btn.pack(pady=20)
