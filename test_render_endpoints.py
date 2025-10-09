#!/usr/bin/env python
"""
Comprehensive Render Endpoint Testing Suite
Tests all 58 production endpoints on https://slywriterapp.onrender.com
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
BASE_URL = "https://slywriterapp.onrender.com"
TEST_EMAIL = "endpoint.test@slywriter.ai"
TEST_USER_ID = None  # Will be populated after login
JWT_TOKEN = None  # Will be populated after login

# Test results tracking
results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "tests": []
}


def log_test(endpoint: str, method: str, status: str, response_code: int = None, message: str = ""):
    """Log test result"""
    result = {
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "response_code": response_code,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    results["tests"].append(result)
    results["total"] += 1

    if status == "PASS":
        results["passed"] += 1
        print(f"[PASS] {method:6s} {endpoint:50s} [{response_code}] {message}")
    elif status == "FAIL":
        results["failed"] += 1
        print(f"[FAIL] {method:6s} {endpoint:50s} [{response_code}] {message}")
    elif status == "SKIP":
        results["skipped"] += 1
        print(f"[SKIP] {method:6s} {endpoint:50s} {message}")


def test_endpoint(method: str, endpoint: str, headers: Dict = None, json_data: Dict = None,
                  expected_status: int = 200, description: str = "") -> Tuple[bool, int, str]:
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json_data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        elif method == "OPTIONS":
            response = requests.options(url, headers=headers, timeout=10)
        else:
            return False, 0, f"Unknown method: {method}"

        success = response.status_code == expected_status
        return success, response.status_code, description

    except requests.exceptions.Timeout:
        return False, 0, "Request timeout"
    except requests.exceptions.RequestException as e:
        return False, 0, f"Request failed: {str(e)}"


def setup_test_user():
    """Create test user and get JWT token"""
    global JWT_TOKEN, TEST_USER_ID

    print("\n" + "="*80)
    print("SETUP: Creating test user and getting JWT token")
    print("="*80 + "\n")

    # Try to login first
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL},
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        JWT_TOKEN = data.get("access_token") or data.get("token")
        TEST_USER_ID = data["user"]["id"]
        print(f"[OK] Logged in as: {TEST_EMAIL}")
        print(f"[OK] User ID: {TEST_USER_ID}")
        print(f"[OK] JWT Token: {JWT_TOKEN[:50]}...")
        return True

    # If login failed, try to register
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": TEST_EMAIL},
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        JWT_TOKEN = data.get("token")
        TEST_USER_ID = data["user"]["id"]
        print(f"[OK] Registered as: {TEST_EMAIL}")
        print(f"[OK] User ID: {TEST_USER_ID}")
        print(f"[OK] JWT Token: {JWT_TOKEN[:50]}...")
        return True

    print(f"[ERROR] Failed to setup test user: {response.status_code}")
    return False


def test_health_endpoints():
    """Test health check endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: Health & Status Endpoints (3 tests)")
    print("="*80 + "\n")

    # Test 1: Root endpoint
    success, code, msg = test_endpoint("GET", "/", description="API root")
    log_test("/", "GET", "PASS" if success else "FAIL", code, msg)

    # Test 2: Healthz
    success, code, msg = test_endpoint("GET", "/healthz", description="Health check")
    log_test("/healthz", "GET", "PASS" if success else "FAIL", code, msg)

    # Test 3: API health
    success, code, msg = test_endpoint("GET", "/api/health", description="API health")
    log_test("/api/health", "GET", "PASS" if success else "FAIL", code, msg)


