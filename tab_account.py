import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from auth import sign_in_with_google, sign_out, get_saved_user
import requests

SERVER_URL = "https://slywriterapp.onrender.com"

class AccountTab(ttk.Frame):
    USAGE_FILE = "usage_data.json"

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.words_used = 0
        self.plan = "free"
        self.google_info = None
        self._pending_auto_login = None

        self.plan_limits = {
            'free': 10000,
            'pro': 50000,
            'enterprise': None
        }

        self.build_ui()

        saved = get_saved_user()
        if saved:
            self._pending_auto_login = saved

        self.start_auto_update()

    def build_ui(self):
        self.signin_btn = ttk.Button(self, text="Sign In with Google", command=self._do_google_sign_in)
        self.signin_btn.pack(pady=10)

        self.status_label = ttk.Label(self, text="")
        self.status_label.pack(pady=5)

        ttk.Button(self, text="Manual Sign In", command=self._do_manual_sign_in).pack(pady=10)
        ttk.Button(self, text="Log Out", command=self._do_logout).pack(pady=10)

        self.usage_label = ttk.Label(self, text="")
        self.usage_label.pack(pady=(20, 2))

        self.canvas = tk.Canvas(self, width=300, height=20, bd=0, highlightthickness=0)
        self.canvas.pack()
        self.progress_bar = self.canvas.create_rectangle(0, 0, 0, 20, fill="green", outline="")

    def _do_google_sign_in(self):
        info = sign_in_with_google()
        if info:
            self.google_info = info
            self.load_usage()
            self.app.on_login(info)
            self._render_user_status()
            self.update_usage_display()

    def _do_manual_sign_in(self):
        info = {"id": "man123", "email": "man@example.com", "name": "Manual User"}
        self.google_info = info
        self.load_usage()
        self.app.on_login(info)
        self._render_user_status()
        self.update_usage_display()

    def _do_logout(self):
        sign_out()
        self.google_info = None
        self.words_used = 0
        self.update_usage_display()
        self._render_user_status()
        self.app.on_logout()
        messagebox.showinfo("Logged Out", "You have been logged out.")

    def _render_user_status(self):
        if self.google_info:
            email = self.google_info.get("email", "Unknown")
            self.status_label.config(text=f"Signed in as: {email}")
            self.signin_btn.pack_forget()
        else:
            self.status_label.config(text="")
            self.signin_btn.pack(pady=10)

    def update_for_login(self, user_info):
        self.google_info = user_info
        self.load_usage()
        self._render_user_status()
        self.update_usage_display()

    def get_user_plan(self):
        return self.plan

    def get_gradient_color(self, percent: float) -> str:
        percent = max(0, min(percent, 1))
        if percent < 0.5:
            r = int(255 * (percent * 2))
            g = 255
        else:
            r = 255
            g = int(255 * (1 - (percent - 0.5) * 2))
        b = 0
        return f'#{r:02x}{g:02x}{b:02x}'

    def update_usage_display(self):
        current_plan = self.get_user_plan()
        limit = self.plan_limits[current_plan]

        if limit is None:
            self.usage_label.config(text="Enterprise Plan – Unlimited words")
            self.canvas.itemconfig(self.progress_bar, fill="", outline="")
            self.canvas.coords(self.progress_bar, 0, 0, 300, 0)
            return

        percent = min(self.words_used / limit, 1.0)
        color = self.get_gradient_color(percent)
        label_text = f"{current_plan.capitalize()} Plan – {self.words_used:,} / {limit:,} words"
        self.usage_label.config(text=label_text)

        bar_width = int(300 * percent)
        self.canvas.coords(self.progress_bar, 0, 0, bar_width, 20)
        self.canvas.itemconfig(self.progress_bar, fill=color)

    def start_auto_update(self):
        self.update_usage_display()
        self.after(5000, self.start_auto_update)

    def increment_words_used(self, amount=10):
        self.words_used += amount
        self.save_usage()
        self.update_usage_display()
        self._sync_usage_to_server(amount)

    def has_words_remaining(self):
        limit = self.plan_limits.get(self.plan)
        return limit is None or self.words_used < limit

    def save_usage(self):
        if not self.google_info:
            return
        try:
            uid = self.google_info.get("id", "unknown")
            data = {}

            if os.path.exists(self.USAGE_FILE):
                with open(self.USAGE_FILE, 'r') as f:
                    data = json.load(f)

            data[uid] = self.words_used

            with open(self.USAGE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print("⚠️ Failed to save usage data:", e)

    def load_usage(self):
        if not self.google_info:
            return

        uid = self.google_info.get("id", "unknown")

        # Try server first
        try:
            resp = requests.get(f"{SERVER_URL}/get_usage", params={"user_id": uid})
            if resp.status_code == 200:
                self.words_used = resp.json().get("words", 0)
                self.save_usage()  # sync to local
                self.update_usage_display()
                return
        except Exception as e:
            print("⚠️ Failed to load usage data from server:", e)

        # Fallback to local
        try:
            if os.path.exists(self.USAGE_FILE):
                with open(self.USAGE_FILE, 'r') as f:
                    data = json.load(f)
                    self.words_used = data.get(uid, 0)
            else:
                self.words_used = 0
            self.update_usage_display()
        except Exception as e2:
            print("⚠️ Failed to load local usage data:", e2)

    def _sync_usage_to_server(self, amount):
        if not self.google_info:
            return
        try:
            requests.post(f"{SERVER_URL}/update_usage", json={
                "user_id": self.google_info.get("id", "unknown"),
                "words": amount
            })
        except Exception as e:
            print("⚠️ Failed to sync to server:", e)
