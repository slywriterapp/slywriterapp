"""Splash screen functionality."""

import os
import ttkbootstrap as tb
from PIL import Image, ImageTk
import threading
import time


def show_splash_screen(app, after_callback):
    """Show the application splash screen with animated logo."""
    splash = tb.Toplevel(app)
    splash.overrideredirect(True)
    splash.geometry("600x460+500+250")
    sly_bg = "#181816"
    splash.configure(bg=sly_bg)
    splash.update_idletasks()

    # Load and resize logo
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logo_path = os.path.join(script_dir, "slywriter_logo.png")
    
    try:
        logo = Image.open(logo_path).resize((250, 250), Image.LANCZOS)
        logo_img = ImageTk.PhotoImage(logo)

        logo_label = tb.Label(splash, image=logo_img, bootstyle="default", background=sly_bg)
        logo_label.image = logo_img
        logo_label.pack(pady=(60, 20))
    except Exception as e:
        print(f"Could not load logo: {e}")
        # Create a simple text logo as fallback
        logo_label = tb.Label(splash, text="SLY", bootstyle="default", 
                             foreground="lime", background=sly_bg, 
                             font=("Courier", 48, "bold"))
        logo_label.pack(pady=(60, 20))

    text_label = tb.Label(splash, text="", bootstyle="default", 
                         foreground="lime", background=sly_bg, 
                         font=("Courier", 28, "bold"))
    text_label.pack()

    def animate_typing():
        """Animate the typing of 'SlyWriter'."""
        app_name = "SlyWriter"
        for ch in app_name:
            text_label.config(text=text_label.cget("text") + ch)
            splash.update()
            time.sleep(3 / len(app_name))
        time.sleep(1.5)
        splash.destroy()
        app.after(10, after_callback)

    threading.Thread(target=animate_typing, daemon=True).start()