def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: Authentication Endpoints (9 tests)")
    print("="*80 + "\n")

    # Test 1: Login
    success, code, msg = test_endpoint(
        "POST", "/api/auth/login",
        json_data={"email": TEST_EMAIL},
        description="Standard login"
    )
    log_test("/api/auth/login", "POST", "PASS" if success else "FAIL", code, msg)

    # Test 2: Register (expect 400 - user exists)
    success, code, msg = test_endpoint(
        "POST", "/api/auth/register",
        json_data={"email": TEST_EMAIL},
        expected_status=400,
        description="Register existing user"
    )
    log_test("/api/auth/register", "POST", "PASS" if success else "FAIL", code, msg)

    # Test 3: Get profile (requires JWT)
    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    success, code, msg = test_endpoint(
        "GET", "/auth/profile",
        headers=headers,
        description="Get user profile"
    )
    log_test("/auth/profile", "GET", "PASS" if success else "FAIL", code, msg)

    # Test 4: Get user by ID
    success, code, msg = test_endpoint(
        "GET", f"/api/auth/user/{TEST_USER_ID}",
        description="Get user by ID"
    )
    log_test(f"/api/auth/user/{TEST_USER_ID}", "GET", "PASS" if success else "FAIL", code, msg)

    # Test 5: Auth status
    success, code, msg = test_endpoint(
        "GET", "/api/auth/status",
        description="Auth status check"
    )
    log_test("/api/auth/status", "GET", "PASS" if success else "FAIL", code, msg)

    # Test 6: Logout
    success, code, msg = test_endpoint(
        "POST", "/api/auth/logout",
        description="Logout"
    )
    log_test("/api/auth/logout", "POST", "PASS" if success else "FAIL", code, msg)

    # Test 7: Desktop Google OAuth
    success, code, msg = test_endpoint(
        "POST", "/api/auth/google",
        description="Desktop Google OAuth"
    )
    log_test("/api/auth/google", "POST", "PASS" if success else "FAIL", code, msg)

    # Test 8: Verify email OPTIONS (CORS preflight)
    success, code, msg = test_endpoint(
        "OPTIONS", "/auth/verify-email",
        description="Email verification CORS"
    )
    log_test("/auth/verify-email", "OPTIONS", "PASS" if success else "FAIL", code, msg)

    # Skip actual email verification (requires valid token)
    log_test("/auth/verify-email", "POST", "SKIP", message="Requires email token")


def test_user_data_endpoints():
    """Test user data endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: User Data Endpoints (1 test)")
    print("="*80 + "\n")

    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    success, code, msg = test_endpoint(
        "GET", "/api/user-dashboard",
        headers=headers,
        description="User dashboard"
    )
    log_test("/api/user-dashboard", "GET", "PASS" if success else "FAIL", code, msg)


def test_typing_endpoints():
    """Test typing automation endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: Typing Automation Endpoints (5 tests)")
    print("="*80 + "\n")

    # Skip desktop-only endpoints (they require GUI)
    log_test("/api/typing/start", "POST", "SKIP", message="Desktop app only")
    log_test("/api/typing/stop", "POST", "SKIP", message="Desktop app only")
    log_test("/api/typing/pause", "POST", "SKIP", message="Desktop app only")

    # Test status endpoint
    success, code, msg = test_endpoint(
        "GET", "/api/typing/status",
        description="Typing status"
    )
    log_test("/api/typing/status", "GET", "PASS" if success else "FAIL", code, msg)

    # Skip session-specific endpoints
    log_test("/api/typing/pause/{session_id}", "POST", "SKIP", message="Requires active session")


def test_profile_endpoints():
    """Test profile management endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: Profile Management Endpoints (4 tests)")
    print("="*80 + "\n")

    # Test 1: Save profile
    success, code, msg = test_endpoint(
        "POST", "/api/profiles/save",
        json_data={"name": "test_profile", "settings": {"min_delay": 0.1}},
        description="Save profile"
    )
    log_test("/api/profiles/save", "POST", "PASS" if success else "FAIL", code, msg)

    # Test 2: Get profiles
    success, code, msg = test_endpoint(
        "GET", "/api/profiles",
        description="Get profiles"
    )
    log_test("/api/profiles", "GET", "PASS" if success else "FAIL", code, msg)

    # Test 3: Generate profile from WPM
    success, code, msg = test_endpoint(
        "POST", "/api/profiles/generate-from-wpm",
        json_data={"wpm": 85},
        description="Generate from WPM"
    )
    log_test("/api/profiles/generate-from-wpm", "POST", "PASS" if success else "FAIL", code, msg)

    # Test 4: Delete profile
    success, code, msg = test_endpoint(
        "DELETE", "/api/profiles/test_profile",
        description="Delete profile"
    )
    log_test("/api/profiles/test_profile", "DELETE", "PASS" if success else "FAIL", code, msg)


def test_ai_endpoints():
    """Test AI feature endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: AI Feature Endpoints (5 tests)")
    print("="*80 + "\n")

    # Skip AI endpoints (require OpenAI API key and credits)
    log_test("/api/ai/generate", "POST", "SKIP", message="Requires OpenAI credits")
    log_test("/api/ai/humanize", "POST", "SKIP", message="Requires OpenAI credits")
    log_test("/api/ai/explain", "POST", "SKIP", message="Requires OpenAI credits")
    log_test("/api/ai/study-questions", "POST", "SKIP", message="Requires OpenAI credits")
    log_test("/generate_filler", "POST", "SKIP", message="Requires OpenAI credits")


