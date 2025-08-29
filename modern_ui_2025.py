# modern_ui_2025.py - Ultra-modern UI components for 2025 aesthetic

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageFilter, ImageTk
import math

# Utility function for scroll support
def add_scroll_support(widget, canvas=None):
    """Add mouse wheel scroll support to any widget
    
    Args:
        widget: The widget to add scroll support to
        canvas: The canvas to scroll (if not provided, searches for canvas in widget)
    """
    if canvas is None:
        # Try to find a canvas in the widget
        for child in widget.winfo_children():
            if isinstance(child, tk.Canvas):
                canvas = child
                break
            # Search recursively in frames
            elif isinstance(child, (tk.Frame, ttk.Frame)):
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Canvas):
                        canvas = subchild
                        break
                if canvas:
                    break
    
    if canvas:
        def on_mousewheel(event):
            # Only scroll if the widget is visible and mouse is over it
            try:
                x, y = widget.winfo_pointerxy()
                widget_x = widget.winfo_rootx()
                widget_y = widget.winfo_rooty()  
                widget_width = widget.winfo_width()
                widget_height = widget.winfo_height()
                
                if (widget_x <= x <= widget_x + widget_width and 
                    widget_y <= y <= widget_y + widget_height):
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass  # Widget might be destroyed
        
        # Bind to widget and canvas
        widget.bind("<MouseWheel>", on_mousewheel)
        if canvas != widget:
            canvas.bind("<MouseWheel>", on_mousewheel)
        
        # Also bind to all children for better coverage
        for child in widget.winfo_children():
            child.bind("<MouseWheel>", on_mousewheel)
        
        return True
    return False

# Modern color palette
COLORS = {
    'primary': '#8B5CF6',      # Purple
    'primary_dark': '#6B4CF6',  # Darker purple
    'primary_light': '#AB7CF6', # Lighter purple
    'accent': '#EC4899',        # Pink
    'accent_light': '#FC6BA9',  # Light pink
    'background': '#0A0A0F',     # Deep dark
    'surface': '#1A1A2E',        # Card background
    'surface_light': '#2A2A3E',  # Lighter surface
    'glass': '#1A1A2E99',        # Glass effect
    'text_primary': '#FFFFFF',   # Primary text
    'text_secondary': '#B4B4B8', # Secondary text
    'text_dim': '#6B7280',       # Dimmed text
    'success': '#10B981',        # Green
    'error': '#EF4444',          # Red
    'warning': '#F59E0B',        # Amber
    'border': '#374151',         # Border color
    'glow': '#8B5CF633',         # Glow effect
}

class GlassmorphicCard(tk.Frame):
    """Modern card with glassmorphic effect"""
    
    def __init__(self, parent, title="", width=None, height=None, **kwargs):
        # Base frame with dark background
        super().__init__(parent, bg=COLORS['background'], highlightthickness=0, **kwargs)
        
        if width:
            self.configure(width=width)
        if height:
            self.configure(height=height)
            
        # Create glass effect container
        self.glass_frame = tk.Frame(self, bg=COLORS['surface'], highlightthickness=1,
                                    highlightbackground=COLORS['border'], highlightcolor=COLORS['border'])
        self.glass_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Add title if provided
        if title:
            self.title_frame = tk.Frame(self.glass_frame, bg=COLORS['surface'], height=40)
            self.title_frame.pack(fill='x', padx=16, pady=(12, 0))
            self.title_frame.pack_propagate(False)
            
            self.title_label = tk.Label(self.title_frame, text=title, 
                                       font=('Segoe UI', 12, 'bold'),
                                       fg=COLORS['text_primary'], 
                                       bg=COLORS['surface'])
            self.title_label.pack(side='left')
            
            # Gradient line under title
            self.separator = tk.Frame(self.glass_frame, height=1, bg=COLORS['primary'])
            self.separator.pack(fill='x', padx=16, pady=(0, 12))
        
        # Content area
        self.content = tk.Frame(self.glass_frame, bg=COLORS['surface'])
        self.content.pack(fill='both', expand=True, padx=16, pady=(0, 16))
        
    def add_glow_effect(self):
        """Add subtle glow effect to card"""
        # This would require canvas for proper glow, simplified for now
        self.configure(highlightthickness=2, highlightbackground=COLORS['glow'])


