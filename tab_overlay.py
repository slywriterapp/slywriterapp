# tab_overlay.py

import tkinter as tk
from tkinter import ttk
import config

class OverlayTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.overlay_enabled = tk.BooleanVar(value=False)
        self.overlay_opacity = tk.DoubleVar(value=0.9)
        self.overlay_width = tk.IntVar(value=300)
        self.overlay_height = tk.IntVar(value=60)
        self.overlay_x = tk.IntVar(value=50)  # Distance from right edge
        self.overlay_y = tk.IntVar(value=50)  # Distance from top
        self.overlay_window = None
        self.overlay_label = None
        
        self.build_ui()
        
        # Load overlay setting from config
        self.load_from_config()
        
        # Listen for setting changes
        self.overlay_enabled.trace_add('write', lambda *a: self._on_overlay_toggle())
        self.overlay_opacity.trace_add('write', lambda *a: self._on_opacity_change())
        self.overlay_width.trace_add('write', lambda *a: self._on_size_change())
        self.overlay_height.trace_add('write', lambda *a: self._on_size_change())
    
    def build_ui(self):
        # Title with logo
        title_frame = tk.Frame(self)
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
            fg=config.LIME_GREEN
        )
        title_label.pack(side='left')
        
        # Description
        desc_label = tk.Label(
            self,
            text="Display a floating overlay showing what the typing engine is currently doing.\nDraggable overlay window shows typing status in real-time. Right-click to close.",
            font=('Segoe UI', 10),
            justify='center',
            wraplength=400
        )
        desc_label.pack(pady=(0, 20))
        
        # Toggle switch
        toggle_frame = tk.Frame(self)
        toggle_frame.pack(pady=20)
        
        tk.Label(toggle_frame, text="Enable Overlay:", font=('Segoe UI', 12)).pack(side='left', padx=(0, 10))
        
        self.overlay_check = tk.Checkbutton(
            toggle_frame,
            text="ON/OFF",
            variable=self.overlay_enabled,
            font=('Segoe UI', 12, 'bold'),
            fg=config.LIME_GREEN
        )
        self.overlay_check.pack(side='left')
        
        # Opacity control
        opacity_frame = tk.Frame(self)
        opacity_frame.pack(pady=10)
        
        tk.Label(opacity_frame, text="Overlay Opacity:", font=('Segoe UI', 11)).pack(anchor='w')
        
        opacity_control_frame = tk.Frame(opacity_frame)
        opacity_control_frame.pack(fill='x', pady=5)
        
        self.opacity_scale = tk.Scale(
            opacity_control_frame,
            from_=0.3,
            to=1.0,
            resolution=0.1,
            orient='horizontal',
            variable=self.overlay_opacity,
            command=self._on_opacity_change,
            length=200
        )
        self.opacity_scale.pack(side='left')
        
        self.opacity_value_label = tk.Label(opacity_control_frame, text="90%", font=('Segoe UI', 10))
        self.opacity_value_label.pack(side='left', padx=(10, 0))
        
        # Size controls
        size_frame = tk.Frame(self)
        size_frame.pack(pady=10)
        
        tk.Label(size_frame, text="Overlay Size:", font=('Segoe UI', 11)).pack(anchor='w')
        
        # Width control
        width_control_frame = tk.Frame(size_frame)
        width_control_frame.pack(fill='x', pady=2)
        
        tk.Label(width_control_frame, text="Width:", font=('Segoe UI', 9)).pack(side='left')
        
        self.width_scale = tk.Scale(
            width_control_frame,
            from_=200,
            to=500,
            resolution=10,
            orient='horizontal',
            variable=self.overlay_width,
            command=self._on_size_change,
            length=150
        )
        self.width_scale.pack(side='left', padx=(5, 5))
        
        self.width_value_label = tk.Label(width_control_frame, text="300px", font=('Segoe UI', 9))
        self.width_value_label.pack(side='left')
        
        # Height control  
        height_control_frame = tk.Frame(size_frame)
        height_control_frame.pack(fill='x', pady=2)
        
        tk.Label(height_control_frame, text="Height:", font=('Segoe UI', 9)).pack(side='left')
        
        self.height_scale = tk.Scale(
            height_control_frame,
            from_=40,
            to=120,
            resolution=5,
            orient='horizontal',
            variable=self.overlay_height,
            command=self._on_size_change,
            length=150
        )
        self.height_scale.pack(side='left', padx=(5, 5))
        
        self.height_value_label = tk.Label(height_control_frame, text="60px", font=('Segoe UI', 9))
        self.height_value_label.pack(side='left')
        
        # Reset position button
        reset_frame = tk.Frame(self)
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
            self,
            text="Overlay: Disabled",
            font=('Segoe UI', 10, 'italic'),
            fg="#888888"
        )
        self.status_label.pack(pady=(20, 0))
        
        # Preview area
        preview_frame = tk.LabelFrame(self, text="Overlay Preview", font=('Segoe UI', 10, 'bold'))
        preview_frame.pack(pady=(30, 20), padx=20, fill='x')
        
        self.preview_label = tk.Label(
            preview_frame,
            text="SlyWriter Status: Ready",
            font=('Segoe UI', 11, 'bold'),
            fg=config.LIME_GREEN,
            bg="#000000",
            padx=10,
            pady=5
        )
        self.preview_label.pack(pady=10)
    
    def _on_overlay_toggle(self):
        if self.overlay_enabled.get():
            self._create_overlay()
            self.status_label.config(text="Overlay: Enabled", fg=config.LIME_GREEN)
        else:
            self._destroy_overlay()
            self.status_label.config(text="Overlay: Disabled", fg="#888888")
        
        # Save setting
        if hasattr(self.app, 'on_setting_change'):
            self.app.on_setting_change()
    
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
        
        # Create overlay content
        overlay_frame = tk.Frame(self.overlay_window, bg="#000000", bd=2, relief="ridge")
        overlay_frame.pack(fill='both', expand=True)
        
        # Create status frame with logo and text
        status_frame = tk.Frame(overlay_frame, bg="#000000")
        status_frame.pack(expand=True, fill='both')
        
        # No logo needed - just clean text display
        
        # Status text - centered without logo
        self.overlay_label = tk.Label(
            status_frame,
            text="SlyWriter: Ready",
            font=('Segoe UI', 11, 'bold'),
            fg=config.LIME_GREEN,
            bg="#000000",
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
    
    def update_overlay_text(self, text):
        """Update the overlay text (called by typing engine)"""
        if self.overlay_label:
            self.overlay_label.config(text=f"SlyWriter: {text}")
        # Also update preview
        self.preview_label.config(text=f"SlyWriter Status: {text}")
    
    def set_theme(self, dark_mode):
        """Update theme colors"""
        bg_color = "#181816" if dark_mode else "#ffffff"
        fg_color = "#ffffff" if dark_mode else "#000000"
        
        self.config(bg=bg_color)
        # Update other widgets as needed
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=bg_color)
            elif isinstance(widget, tk.Frame):
                widget.config(bg=bg_color)
                # Update frame children too
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        child.config(bg=bg_color)
    
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
            
            # Update UI labels
            self.width_value_label.config(text=f"{overlay_width}px")
            self.height_value_label.config(text=f"{overlay_height}px")
            
            # Trigger overlay creation if it was enabled
            if overlay_enabled:
                self._on_overlay_toggle()