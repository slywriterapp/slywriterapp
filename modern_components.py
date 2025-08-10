# modern_components.py - Modern UI Components with Shadows and Cards

import tkinter as tk
from tkinter import ttk
import config

class ModernCard(tk.Frame):
    """Modern card component with subtle shadow effect"""
    
    def __init__(self, parent, title=None, dark_mode=False, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.dark_mode = dark_mode
        self._setup_colors()
        
        # Create shadow effect with layered frames
        self.shadow_frame = tk.Frame(
            self,
            bg=self.shadow_color,
            relief='flat'
        )
        self.shadow_frame.pack(fill='both', expand=True, padx=(2, 0), pady=(2, 0))
        
        # Main card frame
        self.card_frame = tk.Frame(
            self.shadow_frame,
            bg=self.card_bg,
            relief='flat',
            borderwidth=1,
            highlightbackground=self.border_color,
            highlightthickness=1
        )
        self.card_frame.pack(fill='both', expand=True, padx=(0, 2), pady=(0, 2))
        
        # Title if provided
        if title:
            self.title_frame = tk.Frame(self.card_frame, bg=self.card_bg)
            self.title_frame.pack(fill='x', padx=config.SPACING_LG, pady=(config.SPACING_LG, config.SPACING_SM))
            
            self.title_label = tk.Label(
                self.title_frame,
                text=title,
                font=(config.FONT_PRIMARY, config.FONT_SIZE_LG, 'bold'),
                bg=self.card_bg,
                fg=self.title_fg
            )
            self.title_label.pack(anchor='w')
        
        # Content frame
        self.content_frame = tk.Frame(
            self.card_frame,
            bg=self.card_bg
        )
        self.content_frame.pack(fill='both', expand=True, padx=config.SPACING_LG, pady=(0, config.SPACING_LG))
        
        self.configure(bg=parent.cget('bg'))
    
    def _setup_colors(self):
        """Setup colors based on theme"""
        if self.dark_mode:
            self.card_bg = config.DARK_CARD_BG
            self.title_fg = config.DARK_FG
            self.shadow_color = config.GRAY_900
            self.border_color = config.GRAY_700
        else:
            self.card_bg = config.LIGHT_CARD_BG
            self.title_fg = config.LIGHT_FG
            self.shadow_color = config.GRAY_200
            self.border_color = config.GRAY_200

class ModernTextArea(ModernCard):
    """Modern text area with card styling and proper theming"""
    
    def __init__(self, parent, title=None, placeholder="Enter text...", height=10, dark_mode=False, **kwargs):
        super().__init__(parent, title, dark_mode, **kwargs)
        
        # Text widget with modern styling
        self.text_widget = tk.Text(
            self.content_frame,
            height=height,
            wrap='word',
            font=(config.FONT_PRIMARY, config.FONT_SIZE_BASE),
            bg=config.DARK_ENTRY_BG if dark_mode else config.LIGHT_ENTRY_BG,
            fg=config.DARK_FG if dark_mode else config.LIGHT_FG,
            insertbackground=config.DARK_FG if dark_mode else config.LIGHT_FG,
            relief='flat',
            borderwidth=0,
            highlightthickness=2,
            highlightcolor=config.PRIMARY_BLUE,
            highlightbackground=config.GRAY_300 if not dark_mode else config.GRAY_600,
            selectbackground=config.PRIMARY_BLUE_LIGHT if not dark_mode else config.PRIMARY_BLUE,
            selectforeground="white",
            padx=config.SPACING_BASE,
            pady=config.SPACING_SM
        )
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.content_frame,
            orient='vertical',
            command=self.text_widget.yview
        )
        
        self.text_widget.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack widgets
        self.text_widget.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
        
        # Placeholder handling
        self.placeholder = placeholder
        self.placeholder_active = True
        self._show_placeholder()
        
        # Bind events
        self.text_widget.bind('<FocusIn>', self._on_focus_in)
        self.text_widget.bind('<FocusOut>', self._on_focus_out)
        self.text_widget.bind('<KeyPress>', self._on_key_press)
    
    def _show_placeholder(self):
        """Show placeholder text"""
        if self.placeholder_active and not self.text_widget.get('1.0', 'end-1c'):
            self.text_widget.insert('1.0', self.placeholder)
            self.text_widget.tag_add("placeholder", "1.0", "end")
            placeholder_color = config.GRAY_400 if not self.dark_mode else config.GRAY_500
            self.text_widget.tag_configure("placeholder", foreground=placeholder_color)
    
    def _hide_placeholder(self):
        """Hide placeholder text"""
        if self.placeholder_active:
            current_text = self.text_widget.get('1.0', 'end-1c')
            if current_text == self.placeholder:
                self.text_widget.delete('1.0', 'end')
                self.placeholder_active = False
    
    def _on_focus_in(self, event):
        """Handle focus in"""
        self._hide_placeholder()
    
    def _on_focus_out(self, event):
        """Handle focus out"""
        if not self.text_widget.get('1.0', 'end-1c'):
            self.placeholder_active = True
            self._show_placeholder()
    
    def _on_key_press(self, event):
        """Handle key press"""
        if self.placeholder_active:
            self._hide_placeholder()
    
    def get_text(self):
        """Get text content (excluding placeholder)"""
        if self.placeholder_active:
            return ""
        return self.text_widget.get('1.0', 'end-1c')
    
    def set_text(self, text):
        """Set text content"""
        self.placeholder_active = False
        self.text_widget.delete('1.0', 'end')
        self.text_widget.insert('1.0', text)
        if text:
            normal_color = config.DARK_FG if self.dark_mode else config.LIGHT_FG
            self.text_widget.configure(fg=normal_color)

