# purple_button_theme.py - Purple Button Theme System with Hover Effects

import tkinter as tk
from tkinter import ttk
from config import ACCENT_PURPLE

class PurpleButton(tk.Button):
    """Modern purple button with hover effects"""
    
    def __init__(self, parent, text="", command=None, **kwargs):
        # Default purple styling
        default_config = {
            'text': text,
            'command': command,
            'font': ('Segoe UI', 10, 'bold'),
            'bg': ACCENT_PURPLE,  # #8B5CF6
            'fg': 'white',
            'activebackground': '#7C3AED',  # Darker purple on click
            'activeforeground': 'white',
            'bd': 0,
            'relief': 'flat',
            'cursor': 'hand2',
            'padx': 15,
            'pady': 8,
        }
        
        # Override with any custom kwargs
        default_config.update(kwargs)
        
        super().__init__(parent, **default_config)
        
        # Add hover effects
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        
        # Store original colors
        self.original_bg = self['bg']
        self.hover_bg = '#7C3AED'  # Darker purple for hover
        
    def _on_enter(self, event):
        """Mouse enter - darken button"""
        self.config(bg=self.hover_bg)
        
    def _on_leave(self, event):
        """Mouse leave - restore original color"""
        self.config(bg=self.original_bg)

def apply_purple_ttk_theme(app):
    """Apply purple theme to all TTK buttons and dropdowns"""
    style = app.tb_style
    
    # Purple button styling for TTK buttons
    style.configure("TButton",
                    background=ACCENT_PURPLE,  # #8B5CF6
                    foreground="white", 
                    borderwidth=0,
                    focuscolor="none",
                    relief='flat',
                    font=('Segoe UI', 10, 'bold'),
                    padding=[15, 8])
    
    style.map("TButton",
              background=[('active', '#7C3AED'),      # Darker on click
                         ('pressed', '#6D28D9'),      # Even darker when pressed  
                         ('!active', ACCENT_PURPLE),  # Normal state
                         ('disabled', '#9CA3AF')],    # Gray when disabled
              foreground=[('active', 'white'),
                         ('pressed', 'white'),
                         ('!active', 'white'),
                         ('disabled', '#6B7280')])
    
    # Purple styling for TTK Comboboxes (dropdowns)
    style.configure("TCombobox",
                    fieldbackground=ACCENT_PURPLE,
                    background=ACCENT_PURPLE,
                    foreground="white",
                    selectforeground="white",
                    selectbackground='#7C3AED',
                    borderwidth=0,
                    relief='flat',
                    font=('Segoe UI', 10))
    
    style.map("TCombobox",
              fieldbackground=[('active', '#7C3AED'),
                              ('pressed', '#6D28D9'),
                              ('!active', ACCENT_PURPLE)],
              background=[('active', '#7C3AED'),
                         ('pressed', '#6D28D9'),
                         ('!active', ACCENT_PURPLE)],
              foreground=[('active', 'white'),
                         ('pressed', 'white'),
                         ('!active', 'white')])
    
    # Purple styling for TTK Radiobuttons
    style.configure("TRadiobutton",
                    background="transparent",
                    foreground="white",
                    focuscolor="none",
                    font=('Segoe UI', 10))
    
    style.map("TRadiobutton",
              background=[('active', 'transparent'),
                         ('pressed', 'transparent'),
                         ('!active', 'transparent')],
              foreground=[('active', 'white'),
                         ('pressed', 'white'),
                         ('!active', 'white')])
    
    # Purple styling for TTK Scale widgets (sliders)
    style.configure("TScale",
                    background=ACCENT_PURPLE,
                    troughcolor='#2D2F5A',  # Dark background for track
                    borderwidth=0,
                    lightcolor=ACCENT_PURPLE,
                    darkcolor=ACCENT_PURPLE,
                    focuscolor="none")
    
    style.map("TScale",
              background=[('active', '#7C3AED'),
                         ('pressed', '#6D28D9'),
                         ('!active', ACCENT_PURPLE)])
    
    # Purple styling for TTK Entry widgets  
    style.configure("TEntry",
                    fieldbackground='#2D2F5A',  # Dark background
                    background='#2D2F5A',
                    foreground="white",
                    insertcolor="white",  # Cursor color
                    borderwidth=1,
                    focuscolor=ACCENT_PURPLE,
                    font=('Segoe UI', 10))
    
    style.map("TEntry",
              fieldbackground=[('active', '#343652'),
                              ('focus', '#343652'),
                              ('!active', '#2D2F5A')],
              foreground=[('active', 'white'),
                         ('focus', 'white'),
                         ('!active', 'white')])
    
    # Purple styling for TTK Progressbar widgets
    style.configure("TProgressbar",
                    background=ACCENT_PURPLE,  # Fill color
                    troughcolor='#2D2F5A',     # Track color  
                    borderwidth=0,
                    lightcolor=ACCENT_PURPLE,
                    darkcolor=ACCENT_PURPLE,
                    focuscolor="none")
    
    style.map("TProgressbar",
              background=[('active', '#7C3AED'),
                         ('!active', ACCENT_PURPLE)])

