# modern_theme.py - 2025 UI Theme System

import tkinter as tk
from tkinter import ttk
import config

# ModernButton class removed - using regular tkinter buttons for immediate color display

def apply_global_ttk_theme(app, dark):
    """Apply global TTK theme that affects all tabs"""
    
    # Use the app's TTK style instance
    style = app.tb_style
    
    # FORCE OVERRIDE: Clear any existing styling first
    try:
        # Force refresh the style system
        current_theme = style.theme.name
        style.theme_use(current_theme)
    except:
        pass
    
    # Base colors
    bg = config.DARK_BG if dark else config.LIGHT_BG
    fg = config.DARK_FG if dark else config.LIGHT_FG
    entry_bg = config.DARK_ENTRY_BG if dark else config.LIGHT_ENTRY_BG
    
    # Modern font system
    modern_font = (config.FONT_PRIMARY, config.FONT_SIZE_BASE)
    modern_font_bold = (config.FONT_PRIMARY, config.FONT_SIZE_BASE, 'bold')
    
    # Modern color scheme
    primary = config.PRIMARY_BLUE_LIGHT if not dark else config.PRIMARY_BLUE
    primary_hover = config.PRIMARY_BLUE_LIGHT_HOVER if not dark else config.PRIMARY_BLUE_HOVER
    
    # Modern button styling for TTK buttons - ALWAYS COLORED
    style.configure("TButton",  # Apply to ALL ttk buttons
                    background=primary,
                    foreground="white", 
                    borderwidth=0,
                    focuscolor="none",
                    relief='flat',
                    font=modern_font_bold,
                    padding=[config.SPACING_LG, config.SPACING_SM])
    
    style.map("TButton",  # Apply to ALL ttk buttons
              background=[('active', primary_hover),
                         ('pressed', primary_hover),
                         ('!active', primary),
                         ('disabled', config.GRAY_400)],
              foreground=[('active', "white"),
                         ('pressed', "white"), 
                         ('!active', "white"),
                         ('disabled', config.GRAY_600)])
    
    # AGGRESSIVE Dynamic TCheckbutton styling - FORCE OVERRIDE of ttkbootstrap
    checkbox_bg = config.DARK_BG if dark else config.LIGHT_BG
    checkbox_fg = config.DARK_FG if dark else config.LIGHT_FG
    checkbox_indicator_bg = config.GRAY_600 if dark else config.GRAY_300
    
    # DEBUG: Print what colors we're actually applying
    print(f"[THEME DEBUG] Dark mode: {dark}")
    print(f"[THEME DEBUG] Checkbox BG: {checkbox_bg}, FG: {checkbox_fg}")
    print(f"[THEME DEBUG] Track color: {config.GRAY_600 if dark else config.GRAY_300}")
    
    # FORCE configure with explicit style overrides
    style.configure("TCheckbutton",
                    background=checkbox_bg,
                    foreground=checkbox_fg,
                    font=modern_font,
                    relief='flat',
                    focuscolor='none',
                    # Force override any existing styling
                    borderwidth=0,
                    highlightthickness=0)
    
    # FORCE map with explicit overrides
    style.map("TCheckbutton",
              background=[('active', checkbox_bg), ('!active', checkbox_bg)],
              foreground=[('active', checkbox_fg), ('!active', checkbox_fg)],
              indicatorcolor=[('selected', primary), ('!selected', checkbox_indicator_bg)])
    
    # AGGRESSIVE Dynamic TScale (slider) styling - FORCE OVERRIDE of ttkbootstrap  
    track_color = config.GRAY_600 if dark else config.GRAY_300
    handle_color = primary
    handle_hover = primary_hover
    
    # FORCE configure with explicit style overrides
    style.configure("Horizontal.TScale",
                    background=checkbox_bg,
                    troughcolor=track_color,
                    sliderlength=28,
                    sliderrelief='raised',
                    borderwidth=2,
                    lightcolor=handle_color,
                    darkcolor=handle_color,
                    slidercolor=handle_color,
                    focuscolor='none',
                    # Force override any existing styling
                    highlightthickness=0)
    
    # FORCE map with explicit overrides
    style.map("Horizontal.TScale",
              background=[('active', checkbox_bg), ('!active', checkbox_bg)],
              troughcolor=[('active', track_color), ('!active', track_color)],
              lightcolor=[('active', handle_hover), ('!active', handle_color)],
              darkcolor=[('active', handle_hover), ('!active', handle_color)],
              slidercolor=[('active', handle_hover), ('!active', handle_color)])
    
    # Dynamic TEntry styling using config variables
    entry_bg_color = config.DARK_ENTRY_BG if dark else config.LIGHT_ENTRY_BG
    entry_fg_color = config.DARK_FG if dark else config.LIGHT_FG
    
    style.configure("TEntry",
                    fieldbackground=entry_bg_color,
                    foreground=entry_fg_color,
                    borderwidth=1,
                    relief='flat',
                    focuscolor=primary)
    
    # Force refresh all existing TTK widgets to pick up new styling
    try:
        # Force theme refresh
        style.theme_use(style.theme.name)
        
        # AGGRESSIVE: Recursively update all TTK widgets in the app
        def refresh_ttk_widgets(widget):
            for child in widget.winfo_children():
                if isinstance(child, (ttk.Scale, ttk.Checkbutton, ttk.Entry, ttk.Combobox)):
                    # FORCE multiple refresh methods
                    child.update_idletasks()
                    child.update()
                    # Force style refresh by temporarily changing and restoring style
                    try:
                        current_style = child.cget('style')
                        # Force refresh with explicit style manipulation
                        if isinstance(child, ttk.Scale):
                            child.configure(style='Horizontal.TScale')
                        elif isinstance(child, ttk.Checkbutton):
                            child.configure(style='TCheckbutton')
                        elif isinstance(child, ttk.Entry):
                            child.configure(style='TEntry')
                        # Force immediate update
                        child.update_idletasks()
                    except:
                        pass
                refresh_ttk_widgets(child)
        
        refresh_ttk_widgets(app)
        app.update_idletasks()
    except Exception:
        pass

