import tkinter as tk
from tkinter import ttk
import config

def apply_account_theme(tab, dark):
    """
    Apply SlyWriter Account tab theme (background, fg, canvas, etc) and force proper ttk Button styling.
    """
    bg        = config.DARK_BG if dark else config.LIGHT_BG
    fg        = config.LIGHT_FG if dark else config.DARK_FG
    canvas_bg = "#232323" if dark else "#e0e0e0"

    # Frame itself
    try:
        tab.configure(bg=bg)
    except Exception:
        pass

    # --- Make or update a dedicated Sly.TButton style for contrast ---
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
                widget.configure(bg=bg, fg=fg)
            except Exception:
                try:
                    widget.configure(background=bg, foreground=fg)
                except Exception:
                    pass

    # All children: Buttons and other labels/canvases
    for child in tab.winfo_children():
        if isinstance(child, ttk.Button):
            try:
                child.configure(style=btn_style)
            except Exception:
                pass
        elif isinstance(child, tk.Button):  # fallback: for any old tk.Buttons
            try:
                child.configure(bg=bg, fg=fg)
            except Exception:
                pass
        elif isinstance(child, (tk.Label, ttk.Label)):
            try:
                child.configure(bg=bg, fg=fg)
            except Exception:
                try:
                    child.configure(background=bg, foreground=fg)
                except Exception:
                    pass
        elif isinstance(child, tk.Canvas):
            try:
                child.configure(bg=canvas_bg, highlightthickness=0, bd=0)
            except Exception:
                pass

    # Canvas/progress bar custom bg
    if hasattr(tab, "canvas") and isinstance(tab.canvas, tk.Canvas):
        try:
            tab.canvas.configure(bg=canvas_bg, highlightthickness=0, bd=0)
        except Exception:
            pass