class ModernButton(tk.Frame):
    """Modern button with gradient and hover effects"""
    
    def __init__(self, parent, text="", command=None, variant="primary", 
                 icon=None, width=None, **kwargs):
        super().__init__(parent, bg=parent.cget('bg'), **kwargs)
        
        self.command = command
        self.variant = variant
        self.is_hovered = False
        self.is_pressed = False
        self.is_disabled = False
        
        # Determine colors based on variant
        if variant == "primary":
            self.bg_color = COLORS['primary']
            self.hover_color = COLORS['primary_light']
            self.active_color = COLORS['primary_dark']
            self.text_color = COLORS['text_primary']
        elif variant == "secondary":
            self.bg_color = COLORS['surface_light']
            self.hover_color = COLORS['border']
            self.active_color = COLORS['surface']
            self.text_color = COLORS['text_secondary']
        elif variant == "success":
            self.bg_color = COLORS['success']
            self.hover_color = '#10C971'
            self.active_color = '#0E9761'
            self.text_color = COLORS['text_primary']
        elif variant == "danger":
            self.bg_color = COLORS['error']
            self.hover_color = '#FF5555'
            self.active_color = '#DF3434'
            self.text_color = COLORS['text_primary']
        
        # Create button container with fixed size to prevent shifting
        self.button_frame = tk.Frame(self, bg=self.bg_color, highlightthickness=0)
        self.button_frame.pack(fill='both', expand=True)
        
        # Create inner frame with fixed padding
        self.inner_frame = tk.Frame(self.button_frame, bg=self.bg_color)
        self.inner_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Prevent size changes during hover
        self.pack_propagate(False)
        
        # Button content (icon + text)
        content_frame = tk.Frame(self.inner_frame, bg=self.bg_color)
        content_frame.pack(expand=True, fill='both')
        
        # Inner content for centering
        inner_content = tk.Frame(content_frame, bg=self.bg_color)
        inner_content.place(relx=0.5, rely=0.5, anchor='center')
        
        # Add icon if provided
        if icon:
            self.icon_label = tk.Label(inner_content, text=icon, 
                                      font=('Segoe UI', 14),
                                      fg=self.text_color, bg=self.bg_color)
            self.icon_label.pack(side='left', padx=(0, 6))
        
        # Add text
        self.text_label = tk.Label(inner_content, text=text, 
                                   font=('Segoe UI', 11, 'bold'),
                                   fg=self.text_color, bg=self.bg_color)
        self.text_label.pack(side='left')
        
        # Set width if specified
        if width:
            self.configure(width=width)
        
        # Bind events
        self.bind_events()
    
    def bind_events(self):
        """Bind hover and click events"""
        # Get all child widgets recursively
        def get_all_children(widget):
            children = [widget]
            for child in widget.winfo_children():
                children.extend(get_all_children(child))
            return children
        
        widgets = get_all_children(self)
        
        for widget in widgets:
            widget.bind("<Enter>", self.on_hover_enter)
            widget.bind("<Leave>", self.on_hover_leave)
            widget.bind("<Button-1>", self.on_press)
            widget.bind("<ButtonRelease-1>", self.on_release)
    
    def on_hover_enter(self, event):
        """Handle mouse enter"""
        if not self.is_pressed:
            # Lighter hover effect - brighten slightly
            self.update_color(self.hover_color)
            self.configure(cursor='hand2')
    
    def on_hover_leave(self, event):
        """Handle mouse leave"""
        if not self.is_pressed:
            self.update_color(self.bg_color)
            self.configure(cursor='')
    
    def on_press(self, event):
        """Handle button press"""
        if self.is_disabled:
            return
        self.is_pressed = True
        self.update_color(self.active_color)
    
    def on_release(self, event):
        """Handle button release"""
        if self.is_disabled:
            return
        self.is_pressed = False
        
        # Check if still hovering
        x, y = self.winfo_pointerxy()
        widget_x = self.winfo_rootx()
        widget_y = self.winfo_rooty()
        widget_width = self.winfo_width()
        widget_height = self.winfo_height()
        
        if widget_x <= x <= widget_x + widget_width and widget_y <= y <= widget_y + widget_height:
            self.update_color(self.hover_color)
            if self.command and not self.is_disabled:
                self.command()
        else:
            self.update_color(self.bg_color)
    
    def update_color(self, color):
        """Update all widget colors recursively"""
        def update_widget_color(widget, bg_color):
            try:
                widget.configure(bg=bg_color)
            except:
                pass
            for child in widget.winfo_children():
                update_widget_color(child, bg_color)
        
        update_widget_color(self, color)
    
    def configure(self, **kwargs):
        """Override configure to handle state changes"""
        if 'state' in kwargs:
            state = kwargs.pop('state')
            if state == 'disabled':
                self.is_disabled = True
                # Make button look disabled
                self.update_color(COLORS['border'])
                self.text_label.configure(fg=COLORS['text_dim'])
                if hasattr(self, 'icon_label'):
                    self.icon_label.configure(fg=COLORS['text_dim'])
                self.configure(cursor='')
            else:
                self.is_disabled = False
                # Restore normal colors
                self.update_color(self.bg_color)
                self.text_label.configure(fg=self.text_color)
                if hasattr(self, 'icon_label'):
                    self.icon_label.configure(fg=self.text_color)
        
        # Call parent configure for other options
        super().configure(**kwargs)