def apply_modern_theme(tab, dark):
    """Apply comprehensive modern 2025 theme"""
    
    # Apply global TTK theme first
    apply_global_ttk_theme(tab.app, dark)
    
    # Base colors
    bg = config.DARK_BG if dark else config.LIGHT_BG
    fg = config.DARK_FG if dark else config.LIGHT_FG
    entry_bg = config.DARK_ENTRY_BG if dark else config.LIGHT_ENTRY_BG
    card_bg = config.DARK_CARD_BG if dark else config.LIGHT_CARD_BG
    entry_fg = fg
    
    # Modern font system with consistent sizing
    modern_font = (config.FONT_PRIMARY, config.FONT_SIZE_BASE)
    modern_font_bold = (config.FONT_PRIMARY, config.FONT_SIZE_BASE, 'bold')
    modern_font_large = (config.FONT_PRIMARY, config.FONT_SIZE_XL, 'bold')
    modern_font_small = (config.FONT_PRIMARY, config.FONT_SIZE_SM)
    
    # Apply background colors to all frames with consistent spacing
    for frame in [tab, tab.container, tab.content]:
        try:
            frame.configure(bg=bg, padx=config.SPACING_BASE, pady=config.SPACING_BASE)
        except Exception:
            try:
                frame.configure(bg=bg)
            except Exception:
                pass
    
    # Apply card styling to specific frames
    for frame in [tab.frame_in, tab.lp_frame]:
        try:
            frame.configure(
                bg=card_bg,
                relief='flat',
                borderwidth=1,
                highlightbackground=config.GRAY_300 if not dark else config.GRAY_600,
                highlightthickness=1,
                padx=config.SPACING_LG,
                pady=config.SPACING_LG
            )
        except Exception:
            pass
    
    # Control frame with better spacing
    try:
        tab.ctrl.configure(
            bg=bg,
            padx=config.SPACING_BASE,
            pady=config.SPACING_SM
        )
    except Exception:
        pass
    
    # Settings frame with card styling
    try:
        tab.sf.configure(
            bg=card_bg,
            relief='flat',
            borderwidth=1,
            highlightbackground=config.GRAY_300 if not dark else config.GRAY_600,
            highlightthickness=1,
            padx=config.SPACING_LG,
            pady=config.SPACING_LG,
            font=modern_font_bold
        )
    except Exception:
        pass
    
    # Canvas with modern styling
    tab.canvas.config(
        bg=bg, 
        highlightbackground=bg, 
        highlightthickness=0,
        relief='flat'
    )
    
    # Modern text widgets with enhanced card-like appearance and better dark mode contrast
    for t in tab.text_widgets:
        # Enhanced contrast for dark mode
        text_bg = config.DARK_ENTRY_BG if dark else config.LIGHT_ENTRY_BG
        text_fg = "#ffffff" if dark else "#222222"  # Pure white for dark mode, dark gray for light
        cursor_color = "#ffffff" if dark else "#000000"  # White cursor in dark mode
        
        t.configure(
            bg=text_bg,
            fg=text_fg,
            insertbackground=cursor_color,
            font=modern_font,
            relief='flat',
            borderwidth=1,
            highlightthickness=2,
            highlightcolor=config.PRIMARY_BLUE,
            highlightbackground=config.GRAY_500 if dark else config.GRAY_300,
            selectbackground=config.PRIMARY_BLUE if dark else config.PRIMARY_BLUE_LIGHT,
            selectforeground="white",
            padx=config.SPACING_BASE,
            pady=config.SPACING_SM,
            # Enhanced readability
            wrap='word',
            spacing1=2,  # Extra line spacing for readability
            spacing3=2
        )
    
    # Update placeholder colors
    update_placeholder_color(tab, dark)
    
    # Modern button styling - create buttons on first run, update theme on subsequent runs
    if not hasattr(tab, '_modern_buttons_created'):
        _replace_buttons_with_modern(tab, dark)
    else:
        update_button_theme(tab, dark)
    
    # WPM LABEL - FORCE GREEN IMMEDIATELY AND KEEP IT THAT WAY
    if hasattr(tab, 'wpm_label'):
        tab.wpm_label.configure(bg=bg, fg=config.SUCCESS_GREEN, font=modern_font_bold)
        print(f"[THEME] WPM label forced to green: {config.SUCCESS_GREEN}")
        # Force another update after delay to ensure it sticks
        tab.after(10, lambda: tab.wpm_label.configure(fg=config.SUCCESS_GREEN) if hasattr(tab, 'wpm_label') else None)
    
    # Modern labels - WPM LABEL MUST BE FIRST TO AVOID OVERRIDE
    for widget in tab.widgets_to_style:
        if hasattr(tab, 'wpm_label') and widget is tab.wpm_label:
            # WPM ALWAYS GREEN - FORCE OVERRIDE
            widget.configure(bg=bg, fg=config.SUCCESS_GREEN, font=modern_font_bold)
        elif widget.__class__.__name__ == "Label":
            # Skip wpm_label if it was already handled
            if not (hasattr(tab, 'wpm_label') and widget is tab.wpm_label):
                widget.configure(bg=bg, fg=fg, font=modern_font)
        elif widget.__class__.__name__ != "Button":  # Skip buttons, handled above
            try:
                # Skip wpm_label if it was already handled  
                if not (hasattr(tab, 'wpm_label') and widget is tab.wpm_label):
                    widget.configure(bg=bg, fg=fg, font=modern_font)
            except Exception:
                pass
    
    # Modern labelframe
    tab.sf.configure(bg=bg, fg=fg, font=modern_font_bold)
    for child in tab.sf.winfo_children():
        if child.__class__.__name__ == "Label":
            child.configure(bg=bg, fg=fg, font=modern_font)
    
    # Status label with enhanced contrast - CRITICAL FINAL OVERRIDE
    status_fg = "#ffffff" if dark else "#222222"  # Enhanced contrast
    tab.status_label.configure(bg=bg, fg=status_fg, font=modern_font)
    # FORCE WMP LABEL TO GREEN WITH MULTIPLE METHODS
    tab.wpm_label.configure(bg=bg, fg=config.SUCCESS_GREEN, font=modern_font_bold)
    
    # AGGRESSIVE WPM FIX: Schedule multiple delayed updates to ensure green color sticks
    for delay in [1, 10, 50, 100, 200]:
        tab.after(delay, lambda: tab.wpm_label.configure(fg=config.SUCCESS_GREEN) if hasattr(tab, 'wpm_label') else None)
        
    print(f"[THEME DEBUG] WPM label configured to green {config.SUCCESS_GREEN} with multiple fallbacks")
    
    # Modern TTK styling
    _apply_modern_ttk_styles(tab, dark, bg, fg, entry_bg, entry_fg, modern_font, modern_font_bold)
    
    tab.update_idletasks()

