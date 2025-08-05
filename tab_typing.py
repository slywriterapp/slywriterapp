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

        # --- CONTROL VARIABLES ---
        self.min_delay_var      = tk.DoubleVar()
        self.max_delay_var      = tk.DoubleVar()
        self.pause_freq_var     = tk.IntVar()
        self.typos_var          = tk.BooleanVar()
        self.paste_go_var       = tk.StringVar()
        self.autocap_var        = tk.BooleanVar()
        self.adv_antidetect_var = tk.BooleanVar()  # Premium feature

        self.loading_profile = False

        build_typing_ui(self)
        self._add_premium_setting(self.sf)

        # Set up traces once
        for var in [
            self.min_delay_var, self.max_delay_var,
            self.pause_freq_var, self.typos_var,
            self.paste_go_var, self.autocap_var,
            self.adv_antidetect_var
        ]:
            var.trace_add('write', lambda *a: self._maybe_setting_changed())

        self.update_from_config()

    def _get_premium_status(self):
        usage_mgr = getattr(getattr(self.app, 'account_tab', None), 'usage_mgr', None)
        plan = usage_mgr.get_user_plan() if usage_mgr else "free"
        return plan, plan in ("pro", "enterprise")

    def _add_premium_setting(self, parent_frame):
        row = parent_frame.grid_size()[1]

        # Premium crown label
        tk.Label(
            parent_frame, text="👑 Premium",
            fg="#d4af37", font=('Segoe UI', 10, 'bold'),
            anchor='w', justify='left'
        ).grid(row=row, column=0, sticky='w', pady=(14, 0), padx=(0, 6))

        plan, is_premium = self._get_premium_status()

        # Premium anti-detection toggle
        self.adv_antidetect_check = tk.Checkbutton(
            parent_frame,
            text="Enable AI-based Advanced Anti-Detection\n(AI fake edits, AI filler, variable human pauses)",
            variable=self.adv_antidetect_var,
            state="normal" if is_premium else "disabled",
            fg="#222" if is_premium else "#888",
            anchor='w', justify='left', wraplength=350
        )
        self.adv_antidetect_check.grid(row=row, column=1, sticky='w', pady=(14, 0))

        # Show correct message below
        row += 1
        if is_premium:
            desc_msg = tk.Label(
                parent_frame,
                text="(AI-generated edits, filler, and advanced pauses to defeat all replay/AI detection.)",
                fg=LIME_GREEN,
                font=('Segoe UI', 9),
                anchor='w', justify='left'
            )
            desc_msg.grid(row=row, column=0, columnspan=2, sticky='w', padx=(40, 0), pady=(0, 8))
        else:
            locked_msg = tk.Label(
                parent_frame,
                text="Upgrade to SlyWriter Premium to unlock AI-based undetectability.",
                fg="#bb9200",
                font=('Segoe UI', 9, 'italic'),
                anchor='w', justify='left'
            )
            locked_msg.grid(row=row, column=0, columnspan=2, sticky='w', padx=(40, 0), pady=(0, 8))

    def _maybe_setting_changed(self):
        if self.loading_profile:
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

        # Update scales (from build_typing_ui)
        self.min_delay_scale.set(s['min_delay'])
        self.max_delay_scale.set(s['max_delay'])
        self.pause_freq_scale.set(s['pause_freq'])

        self.loading_profile = False

        self.update_wpm()
        self.update_placeholder_color()

        # Recompute premium state and update toggle/message
        plan, is_premium = self._get_premium_status()
        self.adv_antidetect_check.config(
            state="normal" if is_premium else "disabled",
            fg="#222" if is_premium else "#888"
        )
        # Remove/add messages as needed (if dynamic, would need to recreate below-label, or just refresh UI)

    def toggle_pause(self):
        typing_logic.toggle_pause(self)

    def _clear_input_placeholder(self, event):
        typing_logic.clear_input_placeholder(self, event)

    def _restore_input_placeholder(self, event):
        typing_logic.restore_input_placeholder(self, event)

    def update_placeholder_color(self):
        update_placeholder_color(self, self.app.cfg['settings'].get('dark_mode', False))

    def _get_entry_fg(self):
        return get_entry_fg(self.app.cfg['settings'].get('dark_mode', False))

    def _get_placeholder_fg(self):
        return get_placeholder_fg(self.app.cfg['settings'].get('dark_mode', False))

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
