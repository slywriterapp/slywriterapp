"""
Enhanced WPM Calculator V2 - Comprehensive formula for realistic typing speeds
"""

import random
import math

def wpm_to_delays_v2(target_wpm):
    """
    Advanced WPM to delay conversion with proper mathematical formula
    
    Key Formula:
    - WPM = Words Per Minute
    - CPM = Characters Per Minute = WPM * 5 (average word length)
    - CPS = Characters Per Second = CPM / 60
    - Base Delay = 1 / CPS = 60 / (WPM * 5)
    
    For realistic typing:
    - Add variability based on speed (faster = less variation)
    - Include micro-pauses between words
    - Add sentence pauses
    """
    
    # CORE FORMULA: Convert WPM to base delay per character
    # This is the mathematical relationship between WPM and typing delay
    chars_per_minute = target_wpm * 5  # 5 chars per word on average
    chars_per_second = chars_per_minute / 60
    base_delay_per_char = 1 / chars_per_second
    
    # WPM ranges and their characteristics
    if target_wpm < 20:
        # Hunt and peck typing (10-20 WPM)
        category = "hunt_and_peck"
        variation_percent = 60  # 60% variation
        mistake_rate = 0.08  # 8% typo chance
        pause_freq = 3  # Pause every 3 sentences
        burst_factor = 0  # No burst typing
    elif target_wpm < 40:
        # Slow typing (20-40 WPM)
        category = "slow"
        variation_percent = 45  # 45% variation
        mistake_rate = 0.05  # 5% typo chance
        pause_freq = 5  # Pause every 5 sentences
        burst_factor = 0.05  # Minimal burst
    elif target_wpm < 60:
        # Average typing (40-60 WPM)
        category = "average"
        variation_percent = 35  # 35% variation
        mistake_rate = 0.03  # 3% typo chance
        pause_freq = 8  # Pause every 8 sentences
        burst_factor = 0.10  # Some burst typing
    elif target_wpm < 80:
        # Above average (60-80 WPM)
        category = "above_average"
        variation_percent = 28  # 28% variation
        mistake_rate = 0.025  # 2.5% typo chance
        pause_freq = 10  # Pause every 10 sentences
        burst_factor = 0.15  # Moderate burst
    elif target_wpm < 100:
        # Fast typing (80-100 WPM)
        category = "fast"
        variation_percent = 22  # 22% variation
        mistake_rate = 0.02  # 2% typo chance
        pause_freq = 12  # Pause every 12 sentences
        burst_factor = 0.20  # Significant burst
    elif target_wpm < 120:
        # Very fast (100-120 WPM)
        category = "very_fast"
        variation_percent = 18  # 18% variation
        mistake_rate = 0.018  # 1.8% typo chance
        pause_freq = 15  # Pause every 15 sentences
        burst_factor = 0.25  # High burst
    elif target_wpm < 150:
        # Professional typist (120-150 WPM)
        category = "professional"
        variation_percent = 15  # 15% variation
        mistake_rate = 0.015  # 1.5% typo chance
        pause_freq = 18  # Pause every 18 sentences
        burst_factor = 0.30  # Very high burst
    else:
        # Elite typist (150+ WPM)
        category = "elite"
        variation_percent = 12  # 12% variation
        mistake_rate = 0.01  # 1% typo chance
        pause_freq = 20  # Pause every 20 sentences
        burst_factor = 0.35  # Elite burst patterns
    
    # Calculate min/max delays with proper variation
    variation_multiplier = variation_percent / 100
    
    # Min delay is faster than base (but not too fast to be unrealistic)
    min_delay = base_delay_per_char * (1 - variation_multiplier * 0.7)
    
    # Max delay is slower than base (to account for thinking, harder keys)
    max_delay = base_delay_per_char * (1 + variation_multiplier * 1.3)
    
    # Ensure realistic bounds
    min_delay = max(0.01, min_delay)  # At least 10ms (100 chars/sec max)
    max_delay = min(2.0, max_delay)   # At most 2 seconds per char
    
    # Calculate pause durations based on speed
    if target_wpm < 60:
        pause_min = 1.5
        pause_max = 3.5
    elif target_wpm < 100:
        pause_min = 0.8
        pause_max = 2.0
    else:
        pause_min = 0.4
        pause_max = 1.2
    
    # Word pause (space character) multiplier
    word_pause_multiplier = 1.2 if target_wpm < 60 else 1.1
    
    return {
        "target_wpm": target_wpm,
        "category": category,
        "min_delay": round(min_delay, 4),
        "max_delay": round(max_delay, 4),
        "avg_delay": round(base_delay_per_char, 4),
        "actual_wpm": round(60 / (base_delay_per_char * 5), 1),
        "variation_percent": variation_percent,
        "typo_chance": mistake_rate,
        "pause_frequency": pause_freq,
        "pause_duration_min": pause_min,
        "pause_duration_max": pause_max,
        "burst_variability": burst_factor,
        "word_pause_multiplier": word_pause_multiplier,
        "chars_per_second": round(chars_per_second, 2)
    }

