import tkinter as tk
from config import LIME_GREEN
from typing_ui import build_typing_ui
from typing_theme import (
    apply_typing_theme,
    update_placeholder_color,
    get_entry_fg,
    get_placeholder_fg
)
import typing_logic

PLACEHOLDER_INPUT = "Type here..."
PLACEHOLDER_PREVIEW = "Preview will appear here..."

class TypingTab(tk.Frame):
    PLACEHOLDER_INPUT = PLACEHOLDER_INPUT
    PLACEHOLDER_PREVIEW = PLACEHOLDER_PREVIEW

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.paused = False
        self.widgets_to_style = []
        self.text_widgets = []
        # --- CONTROL VARIABLES ---
        self.min_delay_var   = tk.DoubleVar()
        self.max_delay_var   = tk.DoubleVar()
        self.pause_freq_var  = tk.IntVar()
        self.typos_var       = tk.BooleanVar()
        self.paste_go_var    = tk.StringVar()
        self.autocap_var     = tk.BooleanVar()
        self.adv_antidetect_var = tk.BooleanVar()  # Premium advanced anti-detection

        # -- Prevent trace recursion --
        self.loading_profile = False

        # This will set up self.sf as the settings area (LabelFrame)
        build_typing_ui(self)
        # Add the premium setting to the bottom of the settings area (self.sf)
        self._add_premium_setting(self.sf)

        # --- Set up traces ONLY ONCE! ---
        self.min_delay_var.trace_add('write',   lambda *a: self._maybe_setting_changed())
        self.max_delay_var.trace_add('write',   lambda *a: self._maybe_setting_changed())
        self.pause_freq_var.trace_add('write',  lambda *a: self._maybe_setting_changed())
        self.typos_var.trace_add('write',       lambda *a: self._maybe_setting_changed())
        self.paste_go_var.trace_add('write',    lambda *a: self._maybe_setting_changed())
        self.autocap_var.trace_add('write',     lambda *a: self._maybe_setting_changed())
        self.adv_antidetect_var.trace_add('write', lambda *a: self._maybe_setting_changed())

        self.update_from_config()

    def _add_premium_setting(self, parent_frame):
        # Use grid to match the rest of your settings
        row = parent_frame.grid_size()[1]  # next available row in grid

        # Premium label (small, with crown)
        premium_label = tk.Label(
            parent_frame,
            text="👑 Premium",
            fg="#d4af37",
            font=('Segoe UI', 10, 'bold'),
            anchor='w', justify='left'
        )
        premium_label.grid(row=row, column=0, sticky='w', pady=(14, 0), padx=(0, 6))

        # Determine user premium state
        is_premium = self.app.account_tab.is_premium() if hasattr(self.app, 'account_tab') else False

        # Premium anti-detection toggle
        self.adv_antidetect_check = tk.Checkbutton(
            parent_frame,
            text="Enable AI-based Advanced Anti-Detection\n(AI fake edits, AI filler, variable human pauses)",
            variable=self.adv_antidetect_var,
            state="normal" if is_premium else "disabled",
            fg="#222" if is_premium else "#888",
            anchor='w', justify='left',
            wraplength=350
        )
        self.adv_antidetect_check.grid(row=row, column=1, sticky='w', pady=(14, 0), padx=(0, 0))

        # Description or lock message beneath (full width)
        row += 1
        if not is_premium:
            locked_msg = tk.Label(
                parent_frame,
                text="Upgrade to SlyWriter Premium to unlock AI-based undetectability.",
                fg="#bb9200",
                font=('Segoe UI', 9, 'italic'),
                anchor='w', justify='left'
            )
            locked_msg.grid(row=row, column=0, columnspan=2, sticky='w', padx=(40, 0), pady=(0, 8))
        else:
            desc_msg = tk.Label(
                parent_frame,
                text="(AI-generated edits, filler, and advanced pauses to defeat all replay/AI detection.)",
                fg=LIME_GREEN,
                font=('Segoe UI', 9),
                anchor='w', justify='left'
            )
            desc_msg.grid(row=row, column=0, columnspan=2, sticky='w', padx=(40, 0), pady=(0, 8))

    def _maybe_setting_changed(self):
        if getattr(self, "loading_profile", False):
            return
        self.app.on_setting_change()
        self.update_wpm()

    def update_from_config(self):
        s = self.app.cfg['settings']
        self.loading_profile = True
        self.min_delay_var.set(s['min_delay'])
        self.max_delay_var.set(s['max_delay'])
        self.pause_freq_var.set(s['pause_freq'])
        self.typos_var.set(s['typos_on'])
        self.paste_go_var.set(s.get('paste_go_url', ''))
        self.autocap_var.set(s.get('autocap', False))
        self.adv_antidetect_var.set(s.get('adv_antidetect', False))
        self.min_delay_scale.set(s['min_delay'])
        self.max_delay_scale.set(s['max_delay'])
        self.pause_freq_scale.set(s['pause_freq'])
        self.loading_profile = False
        self.update_wpm()
        self.update_placeholder_color()

    def toggle_pause(self):
        typing_logic.toggle_pause(self)

    def _clear_input_placeholder(self, event):
        typing_logic.clear_input_placeholder(self, event)

    def _restore_input_placeholder(self, event):
        typing_logic.restore_input_placeholder(self, event)

    def update_placeholder_color(self):
        update_placeholder_color(self, self.app.cfg['settings'].get('dark_mode', False))

    def _get_entry_fg(self):
        return get_entry_fg(self, self.app.cfg['settings'].get('dark_mode', False))

    def _get_placeholder_fg(self):
        return get_placeholder_fg(self, self.app.cfg['settings'].get('dark_mode', False))

    def update_wpm(self):
        typing_logic.update_wpm(self)

    def load_file(self):
        typing_logic.load_file(self)

    def paste_clipboard(self):
        typing_logic.paste_clipboard(self)

    def start_typing(self):
        typing_logic.start_typing(self, use_adv_antidetect=self.adv_antidetect_var.get())

    def stop_typing_hotkey(self):
        typing_logic.stop_typing_hotkey(self)

    def update_live_preview(self, text):
        typing_logic.update_live_preview(self, text)

    def update_status(self, text):
        typing_logic.update_status(self, text)

    def set_theme(self, dark):
        apply_typing_theme(self, dark)