class ModernToggle(tk.Frame):
    """iOS-style toggle switch"""
    
    def __init__(self, parent, variable=None, command=None, **kwargs):
        super().__init__(parent, bg=parent.cget('bg'), **kwargs)
        
        self.variable = variable or tk.BooleanVar()
        self.command = command
        
        # Create toggle container
        self.canvas = tk.Canvas(self, width=50, height=26, 
                               bg=parent.cget('bg'), highlightthickness=0)
        self.canvas.pack()
        
        # Draw toggle background
        self.bg_rect = self.canvas.create_rectangle(2, 2, 48, 24,
                                                    fill=COLORS['border'],
                                                    outline='', width=0)
        
        # Draw toggle handle
        self.handle = self.canvas.create_oval(4, 4, 22, 22,
                                             fill=COLORS['text_primary'],
                                             outline='', width=0)
        
        # Initial state
        self.update_state()
        
        # Bind click event
        self.canvas.bind("<Button-1>", self.toggle)
    
    def toggle(self, event=None):
        """Toggle the switch"""
        self.variable.set(not self.variable.get())
        self.update_state()
        if self.command:
            self.command()
    
    def update_state(self):
        """Update visual state based on variable"""
        if self.variable.get():
            # ON state - animate to right
            self.canvas.itemconfig(self.bg_rect, fill=COLORS['primary'])
            self.canvas.coords(self.handle, 28, 4, 46, 22)
        else:
            # OFF state - animate to left
            self.canvas.itemconfig(self.bg_rect, fill=COLORS['border'])
            self.canvas.coords(self.handle, 4, 4, 22, 22)


class ModernSlider(tk.Frame):
    """Modern slider with gradient track and value preview"""
    
    def __init__(self, parent, from_=0, to=100, variable=None, 
                 command=None, label="", unit="", **kwargs):
        super().__init__(parent, bg=parent.cget('bg'), **kwargs)
        
        self.variable = variable or tk.DoubleVar()
        self.command = command
        self.from_ = from_
        self.to = to
        self.unit = unit
        
        # Create container
        container = tk.Frame(self, bg=parent.cget('bg'))
        container.pack(fill='x')
        
        # Label and value display
        if label:
            header_frame = tk.Frame(container, bg=parent.cget('bg'))
            header_frame.pack(fill='x', pady=(0, 8))
            
            label_widget = tk.Label(header_frame, text=label, 
                                   font=('Segoe UI', 10),
                                   fg=COLORS['text_secondary'], 
                                   bg=parent.cget('bg'))
            label_widget.pack(side='left')
            
            self.value_label = tk.Label(header_frame, 
                                       font=('Segoe UI', 10, 'bold'),
                                       fg=COLORS['primary'], 
                                       bg=parent.cget('bg'))
            self.value_label.pack(side='right')
            self.update_value_label()
        
        # Create custom slider using Canvas
        self.canvas = tk.Canvas(container, width=300, height=40, 
                               bg=parent.cget('bg'), highlightthickness=0)
        self.canvas.pack(fill='x')
        
        # Draw track with gradient
        self.track = self.canvas.create_rectangle(10, 18, 290, 22,
                                                  fill=COLORS['surface_light'],
                                                  outline='', width=0)
        
        # Draw progress bar
        self.progress = self.canvas.create_rectangle(10, 18, 10, 22,
                                                     fill=COLORS['primary'],
                                                     outline='', width=0)
        
        # Draw handle
        self.handle = self.canvas.create_oval(5, 13, 25, 33,
                                             fill=COLORS['text_primary'],
                                             outline=COLORS['primary'],
                                             width=2)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.variable.trace_add('write', self.on_value_change)
        
        # Initial position
        self.update_position()
    
    def on_click(self, event):
        """Handle click on track"""
        self.update_from_position(event.x)
    
    def on_drag(self, event):
        """Handle dragging"""
        self.update_from_position(event.x)
    
    def update_from_position(self, x):
        """Update value based on x position"""
        # Constrain x to track bounds
        x = max(10, min(x, 290))
        
        # Calculate value
        ratio = (x - 10) / 280
        value = self.from_ + (self.to - self.from_) * ratio
        self.variable.set(value)
    
    def on_value_change(self, *args):
        """Handle value change"""
        self.update_position()
        self.update_value_label()
        if self.command:
            self.command()
    
    def update_position(self):
        """Update visual position based on value"""
        value = self.variable.get()
        ratio = (value - self.from_) / (self.to - self.from_)
        x = 10 + ratio * 280
        
        # Update handle position
        self.canvas.coords(self.handle, x-10, 13, x+10, 33)
        
        # Update progress bar
        self.canvas.coords(self.progress, 10, 18, x, 22)
    
    def update_value_label(self):
        """Update value display"""
        if hasattr(self, 'value_label'):
            value = self.variable.get()
            if self.unit:
                text = f"{value:.1f} {self.unit}"
            else:
                text = f"{value:.1f}"
            self.value_label.configure(text=text)


