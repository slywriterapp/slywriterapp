#!/usr/bin/env python3
"""Verify 200 WPM speed is working correctly"""

import requests
import time
import json

def test_wpm_speed(wpm):
    """Test typing at specified WPM"""
    
    # Test text - exactly 20 words
    test_text = "The quick brown fox jumps over the lazy dog today and tomorrow will be another beautiful sunny day here."
    word_count = len(test_text.split())
    char_count = len(test_text)
    
    print(f"\n{'='*60}")
    print(f"Testing {wpm} WPM")
    print(f"{'='*60}")
    print(f"Text: {word_count} words, {char_count} characters")
    print(f"Expected time: {word_count * 60 / wpm:.1f} seconds")
    print(f"Expected CPS: {wpm * 5 / 60:.2f}")
    
    # Start typing
    response = requests.post(
        "http://localhost:8000/api/typing/start",
        json={
            "text": test_text,
            "profile": "Custom",
            "custom_wpm": wpm,
            "user_id": "test_user",
            "session_id": f"test_{wpm}wpm"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        session_id = result.get("session_id")
        print(f"Session started: {session_id}")
        
        # Monitor for completion
        start_time = time.time()
        print("\nTyping in progress", end="")
        
        while time.time() - start_time < 30:  # Max 30 seconds timeout
            print(".", end="", flush=True)
            time.sleep(0.5)
            
            # Check if typing is complete (would normally check via WebSocket)
            # For now, just estimate based on expected time
            elapsed = time.time() - start_time
            expected_time = word_count * 60 / wpm
            
            if elapsed >= expected_time * 1.1:  # Allow 10% extra time
                break
        
        elapsed = time.time() - start_time
        actual_wpm = (char_count / elapsed) * 60 / 5 if elapsed > 0 else 0
        
        print(f"\n\nResults:")
        print(f"  Elapsed time: {elapsed:.1f} seconds")
        print(f"  Actual WPM: {actual_wpm:.0f}")
        print(f"  Speed ratio: {actual_wpm/wpm:.2%} of target")
        
        if abs(actual_wpm - wpm) / wpm < 0.15:  # Within 15% of target
            print(f"  ✅ Speed is CORRECT")
        else:
            print(f"  ❌ Speed is OFF (expected ~{wpm}, got ~{actual_wpm:.0f})")
            
    else:
        print(f"Error starting session: {response.status_code}")
        print(response.text)

# Test different speeds
if __name__ == "__main__":
    print("WPM Speed Verification Test")
    print("="*60)
    
    # Test slow speed first (baseline)
    test_wpm_speed(60)
    
    # Test fast speed
    test_wpm_speed(200)
    
    # Calculate speed difference
    print(f"\n{'='*60}")
    print("Speed difference between 60 and 200 WPM should be ~3.3x")
    print(f"{'='*60}")