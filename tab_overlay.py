# tab_overlay.py

import tkinter as tk
from tkinter import ttk
import config

class OverlayTab(tk.Frame):
    def __init__(self, parent, app):
        # Get theme colors
        dark = app.cfg.get('settings', {}).get('dark_mode', True)
        bg_color = "#181816" if dark else "#ffffff"
        
        super().__init__(parent, bg=bg_color)
        self.app = app
        
        # Create scrollable container for premium app
        is_premium = hasattr(app, 'tabs') and hasattr(app, 'sidebar')
        if is_premium:
            # Create canvas and scrollbar for scrolling
            self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
            self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
            
            self.scrollable_frame.bind(
                "<Configure>",
                lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            )
            
            self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
            self.canvas.configure(yscrollcommand=self.scrollbar.set)
            
            self.canvas.pack(side="left", fill="both", expand=True)
            self.scrollbar.pack(side="right", fill="y")
            
            # Use scrollable_frame as the parent for widgets
            self.widget_parent = self.scrollable_frame
        else:
            # For standalone use, no scrolling needed
            self.widget_parent = self
        self.overlay_enabled = tk.BooleanVar(value=False)
        self.overlay_opacity = tk.DoubleVar(value=0.9)
        self.overlay_width = tk.IntVar(value=400)  # Increased for longer messages
        self.overlay_height = tk.IntVar(value=80)  # Increased for better visibility
        self.overlay_x = tk.IntVar(value=50)  # Distance from right edge
        self.overlay_y = tk.IntVar(value=50)  # Distance from top
        self.overlay_window = None
        self.overlay_label = None
        
        self.build_ui()
        
        # Load overlay setting from config (after UI is built)
        self.load_from_config()
        
        # Listen for setting changes
        self.overlay_enabled.trace_add('write', lambda *a: self._on_overlay_toggle())
        self.overlay_opacity.trace_add('write', lambda *a: self._on_opacity_change())
        self.overlay_width.trace_add('write', lambda *a: self._on_size_change())
        self.overlay_height.trace_add('write', lambda *a: self._on_size_change())
    
    def build_ui(self):
        print("[OVERLAY] Starting build_ui()")
        # Get theme colors
        dark = self.app.cfg.get('settings', {}).get('dark_mode', True)
        bg_color = "#181816" if dark else "#ffffff"
        fg_color = "#ffffff" if dark else "#000000"
        print(f"[OVERLAY] Theme colors - bg: {bg_color}, fg: {fg_color}")
        
        # Don't add title/description in premium app - it's handled by the wrapper
        # Check if we're in premium app by looking for specific attributes
        is_premium = hasattr(self.app, 'tabs') and hasattr(self.app, 'sidebar')
        
        if not is_premium:
            # Only add title and description for standalone use
            # Title with logo
            title_frame = tk.Frame(self.widget_parent, bg=bg_color)
            title_frame.pack(pady=(20, 10))
            
            try:
                from PIL import Image, ImageTk
                # Load and resize logo
                logo_image = Image.open("slywriter_logo.png")
                logo_image = logo_image.resize((32, 32), Image.Resampling.LANCZOS)
                self.overlay_logo_photo = ImageTk.PhotoImage(logo_image)
                
                logo_label = tk.Label(title_frame, image=self.overlay_logo_photo)
                logo_label.pack(side='left', padx=(0, 10))
            except Exception:
                pass  # Logo is optional here
            
            title_label = tk.Label(
                title_frame, 
                text="SlyWriter Overlay",
                font=('Segoe UI', 16, 'bold'),
                fg=config.ACCENT_PURPLE,
                bg=bg_color
            )
            title_label.pack(side='left')
            
            # Description
            desc_label = tk.Label(
                self.widget_parent,
                text="Display a floating overlay showing what the typing engine is currently doing.\nDraggable overlay window shows typing status in real-time. Right-click to close.",
                font=('Segoe UI', 10),
                justify='center',
                wraplength=400,
                bg=bg_color,
                fg=fg_color
            )
            desc_label.pack(pady=(0, 20))
        
        # Toggle switch
        toggle_frame = tk.Frame(self.widget_parent, bg=bg_color)
        toggle_frame.pack(pady=20)
        
        tk.Label(toggle_frame, text="Enable Overlay:", font=('Segoe UI', 12),
                bg=bg_color, fg=fg_color).pack(side='left', padx=(0, 10))
        
        self.overlay_check = tk.Checkbutton(
            toggle_frame,
            text="ON/OFF",
            variable=self.overlay_enabled,
            font=('Segoe UI', 12, 'bold'),
            fg=config.ACCENT_PURPLE,
            bg=bg_color,
            selectcolor=bg_color,
            activebackground=bg_color
        )
        self.overlay_check.pack(side='left')
        
        # Opacity control with modern styling
        opacity_frame = tk.Frame(self.widget_parent, bg=bg_color)
        opacity_frame.pack(pady=15, padx=20, fill='x')
        
        tk.Label(opacity_frame, text="Overlay Opacity:", font=('Segoe UI', 12, 'bold'),
                bg=bg_color, fg=config.ACCENT_PURPLE).pack(anchor='w', pady=(0, 5))
        
        opacity_control_frame = tk.Frame(opacity_frame, bg=bg_color)
        opacity_control_frame.pack(fill='x', pady=5)
        
        self.opacity_scale = tk.Scale(
            opacity_control_frame,
            from_=0.3,
            to=1.0,
            resolution=0.05,
            orient='horizontal',
            variable=self.overlay_opacity,
            command=self._on_opacity_change,
            length=250,
            bg='#2A2B4E',
            fg='#FFFFFF',
            troughcolor=config.ACCENT_PURPLE,
            activebackground='#8B5CF6',
            highlightthickness=0,
            sliderrelief='raised',
            width=15
        )
        self.opacity_scale.pack(side='left')
        print(f"[OVERLAY] Created opacity scale: {self.opacity_scale}")
        
        self.opacity_value_label = tk.Label(opacity_control_frame, text="90%", font=('Segoe UI', 11, 'bold'),
                                           bg=bg_color, fg='#FFFFFF')
        self.opacity_value_label.pack(side='left', padx=(15, 0))
        
        # Size controls with modern styling
        size_frame = tk.Frame(self.widget_parent, bg=bg_color)
        size_frame.pack(pady=15, padx=20, fill='x')
        
        tk.Label(size_frame, text="Overlay Size:", font=('Segoe UI', 12, 'bold'),
                bg=bg_color, fg=config.ACCENT_PURPLE).pack(anchor='w', pady=(0, 10))
        
        # Width control with modern styling
        width_control_frame = tk.Frame(size_frame, bg=bg_color)
        width_control_frame.pack(fill='x', pady=5)
        
        tk.Label(width_control_frame, text="Width:", font=('Segoe UI', 10),
                bg=bg_color, fg='#B4B4B8').pack(side='left', padx=(0, 10))
        
        self.width_scale = tk.Scale(
            width_control_frame,
            from_=200,
            to=600,
            resolution=10,
            orient='horizontal',
            variable=self.overlay_width,
            command=self._on_size_change,
            length=200,
            bg='#2A2B4E',
            fg='#FFFFFF',
            troughcolor=config.ACCENT_PURPLE,
            activebackground='#8B5CF6',
            highlightthickness=0,
            sliderrelief='raised',
            width=15
        )
        self.width_scale.pack(side='left', padx=(5, 5))
        
        self.width_value_label = tk.Label(width_control_frame, text="300px", font=('Segoe UI', 10, 'bold'),
                                         bg=bg_color, fg='#FFFFFF')
        self.width_value_label.pack(side='left', padx=(10, 0))
        
        # Height control with modern styling
        height_control_frame = tk.Frame(size_frame, bg=bg_color)
        height_control_frame.pack(fill='x', pady=5)
        
        tk.Label(height_control_frame, text="Height:", font=('Segoe UI', 10),
                bg=bg_color, fg='#B4B4B8').pack(side='left', padx=(0, 10))
        
        self.height_scale = tk.Scale(
            height_control_frame,
            from_=40,
            to=150,
            resolution=5,
            orient='horizontal',
            variable=self.overlay_height,
            command=self._on_size_change,
            length=200,
            bg='#2A2B4E',
            fg='#FFFFFF',
            troughcolor=config.ACCENT_PURPLE,
            activebackground='#8B5CF6',
            highlightthickness=0,
            sliderrelief='raised',
            width=15
        )
        self.height_scale.pack(side='left', padx=(5, 5))
        
        self.height_value_label = tk.Label(height_control_frame, text="60px", font=('Segoe UI', 10, 'bold'),
                                          bg=bg_color, fg='#FFFFFF')
        self.height_value_label.pack(side='left', padx=(10, 0))
        
        # Reset position button
        reset_frame = tk.Frame(self.widget_parent, bg=bg_color)
        reset_frame.pack(pady=10)
        
        self.reset_position_btn = tk.Button(
            reset_frame,
            text="Reset Position",
            command=self._reset_overlay_position,
            font=('Segoe UI', 10),
            bg="#003366",
            fg="white",
            activebackground="#001a33",
            activeforeground="white",
            relief="raised",
            borderwidth=2
        )
        self.reset_position_btn.pack()
        
        # Status info
        self.status_label = tk.Label(
            self.widget_parent,
            text="Overlay: Disabled",
            font=('Segoe UI', 10, 'italic'),
            fg="#888888",
            bg=bg_color
        )
        self.status_label.pack(pady=(20, 0))
        
        # Preview area
        preview_frame = tk.LabelFrame(self.widget_parent, text="Overlay Preview", font=('Segoe UI', 10, 'bold'),
                                     bg=bg_color, fg=fg_color)
        preview_frame.pack(pady=(30, 20), padx=20, fill='x')
        
        print("[OVERLAY] Finished build_ui() - all widgets created")
        
        self.preview_label = tk.Label(
            preview_frame,
            text="SlyWriter Status: Ready",
            font=('Segoe UI', 11, 'bold'),
            fg=config.ACCENT_PURPLE,
            bg="#1A1B3E",  # Changed from black to dark blue theme color
            padx=10,
            pady=5
        )
        self.preview_label.pack(pady=10)
    
    def _on_overlay_toggle(self):
        if self.overlay_enabled.get():
            self._create_overlay()
            # Force purple color after creation to prevent theme override
            if self.overlay_label:
                self.overlay_label.config(fg=config.ACCENT_PURPLE, bg="#1A1B3E")
            self.status_label.config(text="Overlay: Enabled", fg=config.ACCENT_PURPLE)
        else:
            self._destroy_overlay()
            self.status_label.config(text="Overlay: Disabled", fg="#888888")
        
        # Save setting
        if hasattr(self.app, 'on_setting_change'):
            self.app.on_setting_change()
        
        # Force overlay colors after any potential theme changes
        self._force_overlay_colors()
    
    def _on_opacity_change(self, value=None):
        """Handle opacity changes"""
        opacity = self.overlay_opacity.get()
        self.opacity_value_label.config(text=f"{int(opacity * 100)}%")
        
        # Update actual overlay if it exists
        if self.overlay_window:
            self.overlay_window.attributes('-alpha', opacity)
        
        # Save setting
        if hasattr(self.app, 'on_setting_change'):
            self.app.on_setting_change()
    
    def _on_size_change(self, value=None):
        """Handle size changes"""
        width = self.overlay_width.get()
        height = self.overlay_height.get()
        
        self.width_value_label.config(text=f"{width}px")
        self.height_value_label.config(text=f"{height}px")
        
        # Update actual overlay if it exists
        if self.overlay_window:
            # Get current position
            current_geo = self.overlay_window.geometry()
            if '+' in current_geo:
                # Extract position from geometry string like "300x60+1570+50"
                size_part, pos_part = current_geo.split('+', 1)
                x_pos, y_pos = pos_part.split('+')
                new_geometry = f"{width}x{height}+{x_pos}+{y_pos}"
                self.overlay_window.geometry(new_geometry)
        
        # Save setting
        if hasattr(self.app, 'on_setting_change'):
            self.app.on_setting_change()
    
    def _reset_overlay_position(self):
        """Reset overlay to default position (top-right corner)"""
        self.overlay_x.set(50)
        self.overlay_y.set(50)
        
        # Update actual overlay if it exists
        if self.overlay_window:
            width = self.overlay_width.get()
            height = self.overlay_height.get()
            x_pos = self.app.winfo_screenwidth() - width - 50
            y_pos = 50
            self.overlay_window.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
        
        # Save position
        if hasattr(self.app, 'on_setting_change'):
            self.app.on_setting_change()
    
    def _create_overlay(self):
        if self.overlay_window:
            return
            
        # Create overlay window
        self.overlay_window = tk.Toplevel(self.app)
        self.overlay_window.title("SlyWriter Overlay")
        self.overlay_window.overrideredirect(True)  # Remove window borders
        self.overlay_window.attributes('-topmost', True)  # Always on top
        self.overlay_window.attributes('-alpha', self.overlay_opacity.get())  # User-controlled transparency
        
        # Position overlay using stored position and size
        width = self.overlay_width.get()
        height = self.overlay_height.get()
        x_pos = self.app.winfo_screenwidth() - width - self.overlay_x.get()
        y_pos = self.overlay_y.get()
        self.overlay_window.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
        
        # Create overlay content with theme colors
        overlay_frame = tk.Frame(self.overlay_window, bg="#1A1B3E", bd=2, relief="ridge")
        overlay_frame.pack(fill='both', expand=True)
        
        # Create status frame with logo and text
        status_frame = tk.Frame(overlay_frame, bg="#1A1B3E")
        status_frame.pack(expand=True, fill='both')
        
        # No logo needed - just clean text display
        
        # Status text - centered without logo
        self.overlay_label = tk.Label(
            status_frame,
            text="SlyWriter: Ready",
            font=('Segoe UI', 11, 'bold'),
            fg=config.ACCENT_PURPLE,
            bg="#1A1B3E",  # Changed from black to dark blue theme color
            padx=10,
            pady=5
        )
        self.overlay_label.pack(expand=True, fill='both')
        
        # Make window draggable - bind to status frame so entire area is draggable
        status_frame.bind("<Button-1>", self._start_move)
        status_frame.bind("<B1-Motion>", self._do_move)
        self.overlay_label.bind("<Button-1>", self._start_move)
        self.overlay_label.bind("<B1-Motion>", self._do_move)
        
        # Close on right-click - bind to status frame so entire area works
        status_frame.bind("<Button-3>", lambda e: self.overlay_enabled.set(False))
        self.overlay_label.bind("<Button-3>", lambda e: self.overlay_enabled.set(False))
    
    def _destroy_overlay(self):
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None
            self.overlay_label = None
    
    def _start_move(self, event):
        self.overlay_window.x = event.x
        self.overlay_window.y = event.y
    
    def _do_move(self, event):
        deltax = event.x - self.overlay_window.x
        deltay = event.y - self.overlay_window.y
        x = self.overlay_window.winfo_x() + deltax
        y = self.overlay_window.winfo_y() + deltay
        self.overlay_window.geometry(f"+{x}+{y}")
        
        # Save new position (convert to distance from right edge and top)
        screen_width = self.app.winfo_screenwidth()
        width = self.overlay_width.get()
        self.overlay_x.set(screen_width - x - width)  # Distance from right edge
        self.overlay_y.set(y)  # Distance from top
        
        # Save position to config
        if hasattr(self.app, 'on_setting_change'):
            self.app.on_setting_change()
    
    def _force_overlay_colors(self):
        """Force overlay to maintain purple colors after theme changes"""
        if self.overlay_label:
            self.overlay_label.config(fg=config.ACCENT_PURPLE, bg="#1A1B3E")
        if hasattr(self, 'preview_label') and self.preview_label:
            self.preview_label.config(fg=config.ACCENT_PURPLE, bg="#1A1B3E")
    
    def update_overlay_text(self, text):
        """Update the overlay text (called by typing engine)"""
        if self.overlay_label:
            self.overlay_label.config(text=f"SlyWriter: {text}", fg=config.ACCENT_PURPLE, bg="#1A1B3E")
        # Also update preview
        self.preview_label.config(text=f"SlyWriter Status: {text}", fg=config.ACCENT_PURPLE, bg="#1A1B3E")
        # Force colors to ensure they persist
        self._force_overlay_colors()
    
    def set_theme(self, dark_mode):
        """Update theme colors"""
        bg_color = "#181816" if dark_mode else "#ffffff"
        fg_color = "#ffffff" if dark_mode else "#000000"
        
        self.config(bg=bg_color)
        
        # Recursively update all widgets
        self._apply_theme_to_widget(self, bg_color, fg_color)
    
    def _apply_theme_to_widget(self, widget, bg_color, fg_color):
        """Recursively apply theme to widget and all children"""
        try:
            # Apply to the widget itself
            if hasattr(widget, 'config'):
                if isinstance(widget, (tk.Label, tk.Frame, tk.LabelFrame, tk.Button, tk.Checkbutton)):
                    # Special handling for overlay-specific colored labels
                    if widget is self.preview_label:
                        # Keep preview label purple with theme background
                        widget.config(bg="#1A1B3E", fg=config.ACCENT_PURPLE)
                    elif hasattr(widget, 'cget') and 'SlyWriter' in widget.cget('text'):
                        # Keep any SlyWriter status labels purple  
                        widget.config(bg=bg_color, fg=config.ACCENT_PURPLE)
                    else:
                        # Standard theming for other widgets
                        widget.config(bg=bg_color, fg=fg_color)
                elif isinstance(widget, tk.Text):
                    widget.config(bg=bg_color, fg=fg_color, insertbackground=fg_color)
                elif isinstance(widget, tk.Scale):
                    # Special handling for Scale widgets to make them visible
                    import config
                    widget.config(
                        bg=bg_color,
                        fg=fg_color,
                        troughcolor=config.ACCENT_PURPLE,  # Purple trough for visibility
                        highlightbackground=bg_color,
                        activebackground=config.ACCENT_PURPLE,
                        sliderrelief='flat',
                        highlightthickness=0
                    )
            
            # Apply to all children
            for child in widget.winfo_children():
                self._apply_theme_to_widget(child, bg_color, fg_color)
                
        except Exception:
            pass  # Ignore any theme errors
    
    def load_from_config(self):
        """Load overlay settings from config"""
        if hasattr(self.app, 'cfg'):
            overlay_enabled = self.app.cfg['settings'].get('overlay_enabled', False)
            overlay_opacity = self.app.cfg['settings'].get('overlay_opacity', 0.9)
            overlay_width = self.app.cfg['settings'].get('overlay_width', 300)
            overlay_height = self.app.cfg['settings'].get('overlay_height', 60)
            overlay_x = self.app.cfg['settings'].get('overlay_x', 50)
            overlay_y = self.app.cfg['settings'].get('overlay_y', 50)
            
            self.overlay_enabled.set(overlay_enabled)
            self.overlay_opacity.set(overlay_opacity)
            self.overlay_width.set(overlay_width)
            self.overlay_height.set(overlay_height)
            self.overlay_x.set(overlay_x)
            self.overlay_y.set(overlay_y)
            
            # Update UI labels if they exist
            if hasattr(self, 'width_value_label'):
                self.width_value_label.config(text=f"{overlay_width}px")
            if hasattr(self, 'height_value_label'):
                self.height_value_label.config(text=f"{overlay_height}px")
            if hasattr(self, 'opacity_value_label'):
                self.opacity_value_label.config(text=f"{int(overlay_opacity * 100)}%")
            
            # Trigger overlay creation if it was enabled
            if overlay_enabled:
                self._on_overlay_toggle()