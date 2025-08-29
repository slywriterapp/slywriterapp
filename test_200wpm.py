#!/usr/bin/env python3
"""Test 200 WPM typing speed"""

import time
import pyautogui

# Test text (10 words = should take 3 seconds at 200 WPM)
test_text = "The quick brown fox jumps over the lazy dog today."

print("Testing 200 WPM typing speed")
print(f"Text: {test_text}")
print(f"Word count: {len(test_text.split())}")
print(f"Expected time at 200 WPM: {len(test_text.split()) * 60 / 200:.1f} seconds")

print("\nStarting in 3 seconds (switch to target window)...")
time.sleep(3)

# Type at approximately 200 WPM
# 200 WPM = 1000 CPM = 16.67 chars/second = 60ms per char
start_time = time.time()

for char in test_text:
    pyautogui.write(char)
    time.sleep(0.06)  # 60ms per character for 200 WPM

end_time = time.time()
elapsed = end_time - start_time

print(f"\nTyping complete!")
print(f"Elapsed time: {elapsed:.2f} seconds")
print(f"Characters typed: {len(test_text)}")
print(f"Actual CPS: {len(test_text)/elapsed:.2f}")
print(f"Actual WPM: {(len(test_text)/elapsed) * 60 / 5:.0f}")