def replace_button_with_purple(parent, old_button_text, command, **kwargs):
    """Find and replace a button with purple styled version"""
    for widget in parent.winfo_children():
        if isinstance(widget, (tk.Button, ttk.Button)):
            if hasattr(widget, 'cget') and widget.cget('text') == old_button_text:
                # Get position info
                grid_info = widget.grid_info()
                pack_info = widget.pack_info()
                
                # Create purple replacement
                new_button = PurpleButton(parent, text=old_button_text, command=command, **kwargs)
                
                # Position it in the same place
                if grid_info:
                    widget.destroy()
                    new_button.grid(**grid_info)
                elif pack_info:
                    widget.destroy()
                    new_button.pack(**pack_info)
                
                return new_button
        
        # Recursively search child widgets
        replace_button_with_purple(widget, old_button_text, command, **kwargs)
    
    return None

def style_all_buttons_purple(root_widget):
    """Recursively style all buttons in a widget tree"""
    for widget in root_widget.winfo_children():
        if isinstance(widget, tk.Button) and not isinstance(widget, PurpleButton):
            # Apply purple styling to regular buttons
            widget.config(
                bg=ACCENT_PURPLE,
                fg='white',
                font=('Segoe UI', 10, 'bold'),
                activebackground='#7C3AED',
                activeforeground='white',
                bd=0,
                relief='flat',
                cursor='hand2'
            )
            
            # Add hover effects
            def make_hover_handlers(btn):
                def on_enter(event):
                    btn.config(bg='#7C3AED')
                def on_leave(event):  
                    btn.config(bg=ACCENT_PURPLE)
                return on_enter, on_leave
            
            enter_handler, leave_handler = make_hover_handlers(widget)
            widget.bind('<Enter>', enter_handler)
            widget.bind('<Leave>', leave_handler)
        
        elif isinstance(widget, ttk.Button):
            # TTK buttons will be styled by the theme system
            pass
            
        # Recursively process child widgets
        style_all_buttons_purple(widget)

def theme_popup_window(window):
    """Apply dark theme to popup windows"""
    try:
        # Set window background to dark
        window.configure(bg='#1A1B3E')  # Dark background
        
        # Style all child widgets
        def apply_dark_theme_recursive(widget):
            try:
                # Style labels
                if isinstance(widget, tk.Label):
                    widget.configure(bg='#1A1B3E', fg='white', font=('Segoe UI', 10))
                
                # Style frames  
                elif isinstance(widget, tk.Frame):
                    widget.configure(bg='#1A1B3E')
                
                # Style text widgets
                elif isinstance(widget, tk.Text):
                    widget.configure(bg='#2D2F5A', fg='white', insertbackground='white',
                                   font=('Segoe UI', 10))
                
                # Style entry widgets
                elif isinstance(widget, tk.Entry):
                    widget.configure(bg='#2D2F5A', fg='white', insertbackground='white',
                                   font=('Segoe UI', 10))
                
                # Style buttons with purple theme
                elif isinstance(widget, tk.Button):
                    widget.configure(bg=ACCENT_PURPLE, fg='white', 
                                   activebackground='#7C3AED', activeforeground='white',
                                   font=('Segoe UI', 10, 'bold'), bd=0, cursor='hand2')
                
                # Recursively apply to children
                for child in widget.winfo_children():
                    apply_dark_theme_recursive(child)
                    
            except tk.TclError:
                # Skip widgets that can't be configured
                pass
        
        apply_dark_theme_recursive(window)
        
    except Exception as e:
        print(f"Error theming popup: {e}")

# Monkey patch messagebox and simpledialog to auto-theme
original_messagebox_showinfo = None
original_messagebox_showerror = None
original_messagebox_showwarning = None
original_simpledialog_askstring = None

def setup_popup_theming():
    """Setup automatic popup window theming"""
    global original_messagebox_showinfo, original_messagebox_showerror, original_messagebox_showwarning, original_simpledialog_askstring
    
    try:
        import tkinter.messagebox as messagebox
        import tkinter.simpledialog as simpledialog
        
        # Store originals
        if not original_messagebox_showinfo:
            original_messagebox_showinfo = messagebox.showinfo
            original_messagebox_showerror = messagebox.showerror
            original_messagebox_showwarning = messagebox.showwarning
            original_simpledialog_askstring = simpledialog.askstring
        
        def themed_showinfo(title, message, **kwargs):
            result = original_messagebox_showinfo(title, message, **kwargs)
            return result
            
        def themed_showerror(title, message, **kwargs):
            result = original_messagebox_showerror(title, message, **kwargs)
            return result
            
        def themed_showwarning(title, message, **kwargs):
            result = original_messagebox_showwarning(title, message, **kwargs)
            return result
            
        def themed_askstring(title, prompt, **kwargs):
            result = original_simpledialog_askstring(title, prompt, **kwargs)
            return result
        
        # Replace with themed versions
        messagebox.showinfo = themed_showinfo
        messagebox.showerror = themed_showerror  
        messagebox.showwarning = themed_showwarning
        simpledialog.askstring = themed_askstring
        
    except Exception as e:
        print(f"Error setting up popup theming: {e}")