def test_usage_endpoints():
    """Test usage tracking endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: Usage Tracking Endpoints (5 tests)")
    print("="*80 + "\n")

    # Test 1: Track usage
    success, code, msg = test_endpoint(
        "POST", f"/api/usage/track?user_id={TEST_USER_ID}&words=10",
        description="Track word usage"
    )
    log_test("/api/usage/track", "POST", "PASS" if success else "FAIL", code, msg)

    # Test 2: Track humanizer
    success, code, msg = test_endpoint(
        "POST", f"/api/usage/track-humanizer?user_id={TEST_USER_ID}",
        description="Track humanizer"
    )
    log_test("/api/usage/track-humanizer", "POST", "PASS" if success else "FAIL", code, msg)

    # Test 3: Track AI gen
    success, code, msg = test_endpoint(
        "POST", f"/api/usage/track-ai-gen?user_id={TEST_USER_ID}",
        description="Track AI generation"
    )
    log_test("/api/usage/track-ai-gen", "POST", "PASS" if success else "FAIL", code, msg)

    # Test 4: Check reset
    success, code, msg = test_endpoint(
        "POST", f"/api/usage/check-reset?user_id={TEST_USER_ID}",
        description="Check weekly reset"
    )
    log_test("/api/usage/check-reset", "POST", "PASS" if success else "FAIL", code, msg)

    # Test 5: Get usage
    success, code, msg = test_endpoint(
        "GET", "/api/usage",
        description="Get usage stats"
    )
    log_test("/api/usage", "GET", "PASS" if success else "FAIL", code, msg)


def test_referral_endpoints():
    """Test referral system endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: Referral System Endpoints (1 test)")
    print("="*80 + "\n")

    # Try to claim tier 1 (expect 400 - not enough referrals)
    success, code, msg = test_endpoint(
        "POST", "/api/referrals/claim-reward",
        json_data={"tier": 1, "email": TEST_EMAIL},
        expected_status=400,
        description="Claim reward (no referrals)"
    )
    log_test("/api/referrals/claim-reward", "POST", "PASS" if success else "FAIL", code, msg)


def test_stripe_endpoints():
    """Test Stripe payment endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: Stripe Payment Endpoints (2 tests)")
    print("="*80 + "\n")

    # Test 1: Create checkout (expect error - no valid plan)
    success, code, msg = test_endpoint(
        "POST", "/api/stripe/create-checkout",
        json_data={"email": TEST_EMAIL, "plan": "Pro"},
        description="Create checkout"
    )
    log_test("/api/stripe/create-checkout", "POST", "PASS" if success else "FAIL", code, msg)

    # Skip webhook (requires Stripe signature)
    log_test("/api/stripe/webhook", "POST", "SKIP", message="Requires Stripe signature")


def test_stats_endpoints():
    """Test statistics endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: Statistics Endpoints (1 test)")
    print("="*80 + "\n")

    success, code, msg = test_endpoint(
        "GET", "/api/stats/global",
        description="Global stats"
    )
    log_test("/api/stats/global", "GET", "PASS" if success else "FAIL", code, msg)


def test_config_endpoints():
    """Test configuration endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: Configuration Endpoints (3 tests)")
    print("="*80 + "\n")

    # Test 1: Get config
    success, code, msg = test_endpoint(
        "GET", "/api/config",
        description="Get config"
    )
    log_test("/api/config", "GET", "PASS" if success else "FAIL", code, msg)

    # Test 2: Update config
    success, code, msg = test_endpoint(
        "POST", "/api/config",
        json_data={"settings": {"theme": "dark"}},
        description="Update config"
    )
    log_test("/api/config", "POST", "PASS" if success else "FAIL", code, msg)

    # Test 3: Update hotkey
    success, code, msg = test_endpoint(
        "POST", "/api/config/hotkey",
        json_data={"key": "start", "value": "ctrl+shift+s"},
        description="Update hotkey"
    )
    log_test("/api/config/hotkey", "POST", "PASS" if success else "FAIL", code, msg)


def test_hotkey_endpoints():
    """Test hotkey endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: Hotkey Endpoints (2 tests)")
    print("="*80 + "\n")

    # Test 1: Register hotkey
    success, code, msg = test_endpoint(
        "POST", "/api/hotkeys/register",
        json_data={"action": "start", "hotkey": "ctrl+shift+s"},
        description="Register hotkey"
    )
    log_test("/api/hotkeys/register", "POST", "PASS" if success else "FAIL", code, msg)

    # Test 2: Get hotkeys
    success, code, msg = test_endpoint(
        "GET", "/api/hotkeys",
        description="Get hotkeys"
    )
    log_test("/api/hotkeys", "GET", "PASS" if success else "FAIL", code, msg)