class ModernTextArea(tk.Frame):
    """Modern text area with syntax highlighting feel"""
    
    def __init__(self, parent, height=10, placeholder="", **kwargs):
        super().__init__(parent, bg=COLORS['surface'], **kwargs)
        
        self.placeholder = placeholder
        
        # Create container with border
        self.container = tk.Frame(self, bg=COLORS['surface'], 
                                 highlightthickness=1,
                                 highlightbackground=COLORS['border'],
                                 highlightcolor=COLORS['primary'])
        self.container.pack(fill='both', expand=True)
        
        # Line numbers area
        self.line_numbers = tk.Text(self.container, width=4, height=height,
                                   bg=COLORS['background'], fg=COLORS['text_dim'],
                                   font=('Courier New', 10), state='disabled',
                                   relief='flat', bd=0)
        self.line_numbers.pack(side='left', fill='y')
        
        # Main text area
        self.text = tk.Text(self.container, height=height,
                           bg=COLORS['surface'], fg=COLORS['text_primary'],
                           insertbackground=COLORS['primary'],
                           font=('Courier New', 11), relief='flat', bd=0,
                           wrap='word')
        self.text.pack(side='left', fill='both', expand=True, padx=(8, 0))
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.container, orient='vertical',
                                       command=self.sync_scroll)
        self.scrollbar.pack(side='right', fill='y')
        
        self.text.config(yscrollcommand=self.scrollbar.set)
        
        # Placeholder handling
        if placeholder:
            self.add_placeholder()
            self.text.bind("<FocusIn>", self.remove_placeholder)
            self.text.bind("<FocusOut>", self.add_placeholder_if_empty)
        
        # Update line numbers on change
        self.text.bind("<<Change>>", self.update_line_numbers)
        self.text.bind("<Configure>", self.update_line_numbers)
        self.text.bind("<KeyRelease>", self.update_line_numbers)
        
        # Initial line numbers
        self.update_line_numbers()
    
    def sync_scroll(self, *args):
        """Sync scrolling between text and line numbers"""
        self.text.yview(*args)
        self.line_numbers.yview(*args)
    
    def update_line_numbers(self, event=None):
        """Update line numbers display"""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', 'end')
        
        # Get number of lines
        lines = self.text.get('1.0', 'end').count('\n')
        line_numbers_string = '\n'.join(str(i) for i in range(1, lines + 1))
        self.line_numbers.insert('1.0', line_numbers_string)
        self.line_numbers.config(state='disabled')
    
    def add_placeholder(self):
        """Add placeholder text"""
        if not self.text.get('1.0', 'end-1c'):
            self.text.insert('1.0', self.placeholder)
            self.text.tag_add('placeholder', '1.0', 'end')
            self.text.tag_config('placeholder', foreground=COLORS['text_dim'])
    
    def remove_placeholder(self, event=None):
        """Remove placeholder text on focus"""
        if self.text.get('1.0', 'end-1c') == self.placeholder:
            self.text.delete('1.0', 'end')
            self.text.tag_remove('placeholder', '1.0', 'end')
    
    def add_placeholder_if_empty(self, event=None):
        """Add placeholder if text is empty"""
        if not self.text.get('1.0', 'end-1c'):
            self.add_placeholder()
    
    def get(self, *args):
        """Get text content"""
        content = self.text.get(*args)
        if content == self.placeholder:
            return ""
        return content
    
    def insert(self, *args):
        """Insert text"""
        self.remove_placeholder()
        self.text.insert(*args)
        self.update_line_numbers()
    
    def delete(self, *args):
        """Delete text"""
        self.text.delete(*args)
        self.update_line_numbers()


