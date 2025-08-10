# modern_cards.py - Modern Card Components with Neumorphism

import tkinter as tk
from tkinter import ttk
import config

class ModernCard(tk.Frame):
    """Modern card component with subtle shadows and neumorphism"""
    
    def __init__(self, parent, title=None, dark_mode=False, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.dark_mode = dark_mode
        self._setup_colors()
        
        # Configure main frame
        self.configure(
            bg=self.card_bg,
            relief='flat',
            borderwidth=0,
            padx=16,
            pady=16
        )
        
        # Create shadow effect with multiple frames
        self._create_shadow_effect()
        
        # Add title if provided
        if title:
            self.title_label = tk.Label(
                self,
                text=title,
                font=(config.FONT_PRIMARY, 12, 'bold'),
                bg=self.card_bg,
                fg=self.title_fg
            )
            self.title_label.pack(anchor='w', pady=(0, 12))
    
    def _setup_colors(self):
        """Setup colors based on theme"""
        if self.dark_mode:
            self.card_bg = config.DARK_CARD_BG
            self.title_fg = config.DARK_FG
            self.shadow_color = "#000000"
        else:
            self.card_bg = config.LIGHT_CARD_BG
            self.title_fg = config.LIGHT_FG
            self.shadow_color = "#00000015"  # Very light shadow
    
    def _create_shadow_effect(self):
        """Create subtle shadow effect for depth"""
        # This is simulated since tkinter doesn't support real shadows
        # We use colored borders to create the illusion
        self.configure(highlightbackground=config.GRAY_200 if not self.dark_mode else config.GRAY_700,
                      highlightthickness=1)

class ModernStatsCard(ModernCard):
    """Specialized card for statistics display"""
    
    def __init__(self, parent, title, value, subtitle=None, color=config.PRIMARY_BLUE, dark_mode=False, **kwargs):
        super().__init__(parent, title, dark_mode, **kwargs)
        
        # Value display
        self.value_label = tk.Label(
            self,
            text=str(value),
            font=(config.FONT_PRIMARY, 24, 'bold'),
            bg=self.card_bg,
            fg=color
        )
        self.value_label.pack(anchor='w', pady=(0, 4))
        
        # Subtitle if provided
        if subtitle:
            self.subtitle_label = tk.Label(
                self,
                text=subtitle,
                font=(config.FONT_PRIMARY, 9),
                bg=self.card_bg,
                fg=config.GRAY_500
            )
            self.subtitle_label.pack(anchor='w')
    
    def update_value(self, new_value, color=None):
        """Update the displayed value"""
        self.value_label.config(text=str(new_value))
        if color:
            self.value_label.config(fg=color)

class ModernInputCard(ModernCard):
    """Card specifically for input fields with modern styling"""
    
    def __init__(self, parent, title, placeholder="Enter text...", dark_mode=False, **kwargs):
        super().__init__(parent, title, dark_mode, **kwargs)
        
        # Create modern text input
        self.text_var = tk.StringVar()
        
        input_bg = config.DARK_ENTRY_BG if dark_mode else config.LIGHT_ENTRY_BG
        input_fg = config.DARK_FG if dark_mode else config.LIGHT_FG
        
        self.input_frame = tk.Frame(self, bg=self.card_bg)
        self.input_frame.pack(fill='x', pady=(0, 8))
        
        self.entry = tk.Entry(
            self.input_frame,
            textvariable=self.text_var,
            font=(config.FONT_PRIMARY, 10),
            bg=input_bg,
            fg=input_fg,
            relief='flat',
            borderwidth=1,
            highlightthickness=2,
            highlightcolor=config.PRIMARY_BLUE,
            highlightbackground=config.GRAY_300 if not dark_mode else config.GRAY_600
        )
        self.entry.pack(fill='x', ipady=8, ipadx=12)
        
        # Placeholder handling
        self.placeholder = placeholder
        self.placeholder_active = True
        self._show_placeholder()
        
        # Bind events for placeholder behavior
        self.entry.bind('<FocusIn>', self._on_focus_in)
        self.entry.bind('<FocusOut>', self._on_focus_out)
    
    def _show_placeholder(self):
        """Show placeholder text"""
        if self.placeholder_active and not self.text_var.get():
            self.entry.config(fg=config.GRAY_400)
            self.text_var.set(self.placeholder)
    
    def _hide_placeholder(self):
        """Hide placeholder text"""
        if self.placeholder_active and self.text_var.get() == self.placeholder:
            self.entry.config(fg=config.DARK_FG if self.dark_mode else config.LIGHT_FG)
            self.text_var.set("")
            self.placeholder_active = False
    
    def _on_focus_in(self, event):
        """Handle focus in event"""
        self._hide_placeholder()
    
    def _on_focus_out(self, event):
        """Handle focus out event"""
        if not self.text_var.get():
            self.placeholder_active = True
            self._show_placeholder()
    
    def get_value(self):
        """Get the actual value (not placeholder)"""
        if self.placeholder_active:
            return ""
        return self.text_var.get()
    
    def set_value(self, value):
        """Set the value"""
        self.placeholder_active = False
        self.text_var.set(value)
        self.entry.config(fg=config.DARK_FG if self.dark_mode else config.LIGHT_FG)

class ModernToggleSwitch(tk.Frame):
    """Modern iOS-style toggle switch"""
    
    def __init__(self, parent, text="Toggle", variable=None, dark_mode=False, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.dark_mode = dark_mode
        self.variable = variable or tk.BooleanVar()
        self.is_on = self.variable.get()
        
        bg = config.DARK_BG if dark_mode else config.LIGHT_BG
        fg = config.DARK_FG if dark_mode else config.LIGHT_FG
        
        self.configure(bg=bg)
        
        # Label
        self.label = tk.Label(
            self,
            text=text,
            font=(config.FONT_PRIMARY, 10),
            bg=bg,
            fg=fg
        )
        self.label.pack(side='left', padx=(0, 12))
        
        # Toggle switch canvas
        self.switch_canvas = tk.Canvas(
            self,
            width=50,
            height=25,
            bg=bg,
            highlightthickness=0
        )
        self.switch_canvas.pack(side='left')
        
        # Draw the switch
        self._draw_switch()
        
        # Bind click event
        self.switch_canvas.bind('<Button-1>', self._toggle)
        
        # Bind variable changes
        self.variable.trace_add('write', self._on_variable_change)
    
    def _draw_switch(self):
        """Draw the toggle switch"""
        self.switch_canvas.delete('all')
        
        # Switch background
        bg_color = config.PRIMARY_BLUE if self.is_on else (config.GRAY_400 if not self.dark_mode else config.GRAY_600)
        
        # Draw rounded rectangle background
        self.switch_canvas.create_oval(2, 2, 23, 23, fill=bg_color, outline="")
        self.switch_canvas.create_rectangle(12, 2, 38, 23, fill=bg_color, outline="")
        self.switch_canvas.create_oval(27, 2, 48, 23, fill=bg_color, outline="")
        
        # Draw switch handle
        handle_x = 35 if self.is_on else 15
        handle_color = "white"
        
        self.switch_canvas.create_oval(handle_x-10, 4, handle_x+10, 21, fill=handle_color, outline="")
    
    def _toggle(self, event=None):
        """Toggle the switch"""
        self.is_on = not self.is_on
        self.variable.set(self.is_on)
        self._animate_toggle()
    
    def _animate_toggle(self):
        """Animate the toggle transition"""
        # Simple redraw - could be enhanced with smooth animation
        self._draw_switch()
    
    def _on_variable_change(self, *args):
        """Handle variable changes"""
        new_value = self.variable.get()
        if new_value != self.is_on:
            self.is_on = new_value
            self._draw_switch()