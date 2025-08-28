"""
WPM Calculator - Proper formula for converting WPM to realistic typing delays
"""

import random
import math

def wpm_to_delays(target_wpm):
    """
    Convert target WPM to min/max delays with realistic variation
    
    Formula:
    - Average WPM = 60 seconds / (avg_delay_per_char * 5 chars_per_word)
    - So: avg_delay = 60 / (WPM * 5)
    - We add 20-40% variation for natural typing
    """
    
    # Calculate base delay per character
    # WPM = Words Per Minute, average word = 5 characters
    # So characters per minute = WPM * 5
    # Seconds per character = 60 / (WPM * 5)
    avg_delay = 60.0 / (target_wpm * 5)
    
    # Add realistic variation (faster typists have less variation)
    if target_wpm < 40:
        # Very slow typing - high variation (40%)
        variation = 0.4
    elif target_wpm < 80:
        # Average typing - moderate variation (30%)
        variation = 0.3
    elif target_wpm < 120:
        # Fast typing - lower variation (25%)
        variation = 0.25
    else:
        # Very fast typing - minimal variation (20%)
        variation = 0.2
    
    # Calculate min/max delays
    min_delay = avg_delay * (1 - variation)
    max_delay = avg_delay * (1 + variation)
    
    # Ensure reasonable bounds
    min_delay = max(0.01, min_delay)  # At least 10ms
    max_delay = min(1.0, max_delay)    # At most 1 second
    
    return {
        "min_delay": round(min_delay, 3),
        "max_delay": round(max_delay, 3),
        "avg_delay": round(avg_delay, 3),
        "actual_wpm": round(60 / (avg_delay * 5), 0)
    }

def calculate_pause_frequency(wpm):
    """
    Calculate how often to pause based on WPM
    Slower typists pause more frequently
    """
    if wpm < 40:
        return 5  # Pause every 5 sentences
    elif wpm < 60:
        return 8  # Pause every 8 sentences
    elif wpm < 100:
        return 12  # Pause every 12 sentences
    elif wpm < 150:
        return 15  # Pause every 15 sentences
    else:
        return 20  # Pause every 20 sentences

def get_typing_profile(wpm):
    """
    Get a complete typing profile for a given WPM
    """
    delays = wpm_to_delays(wpm)
    
    return {
        "target_wpm": wpm,
        "min_delay": delays["min_delay"],
        "max_delay": delays["max_delay"],
        "avg_delay": delays["avg_delay"],
        "actual_wpm": delays["actual_wpm"],
        "pause_frequency": calculate_pause_frequency(wpm),
        "pause_duration_min": 1.0 if wpm < 60 else 0.5,
        "pause_duration_max": 3.0 if wpm < 60 else 1.5,
        "typo_chance": 0.05 if wpm < 40 else 0.03 if wpm < 80 else 0.02 if wpm < 120 else 0.015
    }

# Test the formulas
if __name__ == "__main__":
    test_wpms = [30, 50, 70, 100, 120, 150, 200, 300, 400]
    
    print("WPM to Delay Conversion Table:")
    print("-" * 80)
    print(f"{'Target WPM':<12} {'Min Delay':<12} {'Max Delay':<12} {'Avg Delay':<12} {'Actual WPM':<12}")
    print("-" * 80)
    
    for wpm in test_wpms:
        profile = get_typing_profile(wpm)
        print(f"{profile['target_wpm']:<12} "
              f"{profile['min_delay']:<12.3f} "
              f"{profile['max_delay']:<12.3f} "
              f"{profile['avg_delay']:<12.3f} "
              f"{profile['actual_wpm']:<12.0f}")
    
    print("\n" + "=" * 80)
    print("\nDetailed Profiles for Key Speeds:")
    print("=" * 80)
    
    for wpm in [60, 100, 150]:
        profile = get_typing_profile(wpm)
        print(f"\n{wpm} WPM Profile:")
        print(f"  Delays: {profile['min_delay']:.3f}s - {profile['max_delay']:.3f}s")
        print(f"  Actual WPM: ~{profile['actual_wpm']}")
        print(f"  Pause every: {profile['pause_frequency']} sentences")
        print(f"  Pause duration: {profile['pause_duration_min']}-{profile['pause_duration_max']}s")
        print(f"  Typo chance: {profile['typo_chance']*100:.1f}%")