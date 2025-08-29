# tab_typing_modern.py - Ultra-modern typing tab with 2025 aesthetics

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import typing_logic
from modern_ui_2025 import *
try:
    from utils import is_premium_user as _is_premium_user
    def is_premium_user(app=None):
        """Wrapper for is_premium_user that handles app parameter"""
        if app:
            return _is_premium_user(app)
        return True  # Default to True if no app provided
except ImportError:
    def is_premium_user(app=None):
        return True  # Default to True for testing

class ModernTypingTab(tk.Frame):
    """Modern typing tab with 2025 UI design"""
    
    PLACEHOLDER_INPUT = "Start typing or paste your text here..."
    PLACEHOLDER_PREVIEW = "Live preview will appear as you type..."
    
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS['background'])
        self.app = app
        self.paused = False
        
        # Control variables
        self.min_delay_var = tk.DoubleVar(value=0.05)
        self.max_delay_var = tk.DoubleVar(value=0.15)
        self.pause_freq_var = tk.IntVar(value=5)
        self.typos_var = tk.BooleanVar(value=False)
        self.preview_only_var = tk.BooleanVar(value=False)
        self.adv_antidetect_var = tk.BooleanVar(value=False)
        
        self.loading_profile = False
        
        # Build the modern UI
        try:
            self.build_ui()
        except Exception as e:
            print(f"[MODERN TYPING] Critical error building UI: {e}")
            # Create minimal fallback UI
            self._create_fallback_ui()
        
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
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(
            int(-1*(e.delta/120)), "units"))
        
        # Main container inside scrollable frame
        main_container = tk.Frame(self.scrollable_frame, bg=COLORS['background'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Top stats row
        self.build_stats_row(main_container)
        
        # Main content area with two columns
        content_frame = tk.Frame(main_container, bg=COLORS['background'])
        content_frame.pack(fill='both', expand=True, pady=(20, 0))
        
        # Left column - Input and Preview
        left_column = tk.Frame(content_frame, bg=COLORS['background'])
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        self.build_input_section(left_column)
        self.build_preview_section(left_column)
        
        # Right column - Simple Controls at top
        right_column = tk.Frame(content_frame, bg=COLORS['background'])
        right_column.pack(side='right', fill='y', padx=(10, 0))
        
        self.build_simple_controls(right_column)
        
        # Speed controls section below main content
        speed_section = tk.Frame(main_container, bg=COLORS['background'])
        speed_section.pack(fill='x', pady=(20, 0))
        
        self.build_speed_controls(speed_section)
    
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
                                  value="0", unit="min", icon="⏱")
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
        
        # Progress bar
        self.progress_bar = ModernProgressBar(preview_card.content)
        self.progress_bar.pack(fill='x', pady=(0, 10))
        
        # Modern preview text area
        self.live_preview = ModernTextArea(preview_card.content, height=8,
                                          placeholder=self.PLACEHOLDER_PREVIEW)
        self.live_preview.pack(fill='both', expand=True)
        self.live_preview.text.config(state='disabled')  # Make it read-only
        
        # Status label
        self.status_label = tk.Label(preview_card.content, 
                                    text="Ready to type",
                                    font=('Segoe UI', 10, 'italic'),
                                    fg=COLORS['text_secondary'],
                                    bg=COLORS['surface'])
        self.status_label.pack(pady=(10, 0))
    
    def build_simple_controls(self, parent):
        """Build simplified action controls - just Start/Pause/Stop"""
        # Controls Card
        controls_card = GlassmorphicCard(parent, title="🎮 Controls", width=250)
        controls_card.pack(fill='x')
        
        # Start Button
        self.start_btn = ModernButton(controls_card.content, text="Start Typing", 
                                     icon="▶", command=self.start_typing, 
                                     variant="success", width=200)
        self.start_btn.pack(pady=(10, 8))
        
        # Pause Button
        self.pause_btn = ModernButton(controls_card.content, text="Pause", 
                                     icon="⏸", command=self.pause_typing,
                                     variant="primary", width=200)
        self.pause_btn.pack(pady=8)
        
        # Stop Button
        self.stop_btn = ModernButton(controls_card.content, text="Stop", 
                                    icon="⏹", command=self.stop_typing,
                                    variant="danger", width=200)
        self.stop_btn.pack(pady=(8, 10))
    
    def build_speed_controls(self, parent):
        """Build speed and feature controls in a horizontal layout"""
        # Speed Controls Card
        speed_card = GlassmorphicCard(parent, title="⚡ Speed & Features")
        speed_card.pack(fill='x')
        
        # Create two columns for controls
        controls_container = tk.Frame(speed_card.content, bg=COLORS['surface'])
        controls_container.pack(fill='both', expand=True)
        
        # Left side - Speed sliders
        left_frame = tk.Frame(controls_container, bg=COLORS['surface'])
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 20))
        
        # Min Delay Slider
        self.min_delay_slider = ModernSlider(left_frame,
                                            from_=0.01, to=0.5,
                                            variable=self.min_delay_var,
                                            label="Min Delay", unit="s")
        self.min_delay_slider.pack(fill='x', pady=(0, 15))
        
        # Max Delay Slider
        self.max_delay_slider = ModernSlider(left_frame,
                                            from_=0.05, to=1.0,
                                            variable=self.max_delay_var,
                                            label="Max Delay", unit="s")
        self.max_delay_slider.pack(fill='x', pady=(0, 15))
        
        # Pause Frequency Slider
        self.pause_freq_slider = ModernSlider(left_frame,
                                             from_=0, to=20,
                                             variable=self.pause_freq_var,
                                             label="Pause Frequency", unit="")
        self.pause_freq_slider.pack(fill='x')
        
        # Right side - Feature toggles
        right_frame = tk.Frame(controls_container, bg=COLORS['surface'])
        right_frame.pack(side='right', fill='y', padx=(20, 0))
        
        features_label = tk.Label(right_frame, text="Features",
                                 font=('Segoe UI', 11, 'bold'),
                                 fg=COLORS['text_primary'], bg=COLORS['surface'])
        features_label.pack(anchor='w', pady=(0, 15))
        
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
        
        # Advanced Anti-detect Toggle (Premium)
        if is_premium_user(self.app):
            antidetect_frame = tk.Frame(right_frame, bg=COLORS['surface'])
            antidetect_frame.pack(fill='x', pady=(0, 12))
            
            label_frame = tk.Frame(antidetect_frame, bg=COLORS['surface'])
            label_frame.pack(side='left')
            
            tk.Label(label_frame, text="Advanced Anti-detect",
                    font=('Segoe UI', 10), fg=COLORS['accent'],
                    bg=COLORS['surface']).pack(side='left')
            
            tk.Label(label_frame, text="PRO",
                    font=('Segoe UI', 8, 'bold'), fg=COLORS['warning'],
                    bg=COLORS['surface']).pack(side='left', padx=(5, 0))
            
            ModernToggle(antidetect_frame, variable=self.adv_antidetect_var).pack(side='right', padx=(20, 0))
        
        # WPM Display
        wpm_frame = tk.Frame(right_frame, bg=COLORS['surface'])
        wpm_frame.pack(fill='x', pady=(20, 0))
        
        tk.Label(wpm_frame, text="Current Speed:",
                font=('Segoe UI', 10), fg=COLORS['text_dim'],
                bg=COLORS['surface']).pack(side='left')
        
        self.wpm_label = tk.Label(wpm_frame, text="0 WPM",
                                 font=('Segoe UI', 12, 'bold'), 
                                 fg=COLORS['primary'],
                                 bg=COLORS['surface'])
        self.wpm_label.pack(side='right')
    
    def build_controls_section(self, parent):
        """Legacy method for compatibility"""
        # Controls Card
        controls_card = GlassmorphicCard(parent, title="⚙ Controls", width=350)
        controls_card.pack(fill='y')
        
        # Action Buttons
        actions_frame = tk.Frame(controls_card.content, bg=COLORS['surface'])
        actions_frame.pack(fill='x', pady=(0, 20))
        
        self.start_btn = ModernButton(actions_frame, text="Start Typing", 
                                     icon="▶", command=self.start_typing, 
                                     variant="success", width=150)
        self.start_btn.pack(pady=(0, 10))
        
        button_row = tk.Frame(actions_frame, bg=COLORS['surface'])
        button_row.pack()
        
        self.pause_btn = ModernButton(button_row, text="Pause", 
                                     icon="⏸", command=self.pause_typing,
                                     variant="primary", width=70)
        self.pause_btn.pack(side='left', padx=(0, 10))
        
        self.stop_btn = ModernButton(button_row, text="Stop", 
                                    icon="⏹", command=self.stop_typing,
                                    variant="danger", width=70)
        self.stop_btn.pack(side='left')
        
        # Separator
        sep = tk.Frame(controls_card.content, height=1, bg=COLORS['border'])
        sep.pack(fill='x', pady=20)
        
        # Speed Controls
        speed_label = tk.Label(controls_card.content, text="⚡ Speed Settings",
                              font=('Segoe UI', 11, 'bold'),
                              fg=COLORS['text_primary'], bg=COLORS['surface'])
        speed_label.pack(anchor='w', pady=(0, 15))
        
        # Min Delay Slider
        self.min_delay_slider = ModernSlider(controls_card.content,
                                            from_=0.01, to=0.5,
                                            variable=self.min_delay_var,
                                            label="Min Delay", unit="s")
        self.min_delay_slider.pack(fill='x', pady=(0, 15))
        
        # Max Delay Slider
        self.max_delay_slider = ModernSlider(controls_card.content,
                                            from_=0.05, to=1.0,
                                            variable=self.max_delay_var,
                                            label="Max Delay", unit="s")
        self.max_delay_slider.pack(fill='x', pady=(0, 15))
        
        # Pause Frequency Slider
        self.pause_freq_slider = ModernSlider(controls_card.content,
                                             from_=0, to=20,
                                             variable=self.pause_freq_var,
                                             label="Pause Frequency", unit="")
        self.pause_freq_slider.pack(fill='x', pady=(0, 20))
        
        # Separator
        sep2 = tk.Frame(controls_card.content, height=1, bg=COLORS['border'])
        sep2.pack(fill='x', pady=20)
        
        # Features
        features_label = tk.Label(controls_card.content, text="✨ Features",
                                 font=('Segoe UI', 11, 'bold'),
                                 fg=COLORS['text_primary'], bg=COLORS['surface'])
        features_label.pack(anchor='w', pady=(0, 15))
        
        # Typos Toggle
        typos_frame = tk.Frame(controls_card.content, bg=COLORS['surface'])
        typos_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(typos_frame, text="Random Typos",
                font=('Segoe UI', 10), fg=COLORS['text_secondary'],
                bg=COLORS['surface']).pack(side='left')
        
        ModernToggle(typos_frame, variable=self.typos_var).pack(side='right')
        
        # Preview Only Toggle
        preview_frame = tk.Frame(controls_card.content, bg=COLORS['surface'])
        preview_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(preview_frame, text="Preview Only",
                font=('Segoe UI', 10), fg=COLORS['text_secondary'],
                bg=COLORS['surface']).pack(side='left')
        
        ModernToggle(preview_frame, variable=self.preview_only_var).pack(side='right')
        
        # Advanced Anti-detect Toggle (Premium)
        if is_premium_user(self.app):
            antidetect_frame = tk.Frame(controls_card.content, bg=COLORS['surface'])
            antidetect_frame.pack(fill='x', pady=(0, 10))
            
            tk.Label(antidetect_frame, text="Advanced Anti-detect",
                    font=('Segoe UI', 10), fg=COLORS['accent'],
                    bg=COLORS['surface']).pack(side='left')
            
            tk.Label(antidetect_frame, text="PRO",
                    font=('Segoe UI', 8, 'bold'), fg=COLORS['warning'],
                    bg=COLORS['surface']).pack(side='left', padx=5)
            
            ModernToggle(antidetect_frame, variable=self.adv_antidetect_var).pack(side='right')
        
        # WPM Display
        sep3 = tk.Frame(controls_card.content, height=1, bg=COLORS['border'])
        sep3.pack(fill='x', pady=(20, 10))
        
        wpm_frame = tk.Frame(controls_card.content, bg=COLORS['surface'])
        wpm_frame.pack(fill='x')
        
        tk.Label(wpm_frame, text="Current Speed:",
                font=('Segoe UI', 10), fg=COLORS['text_dim'],
                bg=COLORS['surface']).pack(side='left')
        
        self.wpm_label = tk.Label(wpm_frame, text="0 WPM",
                                 font=('Segoe UI', 12, 'bold'), 
                                 fg=COLORS['primary'],
                                 bg=COLORS['surface'])
        self.wpm_label.pack(side='right')
    
    def setup_callbacks(self):
        """Setup variable callbacks"""
        for var in [self.min_delay_var, self.max_delay_var, 
                   self.pause_freq_var, self.typos_var,
                   self.preview_only_var, self.adv_antidetect_var]:
            var.trace_add('write', lambda *args: self.on_setting_change())
        
        # Text change callback
        self.text_input.text.bind("<<Modified>>", self.on_text_change)
    
    def on_setting_change(self):
        """Handle setting changes"""
        if not self.loading_profile:
            self.app.on_setting_change()
            self.update_wpm()
    
    def on_text_change(self, event=None):
        """Handle text input changes"""
        text = self.text_input.get('1.0', 'end-1c')
        if text and text != self.text_input.placeholder:
            # Update character count
            self.chars_card.update_value(str(len(text)))
            
            # Update estimated time
            wpm = self.calculate_wpm()
            if wpm > 0:
                words = len(text.split())
                minutes = words / wpm
                self.time_card.update_value(f"{minutes:.1f}")
        else:
            self.chars_card.update_value("0")
            self.time_card.update_value("0")
    
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
        self.wpm_label.configure(text=f"{wpm} WPM")
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
        
        # Update status
        self.status_label.configure(text="⚡ Typing in progress...", 
                                   fg=COLORS['success'])
        
        # Update buttons
        self.start_btn.text_label.configure(text="Running...")
        
        # Start typing logic
        if hasattr(self.app, 'start_typing'):
            self.app.start_typing()
        else:
            # Compatibility with different app structures
            import typing_engine as engine
            engine.start_typing(self)
    
    def pause_typing(self):
        """Pause typing operation"""
        self.paused = not self.paused
        if self.paused:
            self.status_label.configure(text="⏸ Paused", fg=COLORS['warning'])
            self.pause_btn.text_label.configure(text="Resume")
        else:
            self.status_label.configure(text="⚡ Resumed", fg=COLORS['success'])
            self.pause_btn.text_label.configure(text="Pause")
        
        # Toggle pause in engine
        import typing_engine as engine
        if hasattr(engine, 'pause_flag'):
            if self.paused:
                engine.pause_flag.set()
            else:
                engine.pause_flag.clear()
    
    def stop_typing(self):
        """Stop typing operation"""
        self.status_label.configure(text="⏹ Stopped", fg=COLORS['error'])
        self.start_btn.text_label.configure(text="Start Typing")
        self.progress_bar.set_progress(0)
        
        if hasattr(self.app, 'stop_typing'):
            self.app.stop_typing()
        else:
            # Compatibility with different app structures
            import typing_engine as engine
            engine.stop_typing()
    
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
        self.chars_card.update_value("0")
        self.time_card.update_value("0")
        self.progress_bar.set_progress(0)
    
    def update_preview(self, text, progress=0):
        """Update preview area"""
        self.live_preview.text.config(state='normal')
        self.live_preview.delete('1.0', 'end')
        self.live_preview.insert('1.0', text)
        self.live_preview.text.config(state='disabled')
        
        # Update progress
        self.progress_bar.set_progress(progress)
        self.progress_card.update_value(str(int(progress)))
    
    def _create_fallback_ui(self):
        """Create minimal fallback UI if modern UI fails"""
        print("[MODERN TYPING] Creating fallback UI")
        
        # Simple label to show something
        label = tk.Label(self, text="Modern Typing Tab (Loading...)",
                        font=('Segoe UI', 14), fg='white', bg='#0A0A0F')
        label.pack(pady=50)
        
        # Basic text area
        self.text_input = tk.Text(self, height=10, width=60)
        self.text_input.pack(pady=10)
        
        self.live_preview = tk.Text(self, height=10, width=60, state='disabled')
        self.live_preview.pack(pady=10)
    
    # Add any other required methods for compatibility
    def update_placeholder_color(self):
        """Compatibility method"""
        pass
    
    def set_theme(self, dark_mode):
        """Theme compatibility"""
        pass