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
            # Use the user endpoint which includes referral data
            resp = requests.get(f"{SERVER_URL}/api/auth/user/{self.user_id}")
            if resp.status_code == 200:
                data = resp.json()
                # Extract referral data from nested object
                referral_data = data.get("referrals", {})
                self.referrals = referral_data.get("count", 0)
                self.referral_code = referral_data.get("code", "")
                # Note: referred_by is not included in the API response
                # tier_claimed indicates if any bonuses have been claimed
                self.bonus_claimed = referral_data.get("tier_claimed", 0) > 0
        except Exception as e:
            print("⚠️ Failed to load referrals:", e)

    def get_referral_bonus(self):
        # returns bonus words for this user's referrals
        return (self.referrals // 2) * 1000

    def set_user_id(self, user_id):
        self.user_id = user_id
        self.load_from_server()
