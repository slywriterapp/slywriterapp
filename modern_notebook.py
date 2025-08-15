# modern_notebook.py - Modern Notebook Tab Styling

import tkinter as tk
from tkinter import ttk
import config

def apply_modern_notebook_style(notebook_widget, dark_mode=False):
    """Apply comprehensive modern styling to notebook tabs"""
    
    style = ttk.Style()
    
    # Base colors
    bg = config.DARK_BG if dark_mode else config.LIGHT_BG
    
    # Tab colors - modern gradient approach
    if dark_mode:
        tab_bg = config.GRAY_700
        tab_active = config.PRIMARY_BLUE
        tab_hover = config.PRIMARY_BLUE_HOVER  
        tab_fg = config.GRAY_300
        tab_active_fg = "white"
    else:
        tab_bg = config.GRAY_100
        tab_active = config.PRIMARY_BLUE_LIGHT
        tab_hover = config.PRIMARY_BLUE_LIGHT_HOVER
        tab_fg = config.GRAY_600
        tab_active_fg = "white"
    
    # Configure main notebook
    style.configure("Modern.TNotebook",
                    background=bg,
                    borderwidth=0,
                    tabposition="n")
    
    # Modern tab styling with bold text and better padding
    style.configure("Modern.TNotebook.Tab",
                    background=tab_bg,
                    foreground=tab_fg,
                    padding=[20, 14],  # More generous padding
                    borderwidth=0,
                    font=(config.FONT_PRIMARY, 10, 'bold'),
                    focuscolor="none")
    
    # Advanced tab state styling
    style.map("Modern.TNotebook.Tab",
              background=[
                  ('selected', tab_active),
                  ('active', tab_hover),
                  ('!active', tab_bg)
              ],
              foreground=[
                  ('selected', tab_active_fg),
                  ('active', tab_active_fg),
                  ('!active', tab_fg)
              ],
              expand=[('selected', [1, 1, 1, 0])])  # Slight expansion when selected
    
    # Apply the style
    if hasattr(notebook_widget, 'configure'):
        notebook_widget.configure(style="Modern.TNotebook")
    
    return style

def create_modern_tab_frame(parent, dark_mode=False):
    """Create a modern-styled frame for tab content"""
    
    bg = config.DARK_BG if dark_mode else config.LIGHT_BG
    
    frame = ttk.Frame(parent)
    frame.configure(style="ModernTab.TFrame")
    
    # Configure frame style
    style = ttk.Style()
    style.configure("ModernTab.TFrame",
                    background=bg,
                    borderwidth=0,
                    relief="flat")
    
    return frame

def add_tab_with_icon(notebook, frame, text, icon="", dark_mode=False):
    """Add a tab with optional icon support"""
    
    # For now, we'll use emoji icons since tkinter doesn't support image tabs easily
    display_text = f"{icon} {text}" if icon else text
    
    notebook.add(frame, text=display_text)
    
    # Apply modern styling if not already applied
    if not hasattr(notebook, '_modern_styled'):
        apply_modern_notebook_style(notebook, dark_mode)
        notebook._modern_styled = True

# Tab icons mapping (emoji-based for simplicity)
TAB_ICONS = {
    "Account": "👤",
    "Typing": "⌨️",
    "Hotkeys": "🎹", 
    "Diagnostics": "📊",
    "Humanizer": "🤖",
    "Overlay": "📱",
    "Learn": "🎓"
}