class ModernProgressBar(tk.Frame):
    """Modern progress bar with smooth animations"""
    
    def __init__(self, parent, width=300, height=8, dark_mode=False, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.width = width
        self.height = height
        self.dark_mode = dark_mode
        self.progress = 0.0
        
        self._setup_colors()
        
        # Configure frame
        self.configure(bg=parent.cget('bg'), height=height + 4)
        
        # Progress canvas
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=self.track_color,
            highlightthickness=0,
            relief='flat'
        )
        self.canvas.pack(pady=2)
        
        # Draw initial state
        self._draw_progress()
    
    def _setup_colors(self):
        """Setup colors based on theme"""
        if self.dark_mode:
            self.track_color = config.GRAY_700
            self.fill_color = config.SUCCESS_GREEN
            self.bg_color = config.DARK_BG
        else:
            self.track_color = config.GRAY_200
            self.fill_color = config.SUCCESS_GREEN
            self.bg_color = config.LIGHT_BG
    
    def _draw_progress(self):
        """Draw the progress bar"""
        self.canvas.delete('all')
        
        # Background track
        self.canvas.create_rectangle(
            0, 0, self.width, self.height,
            fill=self.track_color,
            outline=""
        )
        
        # Progress fill
        if self.progress > 0:
            fill_width = int(self.width * self.progress)
            self.canvas.create_rectangle(
                0, 0, fill_width, self.height,
                fill=self.fill_color,
                outline=""
            )
    
    def set_progress(self, value):
        """Set progress value (0.0 to 1.0)"""
        self.progress = max(0.0, min(1.0, value))
        self._draw_progress()
    
    def animate_to_progress(self, target_value, duration=500):
        """Animate to target progress value"""
        target_value = max(0.0, min(1.0, target_value))
        start_progress = self.progress
        steps = 30
        step_duration = duration // steps
        step_size = (target_value - start_progress) / steps
        
        def animate_step(step):
            if step < steps:
                new_progress = start_progress + (step_size * step)
                self.set_progress(new_progress)
                self.after(step_duration, lambda: animate_step(step + 1))
            else:
                self.set_progress(target_value)
        
        animate_step(1)

class ModernPanel(tk.Frame):
    """Modern panel with consistent spacing and styling"""
    
    def __init__(self, parent, title=None, dark_mode=False, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.dark_mode = dark_mode
        bg = config.DARK_BG if dark_mode else config.LIGHT_BG
        fg = config.DARK_FG if dark_mode else config.LIGHT_FG
        
        self.configure(bg=bg, padx=config.SPACING_LG, pady=config.SPACING_LG)
        
        # Title if provided
        if title:
            self.title_label = tk.Label(
                self,
                text=title,
                font=(config.FONT_PRIMARY, config.FONT_SIZE_XL, 'bold'),
                bg=bg,
                fg=fg
            )
            self.title_label.pack(anchor='w', pady=(0, config.SPACING_LG))