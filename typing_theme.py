# typing_theme.py

import config
from config import LIME_GREEN

def apply_typing_theme(tab, dark):
    bg = config.DARK_BG if dark else config.LIGHT_BG
    fg = config.DARK_FG if dark else config.LIGHT_FG
    entry_bg = config.DARK_ENTRY_BG if dark else "white"
    entry_fg = get_entry_fg(dark)
    accent = "#4a90e2" if dark else "#0078d7"

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

    # Label and button colors
    for widget in tab.widgets_to_style:
        if hasattr(tab, 'wpm_label') and widget is tab.wpm_label:
            widget.configure(bg=bg, fg=LIME_GREEN)
        elif widget.__class__.__name__ == "Label":
            widget.configure(bg=bg, fg=fg)
        elif widget.__class__.__name__ == "Button":
            btn_bg = accent if widget is tab.start_btn else ("orange" if widget is tab.pause_btn else "red")
            widget.configure(bg=btn_bg, activebackground=btn_bg, fg="white", relief="raised")
        else:
            try:
                widget.configure(bg=bg, fg=fg)
            except Exception:
                pass

    # Settings labelframe
    tab.sf.configure(bg=bg)
    for child in tab.sf.winfo_children():
        if child.__class__.__name__ == "Label":
            child.configure(bg=bg, fg=fg)

    # Status label
    tab.status_label.configure(bg=bg, fg=fg)
    tab.wpm_label.configure(bg=bg, fg=LIME_GREEN)

    try:
        tab.app.prof_box.configure(background=entry_bg, foreground=entry_fg)
    except Exception:
        pass

    # Style ttk scales/entries/checks for best match
    import tkinter.ttk as ttk
    style = ttk.Style()
    style.theme_use("default")
    slider_trough = "#444444" if dark else "#cccccc"
    style.configure("TScale",
                    troughcolor=slider_trough,
                    background=bg)
    style.configure("TEntry",
                    fieldbackground=entry_bg,
                    foreground=entry_fg,
                    background=entry_bg)
    style.configure("TCheckbutton",
                    background=bg, foreground=fg)
    style.configure("TLabelframe",
                    background=bg, foreground=fg)
    style.configure("TLabelframe.Label",
                    background=bg, foreground=fg)

    tab.update_idletasks()

def update_placeholder_color(tab, dark):
    placeholder_fg = get_placeholder_fg(dark)
    entry_fg = get_entry_fg(dark)
    tab.text_input.tag_configure("placeholder", foreground=placeholder_fg)
    tab.live_preview.tag_configure("placeholder", foreground=placeholder_fg)
    # If placeholder is present, use gray, otherwise normal fg
    if tab.text_input.get('1.0', 'end').strip() == tab.PLACEHOLDER_INPUT:
        tab.text_input.config(fg=placeholder_fg)
    else:
        tab.text_input.config(fg=entry_fg)
    if tab.live_preview.get('1.0', 'end').strip() == tab.PLACEHOLDER_PREVIEW:
        tab.live_preview.config(fg=placeholder_fg)
    else:
        tab.live_preview.config(fg=entry_fg)

def get_entry_fg(dark=False):
    # Only one parameter, "dark"
    return config.LIGHT_FG if not dark else config.DARK_FG

def get_placeholder_fg(dark=False):
    # Only one parameter, "dark"
    return "#888"  # Can adjust for dark/light mode if needed
