# sly_splash.py

import os
import ttkbootstrap as tb
from PIL import Image, ImageTk
import threading
import time

def show_splash_screen(app, after_callback):
    splash = tb.Toplevel(app)
    splash.overrideredirect(True)
    splash.geometry("600x460+500+250")
    sly_bg = "#181816"
    splash.configure(bg=sly_bg)
    splash.update_idletasks()

    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slywriter_logo.png")
    logo = Image.open(logo_path).resize((250, 250), Image.LANCZOS)
    logo_img = ImageTk.PhotoImage(logo)

    logo_label = tb.Label(splash, image=logo_img, bootstyle="default", background=sly_bg)
    logo_label.image = logo_img
    logo_label.pack(pady=(60, 20))

    text_label = tb.Label(splash, text="", bootstyle="default", foreground="lime", background=sly_bg, font=("Courier", 28, "bold"))
    text_label.pack()

    def animate_typing():
        for ch in "SlyWriter":
            text_label.config(text=text_label.cget("text") + ch)
            splash.update()
            time.sleep(3 / len("SlyWriter"))
        time.sleep(1.5)
        splash.destroy()
        app.after(10, after_callback)

    threading.Thread(target=animate_typing, daemon=True).start()
