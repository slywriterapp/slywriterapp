#!/usr/bin/env python3
"""
Reset Terms Acceptance

This script removes the terms acceptance from config.json,
forcing the terms dialog to appear on next app launch.

Usage: python reset_terms_acceptance.py
"""

import json
import os

def reset_terms():
    """Remove terms acceptance from config"""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")

    if not os.path.exists(config_path):
        print("[ERROR] config.json not found")
        return False

    try:
        # Load config
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Remove legal section if exists
        if "legal" in config:
            del config["legal"]
            print("[OK] Removed 'legal' section from config")
        else:
            print("[INFO] No 'legal' section found in config (already reset)")

        # Save config
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        print("[SUCCESS] Terms acceptance reset!")
        print("[NEXT] Launch the app to see the terms dialog")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to reset terms: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("RESET TERMS ACCEPTANCE")
    print("=" * 60)
    print()

    success = reset_terms()

    print()
    print("=" * 60)
    if success:
        print("✓ Reset complete")
    else:
        print("✗ Reset failed")
    print("=" * 60)
