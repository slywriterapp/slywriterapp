import time
import tkinter as tk
from tkinter import messagebox
from config import LIME_GREEN
from typing_ui import build_typing_ui
from typing_theme import (
    apply_typing_theme,
    update_placeholder_color,
    get_entry_fg,
    get_placeholder_fg
)
import typing_logic
import typing_engine
import clipboard
import unicodedata

PLACEHOLDER_INPUT = "Type here..."
PLACEHOLDER_PREVIEW = "Preview will appear here..."

class TypingTab(tk.Frame):
    PLACEHOLDER_INPUT = PLACEHOLDER_INPUT
    PLACEHOLDER_PREVIEW = PLACEHOLDER_PREVIEW

    def __init__(self, parent, app):
        super().__init__(parent)
        print("[TypingTab] __init__ called")
        self.app = app
        self.paused = False
        self._typing_interrupted = False
        self._last_preview_text = ""

        # --- CONTROL VARIABLES ---
        self.min_delay_var      = tk.DoubleVar()
        self.max_delay_var      = tk.DoubleVar()
        self.pause_freq_var     = tk.IntVar()
        self.typos_var          = tk.BooleanVar()
        self.paste_go_var       = tk.StringVar()
        self.autocap_var        = tk.BooleanVar()
        self.preview_only_var   = tk.BooleanVar()
        self.adv_antidetect_var = tk.BooleanVar()

        self.loading_profile = False

        # For throttling preview updates
        self._last_preview_update_time = 0
        self._preview_throttle_interval = 0.1  # 100 ms minimum between updates

        # Build UI once
        build_typing_ui(self)
        self._add_preview_only_checkbox(self.sf)
        self._add_premium_setting(self.sf)

        # Setup variable traces only once
        for var in [
            self.min_delay_var, self.max_delay_var,
            self.pause_freq_var, self.typos_var,
            self.paste_go_var, self.autocap_var,
            self.preview_only_var,
            self.adv_antidetect_var
        ]:
            var.trace_add('write', lambda *a: self._maybe_setting_changed())

        self.update_from_config()

    def _add_preview_only_checkbox(self, parent_frame):
        row = parent_frame.grid_size()[1]
        self.preview_only_check = tk.Checkbutton(
            parent_frame,
            text="Preview Only Mode (No actual typing, only preview)",
            variable=self.preview_only_var,
            anchor='w', justify='left',
            fg="#222",
            wraplength=350
        )
        self.preview_only_check.grid(row=row, column=0, columnspan=2, sticky='w', pady=(10, 8))

    def _get_premium_status(self):
        usage_mgr = getattr(getattr(self.app, 'account_tab', None), 'usage_mgr', None)
        plan = usage_mgr.get_user_plan() if usage_mgr else "free"
        return plan, plan in ("pro", "enterprise")

    def _add_premium_setting(self, parent_frame):
        row = parent_frame.grid_size()[1]

        tk.Label(
            parent_frame, text="👑 Premium",
            fg="#d4af37", font=('Segoe UI', 10, 'bold'),
            anchor='w', justify='left'
        ).grid(row=row, column=0, sticky='w', pady=(14, 0), padx=(0, 6))

        plan, is_premium = self._get_premium_status()

        self.adv_antidetect_check = tk.Checkbutton(
            parent_frame,
            text="Enable AI-based Advanced Anti-Detection\n(AI fake edits, AI filler, variable human pauses)",
            variable=self.adv_antidetect_var,
            state="normal" if is_premium else "disabled",
            fg="#222" if is_premium else "#888",
            anchor='w', justify='left', wraplength=350
        )
        self.adv_antidetect_check.grid(row=row, column=1, sticky='w', pady=(14, 0))

        row += 1
        if is_premium:
            self.premium_message = tk.Label(
                parent_frame,
                text="(AI-generated edits, filler, and advanced pauses to defeat all replay/AI detection.)",
                fg=LIME_GREEN,
                font=('Segoe UI', 9),
                anchor='w', justify='left'
            )
        else:
            self.premium_message = tk.Label(
                parent_frame,
                text="Upgrade to SlyWriter Premium to unlock AI-based undetectability.",
                fg="#bb9200",
                font=('Segoe UI', 9, 'italic'),
                anchor='w', justify='left'
            )
        self.premium_message.grid(row=row, column=0, columnspan=2, sticky='w', padx=(40, 0), pady=(0, 8))

    def _maybe_setting_changed(self):
        if self.loading_profile:
            return
        print("[TypingTab] Settings changed")
        self.app.on_setting_change()
        self.update_wpm()

    def update_from_config(self):
        print("[TypingTab] update_from_config called")
        s = self.app.cfg['settings']
        self.loading_profile = True

        self.min_delay_var.set(s['min_delay'])
        self.max_delay_var.set(s['max_delay'])
        self.pause_freq_var.set(s['pause_freq'])
        self.typos_var.set(s['typos_on'])
        self.paste_go_var.set(s.get('paste_go_url', ''))
        self.autocap_var.set(s.get('autocap', False))
        self.preview_only_var.set(s.get('preview_only', False))
        self.adv_antidetect_var.set(s.get('adv_antidetect', False))

        self.min_delay_scale.set(s['min_delay'])
        self.max_delay_scale.set(s['max_delay'])
        self.pause_freq_scale.set(s['pause_freq'])

        self.loading_profile = False

        self.update_wpm()
        self.update_placeholder_color()

        plan, is_premium = self._get_premium_status()
        self.adv_antidetect_check.config(
            state="normal" if is_premium else "disabled",
            fg="#222" if is_premium else "#888"
        )
        if self.premium_message is not None:
            if is_premium:
                self.premium_message.config(
                    text="(AI-generated edits, filler, and advanced pauses to defeat all replay/AI detection.)",
                    fg=LIME_GREEN, font=('Segoe UI', 9, 'normal')
                )
            else:
                self.premium_message.config(
                    text="Upgrade to SlyWriter Premium to unlock AI-based undetectability.",
                    fg="#bb9200", font=('Segoe UI', 9, 'italic')
                )

    def stop_typing_hotkey(self):
        print("[TypingTab] Stopping typing (via hotkey or button)")
        typing_engine.stop_typing_func()
        self.paused = False
        self.pause_btn.config(text='Pause Typing')
        self._typing_interrupted = True
        self.update_status('Typing stopped!')
        self._set_text_input_state('normal')
        self._show_stopped_in_preview()
        self.start_btn.config(bg='#0078d7')
        self.stop_btn.config(bg='red')

    def toggle_pause(self):
        print("[TypingTab] Toggling pause")
        if typing_engine.pause_flag.is_set():
            typing_engine.resume_typing()
        else:
            typing_engine.pause_typing()

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

    def _clean_typing_text(self, text):
        replacements = {
            '’': "'",
            '‘': "'",
            '“': '"',
            '”': '"',
            '—': '-',
            '\u200b': '',
            '\u2013': '-',
        }
        for orig, repl in replacements.items():
            text = text.replace(orig, repl)
        text = unicodedata.normalize('NFKC', text)
        return text

    def start_typing(self):
        print("[TypingTab] start_typing called")
        self._typing_interrupted = False

        self._set_text_input_state('disabled')

        original_status = self.update_status
        def wrapped_status(text):
            original_status(text)
            text_lower = text.lower()
            if text_lower in ('stopped', 'done'):
                self.after(0, lambda: self._set_text_input_state('normal'))

        use_premium = self.adv_antidetect_var.get() and self._get_premium_status()[1]

        raw_text = self.text_input.get('1.0', 'end').strip()
        if not raw_text or raw_text == self.PLACEHOLDER_INPUT:
            raw_text = clipboard.paste().strip()

        if not raw_text:
            return messagebox.showwarning('No Text', 'Enter text or have something on clipboard.')

        raw_text = self._clean_typing_text(raw_text)

        if use_premium:
            stop_flag = typing_engine.stop_flag
            pause_flag = typing_engine.pause_flag
            stop_flag.clear()
            pause_flag.clear()
            from premium_typing import premium_type_with_filler
            premium_type_with_filler(
                raw_text,
                live_preview_callback=self.update_live_preview,
                status_callback=wrapped_status,
                min_delay=self.min_delay_var.get(),
                max_delay=self.max_delay_var.get(),
                typos_on=self.typos_var.get(),
                pause_freq=self.pause_freq_var.get(),
                autocap_enabled=self.autocap_var.get(),
                stop_flag=stop_flag,
                pause_flag=pause_flag,
                preview_only=self.preview_only_var.get()
            )
        else:
            typing_logic.start_typing(
                self,
                use_adv_antidetect=False,
                parent_widget=self,
                status_callback=wrapped_status,
                preview_only=self.preview_only_var.get()
            )

        self.start_btn.config(bg='#0078d7')
        self.stop_btn.config(bg='red')

    def _should_autoscroll(self):
        """Return True if preview is already at bottom, otherwise False."""
        first, last = self.live_preview.yview()
        return abs(last - 1.0) < 0.01

    def update_live_preview(self, text):
        now = time.time()
        # Throttle updates for smoother UI
        if now - getattr(self, '_last_preview_update_time', 0) < self._preview_throttle_interval:
            return
        self._last_preview_update_time = now

        # Skip update if text hasn't changed
        if text == self._last_preview_text:
            return

        # Capture current scroll position before changing content
        autoscroll = self._should_autoscroll()
        
        # Store current scroll position for non-autoscroll users
        current_scroll_top = None
        current_scroll_bottom = None
        if not autoscroll:
            current_scroll_top = self.live_preview.yview()[0]
            current_scroll_bottom = self.live_preview.yview()[1]

        self.live_preview.configure(state='normal')
        try:
            # Use incremental updates instead of full replace when possible
            current_text = self.live_preview.get('1.0', 'end-1c')
            
            if not text.strip():
                if current_text != self.PLACEHOLDER_PREVIEW:
                    self.live_preview.delete('1.0', 'end')
                    self.live_preview.insert('1.0', self.PLACEHOLDER_PREVIEW)
                    self.live_preview.tag_add("placeholder", "1.0", "end")
                    self.live_preview.config(fg=self._get_placeholder_fg())
            else:
                # Check if we can do incremental update (text is longer and starts with current text)
                if (len(text) > len(current_text) and 
                    current_text and 
                    text.startswith(current_text) and
                    current_text != self.PLACEHOLDER_PREVIEW):
                    # Incremental update: just append new characters
                    new_chars = text[len(current_text):]
                    self.live_preview.insert('end', new_chars)
                    self.live_preview.config(fg=self._get_entry_fg())
                else:
                    # Full replace needed
                    self.live_preview.delete('1.0', 'end')
                    self.live_preview.insert('1.0', text)
                    self.live_preview.config(fg=self._get_entry_fg())
            
            # Handle scrolling
            if autoscroll:
                self.live_preview.see('end')
            elif current_scroll_top is not None:
                # Restore scroll position for users who were scrolling
                self.live_preview.yview_moveto(current_scroll_top)
                
        finally:
            self.live_preview.configure(state='disabled')
            self._last_preview_text = text

    def update_status(self, text):
        typing_logic.update_status(self, text)

    def _set_text_input_state(self, state):
        try:
            self.text_input.config(state=state)
        except Exception as e:
            print("[TypingTab] Failed to set text_input state:", e)

    def _show_stopped_in_preview(self):
        self.live_preview.configure(state='normal')
        self.live_preview.delete('1.0', 'end')
        self.live_preview.insert('1.0', "Stopped.")
        self.live_preview.tag_remove("placeholder", "1.0", "end")
        self.live_preview.config(fg=self._get_placeholder_fg())
        self.live_preview.see('end')
        self.live_preview.configure(state='disabled')

    def set_theme(self, dark):
        apply_typing_theme(self, dark)
