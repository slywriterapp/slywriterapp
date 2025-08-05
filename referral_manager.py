# referral_manager.py

import requests

SERVER_URL = "https://slywriterapp.onrender.com"

class ReferralManager:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.referrals = 0
        self.referral_code = ""
        self.referred_by = None
        self.bonus_claimed = False

    def load_from_server(self):
        if not self.user_id:
            return
        try:
            resp = requests.get(f"{SERVER_URL}/get_referrals", params={"user_id": self.user_id})
            if resp.status_code == 200:
                data = resp.json()
                self.referrals = data.get("referrals", 0)
                self.referral_code = data.get("referral_code", "")
                self.referred_by = data.get("referred_by", None)
                self.bonus_claimed = data.get("bonus_claimed", False)
        except Exception as e:
            print("⚠️ Failed to load referrals:", e)

    def get_referral_bonus(self):
        # returns bonus words for this user's referrals
        return (self.referrals // 2) * 1000

    def set_user_id(self, user_id):
        self.user_id = user_id
        self.load_from_server()
