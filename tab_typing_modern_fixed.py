# tab_typing_modern_fixed.py - Fixed modern typing tab with proper wiring

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from modern_ui_2025 import *
import typing_engine as engine

try:
    from utils import is_premium_user as _is_premium_user
except ImportError:
    def _is_premium_user(app):
        return True  # Default for testing

class ModernTypingTab(tk.Frame):
    """Modern typing tab with proper functionality"""
    
    PLACEHOLDER_INPUT = "Start typing or paste your text here..."
    PLACEHOLDER_PREVIEW = "Live preview will appear as you type..."
    
    def _is_premium_user(self):
        """Check if user is premium"""
        try:
            result = _is_premium_user(self.app)
            print(f"[TYPING TAB] Premium check result: {result}")
            return result
        except Exception as e:
            print(f"[TYPING TAB] Premium check error: {e}")
            # Try direct check
            try:
                if hasattr(self.app, 'tabs') and 'Account' in self.app.tabs:
                    account_tab = self.app.tabs['Account']
                    if hasattr(account_tab, 'is_premium'):
                        result = account_tab.is_premium()
                        print(f"[TYPING TAB] Direct account tab premium check: {result}")
                        return result
            except:
                pass
            return False  # Default to False for safety
    
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS['background'])
        self.app = app
        self.paused = False
        self.typing_active = False
        self.total_chars = 0
        self.chars_typed = 0
        
        # Control variables
        self.min_delay_var = tk.DoubleVar(value=0.05)
        self.max_delay_var = tk.DoubleVar(value=0.15)
        self.pause_freq_var = tk.IntVar(value=5)
        self.typos_var = tk.BooleanVar(value=False)
        self.preview_only_var = tk.BooleanVar(value=False)
        self.adv_antidetect_var = tk.BooleanVar(value=False)
        self.premium_filler_var = tk.BooleanVar(value=False)  # Premium AI filler
        
        self.loading_profile = False
        
        # Build the UI
        self.build_ui()
        
        # Setup callbacks
        self.setup_callbacks()
        
        # Load initial config
        try:
            self.update_from_config()
        except Exception as e:
            print(f"[MODERN TYPING] Error loading config: {e}")
    
    def build_ui(self):
        """Build the modern UI layout with scrollable container"""
        # Create scrollable container
        canvas_container = tk.Frame(self, bg=COLORS['background'])
        canvas_container.pack(fill='both', expand=True)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(canvas_container, bg=COLORS['background'],
                               highlightthickness=0, bd=0)
        v_scrollbar = ttk.Scrollbar(canvas_container, orient='vertical',
                                   command=self.canvas.yview)
        
        # Create scrollable frame
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLORS['background'])
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Add scrollable frame to canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=v_scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        
        # Bind mousewheel
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Main container inside scrollable frame
        main_container = tk.Frame(self.scrollable_frame, bg=COLORS['background'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Status Bar at the top
        self.build_status_bar(main_container)
        
        # Stats row
        self.build_stats_row(main_container)
        
        # Main content area
        content_frame = tk.Frame(main_container, bg=COLORS['background'])
        content_frame.pack(fill='both', expand=True, pady=(20, 0))
        
        # Left column - Input and Preview
        left_column = tk.Frame(content_frame, bg=COLORS['background'])
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        self.build_input_section(left_column)
        self.build_preview_section(left_column)
        
        # Right column - Simple Controls
        right_column = tk.Frame(content_frame, bg=COLORS['background'], width=250)
        right_column.pack(side='right', fill='y', padx=(10, 0))
        right_column.pack_propagate(False)  # Fixed width
        
        self.build_simple_controls(right_column)
        
        # Speed controls below
        speed_section = tk.Frame(main_container, bg=COLORS['background'])
        speed_section.pack(fill='x', pady=(20, 0))
        
        self.build_speed_controls(speed_section)
    
    def build_status_bar(self, parent):
        """Build unified status bar that mirrors to overlay"""
        # Status Bar Card
        status_card = GlassmorphicCard(parent, title="📊 Status")
        status_card.pack(fill='x', pady=(0, 20))
        
        # Main status container
        status_container = tk.Frame(status_card.content, bg=COLORS['surface'])
        status_container.pack(fill='x')
        
        # Left side - Status text
        self.status_label = tk.Label(status_container,
                                    text="Ready to type",
                                    font=('Segoe UI', 12, 'bold'),
                                    fg=COLORS['text_primary'],
                                    bg=COLORS['surface'])
        self.status_label.pack(side='left')
        
        # Right side - Live stats
        stats_frame = tk.Frame(status_container, bg=COLORS['surface'])
        stats_frame.pack(side='right')
        
        # Progress
        tk.Label(stats_frame, text="Progress:", font=('Segoe UI', 10),
                fg=COLORS['text_dim'], bg=COLORS['surface']).pack(side='left', padx=(10, 5))
        self.progress_label = tk.Label(stats_frame, text="0%",
                                      font=('Segoe UI', 10, 'bold'),
                                      fg=COLORS['primary'], bg=COLORS['surface'])
        self.progress_label.pack(side='left', padx=(0, 10))
        
        # Characters
        tk.Label(stats_frame, text="Chars:", font=('Segoe UI', 10),
                fg=COLORS['text_dim'], bg=COLORS['surface']).pack(side='left', padx=(10, 5))
        self.chars_label = tk.Label(stats_frame, text="0/0",
                                   font=('Segoe UI', 10, 'bold'),
                                   fg=COLORS['primary'], bg=COLORS['surface'])
        self.chars_label.pack(side='left', padx=(0, 10))
        
        # Time remaining
        tk.Label(stats_frame, text="Time:", font=('Segoe UI', 10),
                fg=COLORS['text_dim'], bg=COLORS['surface']).pack(side='left', padx=(10, 5))
        self.time_label = tk.Label(stats_frame, text="0:00",
                                  font=('Segoe UI', 10, 'bold'),
                                  fg=COLORS['primary'], bg=COLORS['surface'])
        self.time_label.pack(side='left')
        
        # Progress bar below status
        self.progress_bar = ModernProgressBar(status_card.content)
        self.progress_bar.pack(fill='x', pady=(10, 0))
    
    def build_stats_row(self, parent):
        """Build the stats cards row"""
        stats_frame = tk.Frame(parent, bg=COLORS['background'])
        stats_frame.pack(fill='x')
        
        # WPM Card
        self.wpm_card = StatsCard(stats_frame, title="Words Per Minute", 
                                 value="0", unit="WPM", icon="⚡")
        self.wpm_card.pack(side='left', padx=(0, 10))
        
        # Progress Card
        self.progress_card = StatsCard(stats_frame, title="Progress", 
                                       value="0", unit="%", icon="📊")
        self.progress_card.pack(side='left', padx=10)
        
        # Characters Card
        self.chars_card = StatsCard(stats_frame, title="Characters", 
                                   value="0", unit="chars", icon="📝")
        self.chars_card.pack(side='left', padx=10)
        
        # Time Card
        self.time_card = StatsCard(stats_frame, title="Est. Time", 
                                  value="0:00", unit="", icon="⏱")
        self.time_card.pack(side='left', padx=10)
    
    def build_input_section(self, parent):
        """Build the input text area"""
        # Input Card
        input_card = GlassmorphicCard(parent, title="📝 Input Text")
        input_card.pack(fill='both', expand=True, pady=(0, 10))
        
        # Modern text area
        self.text_input = ModernTextArea(input_card.content, height=10,
                                        placeholder=self.PLACEHOLDER_INPUT)
        self.text_input.pack(fill='both', expand=True)
        
        # File operations buttons
        file_ops_frame = tk.Frame(input_card.content, bg=COLORS['surface'])
        file_ops_frame.pack(fill='x', pady=(10, 0))
        
        ModernButton(file_ops_frame, text="Load File", icon="📁",
                    command=self.load_file, variant="secondary").pack(side='left', padx=(0, 5))
        
        ModernButton(file_ops_frame, text="Paste", icon="📋",
                    command=self.paste_clipboard, variant="secondary").pack(side='left', padx=5)
        
        ModernButton(file_ops_frame, text="Clear", icon="🗑",
                    command=self.clear_text_areas, variant="secondary").pack(side='left', padx=5)
    
    def build_preview_section(self, parent):
        """Build the preview area"""
        # Preview Card
        preview_card = GlassmorphicCard(parent, title="👁 Live Preview")
        preview_card.pack(fill='both', expand=True)
        
        # Modern preview text area
        self.live_preview = ModernTextArea(preview_card.content, height=8,
                                          placeholder=self.PLACEHOLDER_PREVIEW)
        self.live_preview.pack(fill='both', expand=True)
        self.live_preview.text.config(state='disabled')  # Read-only
    
    def build_simple_controls(self, parent):
        """Build simplified action controls"""
        # Controls Card with fixed width
        controls_card = GlassmorphicCard(parent, title="🎮 Controls")
        controls_card.pack(fill='x')
        
        # Button container with fixed dimensions
        button_container = tk.Frame(controls_card.content, bg=COLORS['surface'])
        button_container.pack(fill='x', padx=10, pady=5)
        
        # Start Button - Always visible green
        self.start_btn = ModernButton(button_container, text="Start Typing", 
                                     icon="▶", command=self.start_typing, 
                                     variant="success")
        self.start_btn.configure(height=45)
        self.start_btn.pack(fill='x', pady=(5, 8))
        
        # Pause Button - Always visible purple
        self.pause_btn = ModernButton(button_container, text="Pause", 
                                     icon="⏸", command=self.pause_typing,
                                     variant="primary")
        self.pause_btn.configure(height=45)
        self.pause_btn.pack(fill='x', pady=8)
        
        # Stop Button - Always visible red
        self.stop_btn = ModernButton(button_container, text="Stop", 
                                    icon="⏹", command=self.stop_typing,
                                    variant="danger")
        self.stop_btn.configure(height=45)
        self.stop_btn.pack(fill='x', pady=(8, 5))
        
        # Initially disable pause and stop
        self.pause_btn.configure(state='disabled')
        self.stop_btn.configure(state='disabled')
    
    def build_speed_controls(self, parent):
        """Build speed and feature controls"""
        # Speed Controls Card
        speed_card = GlassmorphicCard(parent, title="⚡ Speed & Features")
        speed_card.pack(fill='x')
        
        # Two columns
        controls_container = tk.Frame(speed_card.content, bg=COLORS['surface'])
        controls_container.pack(fill='both', expand=True)
        
        # Left - Sliders
        left_frame = tk.Frame(controls_container, bg=COLORS['surface'])
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 20))
        
        self.min_delay_slider = ModernSlider(left_frame,
                                            from_=0.01, to=0.5,
                                            variable=self.min_delay_var,
                                            label="Min Delay", unit="s")
        self.min_delay_slider.pack(fill='x', pady=(0, 15))
        
        self.max_delay_slider = ModernSlider(left_frame,
                                            from_=0.05, to=1.0,
                                            variable=self.max_delay_var,
                                            label="Max Delay", unit="s")
        self.max_delay_slider.pack(fill='x', pady=(0, 15))
        
        self.pause_freq_slider = ModernSlider(left_frame,
                                             from_=0, to=20,
                                             variable=self.pause_freq_var,
                                             label="Pause Frequency", unit="")
        self.pause_freq_slider.pack(fill='x')
        
        # Right - Features
        right_frame = tk.Frame(controls_container, bg=COLORS['surface'])
        right_frame.pack(side='right', fill='y', padx=(20, 0))
        
        tk.Label(right_frame, text="Features",
                font=('Segoe UI', 11, 'bold'),
                fg=COLORS['text_primary'], bg=COLORS['surface']).pack(anchor='w', pady=(0, 15))
        
        # Typos Toggle
        typos_frame = tk.Frame(right_frame, bg=COLORS['surface'])
        typos_frame.pack(fill='x', pady=(0, 12))
        tk.Label(typos_frame, text="Random Typos",
                font=('Segoe UI', 10), fg=COLORS['text_secondary'],
                bg=COLORS['surface']).pack(side='left')
        ModernToggle(typos_frame, variable=self.typos_var).pack(side='right', padx=(20, 0))
        
        # Preview Only Toggle
        preview_frame = tk.Frame(right_frame, bg=COLORS['surface'])
        preview_frame.pack(fill='x', pady=(0, 12))
        tk.Label(preview_frame, text="Preview Only",
                font=('Segoe UI', 10), fg=COLORS['text_secondary'],
                bg=COLORS['surface']).pack(side='left')
        ModernToggle(preview_frame, variable=self.preview_only_var).pack(side='right', padx=(20, 0))
        
        # Premium Filler Toggle (Show to all, but disable for non-premium)
        filler_frame = tk.Frame(right_frame, bg=COLORS['surface'])
        filler_frame.pack(fill='x', pady=(0, 12))
        
        label_frame = tk.Frame(filler_frame, bg=COLORS['surface'])
        label_frame.pack(side='left', fill='x', expand=True)
        
        tk.Label(label_frame, text="AI Filler Text",
                font=('Segoe UI', 10), fg=COLORS['accent'],
                bg=COLORS['surface']).pack(side='left')
        
        tk.Label(label_frame, text="PREMIUM",
                font=('Segoe UI', 8, 'bold'), fg=COLORS['warning'],
                bg=COLORS['surface']).pack(side='left', padx=(5, 0))
        
        # Info button
        info_btn = tk.Button(label_frame, text="ⓘ", 
                           font=('Segoe UI', 9), 
                           fg=COLORS['text_dim'],
                           bg=COLORS['surface'],
                           bd=0,
                           cursor='hand2',
                           command=self.show_ai_filler_info)
        info_btn.pack(side='left', padx=(5, 0))
        
        # Toggle - disabled for non-premium
        toggle = ModernToggle(filler_frame, variable=self.premium_filler_var)
        toggle.pack(side='right', padx=(20, 0))
        
        # Disable if not premium (prevent toggling)
        if not self._is_premium_user():
            self.premium_filler_var.set(False)
            # Override the toggle method to show premium message
            def show_premium_msg(event=None):
                messagebox.showinfo("Premium Required", 
                                  "Upgrade to Premium to use AI Filler Text!\n\n"
                                  "This feature generates realistic typing patterns with AI.")
            toggle.canvas.unbind("<Button-1>")
            toggle.canvas.bind("<Button-1>", show_premium_msg)
            # Make it look disabled
            toggle.canvas.itemconfig(toggle.bg_rect, fill='#2a2a3e')
            toggle.canvas.itemconfig(toggle.handle, fill='#4a4a5e')
        
        # Separator line
        sep_frame = tk.Frame(right_frame, height=1, bg=COLORS['border'])
        sep_frame.pack(fill='x', pady=(20, 20))
        
        # Enhanced WPM Display - Bigger and more prominent
        wpm_container = tk.Frame(right_frame, bg=COLORS['surface_light'], 
                                highlightthickness=1, highlightbackground=COLORS['primary'])
        wpm_container.pack(fill='x', pady=(0, 10))
        
        wpm_inner = tk.Frame(wpm_container, bg=COLORS['surface_light'])
        wpm_inner.pack(padx=15, pady=12)
        
        tk.Label(wpm_inner, text="Current Speed",
                font=('Segoe UI', 9), fg=COLORS['text_dim'],
                bg=COLORS['surface_light']).pack()
        
        self.wpm_label = tk.Label(wpm_inner, text="0",
                                 font=('Segoe UI', 24, 'bold'), 
                                 fg=COLORS['primary'],
                                 bg=COLORS['surface_light'])
        self.wpm_label.pack()
        
        tk.Label(wpm_inner, text="WPM",
                font=('Segoe UI', 10, 'bold'), 
                fg=COLORS['text_secondary'],
                bg=COLORS['surface_light']).pack()
    
    def setup_callbacks(self):
        """Setup variable callbacks"""
        for var in [self.min_delay_var, self.max_delay_var, 
                   self.pause_freq_var, self.typos_var,
                   self.preview_only_var, self.premium_filler_var]:
            var.trace_add('write', lambda *args: self.on_setting_change())
        
        # Text change callback
        self.text_input.text.bind("<<Modified>>", self.on_text_change)
    
    def on_setting_change(self):
        """Handle setting changes"""
        if not self.loading_profile:
            if hasattr(self.app, 'on_setting_change'):
                self.app.on_setting_change()
            self.update_wpm()
    
    def on_text_change(self, event=None):
        """Handle text input changes"""
        text = self.text_input.get('1.0', 'end-1c')
        if text and text != self.text_input.placeholder:
            self.total_chars = len(text)
            self.chars_card.update_value(str(self.total_chars))
            self.update_time_estimate()
        else:
            self.total_chars = 0
            self.chars_card.update_value("0")
            self.time_card.update_value("0:00")
    
    def update_time_estimate(self):
        """Update estimated time based on current settings"""
        if self.total_chars > 0:
            avg_delay = (self.min_delay_var.get() + self.max_delay_var.get()) / 2
            total_seconds = self.total_chars * avg_delay
            
            # Add pause time
            pause_freq = self.pause_freq_var.get()
            if pause_freq > 0:
                num_pauses = self.total_chars // pause_freq
                total_seconds += num_pauses * 2  # 2 seconds per pause
            
            # Format time
            minutes = int(total_seconds // 60)
            seconds = int(total_seconds % 60)
            self.time_card.update_value(f"{minutes}:{seconds:02d}")
    
    def calculate_wpm(self):
        """Calculate current WPM based on delays"""
        avg_delay = (self.min_delay_var.get() + self.max_delay_var.get()) / 2
        if avg_delay > 0:
            chars_per_sec = 1 / avg_delay
            words_per_min = (chars_per_sec * 60) / 5  # Average 5 chars per word
            return int(words_per_min)
        return 0
    
    def update_wpm(self):
        """Update WPM display"""
        wpm = self.calculate_wpm()
        self.wpm_label.configure(text=str(wpm))  # Just the number for big display
        self.wpm_card.update_value(str(wpm))
    
    def update_from_config(self):
        """Load settings from config"""
        self.loading_profile = True
        
        try:
            s = self.app.cfg.get('settings', {})
            self.min_delay_var.set(s.get('min_delay', 0.05))
            self.max_delay_var.set(s.get('max_delay', 0.15))
            self.pause_freq_var.set(s.get('pause_freq', 5))
            self.typos_var.set(s.get('typos_on', False))
            self.preview_only_var.set(s.get('preview_only', False))
            self.adv_antidetect_var.set(s.get('adv_antidetect', False))
            self.premium_filler_var.set(s.get('premium_filler', False))
        except Exception as e:
            print(f"[MODERN TYPING] Error in config: {e}")
        
        self.loading_profile = False
        self.update_wpm()
    
    def start_typing(self):
        """Start typing operation"""
        text = self.text_input.get('1.0', 'end-1c')
        if not text or text == self.text_input.placeholder:
            messagebox.showwarning("No Text", "Please enter some text to type.")
            return
        
        # Reset counters
        self.chars_typed = 0
        self.total_chars = len(text)
        self.typing_active = True
        
        # Update UI state
        self.status_label.configure(text="⚡ Typing in progress...", fg=COLORS['success'])
        self.start_btn.configure(state='disabled')
        self.pause_btn.configure(state='normal')
        self.stop_btn.configure(state='normal')
        
        # Update overlay if it exists
        self.update_overlay_status("Typing...")
        
        # Check if we need to use premium AI filler typing
        if self.premium_filler_var.get() and self._is_premium_user():
            # Use premium typing with AI filler
            try:
                from premium_typing import premium_type_with_filler
                import threading
                
                # Create stop and pause flags that match the engine's
                stop_flag = engine._stop_flag
                pause_flag = engine._pause_flag
                
                # Clear flags before starting
                stop_flag.clear()
                pause_flag.clear()
                
                # Use premium typing with AI filler
                premium_type_with_filler(
                    goal_text=text,
                    live_preview_callback=self.update_preview,
                    status_callback=self.update_status,
                    min_delay=self.min_delay_var.get(),
                    max_delay=self.max_delay_var.get(),
                    typos_on=self.typos_var.get(),
                    pause_freq=self.pause_freq_var.get(),
                    preview_only=self.preview_only_var.get(),
                    stop_flag=stop_flag,
                    pause_flag=pause_flag
                )
            except Exception as e:
                print(f"[MODERN TYPING] Error with premium typing: {e}")
                # Fallback to regular typing
                engine.start_typing_from_input(
                    text=text,
                    live_preview_callback=self.update_preview,
                    status_callback=self.update_status,
                    min_delay=self.min_delay_var.get(),
                    max_delay=self.max_delay_var.get(),
                    typos_on=self.typos_var.get(),
                    pause_freq=self.pause_freq_var.get(),
                    preview_only=self.preview_only_var.get()
                )
        else:
            # Start regular typing with engine
            try:
                engine.start_typing_from_input(
                    text=text,
                    live_preview_callback=self.update_preview,
                    status_callback=self.update_status,
                    min_delay=self.min_delay_var.get(),
                    max_delay=self.max_delay_var.get(),
                    typos_on=self.typos_var.get(),
                    pause_freq=self.pause_freq_var.get(),
                    preview_only=self.preview_only_var.get()
                )
            except Exception as e:
                print(f"[MODERN TYPING] Error starting typing: {e}")
                self.stop_typing()
    
    def pause_typing(self):
        """Pause/Resume typing operation"""
        if not self.typing_active:
            return
            
        self.paused = not self.paused
        
        if self.paused:
            engine.pause_typing()
            self.status_label.configure(text="⏸ Paused", fg=COLORS['warning'])
            self.pause_btn.text_label.configure(text="Resume")
            self.update_overlay_status("Paused")
        else:
            engine.resume_typing()
            self.status_label.configure(text="⚡ Resumed", fg=COLORS['success'])
            self.pause_btn.text_label.configure(text="Pause")
            self.update_overlay_status("Typing...")
    
    def stop_typing(self):
        """Stop typing operation"""
        self.typing_active = False
        self.paused = False
        
        # Stop engine (check if we're in the typing thread)
        import threading
        current_thread = threading.current_thread()
        if current_thread.name != 'MainThread':
            # We're in the typing thread, schedule stop for main thread
            self.after(0, lambda: engine.stop_typing_func())
        else:
            # We're in main thread, safe to stop directly
            engine.stop_typing_func()
        
        # Update UI
        self.status_label.configure(text="⏹ Stopped", fg=COLORS['error'])
        self.start_btn.configure(state='normal')
        self.pause_btn.text_label.configure(text="Pause")
        self.pause_btn.configure(state='disabled')
        self.stop_btn.configure(state='disabled')
        
        # Reset progress
        self.progress_bar.set_progress(0)
        self.progress_label.configure(text="0%")
        self.progress_card.update_value("0")
        self.chars_label.configure(text="0/0")
        
        self.update_overlay_status("Ready")
    
    def update_preview(self, text):
        """Update preview area with typed text"""
        self.live_preview.text.config(state='normal')
        self.live_preview.delete('1.0', 'end')
        self.live_preview.insert('1.0', text)
        self.live_preview.text.config(state='disabled')
        
        # Update progress
        if self.total_chars > 0:
            self.chars_typed = len(text)
            progress = (self.chars_typed / self.total_chars) * 100
            
            # Update all progress indicators
            self.progress_bar.set_progress(progress)
            self.progress_label.configure(text=f"{int(progress)}%")
            self.progress_card.update_value(str(int(progress)))
            self.chars_label.configure(text=f"{self.chars_typed}/{self.total_chars}")
            
            # Update time remaining
            if self.chars_typed < self.total_chars:
                chars_left = self.total_chars - self.chars_typed
                avg_delay = (self.min_delay_var.get() + self.max_delay_var.get()) / 2
                seconds_left = chars_left * avg_delay
                
                minutes = int(seconds_left // 60)
                seconds = int(seconds_left % 60)
                self.time_label.configure(text=f"{minutes}:{seconds:02d}")
            else:
                self.time_label.configure(text="0:00")
                
            # Check if complete
            if progress >= 100:
                self.status_label.configure(text="✅ Complete!", fg=COLORS['success'])
                # Schedule stop_typing to run in main thread to avoid threading issues
                self.after(100, self.handle_typing_complete)
    
    def update_status(self, message):
        """Update status from engine"""
        self.status_label.configure(text=message)
        self.update_overlay_status(message)
    
    def update_overlay_status(self, message):
        """Update overlay if it exists"""
        try:
            if hasattr(self.app, 'tabs') and 'Overlay' in self.app.tabs:
                overlay_tab = self.app.tabs['Overlay']
                if hasattr(overlay_tab, 'update_overlay_text'):
                    # Format status for overlay
                    if self.typing_active:
                        status = f"{message} | {self.chars_typed}/{self.total_chars} chars | {int((self.chars_typed/max(1, self.total_chars))*100)}%"
                    else:
                        status = message
                    overlay_tab.update_overlay_text(status)
        except Exception as e:
            print(f"[MODERN TYPING] Error updating overlay: {e}")
    
    def load_file(self):
        """Load text from file"""
        file_path = filedialog.askopenfilename(
            title="Select Text File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_input.delete('1.0', 'end')
                    self.text_input.insert('1.0', content)
                    self.on_text_change()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
    
    def paste_clipboard(self):
        """Paste from clipboard"""
        try:
            text = self.clipboard_get()
            self.text_input.delete('1.0', 'end')
            self.text_input.insert('1.0', text)
            self.on_text_change()
        except:
            messagebox.showwarning("Clipboard", "No text in clipboard")
    
    def clear_text_areas(self):
        """Clear all text areas"""
        self.text_input.delete('1.0', 'end')
        self.live_preview.text.config(state='normal')
        self.live_preview.delete('1.0', 'end')
        self.live_preview.text.config(state='disabled')
        
        # Reset stats
        self.chars_card.update_value("0")
        self.time_card.update_value("0:00")
        self.progress_bar.set_progress(0)
        self.chars_typed = 0
        self.total_chars = 0
    
    def show_ai_filler_info(self):
        """Show information about AI filler feature"""
        info_text = """🤖 AI Filler Text (Premium Feature)

This advanced feature makes your typing appear even more human-like by:

• Generating realistic "false starts" and rewrites
• Adding thoughtful pauses as if reconsidering wording  
• Typing temporary filler text then deleting it
• Creating natural typing patterns that mimic real human behavior

The AI generates contextually relevant filler phrases that match your text, 
making it appear as if you're naturally composing and editing as you type.

Perfect for avoiding detection by advanced monitoring systems.

⚠️ Premium users only - Upgrade to unlock this feature!"""
        
        messagebox.showinfo("AI Filler Text", info_text)
    
    # Compatibility methods for app integration
    def update_placeholder_color(self):
        """Compatibility method"""
        pass
    
    def set_theme(self, dark_mode):
        """Theme compatibility"""
        pass
    
    def _handle_undo(self, event):
        """Handle undo"""
        try:
            self.text_input.text.edit_undo()
        except:
            pass
        return 'break'
    
    def _handle_redo(self, event):
        """Handle redo"""
        try:
            self.text_input.text.edit_redo()
        except:
            pass
        return 'break'
    
    def handle_typing_complete(self):
        """Handle typing completion in main thread"""
        self.typing_active = False
        self.paused = False
        
        # Update UI
        self.start_btn.configure(state='normal')
        self.pause_btn.text_label.configure(text="Pause")
        self.pause_btn.configure(state='disabled')
        self.stop_btn.configure(state='disabled')
        
        # Update overlay
        self.update_overlay_status("Complete!")
        
        # Note: Don't call engine.stop_typing_func() here as typing already finished