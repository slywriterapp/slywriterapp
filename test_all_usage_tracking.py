#!/usr/bin/env python3
"""
Comprehensive Usage Tracking Test Suite

Tests all usage tracking endpoints with the Render PostgreSQL database:
- Word tracking
- AI generation tracking
- Humanizer tracking

Run this BEFORE testing with desktop app to verify API endpoints work.
"""

import requests
import sys
import json
from datetime import datetime

API_URL = "https://slywriterapp.onrender.com"
TEST_USER_ID = 1  # slywriterteam@gmail.com

def print_header(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def get_user_usage():
    """Get current usage stats from server"""
    try:
        response = requests.get(f"{API_URL}/api/auth/user/{TEST_USER_ID}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[FAIL] Failed to get user data: {response.status_code}")
            return None
    except Exception as e:
        print(f"[FAIL] Error getting user data: {e}")
        return None

def test_word_tracking():
    """Test word usage tracking endpoint"""
    print_header("TEST 1: Word Usage Tracking")

    # Get before state
    print("\nStep 1: Get current usage...")
    before = get_user_usage()
    if not before:
        return False

    before_words = before['usage']
    print(f"[OK] Current usage: {before_words} words")
    print(f"[OK] Words remaining: {before['words_remaining']}")

    # Track words
    test_words = 15
    print(f"\nStep 2: Track {test_words} words...")
    try:
        response = requests.post(
            f"{API_URL}/api/usage/track",
            params={"user_id": TEST_USER_ID, "words": test_words},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"[OK] [BACKEND] Tracked {test_words} words. Total: {data.get('usage', 'unknown')}")
        else:
            print(f"[FAIL] Word tracking failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Word tracking error: {e}")
        return False

    # Verify
    print("\nStep 3: Verify usage increased...")
    after = get_user_usage()
    if not after:
        return False

    after_words = after['usage']
    expected_words = before_words + test_words

    if after_words == expected_words:
        print(f"[PASS] Usage increased correctly!")
        print(f"  Before: {before_words} words")
        print(f"  After:  {after_words} words")
        print(f"  Change: +{test_words} words")
        return True
    else:
        print(f"[FAIL] Usage mismatch!")
        print(f"  Expected: {expected_words}")
        print(f"  Actual:   {after_words}")
        return False

def test_ai_generation_tracking():
    """Test AI generation usage tracking endpoint"""
    print_header("TEST 2: AI Generation Usage Tracking")

    # Get before state
    print("\nStep 1: Get current AI gen usage...")
    before = get_user_usage()
    if not before:
        return False

    before_ai_gen = before['ai_gen_usage']
    print(f"[OK] Current AI gen usage: {before_ai_gen} uses")
    print(f"[OK] AI gen remaining: {before['ai_gen_remaining']}")

    # Track AI generation
    print("\nStep 2: Track AI generation...")
    try:
        response = requests.post(
            f"{API_URL}/api/usage/track-ai-gen",
            params={"user_id": TEST_USER_ID},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"[OK] [BACKEND] Tracked AI generation. Total uses: {data.get('usage', 'unknown')}")
        else:
            print(f"[FAIL] AI gen tracking failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] AI gen tracking error: {e}")
        return False

    # Verify
    print("\nStep 3: Verify AI gen usage increased...")
    after = get_user_usage()
    if not after:
        return False

    after_ai_gen = after['ai_gen_usage']
    expected_ai_gen = before_ai_gen + 1

    if after_ai_gen == expected_ai_gen:
        print(f"[PASS] AI gen usage increased correctly!")
        print(f"  Before: {before_ai_gen} uses")
        print(f"  After:  {after_ai_gen} uses")
        print(f"  Change: +1 use")
        return True
    else:
        print(f"[FAIL] AI gen usage mismatch!")
        print(f"  Expected: {expected_ai_gen}")
        print(f"  Actual:   {after_ai_gen}")
        return False

def test_humanizer_tracking():
    """Test humanizer usage tracking endpoint"""
    print_header("TEST 3: Humanizer Usage Tracking")

    # Get before state
    print("\nStep 1: Get current humanizer usage...")
    before = get_user_usage()
    if not before:
        return False

    before_humanizer = before['humanizer_usage']
    print(f"[OK] Current humanizer usage: {before_humanizer} uses")
    print(f"[OK] Humanizer remaining: {before['humanizer_remaining']}")

    # Track humanizer
    print("\nStep 2: Track humanizer...")
    try:
        response = requests.post(
            f"{API_URL}/api/usage/track-humanizer",
            params={"user_id": TEST_USER_ID},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            print(f"[OK] [BACKEND] Tracked humanizer. Total uses: {data.get('usage', 'unknown')}")
        else:
            print(f"[FAIL] Humanizer tracking failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Humanizer tracking error: {e}")
        return False

    # Verify
    print("\nStep 3: Verify humanizer usage increased...")
    after = get_user_usage()
    if not after:
        return False

    after_humanizer = after['humanizer_usage']
    expected_humanizer = before_humanizer + 1

    if after_humanizer == expected_humanizer:
        print(f"[PASS] Humanizer usage increased correctly!")
        print(f"  Before: {before_humanizer} uses")
        print(f"  After:  {after_humanizer} uses")
        print(f"  Change: +1 use")
        return True
    else:
        print(f"[FAIL] Humanizer usage mismatch!")
        print(f"  Expected: {expected_humanizer}")
        print(f"  Actual:   {after_humanizer}")
        return False

def main():
    """Run all tests"""
    print_header("COMPREHENSIVE USAGE TRACKING TEST SUITE")
    print(f"Target: {API_URL}")
    print(f"Test User: {TEST_USER_ID} (slywriterteam@gmail.com)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all tests
    results = {}
    results['word_tracking'] = test_word_tracking()
    results['ai_generation'] = test_ai_generation_tracking()
    results['humanizer'] = test_humanizer_tracking()

    # Summary
    print_header("TEST SUMMARY")
    passed_count = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nTests Run: {total}")
    print(f"[PASS] Passed: {passed_count}")
    print(f"[FAIL] Failed: {total - passed_count}")
    print(f"\nPass Rate: {(passed_count/total)*100:.1f}%")

    # Detailed results
    print("\nDetailed Results:")
    for test_name, test_passed in results.items():
        status = "[PASS]" if test_passed else "[FAIL]"
        print(f"  {status} {test_name}")

    # Final status
    print("\n" + "=" * 80)
    if passed_count == total:
        print("[SUCCESS] All usage tracking endpoints are working!")
        print("\nYou can now:")
        print("1. Test with desktop app (type some text)")
        print("2. Use AI generation (Ctrl+Alt+G)")
        print("3. Use humanizer (enable in Humanizer tab)")
        print("\nAll usage will be tracked correctly with PostgreSQL!")
        print("\nChanges made:")
        print("- Word tracking: Fixed endpoint to /api/usage/track")
        print("- AI generation: Added tracking to /api/usage/track-ai-gen")
        print("- Humanizer: Added tracking to /api/usage/track-humanizer")
        print("- Premium filler: Added tracking to /api/usage/track-ai-gen")
        sys.exit(0)
    else:
        print("[FAILURE] Some endpoints are not working!")
        print("\nCheck:")
        print("1. Is Render server up?")
        print("2. Are the endpoints deployed?")
        print("3. Is PostgreSQL database accessible?")
        sys.exit(1)

if __name__ == "__main__":
    main()
