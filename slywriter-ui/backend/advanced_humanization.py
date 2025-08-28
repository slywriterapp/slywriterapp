"""
Advanced Humanization System for SlyWriter
Ultra-realistic typing patterns to counter detection systems
"""

import random
import time
import math
from typing import Tuple, List, Dict, Optional

class AdvancedHumanizer:
    """
    Sophisticated typing humanization to bypass detection systems
    """
    
    def __init__(self):
        # Extended keyboard layout with common mistypes
        self.keyboard_neighbors = {
            # Top row
            'q': ['w', 'a', '1', '2', 's'],
            'w': ['q', 'e', 's', 'a', '2', '3'],
            'e': ['w', 'r', 'd', 's', '3', '4'],
            'r': ['e', 't', 'f', 'd', '4', '5'],
            't': ['r', 'y', 'g', 'f', '5', '6'],
            'y': ['t', 'u', 'h', 'g', '6', '7'],
            'u': ['y', 'i', 'j', 'h', '7', '8'],
            'i': ['u', 'o', 'k', 'j', '8', '9'],
            'o': ['i', 'p', 'l', 'k', '9', '0'],
            'p': ['o', 'l', '0', '-', '['],
            
            # Middle row
            'a': ['q', 'w', 's', 'z'],
            's': ['a', 'd', 'w', 'e', 'x', 'z'],
            'd': ['s', 'f', 'e', 'r', 'c', 'x'],
            'f': ['d', 'g', 'r', 't', 'v', 'c'],
            'g': ['f', 'h', 't', 'y', 'b', 'v'],
            'h': ['g', 'j', 'y', 'u', 'n', 'b'],
            'j': ['h', 'k', 'u', 'i', 'm', 'n'],
            'k': ['j', 'l', 'i', 'o', ',', 'm'],
            'l': ['k', 'o', 'p', '.', ';'],
            
            # Bottom row
            'z': ['x', 'a', 's'],
            'x': ['z', 'c', 's', 'd'],
            'c': ['x', 'v', 'd', 'f'],
            'v': ['c', 'b', 'f', 'g'],
            'b': ['v', 'n', 'g', 'h'],
            'n': ['b', 'm', 'h', 'j'],
            'm': ['n', 'j', 'k', ','],
            
            # Space bar common mistakes
            ' ': ['v', 'b', 'n', 'c']  # Hit nearby keys with thumb
        }
        
        # Common typo patterns
        self.typo_patterns = {
            'double_tap': 0.15,      # Type same key twice: 'the' -> 'tthe'
            'neighbor_key': 0.40,     # Hit neighboring key: 'the' -> 'thr'
            'transposition': 0.20,    # Swap two characters: 'the' -> 'hte'
            'missed_key': 0.10,       # Skip a character: 'the' -> 'te'
            'wrong_case': 0.10,       # Wrong capitalization: 'The' -> 'THe'
            'sticky_key': 0.05        # Key stuck: 'the' -> 'thhe'
        }
        
        # Fatigue simulation
        self.fatigue_level = 0.0
        self.chars_typed = 0
        
        # Hand alternation tracking
        self.left_hand_keys = set('qwertasdfgzxcvb12345')
        self.right_hand_keys = set('yuiophjklnm67890')
        self.last_hand = None
        
        # Common word corrections (muscle memory)
        self.common_corrections = {
            'teh': 'the',
            'adn': 'and',
            'taht': 'that',
            'thsi': 'this',
            'wiht': 'with',
            'ahve': 'have',
            'waht': 'what',
            'thier': 'their',
            'recieve': 'receive',
            'occured': 'occurred'
        }
        
    def generate_advanced_typo(self, char: str, context: str = "", position: int = 0) -> Tuple[str, bool]:
        """
        Generate sophisticated typo based on context and patterns
        Returns: (typo_char, should_correct)
        """
        char_lower = char.lower()
        
        # Choose typo type based on weighted probabilities
        typo_type = self._choose_typo_type()
        
        if typo_type == 'neighbor_key':
            # Hit neighboring key
            if char_lower in self.keyboard_neighbors:
                typo = random.choice(self.keyboard_neighbors[char_lower])
                return (typo.upper() if char.isupper() else typo, True)
        
        elif typo_type == 'double_tap':
            # Double tap same key
            return (char + char, True)
        
        elif typo_type == 'transposition':
            # This needs to be handled at word level
            return (char, False)
        
        elif typo_type == 'missed_key':
            # Skip this character entirely
            return ('', True)
        
        elif typo_type == 'wrong_case':
            # Wrong capitalization
            return (char.swapcase(), True)
        
        elif typo_type == 'sticky_key':
            # Key gets stuck, multiple chars
            repeat = random.choice([2, 3])
            return (char * repeat, True)
        
        return (char, False)
    
    def _choose_typo_type(self) -> str:
        """Choose typo type based on weighted probabilities"""
        rand = random.random()
        cumulative = 0
        
        for typo_type, probability in self.typo_patterns.items():
            cumulative += probability
            if rand <= cumulative:
                return typo_type
        
        return 'neighbor_key'  # Default
    
    def calculate_dynamic_delay(self, 
                              char: str, 
                              prev_char: str, 
                              base_delay: float,
                              wpm: int,
                              position_in_text: int,
                              total_chars: int) -> float:
        """
        Calculate sophisticated, context-aware typing delay
        """
        delay = base_delay
        
        # 1. Fatigue simulation (typing gets slower over time)
        fatigue_factor = 1.0 + (self.fatigue_level * 0.3)
        delay *= fatigue_factor
        
        # Update fatigue
        self.chars_typed += 1
        if self.chars_typed % 100 == 0:
            self.fatigue_level = min(1.0, self.fatigue_level + 0.05)
        
        # 2. Hand alternation (same hand = slightly slower)
        current_hand = self._get_hand(char.lower())
        if current_hand and self.last_hand == current_hand:
            delay *= random.uniform(1.05, 1.15)  # Same hand penalty
        self.last_hand = current_hand
        
        # 3. Bigram difficulty (some letter combinations are harder)
        if prev_char and char:
            bigram_delay = self._get_bigram_difficulty(prev_char.lower() + char.lower())
            delay *= bigram_delay
        
        # 4. Capital letters (shift key adds delay)
        if char.isupper():
            delay *= random.uniform(1.2, 1.4)
        
        # 5. Special characters (even more delay)
        if not char.isalnum() and char != ' ':
            delay *= random.uniform(1.3, 1.6)
        
        # 6. Numbers (reaching to number row)
        if char.isdigit():
            delay *= random.uniform(1.25, 1.5)
        
        # 7. Start of text (warming up)
        if position_in_text < 20:
            warmup_factor = 1.3 - (position_in_text * 0.015)
            delay *= warmup_factor
        
        # 8. End of text (rushing to finish)
        if total_chars > 0:
            progress = position_in_text / total_chars
            if progress > 0.8:
                rush_factor = 0.9 - (progress - 0.8) * 0.3
                delay *= rush_factor
        
        # 9. After punctuation (micro pause)
        if prev_char in '.!?,;:':
            delay *= random.uniform(1.5, 2.5)
        
        # 10. Random micro-variations (human inconsistency)
        delay *= random.uniform(0.85, 1.15)
        
        # 11. Burst typing simulation
        if random.random() < 0.05:  # 5% chance of burst
            if random.random() < 0.5:  # Fast burst
                delay *= random.uniform(0.5, 0.7)
            else:  # Slow burst (hesitation)
                delay *= random.uniform(1.5, 2.0)
        
        return max(0.01, delay)  # Minimum 10ms
    
    def _get_hand(self, char: str) -> Optional[str]:
        """Determine which hand types a character"""
        if char in self.left_hand_keys:
            return 'left'
        elif char in self.right_hand_keys:
            return 'right'
        return None
    
    def _get_bigram_difficulty(self, bigram: str) -> float:
        """Get typing difficulty multiplier for character pairs"""
        # Common easy bigrams (rolled on same hand)
        easy_bigrams = {'er', 're', 'rt', 'tr', 'as', 'sa', 'df', 'fd', 
                       'jk', 'kj', 'ui', 'iu', 'op', 'po'}
        
        # Hard bigrams (awkward finger positions)
        hard_bigrams = {'za', 'az', 'xq', 'qx', 'mk', 'km', 'pl', 'lp',
                       'zx', 'xz', 'qp', 'pq', 'ws', 'sw'}
        
        if bigram in easy_bigrams:
            return random.uniform(0.85, 0.95)
        elif bigram in hard_bigrams:
            return random.uniform(1.15, 1.35)
        else:
            return 1.0
    
    def simulate_correction_behavior(self, typo_made: bool, chars_since_typo: int) -> bool:
        """
        Decide whether to correct a typo based on realistic patterns
        """
        if not typo_made:
            return False
        
        # Immediate correction (noticed right away)
        if chars_since_typo <= 2:
            return random.random() < 0.70  # 70% chance
        
        # Delayed correction (noticed after a few chars)
        elif chars_since_typo <= 5:
            return random.random() < 0.25  # 25% chance
        
        # Late correction (going back to fix)
        elif chars_since_typo <= 10:
            return random.random() < 0.05  # 5% chance
        
        # Missed typo (never corrected)
        return False
    
    def generate_natural_pauses(self, text: str, position: int) -> Optional[float]:
        """
        Generate natural pause durations based on context
        """
        if position >= len(text):
            return None
        
        char = text[position]
        
        # Thinking pauses (before difficult words)
        if position < len(text) - 5:
            next_word = ""
            for i in range(position, min(position + 15, len(text))):
                if text[i] == ' ':
                    break
                next_word += text[i]
            
            # Complex words trigger thinking
            if len(next_word) > 10 or any(c in next_word for c in 'xqz'):
                if random.random() < 0.1:  # 10% chance
                    return random.uniform(1.0, 3.0)
        
        # Sentence boundary pauses
        if char in '.!?':
            if random.random() < 0.3:  # 30% chance
                return random.uniform(0.5, 2.0)
        
        # Paragraph pauses
        if position > 0 and text[position-1:position+1] == '\\n\\n':
            return random.uniform(2.0, 5.0)
        
        # Random micro-pauses (distraction)
        if random.random() < 0.002:  # 0.2% chance per character
            return random.uniform(3.0, 10.0)  # Got distracted
        
        return None
    
    def apply_rhythm_variation(self, base_delay: float, rhythm_phase: float) -> float:
        """
        Apply natural rhythm variations (people don't type at constant speed)
        """
        # Sine wave rhythm (natural speeding up and slowing down)
        rhythm_factor = 1.0 + 0.15 * math.sin(rhythm_phase)
        
        # Occasional rhythm breaks
        if random.random() < 0.02:  # 2% chance
            rhythm_factor *= random.choice([0.7, 1.3])  # Speed burst or slow patch
        
        return base_delay * rhythm_factor

# Test the advanced humanizer
if __name__ == "__main__":
    humanizer = AdvancedHumanizer()
    
    test_text = "The quick brown fox jumps over the lazy dog."
    prev_char = ""
    
    print("Advanced Humanization Test")
    print("-" * 50)
    
    for i, char in enumerate(test_text):
        # Calculate delay
        delay = humanizer.calculate_dynamic_delay(
            char, prev_char, 0.1, 60, i, len(test_text)
        )
        
        # Check for typo
        if random.random() < 0.03:  # 3% typo chance
            typo, should_correct = humanizer.generate_advanced_typo(char, test_text, i)
            print(f"Char: '{char}' -> Typo: '{typo}' (Delay: {delay:.3f}s, Correct: {should_correct})")
        else:
            print(f"Char: '{char}' (Delay: {delay:.3f}s)")
        
        prev_char = char
    
    print("-" * 50)
    print(f"Final fatigue level: {humanizer.fatigue_level:.2f}")