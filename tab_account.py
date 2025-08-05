import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.simpledialog as sd
from auth import sign_in_with_google, sign_out, get_saved_user
from account_usage import AccountUsageManager

SERVER_URL = "https://slywriterapp.onrender.com"

class AccountTab(tk.Frame):
    def __init__(self, parent, app):
        # Theme: white or black only
        dark = app.cfg['settings'].get('dark_mode', False)
        bg = "#181816" if dark else "#ffffff"
        super().__init__(parent, bg=bg)
        self.app = app
        self.google_info = None
        self._pending_auto_login = None

        self.usage_mgr = AccountUsageManager(self)
        # --- Add is_premium fallback if not present ---
        if not hasattr(self.usage_mgr, "is_premium"):
            self.usage_mgr.is_premium = lambda: getattr(self.usage_mgr, "plan", "free") in ("pro", "enterprise")

        self.bar_width = 300
        self.bar_height = 20

        self.build_ui(bg)

        saved = get_saved_user()
        if saved:
            self._pending_auto_login = saved

        self.start_auto_update()

    def build_ui(self, bg):
        # Use ttk.Buttons for proper theme support
        self.signin_btn = ttk.Button(self, text="Sign In with Google", command=self._do_google_sign_in)
        self.signin_btn.pack(pady=(20, 8))

        self.manual_btn = ttk.Button(self, text="Manual Sign In", command=self._do_manual_sign_in)
        self.manual_btn.pack(pady=8)

        self.logout_btn = ttk.Button(self, text="Log Out", command=self._do_logout)
        self.logout_btn.pack(pady=(8, 12))
        self.logout_btn.pack_forget()  # Hide by default

        self.status_label = tk.Label(self, text="", bg=bg)
        self.status_label.pack(pady=5)

        self.usage_label = tk.Label(self, text="", bg=bg)
        self.usage_label.pack(pady=(20, 2))

        # Progress bar with border
        self.canvas = tk.Canvas(self, width=self.bar_width, height=self.bar_height, bd=0, highlightthickness=0, bg=bg)
        self.canvas.pack()
        self.bar_border = self.canvas.create_rectangle(
            0, 0, self.bar_width, self.bar_height, outline="#000000", width=2
        )
        self.progress_bar = self.canvas.create_rectangle(
            0, 0, 0, self.bar_height, fill="#66ff00", outline=""
        )

        self.referral_label = tk.Label(self, text="", wraplength=280, justify="center", bg=bg)
        self.referral_label.pack(pady=5)

    def set_theme(self, dark):
        bg = "#181816" if dark else "#ffffff"
        fg = "white" if dark else "black"
        canvas_bg = bg

        for widget in [
            self, self.status_label, self.usage_label, self.referral_label
        ]:
            try:
                widget.configure(bg=bg, fg=fg)
            except Exception:
                pass
        self.canvas.configure(bg=canvas_bg)
        border_color = "#ffffff" if dark else "#000000"
        self.canvas.itemconfig(self.bar_border, outline=border_color)
        self.canvas.itemconfig(self.progress_bar, fill="#66ff00", outline="")

        # ttk Buttons are theme-aware so no need to configure color unless you want to override
        self.update_progress_bar(self.usage_mgr.words_used, self.usage_mgr.get_word_limit())

    def _do_google_sign_in(self):
        info = sign_in_with_google()
        if info:
            self.google_info = info
            # --- Referral bonus logic ---
            import requests
            try:
                uid = info.get("id")
                check = requests.get(f"{SERVER_URL}/get_referrals", params={"user_id": uid})
                if check.status_code == 200:
                    referred_by = check.json().get("referred_by")
                    bonus_check = check.json().get("bonus_claimed", False)
                    if referred_by and not bonus_check:
                        bonus_resp = requests.post(f"{SERVER_URL}/referral_bonus", json={
                            "referrer_id": referred_by,
                            "referred_id": uid
                        })
                        if bonus_resp.status_code == 200 and bonus_resp.json().get("status") == "bonus_applied":
                            messagebox.showinfo("Referral Bonus", "You and your referrer each earned 1000 bonus words!")
            except Exception as e:
                print("⚠️ Referral auto-bonus error:", e)

            self.usage_mgr.load_usage()
            self.app.on_login(info)
            self._render_user_status()
            self.usage_mgr.update_usage_display()

    def _do_manual_sign_in(self):
        email = sd.askstring("Manual Sign-In", "Enter your email:")
        if not email:
            return
        import requests
        try:
            r = requests.post(f"{SERVER_URL}/manual_login_start", json={"email": email})
            if r.status_code == 200:
                code = sd.askstring("Verify Email", "Enter the verification code sent to your email:")
                if not code:
                    return
                r2 = requests.post(f"{SERVER_URL}/manual_login_verify", json={"email": email, "code": code})
                if r2.status_code == 200:
                    user_info = r2.json()
                    self.google_info = user_info
                    self.usage_mgr.load_usage()
                    self.app.on_login(user_info)
                    self._render_user_status()
                    self.usage_mgr.update_usage_display()
                    messagebox.showinfo("Manual Sign-In", "Logged in successfully!")
                else:
                    messagebox.showerror("Manual Sign-In", "Invalid code. Try again.")
            else:
                messagebox.showerror("Manual Sign-In", "Could not send verification code. Try again.")
        except Exception as e:
            messagebox.showerror("Manual Sign-In", f"Error: {e}")

    def _do_logout(self):
        # 1. Clear session, usage, and UI
        sign_out()
        self.google_info = None
        self.usage_mgr.words_used = 0
        self.usage_mgr.referrals = 0
        self.usage_mgr.referral_code = None
        self.usage_mgr.plan = "free"
        self.usage_mgr.update_usage_display()
        self.status_label.config(text="")
        self.usage_label.config(text="")
        self.referral_label.config(text="")
        self.canvas.coords(self.progress_bar, 0, 0, 0, self.bar_height)
        # 2. Show sign-in buttons, hide logout
        self.signin_btn.pack(pady=(20, 8))
        self.manual_btn.pack(pady=8)
        self.logout_btn.pack_forget()
        # 3. App disables other tabs and selects Account
        self.app.on_logout()
        self.app.notebook.select(self.app.tabs["Account"])
        messagebox.showinfo("Logged Out", "You have been logged out.")

    def _render_user_status(self):
        # Hide sign-in buttons if signed in, show logout; vice versa if not
        if self.google_info:
            email = self.google_info.get("email", "Unknown")
            plan_str = "Premium" if self.is_premium() else "Free"
            self.status_label.config(text=f"Signed in as: {email}  •  {plan_str} Plan")
            self.signin_btn.pack_forget()
            self.manual_btn.pack_forget()
            self.logout_btn.pack(pady=(8, 12))
        else:
            self.status_label.config(text="")
            self.signin_btn.pack(pady=(20, 8))
            self.manual_btn.pack(pady=8)
            self.logout_btn.pack_forget()

    def is_premium(self):
        """Check premium status using AccountUsageManager."""
        return self.usage_mgr.is_premium()

    def update_for_login(self, user_info):
        self.google_info = user_info
        self.usage_mgr.load_usage()
        self._render_user_status()
        self.usage_mgr.update_usage_display()

    def start_auto_update(self):
        self.usage_mgr.update_usage_display()
        self.after(5000, self.start_auto_update)

    # --- Convenience proxies ---
    def increment_words_used(self, amount=10):
        self.usage_mgr.increment_words_used(amount)

    def has_words_remaining(self):
        return self.usage_mgr.has_words_remaining()

    # --- Progress bar update helper ---
    def update_progress_bar(self, used, limit):
        percent = min(used / max(1, limit), 1.0)
        fill_px = int(self.bar_width * percent)
        self.canvas.coords(self.progress_bar, 0, 0, fill_px, self.bar_height)
        # Border always stays as full bar
