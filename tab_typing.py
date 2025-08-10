import tkinter as tk
from config import LIME_GREEN
from typing_ui import build_typing_ui
from modern_theme import apply_modern_theme, update_placeholder_color, get_entry_fg, get_placeholder_fg
import typing_logic
from utils import is_premium_user

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
        self.preview_only_var = tk.BooleanVar()  # Preview only mode
        self.adv_antidetect_var = tk.BooleanVar()  # Premium feature

        self.loading_profile = False

        build_typing_ui(self)
        self._add_preview_only_checkbox(self.sf)
        self._add_premium_setting(self.sf)

        # Set up traces once
        for var in [
            self.min_delay_var, self.max_delay_var,
            self.pause_freq_var, self.typos_var,
            self.preview_only_var, self.adv_antidetect_var
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
            wraplength=350
            # fg will be set dynamically by set_theme
        )
        self.preview_only_check.grid(row=row, column=0, columnspan=2, sticky='w', pady=(10, 8))

    def _get_premium_status(self):
        is_premium = is_premium_user(self.app)
        plan = "premium" if is_premium else "free"
        return plan, is_premium

    def _add_premium_setting(self, parent_frame):
        row = parent_frame.grid_size()[1]

        # Premium crown label
        tk.Label(
            parent_frame, text="👑 Premium",
            fg="#d4af37", font=('Segoe UI', 10, 'bold'),
            anchor='w', justify='left'
        ).grid(row=row, column=0, sticky='w', pady=(14, 0), padx=(0, 6))

        plan, is_premium = self._get_premium_status()

        # Get theme colors for proper visibility
        dark = self.app.cfg['settings'].get('dark_mode', False)
        bg_color = "#181816" if dark else "#ffffff"
        fg_color = ("#ffffff" if dark else "#222") if is_premium else "#888"
        # Use contrasting color for checkbox interior
        select_color = "#ffffff" if dark else "#f0f0f0"

        # Premium anti-detection toggle
        self.adv_antidetect_check = tk.Checkbutton(
            parent_frame,
            text="Enable AI-based Advanced Anti-Detection\n(AI fake edits, AI filler, variable human pauses)",
            variable=self.adv_antidetect_var,
            state="normal" if is_premium else "disabled",
            fg=fg_color,
            bg=bg_color,
            selectcolor=select_color,
            activebackground=bg_color,
            activeforeground=fg_color,
            anchor='w', justify='left', wraplength=350
        )
        self.adv_antidetect_check.grid(row=row, column=1, sticky='w', pady=(14, 0))

        # Show correct message below
        row += 1
        if is_premium:
            # Get theme colors for proper visibility - force explicit colors
            dark = self.app.cfg['settings'].get('dark_mode', False)
            bg_color = "#181816" if dark else "#ffffff"
            # Force bright green text that will show on both backgrounds
            text_color = "#00FF00" if dark else LIME_GREEN
            
            self.premium_desc_msg = tk.Label(
                parent_frame,
                text="(AI-generated edits, filler, and advanced pauses to defeat all replay/AI detection.)",
                fg=text_color,  # Use bright green in dark mode, lime green in light mode
                bg=bg_color,
                font=('Segoe UI', 9),
                anchor='w', justify='left'
            )
            self.premium_desc_msg.grid(row=row, column=0, columnspan=2, sticky='w', padx=(40, 0), pady=(0, 8))
        # Don't show upgrade message for premium users - feature leak prevention

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
        self.preview_only_var.set(s.get('preview_only', False))
        self.adv_antidetect_var.set(s.get('adv_antidetect', False))

        # Update scales (from build_typing_ui)
        self.min_delay_scale.set(s['min_delay'])
        self.max_delay_scale.set(s['max_delay'])
        self.pause_freq_scale.set(s['pause_freq'])

        self.loading_profile = False

        self.update_wpm()
        self.update_placeholder_color()

        # Recompute premium state and update toggle/message with proper theme colors
        plan, is_premium = self._get_premium_status()
        
        # Apply proper theme colors
        dark = self.app.cfg['settings'].get('dark_mode', False)
        bg_color = "#181816" if dark else "#ffffff"
        fg_color = ("#ffffff" if dark else "#222") if is_premium else "#888"
        select_color = "#ffffff" if dark else "#f0f0f0"
        
        self.adv_antidetect_check.config(
            state="normal" if is_premium else "disabled",
            fg=fg_color,
            bg=bg_color,
            selectcolor=select_color,
            activebackground=bg_color,
            activeforeground=fg_color
        )
        
        # Also update premium description text if it exists
        if hasattr(self, 'premium_desc_msg'):
            text_color = "#00FF00" if dark else LIME_GREEN
            self.premium_desc_msg.config(bg=bg_color, fg=text_color)
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
        return modern_get_entry_fg(self.app.cfg['settings'].get('dark_mode', False))

    def _get_placeholder_fg(self):
        return modern_get_placeholder_fg(self.app.cfg['settings'].get('dark_mode', False))

    def update_wpm(self):
        typing_logic.update_wpm(self)

    def load_file(self):
        typing_logic.load_file(self)

    def paste_clipboard(self):
        typing_logic.paste_clipboard(self)

    def clear_text_areas(self):
        """Clear both input and preview text areas"""
        # Clear input text area and restore placeholder
        self.text_input.delete('1.0', 'end')
        self.text_input.insert('1.0', self.PLACEHOLDER_INPUT)
        self.text_input.tag_add("placeholder", "1.0", "end")
        self.text_input.config(fg=self._get_placeholder_fg())
        
        # Clear preview text area and restore placeholder
        self.live_preview.configure(state='normal')
        self.live_preview.delete('1.0', 'end')
        self.live_preview.insert('1.0', self.PLACEHOLDER_PREVIEW)
        self.live_preview.tag_add("placeholder", "1.0", "end")
        self.live_preview.config(fg=self._get_placeholder_fg())
        self.live_preview.configure(state='disabled')

    def _handle_undo(self, event):
        """Handle Ctrl+Z undo with proper placeholder handling"""
        # Check if we currently have placeholder text
        current_content = self.text_input.get('1.0', 'end').strip()
        has_placeholder = (current_content == self.PLACEHOLDER_INPUT and 
                          "placeholder" in self.text_input.tag_names('1.0'))
        
        if has_placeholder:
            # If it's placeholder text, don't undo, just clear it
            self.text_input.delete('1.0', 'end')
            self.text_input.config(fg=self._get_entry_fg())
        else:
            # Perform normal undo
            try:
                self.text_input.edit_undo()
                # After undo, check if we need to restore placeholder
                content_after_undo = self.text_input.get('1.0', 'end').strip()
                if not content_after_undo:
                    self.text_input.insert('1.0', self.PLACEHOLDER_INPUT)
                    self.text_input.tag_add("placeholder", "1.0", "end")
                    self.text_input.config(fg=self._get_placeholder_fg())
            except tk.TclError:
                # No more undo operations available
                pass
        return "break"  # Prevent default undo behavior

    def _handle_redo(self, event):
        """Handle Ctrl+Y redo with proper placeholder handling"""
        try:
            self.text_input.edit_redo()
            # After redo, make sure we don't have placeholder styling on real text
            content = self.text_input.get('1.0', 'end').strip()
            if content and content != self.PLACEHOLDER_INPUT:
                self.text_input.tag_remove("placeholder", "1.0", "end")
                self.text_input.config(fg=self._get_entry_fg())
        except tk.TclError:
            # No more redo operations available
            pass
        return "break"  # Prevent default redo behavior

    def start_typing(self):
        # Lock profile selector during typing/countdown
        self.app.prof_box.configure(state='disabled')
        typing_logic.start_typing(self, use_adv_antidetect=self.adv_antidetect_var.get(), preview_only=self.preview_only_var.get())

    def stop_typing_hotkey(self):
        typing_logic.stop_typing_hotkey(self)
        # Unlock profile selector after stopping
        self.app.prof_box.configure(state='readonly')

    def update_live_preview(self, text):
        typing_logic.update_live_preview(self, text)

    def update_status(self, text):
        typing_logic.update_status(self, text)

    def set_theme(self, dark):
        apply_modern_theme(self, dark)
        
        # Update premium UI elements with modern colors
        import config
        bg_color = config.DARK_BG if dark else config.LIGHT_BG
        fg_color = config.DARK_FG if dark else config.LIGHT_FG
        
        if hasattr(self, 'premium_desc_msg'):
            text_color = config.SUCCESS_GREEN
            self.premium_desc_msg.config(bg=bg_color, fg=text_color)
        
        if hasattr(self, 'adv_antidetect_check'):
            # selectcolor should be background color, not blue always
            # The checkmark itself will be visible when checked
            checkbox_bg_color = bg_color
            self.adv_antidetect_check.config(
                bg=bg_color,
                fg=fg_color,
                selectcolor=checkbox_bg_color,  # Background color, not blue
                activebackground=bg_color,
                activeforeground=fg_color,
                font=(config.FONT_PRIMARY, 9)
            )
        
        # Style the preview only checkbox
        if hasattr(self, 'preview_only_check'):
            # selectcolor should be background color, not blue always
            # The checkmark itself will be visible when checked
            checkbox_bg_color = bg_color
            self.preview_only_check.config(
                bg=bg_color,
                fg=fg_color,
                selectcolor=checkbox_bg_color,  # Background color, not blue
                activebackground=bg_color,
                activeforeground=fg_color,
                font=(config.FONT_PRIMARY, 9)
            )