def get_char_specific_delay(char, base_min, base_max, wpm_profile):
    """
    Get character-specific delay based on typing difficulty
    """
    # Easy characters (home row)
    easy_chars = set('asdfjkl;ghASFJKL')
    # Medium characters
    medium_chars = set('qwertyuiopzxcvbnmQWERTYUIOPZXCVBNM')
    # Hard characters (numbers, symbols, special)
    
    if char in easy_chars:
        # Home row keys are fastest
        multiplier = random.uniform(0.8, 1.0)
    elif char in medium_chars:
        # Regular letters
        multiplier = random.uniform(0.9, 1.1)
    elif char == ' ':
        # Space has special handling with word pause
        multiplier = random.uniform(
            wpm_profile.get('word_pause_multiplier', 1.1),
            wpm_profile.get('word_pause_multiplier', 1.1) * 1.2
        )
    elif char in '.,':
        # Common punctuation
        multiplier = random.uniform(1.0, 1.3)
    elif char in '!?;:':
        # End punctuation - slightly longer
        multiplier = random.uniform(1.2, 1.5)
    elif char.isupper():
        # Capital letters take longer (shift key)
        multiplier = random.uniform(1.1, 1.4)
    elif char.isdigit():
        # Numbers take longer (reach to number row)
        multiplier = random.uniform(1.2, 1.6)
    else:
        # Special characters are hardest
        multiplier = random.uniform(1.3, 1.8)
    
    # Calculate actual delay
    base_delay = random.uniform(base_min, base_max)
    return base_delay * multiplier

def validate_wpm_range(wpm):
    """
    Ensure WPM is within realistic bounds
    """
    MIN_WPM = 10   # Minimum realistic typing speed
    MAX_WPM = 300  # Maximum realistic typing speed
    
    if wpm < MIN_WPM:
        return MIN_WPM
    elif wpm > MAX_WPM:
        return MAX_WPM
    return wpm

def get_comprehensive_profile(wpm):
    """
    Get a complete typing profile with all parameters
    """
    wpm = validate_wpm_range(wpm)
    profile = wpm_to_delays_v2(wpm)
    
    # Add additional realistic behaviors
    profile.update({
        "micro_hesitations": wpm < 80,  # Slower typists hesitate more
        "zone_out_breaks": wpm < 60,    # Very slow typists take mental breaks
        "correction_delay": 0.2 if wpm > 100 else 0.3,  # Time to correct typos
        "thinking_pauses": wpm < 70,    # Pauses for thinking
        "fatigue_factor": 0.05 if wpm > 120 else 0.10,  # Speed degradation over time
    })
    
    return profile

# Test the formula
if __name__ == "__main__":
    print("=" * 80)
    print("COMPREHENSIVE WPM TO DELAY CONVERSION TABLE")
    print("=" * 80)
    
    test_speeds = [15, 25, 35, 45, 55, 65, 75, 85, 95, 110, 130, 150, 180, 220]
    
    print(f"{'WPM':<6} {'Category':<15} {'Min(ms)':<10} {'Max(ms)':<10} {'Avg(ms)':<10} {'CPS':<8} {'Var%':<6} {'Typo%':<6}")
    print("-" * 80)
    
    for wpm in test_speeds:
        p = wpm_to_delays_v2(wpm)
        print(f"{p['target_wpm']:<6} {p['category']:<15} "
              f"{p['min_delay']*1000:<10.1f} {p['max_delay']*1000:<10.1f} "
              f"{p['avg_delay']*1000:<10.1f} {p['chars_per_second']:<8.2f} "
              f"{p['variation_percent']:<6} {p['typo_chance']*100:<6.1f}")
    
    print("\n" + "=" * 80)
    print("DELAY RANGES FOR COMMON SPEEDS")
    print("=" * 80)
    
    for wpm in [30, 60, 90, 120, 150]:
        p = wpm_to_delays_v2(wpm)
        print(f"\n{wpm} WPM ({p['category'].replace('_', ' ').title()}):")
        print(f"  Character delays: {p['min_delay']*1000:.1f}ms - {p['max_delay']*1000:.1f}ms")
        print(f"  Characters/second: {p['chars_per_second']:.2f}")
        print(f"  Actual WPM: ~{p['actual_wpm']}")
        print(f"  Variation: {p['variation_percent']}%")
        print(f"  Typo chance: {p['typo_chance']*100:.1f}%")
        print(f"  Pauses: Every {p['pause_frequency']} sentences ({p['pause_duration_min']}-{p['pause_duration_max']}s)")