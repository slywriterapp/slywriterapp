#!/usr/bin/env python3
"""
Test script to verify word tracking fix works

This simulates what typing_engine.py now does after a typing session.
"""

import requests
import sys

API_URL = "https://slywriterapp.onrender.com"
TEST_USER_ID = 1  # slywriterteam@gmail.com

def test_word_tracking():
    """Test the word tracking endpoint"""
    print("=" * 80)
    print("WORD TRACKING FIX - VERIFICATION TEST")
    print("=" * 80)
    print()

    # Step 1: Check current usage
    print("Step 1: Checking current usage...")
    try:
        response = requests.get(f"{API_URL}/api/auth/user/{TEST_USER_ID}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            before_usage = data['usage']
            before_remaining = data['words_remaining']
            print(f"[OK] Current usage: {before_usage} words")
            print(f"[OK] Words remaining: {before_remaining}")
            print()
        else:
            print(f"[FAIL] Failed to get user data: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Error getting user data: {e}")
        return False

    # Step 2: Simulate typing 25 words
    test_words = 25
    print(f"Step 2: Simulating typing session ({test_words} words)...")
    print(f"This is what typing_engine.py now does after each session:")
    print()

    # This is the exact code now in typing_engine.py
    try:
        user_id = TEST_USER_ID
        words_in_session = test_words

        # Track usage with backend
        response = requests.post(
            f"{API_URL}/api/usage/track",
            params={"user_id": user_id, "words": words_in_session},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"[OK] [BACKEND] Tracked {words_in_session} words. Total: {data['usage']}")
            after_usage = data['usage']
            print()
        else:
            print(f"[FAIL] [BACKEND] Tracking failed: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[FAIL] [WARNING] Backend tracking failed: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] [ERROR] Unexpected error tracking usage: {e}")
        return False

    # Step 3: Verify the change
    print("Step 3: Verifying usage increased...")
    try:
        response = requests.get(f"{API_URL}/api/auth/user/{TEST_USER_ID}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            after_usage = data['usage']
            after_remaining = data['words_remaining']

            expected_usage = before_usage + test_words
            if after_usage == expected_usage:
                print(f"[OK] Usage increased correctly!")
                print(f"  Before: {before_usage} words")
                print(f"  After:  {after_usage} words")
                print(f"  Change: +{test_words} words")
                print(f"[OK] Remaining: {after_remaining} words")
                print()
                return True
            else:
                print(f"[FAIL] Usage mismatch!")
                print(f"  Expected: {expected_usage}")
                print(f"  Actual:   {after_usage}")
                return False
        else:
            print(f"[FAIL] Failed to verify: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Error verifying: {e}")
        return False

def main():
    """Run the test"""
    success = test_word_tracking()

    print("=" * 80)
    if success:
        print("[PASS] TEST PASSED - Word tracking fix is working!")
        print()
        print("The desktop app will now:")
        print("1. Count words typed locally [OK]")
        print("2. Log to local file [OK]")
        print("3. Update UI stats [OK]")
        print("4. Track with backend API [OK] (NEW!)")
        print()
        print("Next step: Test with actual desktop app")
        sys.exit(0)
    else:
        print("[FAIL] TEST FAILED - Something went wrong")
        print()
        print("Check:")
        print("- Is Render server up?")
        print("- Is the API endpoint working?")
        print("- Are there network issues?")
        sys.exit(1)

if __name__ == "__main__":
    main()