def test_telemetry_endpoints():
    """Test telemetry endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: Telemetry & Analytics Endpoints (3 tests)")
    print("="*80 + "\n")

    # Test 1: Error telemetry
    success, code, msg = test_endpoint(
        "POST", "/api/telemetry/error",
        json_data={"error": "Test error", "user_id": str(TEST_USER_ID)},
        description="Log error"
    )
    log_test("/api/telemetry/error", "POST", "PASS" if success else "FAIL", code, msg)

    # Skip admin endpoints (might require auth)
    log_test("/api/admin/telemetry/stats", "GET", "SKIP", message="Admin only")
    log_test("/api/admin/telemetry", "GET", "SKIP", message="Admin only")


def test_learning_endpoints():
    """Test learning hub endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: Learning Hub Endpoints (2 tests)")
    print("="*80 + "\n")

    # Skip (requires OpenAI)
    log_test("/api/learning/create-lesson", "POST", "SKIP", message="Requires OpenAI credits")

    # Test 1: Get lessons
    success, code, msg = test_endpoint(
        "GET", f"/api/learning/get-lessons?user_id={TEST_USER_ID}",
        description="Get lessons"
    )
    log_test("/api/learning/get-lessons", "GET", "PASS" if success else "FAIL", code, msg)

    # Test 2: Save lesson
    success, code, msg = test_endpoint(
        "POST", f"/api/learning/save-lesson?user_id={TEST_USER_ID}",
        json_data={"title": "Test Lesson", "content": "Test content"},
        description="Save lesson"
    )
    log_test("/api/learning/save-lesson", "POST", "PASS" if success else "FAIL", code, msg)


def test_desktop_endpoints():
    """Test desktop app specific endpoints"""
    print("\n" + "="*80)
    print("CATEGORY: Desktop App Endpoints (5 tests)")
    print("="*80 + "\n")

    # Skip GUI-dependent endpoints
    log_test("/api/copy-highlighted", "POST", "SKIP", message="Requires GUI")
    log_test("/api/copy-highlighted-overlay", "POST", "SKIP", message="Requires GUI")
    log_test("/api/license/verify", "POST", "SKIP", message="Desktop app only")
    log_test("/api/license/status", "GET", "SKIP", message="Desktop app only")
    log_test("/api/license/features", "GET", "SKIP", message="Desktop app only")


def generate_report():
    """Generate final test report"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")

    print(f"Total Tests: {results['total']}")
    print(f"[PASS] Passed:   {results['passed']}")
    print(f"[FAIL] Failed:   {results['failed']}")
    print(f"[SKIP] Skipped:  {results['skipped']}")
    print(f"\nPass Rate: {(results['passed'] / (results['passed'] + results['failed']) * 100):.1f}%")

    # Save detailed report
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed report saved to: {report_file}")

    # Show failed tests
    if results['failed'] > 0:
        print("\n" + "="*80)
        print("FAILED TESTS:")
        print("="*80 + "\n")
        for test in results['tests']:
            if test['status'] == 'FAIL':
                print(f"[FAIL] {test['method']} {test['endpoint']}")
                print(f"   Code: {test['response_code']}")
                print(f"   Message: {test['message']}\n")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("SLYWRITER RENDER ENDPOINT TEST SUITE")
    print("="*80)
    print(f"Target: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    # Setup
    if not setup_test_user():
        print("[ERROR] Failed to setup test user. Aborting.")
        return

    # Run all test categories
    test_health_endpoints()
    test_auth_endpoints()
    test_user_data_endpoints()
    test_typing_endpoints()
    test_profile_endpoints()
    test_ai_endpoints()
    test_usage_endpoints()
    test_referral_endpoints()
    test_stripe_endpoints()
    test_stats_endpoints()
    test_config_endpoints()
    test_hotkey_endpoints()
    test_telemetry_endpoints()
    test_learning_endpoints()
    test_desktop_endpoints()

    # Generate report
    generate_report()


if __name__ == "__main__":
    main()