def _replace_buttons_with_modern(tab, dark):
    """Create or replace buttons with modern styled versions - USING REGULAR BUTTONS FOR IMMEDIATE COLOR DISPLAY"""
    
    # Always recreate buttons to ensure proper theme colors
    if hasattr(tab, '_modern_buttons_created'):
        # Destroy existing buttons before recreating
        if tab.start_btn:
            tab.start_btn.destroy()
        if tab.pause_btn:
            tab.pause_btn.destroy()
        if tab.stop_btn:
            tab.stop_btn.destroy()
    
    # SIMPLE APPROACH: Use regular tkinter Button widgets with guaranteed immediate color display
    button_font = (config.FONT_PRIMARY, config.FONT_SIZE_BASE, 'bold')
    
    # All buttons same size with dark blue interior and distinctive border colors
    border_width = 2  # Minimalist border for clean modern look
    button_width = 12  # Same width for all buttons
    
    # START BUTTON - Use Frame wrapper approach for guaranteed visible borders
    start_wrapper = tk.Frame(tab.ctrl, bg=config.LIME_GREEN, bd=0, relief='flat')
    start_wrapper.pack(side='left', padx=(0, 8))
    
    tab.start_btn = tk.Button(
        start_wrapper,
        text="🚀 Start Typing",
        command=tab.start_typing,
        bg=config.PRIMARY_BLUE,
        fg="white",
        font=button_font,
        relief='flat',
        bd=0,
        cursor='hand2',
        width=button_width,
        height=1,
        activebackground=config.PRIMARY_BLUE_HOVER,
        activeforeground="white"
    )
    tab.start_btn.pack(padx=border_width, pady=border_width)
    
    # Add hover effects for start button
    def start_hover_enter(e):
        start_wrapper.configure(bg="#28A745")  # Brighter lime green
        tab.start_btn.configure(bg=config.PRIMARY_BLUE_HOVER)
    
    def start_hover_leave(e):
        start_wrapper.configure(bg=config.LIME_GREEN)
        tab.start_btn.configure(bg=config.PRIMARY_BLUE)
    
    tab.start_btn.bind("<Enter>", start_hover_enter)
    tab.start_btn.bind("<Leave>", start_hover_leave)
    start_wrapper.bind("<Enter>", start_hover_enter)
    start_wrapper.bind("<Leave>", start_hover_leave)
    
    # PAUSE BUTTON - Use Frame wrapper approach for guaranteed visible borders
    pause_wrapper = tk.Frame(tab.ctrl, bg=config.WARNING_ORANGE, bd=0, relief='flat')
    pause_wrapper.pack(side='left', padx=4)
    
    tab.pause_btn = tk.Button(
        pause_wrapper,
        text="⏸️ Pause",
        command=tab.toggle_pause,
        bg=config.PRIMARY_BLUE,
        fg="white",
        font=button_font,
        relief='flat',
        bd=0,
        cursor='hand2',
        width=button_width,
        height=1,
        activebackground=config.PRIMARY_BLUE_HOVER,
        activeforeground="white"
    )
    tab.pause_btn.pack(padx=border_width, pady=border_width)
    
    # Add hover effects for pause button
    def pause_hover_enter(e):
        pause_wrapper.configure(bg="#D97706")  # Brighter orange
        tab.pause_btn.configure(bg=config.PRIMARY_BLUE_HOVER)
    
    def pause_hover_leave(e):
        pause_wrapper.configure(bg=config.WARNING_ORANGE)
        tab.pause_btn.configure(bg=config.PRIMARY_BLUE)
    
    tab.pause_btn.bind("<Enter>", pause_hover_enter)
    tab.pause_btn.bind("<Leave>", pause_hover_leave)
    pause_wrapper.bind("<Enter>", pause_hover_enter)
    pause_wrapper.bind("<Leave>", pause_hover_leave)
    
    # STOP BUTTON - Use Frame wrapper approach for guaranteed visible borders
    stop_wrapper = tk.Frame(tab.ctrl, bg=config.DANGER_RED, bd=0, relief='flat')
    stop_wrapper.pack(side='right')
    
    tab.stop_btn = tk.Button(
        stop_wrapper,
        text="⏹️ Stop",
        command=tab.stop_typing_hotkey,
        bg=config.PRIMARY_BLUE,
        fg="white",
        font=button_font,
        relief='flat',
        bd=0,
        cursor='hand2',
        width=button_width,
        height=1,
        activebackground=config.PRIMARY_BLUE_HOVER,
        activeforeground="white"
    )
    tab.stop_btn.pack(padx=border_width, pady=border_width)
    
    # Add hover effects for stop button
    def stop_hover_enter(e):
        stop_wrapper.configure(bg="#DC2626")  # Brighter red
        tab.stop_btn.configure(bg=config.PRIMARY_BLUE_HOVER)
    
    def stop_hover_leave(e):
        stop_wrapper.configure(bg=config.DANGER_RED)
        tab.stop_btn.configure(bg=config.PRIMARY_BLUE)
    
    tab.stop_btn.bind("<Enter>", stop_hover_enter)
    tab.stop_btn.bind("<Leave>", stop_hover_leave)
    stop_wrapper.bind("<Enter>", stop_hover_enter)
    stop_wrapper.bind("<Leave>", stop_hover_leave)
    
    # Store wrapper references for theme updates
    tab._start_wrapper = start_wrapper
    tab._pause_wrapper = pause_wrapper
    tab._stop_wrapper = stop_wrapper
    
    tab._modern_buttons_created = True
    
    # FORCE IMMEDIATE COLOR DISPLAY - Apply colors to wrappers and buttons right after creation
    start_wrapper.configure(bg=config.LIME_GREEN)
    pause_wrapper.configure(bg=config.WARNING_ORANGE)
    stop_wrapper.configure(bg=config.DANGER_RED)
    tab.start_btn.configure(bg=config.PRIMARY_BLUE, fg="white")
    tab.pause_btn.configure(bg=config.PRIMARY_BLUE, fg="white")
    tab.stop_btn.configure(bg=config.PRIMARY_BLUE, fg="white")
    
    # Multiple force updates to ensure colors appear on startup
    tab.ctrl.update_idletasks()
    tab.update_idletasks()
    
    # Immediate second update with no delay
    start_wrapper.configure(bg=config.LIME_GREEN)
    pause_wrapper.configure(bg=config.WARNING_ORANGE)
    stop_wrapper.configure(bg=config.DANGER_RED)
    
    # Force delayed refresh to catch any late initialization
    tab.after_idle(lambda: [
        start_wrapper.configure(bg=config.LIME_GREEN),
        pause_wrapper.configure(bg=config.WARNING_ORANGE),
        stop_wrapper.configure(bg=config.DANGER_RED)
    ])
    
    print("[BUTTON] Created regular buttons with immediate color display!")
    print(f"[BUTTON] Start button: bg={config.PRIMARY_BLUE}, border={config.LIME_GREEN}")
    print(f"[BUTTON] Pause button: bg={config.PRIMARY_BLUE}, border={config.WARNING_ORANGE}")
    print(f"[BUTTON] Stop button: bg={config.PRIMARY_BLUE}, border={config.DANGER_RED}")

