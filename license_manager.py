"""
SlyWriter License Manager
Handles license verification, version checking, and device binding
"""

import requests
import hashlib
import platform
import uuid
import json
import os
from datetime import datetime, timedelta

class LicenseManager:
    def __init__(self, server_url="https://slywriterapp.onrender.com", app_version="2.1.6"):
        self.server_url = server_url
        self.app_version = app_version
        self.config_file = "license_config.json"
        self.license_data = None
        self.last_verification = None

    def generate_machine_id(self):
        """Generate unique machine ID based on hardware"""
        # Combine multiple hardware identifiers
        info = f"{platform.node()}-{uuid.getnode()}-{platform.machine()}"
        return hashlib.sha256(info.encode()).hexdigest()[:32]

    def get_device_name(self):
        """Get friendly device name"""
        return platform.node() or f"{platform.system()} Device"

    def load_local_license(self):
        """Load license data from local config"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None

    def save_local_license(self, license_data):
        """Save license data to local config"""
        with open(self.config_file, 'w') as f:
            json.dump(license_data, f, indent=2)

    def verify_license(self, license_key, force=False):
        """
        Verify license with server

        Args:
            license_key: User's email or JWT token
            force: Force verification even if recently verified

        Returns:
            dict: License verification result
        """
        # Check if we need to verify (every 30 minutes unless forced)
        if not force and self.last_verification:
            time_since_last = datetime.now() - self.last_verification
            if time_since_last < timedelta(minutes=30):
                print("[License] Using cached verification")
                return self.license_data

        print("[License] Verifying license with server...")

        machine_id = self.generate_machine_id()
        device_name = self.get_device_name()

        try:
            response = requests.post(
                f"{self.server_url}/api/license/verify",
                json={
                    "license_key": license_key,
                    "machine_id": machine_id,
                    "device_name": device_name,
                    "app_version": self.app_version
                },
                timeout=10
            )

            # Handle version upgrade required (426 status)
            if response.status_code == 426:
                result = response.json()
                print(f"[License] UPDATE REQUIRED: {result.get('message')}")
                return {
                    "valid": False,
                    "error": "update_required",
                    "message": result.get('message'),
                    "update_url": result.get('update_url'),
                    "current_version": result.get('current_version'),
                    "minimum_version": result.get('minimum_version')
                }

            # Handle other errors
            if response.status_code != 200:
                error_data = response.json()
                print(f"[License] Verification failed: {error_data.get('message')}")
                return {
                    "valid": False,
                    "error": error_data.get('error', 'unknown_error'),
                    "message": error_data.get('message', 'License verification failed'),
                    "devices": error_data.get('devices', [])
                }

            # Success
            result = response.json()
            self.license_data = result
            self.last_verification = datetime.now()

            # Save to local config
            self.save_local_license({
                "license_key": license_key,
                "machine_id": machine_id,
                "last_verified": self.last_verification.isoformat(),
                "user_email": result.get('user', {}).get('email'),
                "plan": result.get('user', {}).get('plan')
            })

            print(f"[License] Verification SUCCESS")
            print(f"[License] Plan: {result.get('user', {}).get('plan')}")
            print(f"[License] Features: {result.get('features_enabled')}")

            return result

        except requests.exceptions.Timeout:
            print("[License] Verification timeout - using grace period")
            # Allow grace period if we have recent verification
            local_data = self.load_local_license()
            if local_data and local_data.get('last_verified'):
                last_verified = datetime.fromisoformat(local_data['last_verified'])
                grace_period = datetime.now() - last_verified
                if grace_period < timedelta(hours=24):
                    print("[License] Using cached license (within 24h grace period)")
                    return {
                        "valid": True,
                        "grace_mode": True,
                        "message": "Using cached license (offline mode)"
                    }

            return {
                "valid": False,
                "error": "connection_failed",
                "message": "Could not connect to license server. Please check your internet connection."
            }

        except Exception as e:
            print(f"[License] Verification error: {e}")
            return {
                "valid": False,
                "error": "verification_failed",
                "message": str(e)
            }

    def check_feature_enabled(self, feature_name):
        """Check if a feature is enabled for current license"""
        if not self.license_data or not self.license_data.get('valid'):
            return False

        features = self.license_data.get('features_enabled', {})
        return features.get(feature_name, False)

    def get_plan(self):
        """Get current plan"""
        if not self.license_data or not self.license_data.get('valid'):
            return 'free'

        return self.license_data.get('user', {}).get('plan', 'free')

    def get_limits(self):
        """Get usage limits for current plan"""
        if not self.license_data or not self.license_data.get('valid'):
            return {}

        return self.license_data.get('limits', {})

    def should_show_update_notification(self):
        """Check if update notification should be shown"""
        if not self.license_data:
            return False

        version_info = self.license_data.get('version_info', {})
        return version_info.get('update_available', False)

    def get_update_url(self):
        """Get update download URL"""
        if not self.license_data:
            return "https://github.com/slywriterapp/slywriterapp/releases/latest"

        version_info = self.license_data.get('version_info', {})
        return version_info.get('update_url', "https://github.com/slywriterapp/slywriterapp/releases/latest")


# Global license manager instance
license_manager = None

def get_license_manager(server_url="https://slywriterapp.onrender.com", app_version="2.1.6"):
    """Get or create global license manager instance"""
    global license_manager
    if license_manager is None:
        license_manager = LicenseManager(server_url, app_version)
    return license_manager
