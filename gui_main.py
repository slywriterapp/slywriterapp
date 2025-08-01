import os
import sys
import json
import config
import typing_engine as engine
import clipboard
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import keyboard  # for global hotkeys
import csv
from datetime import datetime
from utils import Tooltip
import time
import threading

# ✅ NEW: Auth imports
from auth import get_saved_user, sign_out

# ── Ensure imports load from this directory ──
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

# ───────── Profile presets ───────────────────────
PROFILE_PRESETS = {
    "Default":    {"min_delay": config.MIN_DELAY_DEFAULT, "max_delay": config.MAX_DELAY_DEFAULT, "typos_on": True,  "pause_freq": config.LONG_PAUSE_DEFAULT},
    "Ultra-Slow": {"min_delay": 0.15, "max_delay": 0.4,                  "typos_on": True,  "pause_freq": 30},
    "Speed Type": {"min_delay": 0.01, "max_delay": 0.05,                 "typos_on": False, "pause_freq": 1000}
}

class TypingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.user = None                      # track whether someone is logged in
        self.withdraw()                       # hide main window until splash finishes
        self.after(10, self.splash_screen)    # schedule splash

    # ── Splash screen with animation ───────────────────────────
    def splash_screen(self):
        splash = tk.Toplevel()
        splash.overrideredirect(True)
        splash.geometry("400x200+500+300")
        splash.configure(bg="#33475b")

        label = tk.Label(splash, text="", fg="white", bg="#33475b", font=("Courier", 24))
        label.pack(expand=True)

        text = "GhostWriter"
        delay = 100  # ms per character

        def type_text():
            for ch in text:
                label.config(text=label.cget("text") + ch)
                splash.update()
                time.sleep(delay / 1000)
            time.sleep(1.5)
            splash.destroy()
            self.after(10, self._post_splash_setup)  # ✅ call setup on main thread

        threading.Thread(target=type_text, daemon=True).start()

    def _post_splash_setup(self):
        self.load_config()
        self.setup_ui()
        self.deiconify()

        # ✅ Auto-login if token is still valid
        saved_user = get_saved_user()
        if saved_user:
            self.user = saved_user
            self.on_login(saved_user)
            self.account_tab.update_for_login(saved_user)


    def load_config(self):
        if os.path.exists(config.CONFIG_FILE):
            with open(config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.cfg = json.load(f)
        else:
            self.cfg = config.DEFAULT_CONFIG.copy()
        self.profiles = self.cfg.get('profiles', [])

    def save_config(self):
        with open(config.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.cfg, f, indent=2)

    # ── Main UI setup ────────────────────────────────
    def setup_ui(self):
        self.title("GhostWriter")
        self.geometry("720x680")
        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        # slider style
        self.style.configure(
            "Black.Horizontal.TScale",
            troughcolor="#888",
            sliderthickness=12
        )
        self.style.layout(
            "Black.Horizontal.TScale",
            [("Horizontal.Scale.trough", {
                "children": [("Horizontal.Scale.thumb", {"side": "left", "sticky": ""})],
                "sticky": "we"
            })]
        )

        # ─── Top bar ───────────────────────────────────────
        top = ttk.Frame(self); top.pack(fill='x', padx=10, pady=5)
        prof_frame = ttk.Frame(top); prof_frame.pack(side='right')
        ttk.Label(prof_frame, text="Profile:").pack(side='left')
        self.active_profile = tk.StringVar(value=self.cfg.get('active_profile','Default'))
        self.prof_box = ttk.Combobox(
            prof_frame,
            values=self.profiles,
            textvariable=self.active_profile,
            state='readonly', width=15
        )
        self.prof_box.pack(side='left')
        Tooltip(self.prof_box, "Select typing profile")
        self.prof_box.bind("<<ComboboxSelected>>", self.on_profile_change)

        for txt, cmd, tip in [
            ('+', self.add_profile,    "Add profile"),
            ('–', self.delete_profile, "Delete profile"),
            ('💾', self.save_profile,  "Save profile")
        ]:
            b = ttk.Button(prof_frame, text=txt, width=2, command=cmd)
            b.pack(side='left', padx=2)
            Tooltip(b, tip)

        help_btn = ttk.Button(top, text='?', width=2, command=self.show_help)
        help_btn.pack(side='right')
        Tooltip(help_btn, "Show usage guide")

        self.dark_var = tk.BooleanVar(value=self.cfg['settings'].get('dark_mode', False))
        dark_chk = ttk.Checkbutton(
            top, text="Dark Mode", variable=self.dark_var,
            command=lambda: self.toggle_dark(self.dark_var.get())
        )
        dark_chk.pack(side='left', padx=5)
        Tooltip(dark_chk, "Toggle dark mode")

        # ─── Notebook & tabs ───────────────────────────────
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        self.tabs = {}

        # ─── Account tab ───────────────────────────────
        acct_frame = ttk.Frame(self.notebook)
        self.notebook.add(acct_frame, text='Account')
        self.tabs['Account'] = acct_frame

        from tab_account import AccountTab
        import typing_engine

        self.account_tab = AccountTab(acct_frame, self)
        self.account_tab.pack(fill='both', expand=True)

        typing_engine.set_account_tab_reference(self.account_tab)
        print("✅ AccountTab reference passed to typing_engine")

        # ─── Other tabs (disabled until login) ─────────────
        for name in ['Typing','Hotkeys','Diagnostics','Scheduler']:
            f = ttk.Frame(self.notebook)
            self.notebook.add(f, text=name)
            self.tabs[name] = f

        # ─── Import & instantiate your existing tabs ───────
        from tab_typing   import TypingTab
        from tab_hotkeys  import HotkeysTab
        from tab_stats    import StatsTab
        from tab_schedule import ScheduleTab

        self.typing_tab  = TypingTab(  self.tabs['Typing'],    self)
        self.hotkeys_tab = HotkeysTab(self.tabs['Hotkeys'],   self)
        self.typing_tab.pack( fill='both', expand=True )
        self.hotkeys_tab.pack(fill='both', expand=True )
        StatsTab(   self.tabs['Diagnostics'], self).pack(fill='both', expand=True)
        ScheduleTab(self.tabs['Scheduler'],   self).pack(fill='both', expand=True)

        # ✅ Lock all but Account on startup
        for name, frame in self.tabs.items():
            if name != 'Account':
                self.notebook.tab(frame, state='disabled')

        self.register_hotkeys()
        self.apply_theme()

    # ── ✅ Unlock after login ───────────────────────────────
    def on_login(self, user_info):
        self.user = user_info
        for name, frame in self.tabs.items():
            if name != 'Account':
                self.notebook.tab(frame, state='normal')
        self.notebook.select(self.tabs['Typing'])

    # ── ✅ Re-lock on logout ───────────────────────────────
    def on_logout(self):
        self.user = None
        for name, frame in self.tabs.items():
            if name != 'Account':
                self.notebook.tab(frame, state='disabled')
        self.notebook.select(self.tabs['Account'])

    # ── Hotkey management ───────────────────────────────
    def set_start_hotkey(self, hk: str):
        self._validate_and_set_hotkey(hk, 'start')

    def set_stop_hotkey(self, hk: str):
        self._validate_and_set_hotkey(hk, 'stop')

    def set_pause_hotkey(self, hk: str):
        self._validate_and_set_hotkey(hk, 'pause')

    def _validate_and_set_hotkey(self, hk: str, key_name: str):
        try:
            keyboard.parse_hotkey(hk)
            self.cfg['settings']['hotkeys'][key_name] = hk
            self.register_hotkeys()
            self.save_config()
        except ValueError:
            messagebox.showwarning("Invalid Hotkey", f"The hotkey '{hk}' is not valid.")

    def register_hotkeys(self):
        for name in ['start','stop','pause']:
            try:
                keyboard.remove_hotkey(self.cfg['settings']['hotkeys'].get(name,''))
            except:
                pass
        start = self.cfg['settings']['hotkeys']['start']
        stop  = self.cfg['settings']['hotkeys']['stop']
        pause = self.cfg['settings']['hotkeys'].get('pause','ctrl+alt+p')

        keyboard.add_hotkey(
            start,
            lambda: None if getattr(self.hotkeys_tab.start_rec, 'recording', False)
                        else self.typing_tab.start_typing()
        )
        keyboard.add_hotkey(
            stop,
            lambda: None if getattr(self.hotkeys_tab.stop_rec,  'recording', False)
                        else self.typing_tab.stop_typing_hotkey()
        )
        keyboard.add_hotkey(
            pause,
            lambda: None if getattr(self.hotkeys_tab.start_rec, 'recording', False)
                        else self.typing_tab.toggle_pause()
        )

    # ── Profiles & settings ─────────────────────────────
    def on_setting_change(self):
        s = self.cfg['settings']
        tt = self.typing_tab
        s['min_delay']    = tt.min_delay_var.get()
        s['max_delay']    = tt.max_delay_var.get()
        s['typos_on']     = tt.typos_var.get()
        s['pause_freq']   = tt.pause_freq_var.get()
        s['paste_go_url'] = tt.paste_go_var.get()
        s['autocap']      = tt.autocap_var.get()
        self.save_config()

    def on_profile_change(self, _=None):
        name = self.active_profile.get()
        if name in PROFILE_PRESETS:
            preset = PROFILE_PRESETS[name]
            self.cfg['settings'].update(preset)
            self.cfg['active_profile'] = name
            self.save_config()
            tt = self.typing_tab
            tt.min_delay_var.set(preset['min_delay'])
            tt.max_delay_var.set(preset['max_delay'])
            tt.typos_var.set(preset['typos_on'])
            tt.pause_freq_var.set(preset['pause_freq'])
            self.on_setting_change()
            tt.update_wpm()

    def reset_hotkeys(self):
        self.cfg['settings']['hotkeys'] = config.DEFAULT_CONFIG['settings']['hotkeys'].copy()
        default = self.cfg['settings']['hotkeys']
        self.hotkeys_tab.start_rec.current = default['start']
        self.hotkeys_tab.start_rec.label.config(text=f"Current hotkey: {default['start']}")
        self.hotkeys_tab.stop_rec.current  = default['stop']
        self.hotkeys_tab.stop_rec.label.config(text=f"Current hotkey: {default['stop']}")
        self.hotkeys_tab.pause_rec.current = default.get('pause','ctrl+alt+p')
        self.hotkeys_tab.pause_rec.label.config(text=f"Current hotkey: {default.get('pause','ctrl+alt+p')}")
        self.register_hotkeys()
        self.save_config()

    def reset_typing_settings(self):
        self.cfg['settings'].update({
            "min_delay":   config.MIN_DELAY_DEFAULT,
            "max_delay":   config.MAX_DELAY_DEFAULT,
            "typos_on":    True,
            "pause_freq":  config.LONG_PAUSE_DEFAULT,
            "paste_go_url":"",
            "autocap":     False
        })
        self.save_config()
        self.on_profile_change()

    def add_profile(self):
        name = simpledialog.askstring('New Profile','Enter profile name:')
        if not name or name in self.profiles: return
        self.profiles.append(name)
        self.prof_box['values'] = self.profiles
        self.active_profile.set(name)
        self.cfg['profiles'] = self.profiles
        self.save_config()

    def delete_profile(self):
        name = self.active_profile.get()
        if name in PROFILE_PRESETS: return
        if messagebox.askyesno('Delete Profile', f"Remove '{name}'?"):
            self.profiles.remove(name)
            self.prof_box['values'] = self.profiles
            self.active_profile.set('Default')
            self.cfg['profiles'] = self.profiles
            self.save_config()

    def save_profile(self):
        self.save_config()

    def toggle_dark(self, is_dark):
        self.cfg['settings']['dark_mode'] = is_dark
        self.apply_theme()
        self.save_config()

    def apply_theme(self):
        dark = self.cfg['settings'].get('dark_mode', False)
        bg, fg = (config.DARK_BG, config.DARK_FG) if dark else (config.LIGHT_BG, config.LIGHT_FG)
        e_bg, e_fg = (config.DARK_ENTRY_BG, config.DARK_FG) if dark else ("white","black")
        entry_fg   = "black" if dark else e_fg
        accent     = "#4a90e2" if dark else "#0078d7"

        self.configure(bg=bg)
        self.style.configure('.', background=bg, foreground=fg)

        tt = self.typing_tab
        tt.text_input.configure(background=e_bg, foreground=fg, insertbackground=fg)
        tt.live_preview .configure(background=e_bg, foreground=fg)
        tt.status_label .configure(foreground=fg)

        self.prof_box.configure(background=e_bg, foreground=entry_fg)
        if dark:
            self.style.configure('TEntry',    foreground='black')
            self.style.configure('TCombobox', foreground='black')
        else:
            self.style.configure('TEntry',    foreground=e_fg)
            self.style.configure('TCombobox', foreground=e_fg)

        tt.start_btn .configure(bg=accent,     activebackground=accent)
        tt.stop_btn  .configure(bg="red",       activebackground="red")
        tt.pause_btn .configure(bg="orange",    activebackground="orange")

    def show_help(self):
        messagebox.showinfo(
            'Help',
            "1. Paste or load text in the Typing tab.\n"
            "2. Configure settings and profiles.\n"
            "3. Press Start, Pause or Stop (or use hotkeys).\n"
            "4. Export logs or schedule tasks."
        )

if __name__ == '__main__':
    app = TypingApp()
    app.mainloop()