def update_button_theme(tab, dark):
    """Update button colors for theme switching without recreating"""
    try:
        # All buttons use dark blue interior with distinctive wrapper borders
        if hasattr(tab, 'start_btn') and hasattr(tab, '_start_wrapper'):
            # Start button: lime green wrapper, dark blue interior
            tab._start_wrapper.configure(bg=config.LIME_GREEN)
            tab.start_btn.configure(bg=config.PRIMARY_BLUE, fg="white",
                                  activebackground=config.PRIMARY_BLUE_HOVER)
        
        if hasattr(tab, 'pause_btn') and hasattr(tab, '_pause_wrapper'):
            # Pause button: orange wrapper, dark blue interior
            tab._pause_wrapper.configure(bg=config.WARNING_ORANGE)
            tab.pause_btn.configure(bg=config.PRIMARY_BLUE, fg="white",
                                  activebackground=config.PRIMARY_BLUE_HOVER)
        
        if hasattr(tab, 'stop_btn') and hasattr(tab, '_stop_wrapper'):
            # Stop button: red wrapper, dark blue interior
            tab._stop_wrapper.configure(bg=config.DANGER_RED)
            tab.stop_btn.configure(bg=config.PRIMARY_BLUE, fg="white",
                                 activebackground=config.PRIMARY_BLUE_HOVER)
            
        print("[BUTTON] Updated button theme colors - all use dark blue interior with colored wrappers!")
    except Exception as e:
        print(f"[BUTTON] Error updating button theme: {e}")

