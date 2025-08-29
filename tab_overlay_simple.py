# tab_overlay_simple.py - Simplified version that will definitely work

import tkinter as tk
from tkinter import ttk
import config

class OverlayTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg='#181816')
        self.app = app
        
        # Variables
        self.overlay_enabled = tk.BooleanVar(value=False)
        self.overlay_opacity = tk.DoubleVar(value=0.9)
        self.overlay_width = tk.IntVar(value=400)
        self.overlay_height = tk.IntVar(value=80)
        self.overlay_x = tk.IntVar(value=50)
        self.overlay_y = tk.IntVar(value=50)
        self.overlay_window = None
        self.overlay_label = None
        
        # Build simple UI directly - no complications
        self.build_simple_ui()
        
        # Load settings after UI is built
        self.load_from_config()
        
        # Listen for changes
        self.overlay_enabled.trace_add('write', lambda *a: self._on_overlay_toggle())
        self.overlay_opacity.trace_add('write', lambda *a: self._on_opacity_change())
        self.overlay_width.trace_add('write', lambda *a: self._on_size_change())
        self.overlay_height.trace_add('write', lambda *a: self._on_size_change())
        
    def build_simple_ui(self):
        """Build a simple, guaranteed-to-work UI"""
        print("[OVERLAY] Building simple UI")
        
        # Main container with padding
        main_frame = tk.Frame(self, bg='#181816')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title = tk.Label(main_frame, text="Overlay Settings", 
                        font=('Segoe UI', 16, 'bold'), 
                        fg='#8B5CF6', bg='#181816')
        title.pack(anchor='w', pady=(0, 20))
        
        # Toggle
        toggle_frame = tk.Frame(main_frame, bg='#181816')
        toggle_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(toggle_frame, text="Enable Overlay:", 
                font=('Segoe UI', 12), fg='#FFFFFF', bg='#181816').pack(side='left', padx=(0, 10))
        
        self.toggle_check = tk.Checkbutton(toggle_frame, text="ON/OFF",
                                          variable=self.overlay_enabled,
                                          font=('Segoe UI', 12, 'bold'),
                                          fg='#8B5CF6', bg='#181816',
                                          selectcolor='#181816',
                                          activebackground='#181816')
        self.toggle_check.pack(side='left')
        
        # Separator
        sep1 = tk.Frame(main_frame, height=2, bg='#2A2B4E')
        sep1.pack(fill='x', pady=10)
        
        # OPACITY SLIDER
        opacity_label = tk.Label(main_frame, text="Opacity Control", 
                                font=('Segoe UI', 14, 'bold'),
                                fg='#8B5CF6', bg='#181816')
        opacity_label.pack(anchor='w', pady=(10, 5))
        
        opacity_frame = tk.Frame(main_frame, bg='#181816')
        opacity_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(opacity_frame, text="Opacity:", font=('Segoe UI', 11),
                fg='#B4B4B8', bg='#181816').pack(side='left', padx=(0, 10))
        
        self.opacity_slider = tk.Scale(opacity_frame,
                                      from_=0.3, to=1.0, resolution=0.05,
                                      orient='horizontal',
                                      variable=self.overlay_opacity,
                                      command=self._on_opacity_change,
                                      length=300,
                                      bg='#2A2B4E', fg='#FFFFFF',
                                      troughcolor='#8B5CF6',
                                      activebackground='#8B5CF6',
                                      highlightthickness=0,
                                      sliderrelief='raised',
                                      width=20)
        self.opacity_slider.pack(side='left', padx=(0, 10))
        
        self.opacity_value = tk.Label(opacity_frame, text="90%", 
                                     font=('Segoe UI', 11, 'bold'),
                                     fg='#FFFFFF', bg='#181816')
        self.opacity_value.pack(side='left')
        
        # Separator
        sep2 = tk.Frame(main_frame, height=2, bg='#2A2B4E')
        sep2.pack(fill='x', pady=10)
        
        # SIZE CONTROLS
        size_label = tk.Label(main_frame, text="Size Controls", 
                             font=('Segoe UI', 14, 'bold'),
                             fg='#8B5CF6', bg='#181816')
        size_label.pack(anchor='w', pady=(10, 5))
        
        # WIDTH SLIDER
        width_frame = tk.Frame(main_frame, bg='#181816')
        width_frame.pack(fill='x', pady=(5, 10))
        
        tk.Label(width_frame, text="Width:  ", font=('Segoe UI', 11),
                fg='#B4B4B8', bg='#181816').pack(side='left', padx=(0, 10))
        
        self.width_slider = tk.Scale(width_frame,
                                    from_=200, to=600, resolution=10,
                                    orient='horizontal',
                                    variable=self.overlay_width,
                                    command=self._on_size_change,
                                    length=300,
                                    bg='#2A2B4E', fg='#FFFFFF',
                                    troughcolor='#8B5CF6',
                                    activebackground='#8B5CF6',
                                    highlightthickness=0,
                                    sliderrelief='raised',
                                    width=20)
        self.width_slider.pack(side='left', padx=(0, 10))
        
        self.width_value = tk.Label(width_frame, text="400px", 
                                   font=('Segoe UI', 11, 'bold'),
                                   fg='#FFFFFF', bg='#181816')
        self.width_value.pack(side='left')
        
        # HEIGHT SLIDER
        height_frame = tk.Frame(main_frame, bg='#181816')
        height_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(height_frame, text="Height:", font=('Segoe UI', 11),
                fg='#B4B4B8', bg='#181816').pack(side='left', padx=(0, 10))
        
        self.height_slider = tk.Scale(height_frame,
                                     from_=40, to=150, resolution=5,
                                     orient='horizontal',
                                     variable=self.overlay_height,
                                     command=self._on_size_change,
                                     length=300,
                                     bg='#2A2B4E', fg='#FFFFFF',
                                     troughcolor='#8B5CF6',
                                     activebackground='#8B5CF6',
                                     highlightthickness=0,
                                     sliderrelief='raised',
                                     width=20)
        self.height_slider.pack(side='left', padx=(0, 10))
        
        self.height_value = tk.Label(height_frame, text="80px", 
                                    font=('Segoe UI', 11, 'bold'),
                                    fg='#FFFFFF', bg='#181816')
        self.height_value.pack(side='left')
        
        # Separator
        sep3 = tk.Frame(main_frame, height=2, bg='#2A2B4E')
        sep3.pack(fill='x', pady=10)
        
        # BUTTONS
        button_frame = tk.Frame(main_frame, bg='#181816')
        button_frame.pack(fill='x', pady=(10, 0))
        
        self.reset_btn = tk.Button(button_frame, text="Reset Position",
                                  command=self._reset_overlay_position,
                                  font=('Segoe UI', 11, 'bold'),
                                  bg='#8B5CF6', fg='#FFFFFF',
                                  activebackground='#6B4CF6',
                                  activeforeground='#FFFFFF',
                                  relief='flat', bd=0,
                                  padx=20, pady=10)
        self.reset_btn.pack(side='left', padx=(0, 10))
        
        # Status
        self.status_label = tk.Label(main_frame,
                                    text="Overlay: Disabled",
                                    font=('Segoe UI', 10, 'italic'),
                                    fg='#888888', bg='#181816')
        self.status_label.pack(anchor='w', pady=(20, 0))
        
        print("[OVERLAY] Simple UI built successfully")
    
    def _on_overlay_toggle(self):
        if self.overlay_enabled.get():
            self._create_overlay()
            self.status_label.config(text="Overlay: Enabled", fg='#8B5CF6')
        else:
            self._destroy_overlay()
            self.status_label.config(text="Overlay: Disabled", fg='#888888')
        
        # Save setting
        if hasattr(self.app, 'on_setting_change'):
            self.app.on_setting_change()
    
    def _on_opacity_change(self, value=None):
        opacity = self.overlay_opacity.get()
        self.opacity_value.config(text=f"{int(opacity * 100)}%")
        
        if self.overlay_window:
            self.overlay_window.attributes('-alpha', opacity)
        
        if hasattr(self.app, 'on_setting_change'):
            self.app.on_setting_change()
    
    def _on_size_change(self, value=None):
        width = self.overlay_width.get()
        height = self.overlay_height.get()
        
        self.width_value.config(text=f"{width}px")
        self.height_value.config(text=f"{height}px")
        
        if self.overlay_window:
            current_geo = self.overlay_window.geometry()
            if '+' in current_geo:
                size_part, pos_part = current_geo.split('+', 1)
                x_pos, y_pos = pos_part.split('+')
                new_geometry = f"{width}x{height}+{x_pos}+{y_pos}"
                self.overlay_window.geometry(new_geometry)
        
        if hasattr(self.app, 'on_setting_change'):
            self.app.on_setting_change()
    
    def _reset_overlay_position(self):
        screen_width = self.app.winfo_screenwidth()
        screen_height = self.app.winfo_screenheight()
        
        width = self.overlay_width.get()
        height = self.overlay_height.get()
        
        x_pos = screen_width - width - 50
        y_pos = 50
        
        self.overlay_x.set(50)
        self.overlay_y.set(50)
        
        if self.overlay_window:
            self.overlay_window.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
        
        if hasattr(self.app, 'on_setting_change'):
            self.app.on_setting_change()
    
    def _create_overlay(self):
        if self.overlay_window:
            return
        
        self.overlay_window = tk.Toplevel(self.app)
        self.overlay_window.title("SlyWriter Overlay")
        self.overlay_window.overrideredirect(True)
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.attributes('-alpha', self.overlay_opacity.get())
        
        width = self.overlay_width.get()
        height = self.overlay_height.get()
        x_pos = self.app.winfo_screenwidth() - width - self.overlay_x.get()
        y_pos = self.overlay_y.get()
        self.overlay_window.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
        
        overlay_frame = tk.Frame(self.overlay_window, bg='#1A1B3E', bd=2, relief='ridge')
        overlay_frame.pack(fill='both', expand=True)
        
        status_frame = tk.Frame(overlay_frame, bg='#1A1B3E')
        status_frame.pack(expand=True, fill='both')
        
        self.overlay_label = tk.Label(status_frame,
                                     text="SlyWriter: Ready",
                                     font=('Segoe UI', 11, 'bold'),
                                     fg='#8B5CF6',
                                     bg='#1A1B3E',
                                     padx=10, pady=5)
        self.overlay_label.pack(expand=True, fill='both')
        
        # Make draggable
        status_frame.bind("<Button-1>", self._start_move)
        status_frame.bind("<B1-Motion>", self._do_move)
        self.overlay_label.bind("<Button-1>", self._start_move)
        self.overlay_label.bind("<B1-Motion>", self._do_move)
        
        # Close on right-click
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
        
        screen_width = self.app.winfo_screenwidth()
        width = self.overlay_width.get()
        self.overlay_x.set(screen_width - x - width)
        self.overlay_y.set(y)
        
        if hasattr(self.app, 'on_setting_change'):
            self.app.on_setting_change()
    
    def update_overlay_text(self, text):
        if self.overlay_label:
            self.overlay_label.config(text=f"SlyWriter: {text}", fg='#8B5CF6', bg='#1A1B3E')
    
    def set_theme(self, dark_mode):
        # Simple theme setting - already dark by default
        pass
    
    def load_from_config(self):
        if hasattr(self.app, 'cfg'):
            settings = self.app.cfg.get('settings', {})
            self.overlay_enabled.set(settings.get('overlay_enabled', False))
            self.overlay_opacity.set(settings.get('overlay_opacity', 0.9))
            self.overlay_width.set(settings.get('overlay_width', 400))
            self.overlay_height.set(settings.get('overlay_height', 80))
            self.overlay_x.set(settings.get('overlay_x', 50))
            self.overlay_y.set(settings.get('overlay_y', 50))