class StatsCard(tk.Frame):
    """Modern stats display card"""
    
    def __init__(self, parent, title="", value="0", unit="", icon="", **kwargs):
        super().__init__(parent, bg=COLORS['surface'], **kwargs)
        
        # Configure frame
        self.configure(highlightthickness=1, highlightbackground=COLORS['border'])
        
        # Content container
        content = tk.Frame(self, bg=COLORS['surface'])
        content.pack(fill='both', expand=True, padx=12, pady=12)
        
        # Icon and title row
        header = tk.Frame(content, bg=COLORS['surface'])
        header.pack(fill='x')
        
        if icon:
            icon_label = tk.Label(header, text=icon, font=('Segoe UI', 16),
                                 fg=COLORS['primary'], bg=COLORS['surface'])
            icon_label.pack(side='left', padx=(0, 8))
        
        title_label = tk.Label(header, text=title, font=('Segoe UI', 10),
                              fg=COLORS['text_dim'], bg=COLORS['surface'])
        title_label.pack(side='left')
        
        # Value display
        value_frame = tk.Frame(content, bg=COLORS['surface'])
        value_frame.pack(fill='x', pady=(8, 0))
        
        self.value_label = tk.Label(value_frame, text=value,
                                   font=('Segoe UI', 20, 'bold'),
                                   fg=COLORS['text_primary'], bg=COLORS['surface'])
        self.value_label.pack(side='left')
        
        if unit:
            unit_label = tk.Label(value_frame, text=unit,
                                font=('Segoe UI', 12),
                                fg=COLORS['text_secondary'], bg=COLORS['surface'])
            unit_label.pack(side='left', padx=(4, 0))
    
    def update_value(self, value):
        """Update displayed value with animation effect"""
        self.value_label.configure(text=value)
        # Add brief highlight effect
        original_color = self.value_label.cget('fg')
        self.value_label.configure(fg=COLORS['primary'])
        self.after(200, lambda: self.value_label.configure(fg=original_color))


class ModernProgressBar(tk.Frame):
    """Modern progress bar with gradient"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=parent.cget('bg'), **kwargs)
        
        self.progress = 0
        
        # Create canvas for custom drawing
        self.canvas = tk.Canvas(self, width=300, height=8,
                               bg=parent.cget('bg'), highlightthickness=0)
        self.canvas.pack(fill='x')
        
        # Background track
        self.track = self.canvas.create_rectangle(0, 2, 300, 6,
                                                  fill=COLORS['surface_light'],
                                                  outline='', width=0)
        
        # Progress bar with gradient effect
        self.bar = self.canvas.create_rectangle(0, 2, 0, 6,
                                               fill=COLORS['primary'],
                                               outline='', width=0)
    
    def set_progress(self, value):
        """Set progress value (0-100)"""
        self.progress = max(0, min(100, value))
        width = self.progress * 3  # 300 pixels total width
        self.canvas.coords(self.bar, 0, 2, width, 6)
        
        # Change color based on progress
        if self.progress < 30:
            color = COLORS['error']
        elif self.progress < 70:
            color = COLORS['warning']
        else:
            color = COLORS['success']
        
        self.canvas.itemconfig(self.bar, fill=color)


class FloatingActionButton(tk.Frame):
    """Floating action button"""
    
    def __init__(self, parent, icon="", command=None, **kwargs):
        super().__init__(parent, bg=COLORS['primary'], **kwargs)
        
        self.command = command
        
        # Make it circular (sort of)
        self.configure(width=56, height=56)
        self.pack_propagate(False)
        
        # Icon
        self.icon_label = tk.Label(self, text=icon, font=('Segoe UI', 20),
                                  fg=COLORS['text_primary'], bg=COLORS['primary'])
        self.icon_label.pack(expand=True)
        
        # Bind events
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.icon_label.bind("<Enter>", self.on_hover)
        self.icon_label.bind("<Leave>", self.on_leave)
        self.icon_label.bind("<Button-1>", self.on_click)
    
    def on_hover(self, event):
        """Hover effect"""
        self.configure(bg=COLORS['primary_light'])
        self.icon_label.configure(bg=COLORS['primary_light'])
        self.configure(cursor='hand2')
    
    def on_leave(self, event):
        """Leave effect"""
        self.configure(bg=COLORS['primary'])
        self.icon_label.configure(bg=COLORS['primary'])
        self.configure(cursor='')
    
    def on_click(self, event):
        """Click handler"""
        if self.command:
            self.command()
            # Visual feedback
            self.configure(bg=COLORS['primary_dark'])
            self.icon_label.configure(bg=COLORS['primary_dark'])
            self.after(100, lambda: self.configure(bg=COLORS['primary']))
            self.after(100, lambda: self.icon_label.configure(bg=COLORS['primary']))