def _apply_modern_ttk_styles(tab, dark, bg, fg, entry_bg, entry_fg, modern_font, modern_font_bold):
    """Apply modern TTK styles for sliders, checkboxes, etc."""
    
    # Use the app's TTK style instance to ensure consistency
    style = tab.app.tb_style
    
    # Modern color scheme
    primary = config.PRIMARY_BLUE_LIGHT if not dark else config.PRIMARY_BLUE
    primary_hover = config.PRIMARY_BLUE_LIGHT_HOVER if not dark else config.PRIMARY_BLUE_HOVER
    
    # TScale and TCheckbutton styling handled globally - no need to duplicate
    
    # Apply to scales and checkboxes - FORCE refresh
    for child in tab.sf.winfo_children():
        if isinstance(child, (ttk.Scale, ttk.Checkbutton)):
            # Force refresh to pick up global styling
            child.update_idletasks()
    
    # Entry styling handled globally - no need to duplicate
    
    
    # Modern button styling for ttk buttons - ALWAYS COLORED
    style.configure("TButton",  # Apply to ALL ttk buttons
                    background=primary,
                    foreground="white", 
                    borderwidth=0,
                    focuscolor="none",
                    relief='flat',
                    font=modern_font_bold,
                    padding=[config.SPACING_LG, config.SPACING_SM])
    
    style.map("TButton",  # Apply to ALL ttk buttons
              background=[('active', primary_hover),
                         ('pressed', primary_hover),
                         ('!active', primary),
                         ('disabled', config.GRAY_400)],
              foreground=[('active', "white"),
                         ('pressed', "white"), 
                         ('!active', "white"),
                         ('disabled', config.GRAY_600)])
    
    # Also configure the Modern.TButton style for consistency
    style.configure("Modern.TButton",
                    background=primary,
                    foreground="white",
                    borderwidth=0,
                    focuscolor="none", 
                    relief='flat',
                    font=modern_font_bold,
                    padding=[config.SPACING_LG, config.SPACING_SM])
    
    style.map("Modern.TButton",
              background=[('active', primary_hover),
                         ('pressed', primary_hover),
                         ('!active', primary)],
              foreground=[('active', "white"),
                         ('pressed', "white"),
                         ('!active', "white")])
    
    # Modern notebook styling with enhanced appearance
    tab_bg = config.GRAY_200 if not dark else config.GRAY_700
    tab_active = primary
    tab_fg = config.GRAY_700 if not dark else config.GRAY_300
    
    style.configure("Modern.TNotebook",
                    background=bg,
                    borderwidth=0,
                    tabposition="n")
    
    style.configure("Modern.TNotebook.Tab",
                    background=tab_bg,
                    foreground=tab_fg,
                    padding=[config.SPACING_XL, config.SPACING_BASE],
                    borderwidth=0,
                    font=modern_font_bold,
                    focuscolor='none')
    
    style.map("Modern.TNotebook.Tab",
              background=[
                  ('selected', tab_active),
                  ('active', primary_hover),
                  ('!selected', tab_bg)
              ],
              foreground=[
                  ('selected', 'white'),
                  ('active', 'white'),
                  ('!selected', tab_fg)
              ])

