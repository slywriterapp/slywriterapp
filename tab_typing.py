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
        self.paused = False
        
        # FIRST: Create safe app accessor immediately - before anything else uses it
        def make_safe_app_accessor():
            captured_app = app
            def get_safe_app():
                return captured_app
            return get_safe_app
        
        self._get_safe_app = make_safe_app_accessor()
        
        # Store app reference for backward compatibility
        self.app = app

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

        # Create closure-based callback that permanently captures app reference
        def make_setting_change_callback():
            # Capture app reference in closure - this can't be overridden by tkinter
            captured_app = app
            def setting_changed():
                if self.loading_profile:
                    return
                # Use captured reference instead of any attribute
                captured_app.on_setting_change()
                self.update_wpm()
            return setting_changed
        
        self._maybe_setting_changed = make_setting_change_callback()
        
        # Create closure-based config updater
        def make_config_updater():
            captured_app = app
            def update_from_config():
                s = captured_app.cfg['settings']
                self.loading_profile = True

                self.min_delay_var.set(s['min_delay'])
                self.max_delay_var.set(s['max_delay'])
                self.pause_freq_var.set(s['pause_freq'])
                self.typos_var.set(s['typos_on'])
                
                # Premium features
                self.preview_only_var.set(s.get('preview_only', False))
                self.adv_antidetect_var.set(s.get('adv_antidetect', False))

                # Update scales if they exist (from build_typing_ui)
                if hasattr(self, 'min_delay_scale'):
                    self.min_delay_scale.set(s['min_delay'])
                if hasattr(self, 'max_delay_scale'):
                    self.max_delay_scale.set(s['max_delay'])
                if hasattr(self, 'pause_freq_scale'):
                    self.pause_freq_scale.set(s['pause_freq'])

                self.loading_profile = False
                self.update_wpm()
                self.update_placeholder_color()
            return update_from_config
        
        self.update_from_config = make_config_updater()

        # Note: _get_safe_app was created at the beginning of constructor
        
        for var in [
            self.min_delay_var, self.max_delay_var,
            self.pause_freq_var, self.typos_var,
            self.preview_only_var, self.adv_antidetect_var
        ]:
            var.trace_add('write', lambda *args: self._maybe_setting_changed())

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

        # Premium crown label (clickable if not premium)
        plan, is_premium = self._get_premium_status()

        if is_premium:
            # Just a label for premium users
            tk.Label(
                parent_frame, text="👑 Premium",
                fg="#d4af37", font=('Segoe UI', 10, 'bold'),
                anchor='w', justify='left'
            ).grid(row=row, column=0, sticky='w', pady=(14, 0), padx=(0, 6))
        else:
            # Clickable label for non-premium users
            import webbrowser
            premium_label = tk.Label(
                parent_frame, text="👑 Upgrade",
                fg="#8b5cf6", font=('Segoe UI', 10, 'bold', 'underline'),
                anchor='w', justify='left',
                cursor="hand2"
            )
            premium_label.grid(row=row, column=0, sticky='w', pady=(14, 0), padx=(0, 6))
            premium_label.bind("<Button-1>", lambda e: webbrowser.open("https://www.slywriter.ai/pricing"))

        # Get theme colors for proper visibility
        dark = self._get_safe_app().cfg['settings'].get('dark_mode', False)
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
            dark = self._get_safe_app().cfg['settings'].get('dark_mode', False)
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

    def update_wpm(self):
        """Update WPM display based on current settings"""
        try:
            min_delay = self.min_delay_var.get()
            max_delay = self.max_delay_var.get()
            if min_delay > 0 and max_delay > 0:
                avg_delay = (min_delay + max_delay) / 2
                wpm = int(60 / (avg_delay * 5))  # Approximate WPM calculation
                if hasattr(self, 'wpm_label'):
                    self.wpm_label.config(text=f"Estimated WPM: {wpm}")
        except (tk.TclError, ZeroDivisionError):
            if hasattr(self, 'wpm_label'):
                self.wpm_label.config(text="Estimated WPM: --")

    def update_placeholder_color(self):
        """Update placeholder colors for theme changes"""
        try:
            update_placeholder_color(self, self._get_safe_app().cfg['settings'].get('dark_mode', False))
        except:
            pass  # Ignore errors during theme switching

    def _get_premium_status(self):
        """Get current premium status"""
        try:
            from utils import is_premium_user, get_user_plan
            is_premium = is_premium_user(self.app)
            plan = get_user_plan(self.app)
            return plan, is_premium
        except:
            return 'free', False

    def _refresh_premium_ui(self):
        """Refresh the premium-related UI elements"""
        # Recompute premium state and update toggle/message with proper theme colors
        plan, is_premium = self._get_premium_status()
        
        # Apply proper theme colors
        dark = self._get_safe_app().cfg['settings'].get('dark_mode', False)
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
    
    def pause_typing(self):
        """Pause the current typing operation"""
        typing_logic.pause_typing(self)
        
    def stop_typing(self):
        """Stop the current typing operation"""  
        typing_logic.stop_typing(self)
        # Unlock profile selector after stopping
        if hasattr(self._get_safe_app(), 'prof_box'):
            self._get_safe_app().prof_box.configure(state='readonly')

    def start_typing(self):
        """Start the typing automation"""
        # Lock profile selector during typing/countdown
        if hasattr(self._get_safe_app(), 'prof_box'):
            self._get_safe_app().prof_box.configure(state='disabled')
        typing_logic.start_typing(self, use_adv_antidetect=self.adv_antidetect_var.get(), preview_only=self.preview_only_var.get())
        
    def find_wpm(self):
        """Calculate and find optimal WPM"""  
        typing_logic.find_wpm(self)

    def _clear_input_placeholder(self, event):
        typing_logic.clear_input_placeholder(self, event)

    def _restore_input_placeholder(self, event):
        typing_logic.restore_input_placeholder(self, event)

    def _get_entry_fg(self):
        """Get entry foreground color based on theme"""
        return get_entry_fg(self._get_safe_app().cfg['settings'].get('dark_mode', False))
    
    def _get_placeholder_fg(self):
        """Get placeholder foreground color based on theme"""
        return get_placeholder_fg(self._get_safe_app().cfg['settings'].get('dark_mode', False))
    
    def update_placeholder_color(self):
        """Update placeholder colors for theme changes"""
        try:
            from modern_theme import update_placeholder_color as update_colors
            update_colors(self, self._get_safe_app().cfg['settings'].get('dark_mode', False))
        except:
            pass  # Ignore errors during theme switching

    def _get_entry_fg_old(self):
        return get_entry_fg(self._get_safe_app().cfg['settings'].get('dark_mode', False))

    def _get_placeholder_fg(self):
        return get_placeholder_fg(self._get_safe_app().cfg['settings'].get('dark_mode', False))

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
    
    def show_wpm_test(self):
        """Show WPM typing test popup"""
        import time
        import threading
        
        # Make time available to all methods
        self.time_module = time
        
        # Create test window
        test_window = tk.Toplevel(self.app)
        test_window.title("📊 Find Your WPM - Typing Speed Test")
        test_window.geometry("700x500")
        test_window.resizable(False, False)
        test_window.transient(self.app)
        test_window.grab_set()
        
        # Center window
        test_window.update_idletasks()
        x = (self._get_safe_app().winfo_x() + (self._get_safe_app().winfo_width() // 2)) - (test_window.winfo_width() // 2)
        y = (self._get_safe_app().winfo_y() + (self._get_safe_app().winfo_height() // 2)) - (test_window.winfo_height() // 2)
        test_window.geometry(f"+{x}+{y}")
        
        # Apply theme
        dark = self._get_safe_app().cfg['settings'].get('dark_mode', False)
        bg_color = "#181816" if dark else "#ffffff"
        fg_color = "#ffffff" if dark else "#222222"
        test_window.configure(bg=bg_color)
        
        # Test state
        self.test_state = {
            'started': False,
            'finished': False,
            'paused': False,
            'start_time': None,
            'words_typed': 0,
            'errors': 0,
            'target_text': "",
            'manual_stop': False
        }
        
        # Header
        header_frame = tk.Frame(test_window, bg=bg_color)
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        tk.Label(header_frame, text="⚡ WPM Typing Speed Test", 
                font=('Segoe UI', 18, 'bold'), bg=bg_color, fg=fg_color).pack()
        tk.Label(header_frame, text="Click START, then type the text below as fast and accurately as you can", 
                font=('Segoe UI', 11), bg=bg_color, fg=fg_color).pack(pady=(5, 0))
        
        # Test text (practice paragraph)
        self.test_state['target_text'] = """The quick brown fox jumps over the lazy dog. This pangram contains every letter of the alphabet and is commonly used for typing practice. Typing speed is measured in words per minute, where a word is defined as five characters including spaces. Regular practice can significantly improve your typing speed and accuracy over time."""
        
        # Target text display
        text_frame = tk.LabelFrame(test_window, text="Text to Type:", 
                                  font=('Segoe UI', 12, 'bold'), bg=bg_color, fg=fg_color)
        text_frame.pack(fill='x', padx=20, pady=10)
        
        target_text_widget = tk.Text(text_frame, height=4, wrap='word', 
                                    font=('Segoe UI', 12), state='disabled',
                                    bg="#f0f0f0" if not dark else "#2a2a2a",
                                    fg=fg_color, relief='flat', padx=10, pady=10)
        target_text_widget.pack(fill='x', padx=10, pady=10)
        target_text_widget.config(state='normal')
        target_text_widget.insert('1.0', self.test_state['target_text'])
        target_text_widget.config(state='disabled')
        
        # Your typing area
        typing_frame = tk.LabelFrame(test_window, text="Your Typing:", 
                                    font=('Segoe UI', 12, 'bold'), bg=bg_color, fg=fg_color)
        typing_frame.pack(fill='x', padx=20, pady=10)
        
        self.typing_area = tk.Text(typing_frame, height=4, wrap='word', 
                                  font=('Segoe UI', 12),
                                  bg="#ffffff" if not dark else "#3c3c3c",
                                  fg=fg_color, insertbackground=fg_color,
                                  relief='flat', padx=10, pady=10)
        self.typing_area.pack(fill='x', padx=10, pady=10)
        self.typing_area.bind('<KeyPress>', lambda e: self._handle_typing_test(e, test_window))
        self.typing_area.focus_set()
        
        # Control and status section
        control_frame = tk.Frame(test_window, bg=bg_color)
        control_frame.pack(fill='x', padx=20, pady=10)
        
        # Start/Stop controls
        controls_top = tk.Frame(control_frame, bg=bg_color)
        controls_top.pack(fill='x', pady=(0, 10))
        
        self.start_test_btn = tk.Button(controls_top, text="🚀 START TEST", 
                                       command=self._start_wpm_test,
                                       font=('Segoe UI', 12, 'bold'), 
                                       bg='#4CAF50', fg='white',
                                       cursor='hand2', padx=20, pady=8)
        self.start_test_btn.pack(side='left', padx=(0, 10))
        
        self.stop_test_btn = tk.Button(controls_top, text="⏹️ STOP TEST", 
                                      command=self._stop_wpm_test,
                                      font=('Segoe UI', 12, 'bold'), 
                                      bg='#f44336', fg='white',
                                      cursor='hand2', padx=20, pady=8,
                                      state='disabled')
        self.stop_test_btn.pack(side='left')
        
        # Status and timer - make more prominent
        status_frame = tk.Frame(control_frame, bg=bg_color, relief='ridge', bd=2)
        status_frame.pack(fill='x', pady=10)
        
        self.status_label = tk.Label(status_frame, text="Ready to start! Click START TEST button when ready.", 
                                    font=('Segoe UI', 13, 'bold'), bg=bg_color, fg=fg_color,
                                    wraplength=400, justify='center')
        self.status_label.pack(pady=8)
        
        self.timer_label = tk.Label(status_frame, text="⏱️ Time: 0.0s", 
                                   font=('Segoe UI', 16, 'bold'), bg=bg_color, fg='#4CAF50')
        self.timer_label.pack(pady=(0, 8))
        
        # Buttons
        button_frame = tk.Frame(test_window, bg=bg_color)
        button_frame.pack(pady=20)
        
        self.retry_btn = tk.Button(button_frame, text="🔄 Retry Test", 
                                  command=lambda: self._reset_wpm_test(test_window),
                                  font=('Segoe UI', 10), padx=15, pady=5,
                                  cursor='hand2', state='disabled')
        self.retry_btn.pack(side='left', padx=5)
        
        self.apply_btn = tk.Button(button_frame, text="✅ Apply This WPM", 
                                  command=lambda: self._apply_wpm_result(test_window),
                                  font=('Segoe UI', 10), padx=15, pady=5,
                                  cursor='hand2', state='disabled',
                                  bg='#4CAF50', fg='white')
        self.apply_btn.pack(side='left', padx=5)
        
        close_btn = tk.Button(button_frame, text="❌ Close", 
                             command=lambda: self._cleanup_wpm_test(test_window),
                             font=('Segoe UI', 10), padx=15, pady=5,
                             cursor='hand2')
        close_btn.pack(side='left', padx=5)
        
        # Bind cleanup to window destruction
        test_window.protocol("WM_DELETE_WINDOW", lambda: self._cleanup_wpm_test(test_window))
        
        # Store test window reference for other methods
        self.current_test_window = test_window
        
        # Start timer update
        self._update_timer(test_window)
        
    def _start_wpm_test(self):
        """Start the WPM test with countdown"""
        if not hasattr(self, 'test_state'):
            return
            
        # Store reference to test window for scheduling
        self.current_test_window = getattr(self, 'current_test_window', None)
        if not self.current_test_window:
            print("Warning: No test window reference found")
            return
            
        # Disable start button during countdown
        self.start_test_btn.config(state='disabled')
        self.stop_test_btn.config(state='disabled')
        
        # Start countdown
        self._countdown(3)
        
    def _countdown(self, seconds):
        """Show countdown before test starts"""
        if seconds > 0:
            self.status_label.config(text=f"🚀 Starting in {seconds}... Get ready!")
            self.timer_label.config(text=f"⏱️ Starting in {seconds}!", fg='#FF9800')
            print(f"Countdown: {seconds}")
            # Force UI update
            self.status_label.update()
            self.timer_label.update()
            # Schedule next countdown update using test window
            if hasattr(self, 'current_test_window') and self.current_test_window:
                self.current_test_window.after(1000, lambda: self._countdown(seconds - 1))
        else:
            # Start the actual test
            print("Countdown finished, starting test")
            self._actually_start_test()
            
    def _actually_start_test(self):
        """Actually start the WPM test after countdown"""
        self.test_state['started'] = True
        self.test_state['paused'] = False
        self.test_state['start_time'] = self.time_module.time()
        
        # Update UI
        self.start_test_btn.config(state='disabled')
        self.stop_test_btn.config(state='normal')
        self.status_label.config(text="GO! Start typing now!")
        self.timer_label.config(text="⏱️ Time: 0.0s", fg='#4CAF50')
        # Force UI update
        self.status_label.update()
        self.timer_label.update()
        
        # Focus typing area
        self.typing_area.focus_set()
        
    def _stop_wpm_test(self):
        """Stop the WPM test and show results"""
        print("Stop button clicked")
        if not hasattr(self, 'test_state'):
            print("No test state found")
            return
            
        if self.test_state.get('finished', False):
            print("Test already finished")
            return
            
        print("Stopping test manually")
        # Mark as manually stopped but don't set finished yet - let _finish_wpm_test handle it
        self.test_state['manual_stop'] = True
        
        # Call finish test which will handle setting finished
        self._finish_wpm_test()
        
    def _finish_wpm_test(self):
        """Finish the WPM test and show results"""
        if not hasattr(self, 'test_state') or self.test_state['finished']:
            return
            
        self.test_state['finished'] = True
        end_time = self.time_module.time()
        
        if not self.test_state['start_time']:
            self.status_label.config(text="Test not started yet!")
            return
        
        # Calculate results
        time_taken = end_time - self.test_state['start_time']
        typed_text = self.typing_area.get('1.0', 'end-1c')
        target_text = self.test_state['target_text']
        
        # Count words (standard: 5 characters = 1 word)
        chars_typed = len(typed_text)
        words_typed = chars_typed / 5
        
        # Calculate WPM
        minutes_taken = time_taken / 60
        wpm = int(words_typed / minutes_taken) if minutes_taken > 0 else 0
        
        # Calculate accuracy
        correct_chars = sum(1 for i, char in enumerate(typed_text) 
                           if i < len(target_text) and char == target_text[i])
        accuracy = int((correct_chars / len(target_text)) * 100) if len(target_text) > 0 else 0
        
        # Store result
        self.test_state['wpm_result'] = wpm
        
        print(f"Final results: WPM={wpm}, Accuracy={accuracy}%")
        
        # Update display
        result_text = f"🎉 Test Complete!\nWPM: {wpm} | Accuracy: {accuracy}% | Time: {time_taken:.1f}s"
        self.status_label.config(text=result_text)
        self.timer_label.config(text=f"⏱️ Final Time: {time_taken:.1f}s", fg='#2196F3')
        
        # Force UI update
        self.status_label.update()
        self.timer_label.update()
        
        # Update UI buttons
        self.start_test_btn.config(state='normal', text="🔄 Start New Test")
        self.stop_test_btn.config(state='disabled')
        self.retry_btn.config(state='normal')
        self.apply_btn.config(state='normal')
        
        # Disable typing area
        self.typing_area.config(state='disabled')
        
        print("WPM test finished and UI updated")
        
    def _update_timer(self, test_window):
        """Update the timer display"""
        try:
            # Check if window still exists
            if not test_window.winfo_exists():
                return
        except tk.TclError:
            return
            
        if not hasattr(self, 'test_state') or not self.test_state:
            return
            
        # Calculate and display elapsed time
        if (self.test_state.get('started', False) and 
            not self.test_state.get('finished', False) and 
            not self.test_state.get('paused', False)):
            if self.test_state.get('start_time'):
                elapsed = self.time_module.time() - self.test_state['start_time']
                self.timer_label.config(text=f"⏱️ Time: {elapsed:.1f}s", fg='#4CAF50')
                # Debug print to confirm timer is updating
                if int(elapsed * 10) % 10 == 0:  # Print every second
                    print(f"Timer update: {elapsed:.1f}s")
        
        # Continue updating if test is still active
        if not self.test_state.get('finished', False):
            test_window.after(100, lambda: self._update_timer(test_window))
    
    def _handle_typing_test(self, event, test_window):
        """Handle typing in the WPM test"""
        # Check if window still exists and test is valid
        try:
            if not test_window.winfo_exists():
                return 'break'
        except tk.TclError:
            return 'break'
            
        if not hasattr(self, 'test_state') or not self.test_state:
            return 'break'
            
        # Only allow typing if test was started with button
        if not self.test_state['started']:
            return 'break'  # Don't allow typing until START is clicked
        
        # Don't process if already finished
        if self.test_state['finished']:
            return 'break'
        
        # Check if test is complete after this keystroke
        test_window.after(10, self._check_test_completion)
    
    def _check_test_completion(self):
        """Check if typing test is complete"""
        if self.test_state['finished']:
            return
            
        typed_text = self.typing_area.get('1.0', 'end-1c')
        target_text = self.test_state['target_text']
        
        if len(typed_text) >= len(target_text):
            self._finish_wpm_test()
    
    def _finish_wpm_test(self):
        """Finish the WPM test and show results"""
        if not hasattr(self, 'test_state') or self.test_state['finished']:
            return
            
        self.test_state['finished'] = True
        end_time = self.time_module.time()
        
        if not self.test_state['start_time']:
            return
        
        # Calculate results
        time_taken = end_time - self.test_state['start_time']
        typed_text = self.typing_area.get('1.0', 'end-1c')
        target_text = self.test_state['target_text']
        
        # Count words (standard: 5 characters = 1 word)
        chars_typed = len(typed_text)
        words_typed = chars_typed / 5
        
        # Calculate WPM
        minutes_taken = time_taken / 60
        wpm = int(words_typed / minutes_taken) if minutes_taken > 0 else 0
        
        # Calculate accuracy
        correct_chars = sum(1 for i, char in enumerate(typed_text) 
                           if i < len(target_text) and char == target_text[i])
        accuracy = int((correct_chars / len(target_text)) * 100) if len(target_text) > 0 else 0
        
        # Store result
        self.test_state['wpm_result'] = wpm
        
        # Update display
        result_text = f"🎉 Test Complete!\nWPM: {wpm} | Accuracy: {accuracy}% | Time: {time_taken:.1f}s"
        self.status_label.config(text=result_text)
        
        # Enable buttons
        self.retry_btn.config(state='normal')
        self.apply_btn.config(state='normal')
        
        # Disable typing area
        self.typing_area.config(state='disabled')
    
    def _reset_wpm_test(self, test_window):
        """Reset the WPM test for another attempt"""
        # Clear typing area
        self.typing_area.config(state='normal')
        self.typing_area.delete('1.0', 'end')
        self.typing_area.focus_set()
        
        # Reset state
        self.test_state = {
            'started': False,
            'finished': False,
            'paused': False,
            'start_time': None,
            'words_typed': 0,
            'errors': 0,
            'manual_stop': False,
            'target_text': self.test_state['target_text']  # Keep same text
        }
        
        # Reset UI
        self.status_label.config(text="Ready to start! Click START TEST button when ready.")
        self.timer_label.config(text="⏱️ Time: 0.0s", fg='#4CAF50')
        self.start_test_btn.config(state='normal', text="▶️ Start Test")
        self.stop_test_btn.config(state='disabled')
        self.retry_btn.config(state='disabled')
        self.apply_btn.config(state='disabled')
    
    def _apply_wpm_result(self, test_window):
        """Apply the calculated WPM to the typing settings"""
        if 'wpm_result' in self.test_state:
            wpm = self.test_state['wpm_result']
            
            # Calculate delays based on WPM (approximate)
            chars_per_second = (wpm * 5) / 60  # 5 chars per word, 60 seconds per minute
            base_delay = 1.0 / chars_per_second if chars_per_second > 0 else 0.1
            
            # Set realistic min/max delays with some variation
            min_delay = max(0.01, base_delay * 0.7)  # 30% faster sometimes
            max_delay = min(0.5, base_delay * 1.5)   # 50% slower sometimes
            
            # Update the sliders
            self.min_delay_var.set(min_delay)
            self.max_delay_var.set(max_delay)
            
            # Update WPM display
            self.wpm_var.set(f"WPM: {wpm}")
            
            # Save to config
            self._get_safe_app().cfg['settings']['min_delay'] = min_delay
            self._get_safe_app().cfg['settings']['max_delay'] = max_delay
            from sly_config import save_config
            save_config(self._get_safe_app().cfg)
            
            # Show confirmation
            import tkinter.messagebox as messagebox
            messagebox.showinfo("WPM Applied", f"Your typing speed of {wpm} WPM has been applied!\n\nDelays updated:\nMin: {min_delay:.3f}s\nMax: {max_delay:.3f}s")
            
            self._cleanup_wpm_test(test_window)
    
    def _update_timer(self, test_window):
        """Update the timer display"""
        try:
            if not hasattr(self, 'test_state') or not self.test_state:
                return
                
            if test_window.winfo_exists() and self.test_state['started'] and not self.test_state['finished']:
                if self.test_state['start_time']:
                    elapsed = self.time_module.time() - self.test_state['start_time']
                    self.timer_label.config(text=f"Time: {elapsed:.1f}s")
                test_window.after(100, lambda: self._update_timer(test_window))
        except (tk.TclError, AttributeError):
            # Window was destroyed or state was cleared
            pass
    
    def _cleanup_wpm_test(self, test_window):
        """Clean up WPM test resources"""
        try:
            # Clear test state to prevent lingering references
            if hasattr(self, 'test_state'):
                self.test_state = None
            
            # Clear widget references
            if hasattr(self, 'typing_area'):
                self.typing_area = None
            if hasattr(self, 'status_label'):
                self.status_label = None
            if hasattr(self, 'timer_label'):
                self.timer_label = None
            if hasattr(self, 'retry_btn'):
                self.retry_btn = None
            if hasattr(self, 'apply_btn'):
                self.apply_btn = None
                
            # Destroy window
            test_window.destroy()
            
        except (tk.TclError, AttributeError):
            # Window already destroyed or attributes don't exist
            pass
