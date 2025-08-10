# account_usage.py

import os
import json
import requests
from referral_manager import ReferralManager

SERVER_URL = "https://slywriterapp.onrender.com"

class AccountUsageManager:
    USAGE_FILE = "usage_data.json"
    plan_limits = {
        'free': 4000,
        'pro': 40000,
        'enterprise': None
    }

    def __init__(self, account_tab):
        self.account_tab = account_tab
        self.words_used = 0
        self.plan = "free"
        self.word_limit = 4000
        self.referral_mgr = ReferralManager()
        self.user_id = None

    def get_user_plan(self):
        return self.plan

    def get_word_limit(self):
        plan_limit = self.plan_limits.get(self.plan)
        referral_bonus = self.referral_mgr.get_referral_bonus() if self.plan == "free" else 0
        if plan_limit is None:
            return None
        return plan_limit + referral_bonus

    def update_usage_display(self):
        current_plan = self.get_user_plan()
        limit = self.get_word_limit()
        self.word_limit = limit  # update for UI

        if limit is None:
            self.account_tab.usage_label.config(text="Enterprise Plan – Unlimited words")
            self.account_tab.canvas.itemconfig(self.account_tab.progress_bar, fill="", outline="")
            self.account_tab.canvas.coords(self.account_tab.progress_bar, 0, 0, 300, 0)
            self.account_tab.referral_label.config(text="")
            return

        percent = min(self.words_used / limit, 1.0)
        color = self.get_gradient_color(percent)
        label_text = f"{current_plan.capitalize()} Plan – {self.words_used:,} / {limit:,} words"

        bonus = self.referral_mgr.get_referral_bonus()
        if current_plan == "free" and bonus > 0:
            label_text += f" (+{bonus} from referrals)"

        self.account_tab.usage_label.config(text=label_text)
        bar_width = int(300 * percent)
        self.account_tab.canvas.coords(self.account_tab.progress_bar, 0, 0, bar_width, 20)
        self.account_tab.canvas.itemconfig(self.account_tab.progress_bar, fill=color)

        code = self.referral_mgr.referral_code
        if code:
            self.account_tab.referral_label.config(
                text=f"Refer friends & earn more words:\nhttps://slywriter.com/signup?ref={code}"
            )
        else:
            self.account_tab.referral_label.config(text="")

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

    def increment_words_used(self, amount=10):
        self.words_used += amount
        self.save_usage()
        self.update_usage_display()
        self._sync_usage_to_server(amount)

    def has_words_remaining(self):
        limit = self.get_word_limit()
        return limit is None or self.words_used < limit

    def save_usage(self):
        google_info = getattr(self.account_tab, 'google_info', None)
        if not google_info:
            return
        try:
            uid = google_info.get("id", "unknown")
            data = {}
            if os.path.exists(self.USAGE_FILE):
                with open(self.USAGE_FILE, 'r') as f:
                    data = json.load(f)
            data[uid] = {
                "words_used": self.words_used,
                "referrals": self.referral_mgr.referrals,
                "referral_code": self.referral_mgr.referral_code
            }
            with open(self.USAGE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print("⚠️ Failed to save usage data:", e)

    def load_usage(self):
        google_info = getattr(self.account_tab, 'google_info', None)
        if not google_info:
            return

        uid = google_info.get("id", "unknown")
        self.user_id = uid
        self.referral_mgr.set_user_id(uid)

        try:
            usage_resp = requests.get(f"{SERVER_URL}/get_usage", params={"user_id": uid})
            if usage_resp.status_code == 200:
                self.words_used = usage_resp.json().get("words", 0)
            else:
                self.words_used = 0

            plan_resp = requests.get(f"{SERVER_URL}/get_plan", params={"user_id": uid})
            if plan_resp.status_code == 200:
                self.plan = plan_resp.json().get("plan", "free")

            self.save_usage()
            self.update_usage_display()
            
            # Force immediate UI update after server data loads
            self.account_tab.update_idletasks()
            return
        except Exception as e:
            print("⚠️ Failed to load usage or plan from server:", e)

        # fallback: load local
        try:
            if os.path.exists(self.USAGE_FILE):
                with open(self.USAGE_FILE, 'r') as f:
                    data = json.load(f)
                    user_data = data.get(uid, {})
                    if isinstance(user_data, dict):
                        self.words_used = user_data.get("words_used", 0)
                        self.referral_mgr.referrals = user_data.get("referrals", 0)
                        self.referral_mgr.referral_code = user_data.get("referral_code", "")
                    else:
                        self.words_used = user_data
            else:
                self.words_used = 0
            self.update_usage_display()
        except Exception as e2:
            print("⚠️ Failed to load local usage data:", e2)

    def _sync_usage_to_server(self, amount):
        google_info = getattr(self.account_tab, 'google_info', None)
        if not google_info:
            return
        try:
            requests.post(f"{SERVER_URL}/update_usage", json={
                "user_id": google_info.get("id", "unknown"),
                "words": amount
            })
        except Exception as e:
            print("⚠️ Failed to sync to server:", e)