def update_placeholder_color(tab, dark):
    """Update placeholder colors with modern palette and enhanced visibility"""
    # Better contrast for placeholders in dark mode
    placeholder_fg = config.GRAY_500 if not dark else config.GRAY_400  # Lighter gray for dark mode
    entry_fg = "#ffffff" if dark else "#222222"  # Match the enhanced text colors
    
    tab.text_input.tag_configure("placeholder", foreground=placeholder_fg)
    tab.live_preview.tag_configure("placeholder", foreground=placeholder_fg)
    
    # Apply current state with enhanced contrast
    if tab.text_input.get('1.0', 'end').strip() == tab.PLACEHOLDER_INPUT:
        tab.text_input.config(fg=placeholder_fg)
    else:
        tab.text_input.config(fg=entry_fg)
        
    if tab.live_preview.get('1.0', 'end').strip() == tab.PLACEHOLDER_PREVIEW:
        tab.live_preview.config(fg=placeholder_fg)
    else:
        tab.live_preview.config(fg=entry_fg)

def get_entry_fg(dark=False):
    """Get entry foreground color"""
    return config.DARK_FG if dark else config.LIGHT_FG

def get_placeholder_fg(dark=False):
    """Get placeholder foreground color"""
    return config.GRAY_400 if not dark else config.GRAY_500

# update_placeholder_color function already defined above - removed duplicate