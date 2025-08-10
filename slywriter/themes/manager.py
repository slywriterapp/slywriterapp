"""Consolidated theme management for SlyWriter."""

from ..core.config import DARK_BG, LIGHT_BG, DARK_FG, LIGHT_FG, DARK_ENTRY_BG, LIME_GREEN
from tkinter import ttk


def apply_app_theme(app):
    """Apply theme to the main application window."""
    dark = app.cfg['settings'].get('dark_mode', False)

    # Get colors safely, fallback if needed
    def get_color(name, default):
        try:
            return app.tb_style.colors.get(name)
        except Exception:
            return default

    bg = get_color('bg', DARK_BG if dark else LIGHT_BG)
    fg = get_color('fg', DARK_FG if dark else LIGHT_FG)
    entry_bg = get_color('inputbg', DARK_ENTRY_BG if dark else "white")
    entry_fg = get_color('inputfg', LIGHT_FG if dark else DARK_FG)
    accent = get_color('primary', "#003366")

    app.configure(bg=bg)

    # Combobox colors update + force redraw to fix selected text color bug
    app.prof_box.configure(background=entry_bg, foreground=entry_fg)
    app.prof_box.event_generate('<FocusOut>')
    app.prof_box.event_generate('<FocusIn>')

    # Update all tabs for theme change
    app.typing_tab.set_theme(dark)
    app.hotkeys_tab.set_theme(dark)
    app.stats_tab.set_theme(dark)
    app.humanizer_tab.set_theme(dark)
    app.account_tab.set_theme(dark)

    # Force idle update to refresh widgets fully
    app.update_idletasks()


def force_theme_refresh(app):
    """Force a complete theme refresh."""
    current = app.cfg.get('settings', {}).get('dark_mode', False)
    app.cfg['settings']['dark_mode'] = not current
    apply_app_theme(app)
    app.cfg['settings']['dark_mode'] = current
    apply_app_theme(app)


def apply_typing_theme(tab, dark):
    """Apply theme to the typing tab."""
    bg = DARK_BG if dark else LIGHT_BG
    fg = DARK_FG if dark else LIGHT_FG
    entry_bg = DARK_ENTRY_BG if dark else "white"
    entry_fg = get_entry_fg(dark)
    accent = "#003366"

    # All backgrounds for frames/canvas
    for frame in [
        tab, tab.container, tab.content,
        tab.frame_in, tab.lp_frame, tab.ctrl, tab.sf
    ]:
        try:
            frame.configure(bg=bg)
        except Exception:
            pass

    # Canvas
    tab.canvas.config(bg=bg, highlightbackground=bg, highlightthickness=0)

    # Text widgets
    for t in tab.text_widgets:
        t.configure(bg=entry_bg, insertbackground=entry_fg)

    update_placeholder_color(tab, dark)


def apply_account_theme(tab, dark):
    """Apply theme to the account tab."""
    bg = DARK_BG if dark else LIGHT_BG
    fg = LIGHT_FG if dark else DARK_FG
    canvas_bg = "#232323" if dark else "#e0e0e0"

    # Frame itself
    try:
        tab.configure(bg=bg)
    except Exception:
        pass

    # Make or update a dedicated Sly.TButton style for contrast
    style = ttk.Style()
    btn_style = "Sly.TButton"
    if dark:
        style.configure(btn_style, background="#232323", foreground="white", borderwidth=2, focusthickness=2)
    else:
        style.configure(btn_style, background="#f5f5f5", foreground="black", borderwidth=2, focusthickness=2)

    # Direct known attributes (labels)
    for attr in ['status_label', 'usage_label', 'referral_label']:
        widget = getattr(tab, attr, None)
        if widget:
            try:
                widget.configure(background=bg, foreground=fg)
            except Exception:
                pass

    # Apply to all buttons with the custom style
    for attr in dir(tab):
        widget = getattr(tab, attr, None)
        if hasattr(widget, 'configure') and hasattr(widget, 'cget'):
            try:
                if widget.winfo_class() == 'TButton':
                    widget.configure(style=btn_style)
            except Exception:
                pass


def get_entry_fg(dark):
    """Get entry foreground color based on theme."""
    return DARK_FG if dark else LIGHT_FG


def get_placeholder_fg(dark):
    """Get placeholder text color based on theme."""
    return "#999999" if dark else "#888888"


def update_placeholder_color(tab, dark):
    """Update placeholder text colors."""
    placeholder_fg = get_placeholder_fg(dark)
    entry_fg = get_entry_fg(dark)
    
    # Update placeholder colors for text widgets
    for t in getattr(tab, 'text_widgets', []):
        try:
            current_text = t.get("1.0", "end-1c")
            if current_text in [tab.PLACEHOLDER_INPUT, tab.PLACEHOLDER_PREVIEW]:
                t.config(fg=placeholder_fg)
            else:
                t.config(fg=entry_fg)
        except Exception:
            pass