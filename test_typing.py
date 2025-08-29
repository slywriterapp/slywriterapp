"""
Test script to verify typing functionality
"""

import requests
import time
import json

API_URL = "http://localhost:8000"

def test_typing(text, profile="Medium", custom_wpm=None):
    """Test typing with given parameters"""
    print(f"\n{'='*50}")
    print(f"Testing: {profile} profile")
    if custom_wpm:
        print(f"Custom WPM: {custom_wpm}")
    print(f"Text: {text[:50]}...")
    print('='*50)
    
    # Start typing
    payload = {
        "text": text,
        "profile": profile,
        "preview_mode": False
    }
    if custom_wpm:
        payload["custom_wpm"] = custom_wpm
    
    response = requests.post(f"{API_URL}/api/typing/start", json=payload)
    
    if response.status_code != 200:
        print(f"[X] Failed to start: {response.text}")
        return False
    
    data = response.json()
    session_id = data.get("session_id")
    print(f"[OK] Started - Session ID: {session_id}")
    
    # Wait for typing to complete
    wait_time = len(text) * 0.1  # Estimate based on text length
    print(f"[...] Waiting {wait_time:.1f} seconds for typing to complete...")
    time.sleep(wait_time)
    
    # Stop typing
    response = requests.post(f"{API_URL}/api/typing/stop/{session_id}")
    if response.status_code == 200:
        print("[OK] Stopped successfully")
    else:
        print(f"[!] Stop response: {response.text}")
    
    return True

def test_all_profiles():
    """Test all profiles"""
    test_text = "The quick brown fox jumps over the lazy dog."
    
    profiles = ["Slow", "Medium", "Fast", "Essay"]
    for profile in profiles:
        test_typing(test_text, profile)
        time.sleep(2)  # Brief pause between tests
    
    # Test custom WPM
    test_typing(test_text, "Custom", custom_wpm=75)
    test_typing(test_text, "Custom", custom_wpm=150)

def test_special_cases():
    """Test edge cases and special scenarios"""
    print("\n" + "="*60)
    print("TESTING SPECIAL CASES")
    print("="*60)
    
    # Empty text
    print("\n1. Testing empty text:")
    test_typing("", "Medium")
    
    # Single character
    print("\n2. Testing single character:")
    test_typing("A", "Fast")
    
    # Special characters
    print("\n3. Testing special characters:")
    test_typing("@#$% Test! (123)", "Medium")
    
    # Very long text
    print("\n4. Testing long text:")
    long_text = "Lorem ipsum " * 50
    test_typing(long_text, "Fast")

def test_wpm_speeds():
    """Test different WPM speeds to verify they work"""
    print("\n" + "="*60)
    print("TESTING WPM SPEEDS")
    print("="*60)
    
    test_text = "Testing different typing speeds."
    speeds = [20, 40, 60, 80, 100, 120, 150, 200]
    
    for wpm in speeds:
        print(f"\n--- Testing {wpm} WPM ---")
        start_time = time.time()
        test_typing(test_text, "Custom", custom_wpm=wpm)
        elapsed = time.time() - start_time
        print(f"Total time: {elapsed:.2f} seconds")
        
        # Calculate expected time
        chars = len(test_text)
        expected_time = (chars / (wpm * 5)) * 60
        print(f"Expected time: ~{expected_time:.2f} seconds")
        
        time.sleep(1)

if __name__ == "__main__":
    print("="*60)
    print("SLYWRITER TYPING ENGINE TEST SUITE")
    print("="*60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{API_URL}/api/health")
        if response.status_code == 200:
            print("[OK] Backend is running")
        else:
            print("[X] Backend health check failed")
            exit(1)
    except:
        print("[X] Cannot connect to backend at", API_URL)
        print("Please ensure the backend is running: python main_enhanced.py")
        exit(1)
    
    # Run tests
    print("\nRunning test suite...")
    
    # Test 1: All profiles
    test_all_profiles()
    
    # Test 2: Special cases
    test_special_cases()
    
    # Test 3: WPM speeds
    test_wpm_speeds()
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)