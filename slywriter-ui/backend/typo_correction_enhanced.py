"""
Enhanced Typo Correction System
- Ensures all typos are corrected
- Supports delayed correction (Grammarly-style)
- Tracks typo positions for batch correction
"""

import time
import random
import pyautogui
import threading
from typing import List, Tuple, Optional
from dataclasses import dataclass
from collections import deque

@dataclass
class TypoEvent:
    """Represents a typo that was made"""
    position: int  # Character position in text
    original_char: str  # What should have been typed
    typo_char: str  # What was actually typed
    timestamp: float  # When the typo was made
    corrected: bool = False  # Whether it's been corrected

class EnhancedTypoCorrector:
    """Advanced typo correction with Grammarly-style delayed corrections"""
    
    def __init__(self, correction_delay: float = 3.0, batch_correction: bool = False):
        """
        Initialize the typo corrector
        
        Args:
            correction_delay: Seconds to wait before correcting typos
            batch_correction: If True, correct multiple typos at once
        """
        self.correction_delay = correction_delay
        self.batch_correction = batch_correction
        self.typo_queue: deque[TypoEvent] = deque()
        self.current_position = 0
        self.correction_thread: Optional[threading.Thread] = None
        self.stop_corrections = threading.Event()
        
    def make_typo_and_track(self, original_char: str, position: int) -> str:
        """
        Generate a typo and track it for later correction
        
        Args:
            original_char: The correct character
            position: Current position in text
            
        Returns:
            The typo character to type
        """
        # Common typo patterns
        typo_char = self._generate_realistic_typo(original_char)
        
        # Track the typo
        typo_event = TypoEvent(
            position=position,
            original_char=original_char,
            typo_char=typo_char,
            timestamp=time.time()
        )
        
        self.typo_queue.append(typo_event)
        
        return typo_char
    
    def _generate_realistic_typo(self, char: str) -> str:
        """Generate a realistic typo based on keyboard proximity"""
        
        # Keyboard layout for proximity-based typos
        keyboard_neighbors = {
            'q': ['w', 'a', '1', '2'],
            'w': ['q', 'e', 's', 'a', '2', '3'],
            'e': ['w', 'r', 'd', 's', '3', '4'],
            'r': ['e', 't', 'f', 'd', '4', '5'],
            't': ['r', 'y', 'g', 'f', '5', '6'],
            'y': ['t', 'u', 'h', 'g', '6', '7'],
            'u': ['y', 'i', 'j', 'h', '7', '8'],
            'i': ['u', 'o', 'k', 'j', '8', '9'],
            'o': ['i', 'p', 'l', 'k', '9', '0'],
            'p': ['o', 'l', '0', '-'],
            
            'a': ['q', 'w', 's', 'z'],
            's': ['a', 'w', 'e', 'd', 'x', 'z'],
            'd': ['s', 'e', 'r', 'f', 'c', 'x'],
            'f': ['d', 'r', 't', 'g', 'v', 'c'],
            'g': ['f', 't', 'y', 'h', 'b', 'v'],
            'h': ['g', 'y', 'u', 'j', 'n', 'b'],
            'j': ['h', 'u', 'i', 'k', 'm', 'n'],
            'k': ['j', 'i', 'o', 'l', 'm'],
            'l': ['k', 'o', 'p'],
            
            'z': ['a', 's', 'x'],
            'x': ['z', 's', 'd', 'c'],
            'c': ['x', 'd', 'f', 'v'],
            'v': ['c', 'f', 'g', 'b'],
            'b': ['v', 'g', 'h', 'n'],
            'n': ['b', 'h', 'j', 'm'],
            'm': ['n', 'j', 'k'],
            
            ' ': [' '],  # Space rarely has typos
        }
        
        char_lower = char.lower()
        
        # Get neighboring keys
        if char_lower in keyboard_neighbors:
            neighbors = keyboard_neighbors[char_lower]
            typo = random.choice(neighbors)
            
            # Preserve case
            if char.isupper():
                typo = typo.upper()
            
            return typo
        
        # For characters not in the map, return the same character
        # (numbers, punctuation, etc. are less likely to have typos)
        return char
    
    def type_with_guaranteed_correction(self, text: str, char: str, position: int, 
                                       immediate_correction: bool = True) -> None:
        """
        Type a character with guaranteed typo correction
        
        Args:
            text: Full text being typed
            char: Character to type
            position: Current position in text
            immediate_correction: If True, correct immediately; if False, use delayed correction
        """
        # Decide if we should make a typo
        should_make_typo = random.random() < 0.05  # 5% typo chance
        
        if should_make_typo and char.isalpha():
            # Make a typo
            typo_char = self.make_typo_and_track(char, position)
            pyautogui.write(typo_char)
            
            if immediate_correction:
                # Correct immediately
                time.sleep(random.uniform(0.2, 0.5))  # Human reaction time
                self._correct_typo_immediately()
            else:
                # Schedule for delayed correction
                if not self.correction_thread or not self.correction_thread.is_alive():
                    self.start_delayed_corrections()
        else:
            # Type correctly
            pyautogui.write(char)
    
    def _correct_typo_immediately(self) -> None:
        """Correct the most recent typo immediately"""
        if not self.typo_queue:
            return
        
        typo = self.typo_queue[-1]
        if not typo.corrected:
            # Backspace and retype
            pyautogui.press('backspace')
            time.sleep(random.uniform(0.05, 0.15))
            pyautogui.write(typo.original_char)
            typo.corrected = True
    
    def start_delayed_corrections(self) -> None:
        """Start the delayed correction thread"""
        self.stop_corrections.clear()
        self.correction_thread = threading.Thread(target=self._delayed_correction_worker)
        self.correction_thread.daemon = True
        self.correction_thread.start()
    
    def _delayed_correction_worker(self) -> None:
        """Worker thread for delayed corrections"""
        while not self.stop_corrections.is_set():
            current_time = time.time()
            corrections_to_make = []
            
            # Find typos ready for correction
            for typo in self.typo_queue:
                if not typo.corrected and (current_time - typo.timestamp) >= self.correction_delay:
                    corrections_to_make.append(typo)
            
            if corrections_to_make:
                if self.batch_correction:
                    self._perform_batch_correction(corrections_to_make)
                else:
                    for typo in corrections_to_make:
                        self._perform_single_delayed_correction(typo)
            
            time.sleep(0.5)  # Check every 500ms
    
    def _perform_single_delayed_correction(self, typo: TypoEvent) -> None:
        """
        Perform a single delayed correction
        Simulates going back to fix a typo like Grammarly
        """
        if typo.corrected:
            return
        
        # Calculate how many characters back we need to go
        chars_since_typo = self.current_position - typo.position
        
        if chars_since_typo > 0:
            # Move cursor back
            for _ in range(chars_since_typo):
                pyautogui.press('left')
            
            # Delete the typo
            pyautogui.press('delete')
            time.sleep(0.05)
            
            # Type the correct character
            pyautogui.write(typo.original_char)
            time.sleep(0.05)
            
            # Move cursor back to original position
            for _ in range(chars_since_typo - 1):
                pyautogui.press('right')
            
            typo.corrected = True
    
    def _perform_batch_correction(self, typos: List[TypoEvent]) -> None:
        """
        Correct multiple typos in one go
        Simulates selecting text and using spell check
        """
        if not typos:
            return
        
        # Sort typos by position (furthest first to maintain positions)
        typos.sort(key=lambda t: t.position, reverse=True)
        
        for typo in typos:
            if not typo.corrected:
                self._perform_single_delayed_correction(typo)
                time.sleep(random.uniform(0.1, 0.3))  # Small delay between corrections
    
    def update_position(self, position: int) -> None:
        """Update the current typing position"""
        self.current_position = position
    
    def stop(self) -> None:
        """Stop the correction thread"""
        self.stop_corrections.set()
        if self.correction_thread:
            self.correction_thread.join(timeout=1)
    
    def get_correction_stats(self) -> dict:
        """Get statistics about typos and corrections"""
        total_typos = len(self.typo_queue)
        corrected = sum(1 for t in self.typo_queue if t.corrected)
        pending = total_typos - corrected
        
        return {
            'total_typos': total_typos,
            'corrected': corrected,
            'pending': pending,
            'correction_rate': (corrected / total_typos * 100) if total_typos > 0 else 0
        }

class TypoPatterns:
    """Advanced typo patterns for more realistic typing"""
    
    @staticmethod
    def double_letter_typo(text: str, position: int) -> Optional[str]:
        """Sometimes type a letter twice (e.g., 'the' -> 'thhe')"""
        if position > 0 and text[position - 1].isalpha():
            if random.random() < 0.02:  # 2% chance
                return text[position - 1]
        return None
    
    @staticmethod
    def missed_letter_typo(char: str) -> bool:
        """Sometimes miss a letter entirely (skip it)"""
        return random.random() < 0.01  # 1% chance
    
    @staticmethod
    def transposition_typo(text: str, position: int) -> Optional[Tuple[str, str]]:
        """Sometimes swap two adjacent letters (e.g., 'the' -> 'hte')"""
        if position < len(text) - 1:
            if random.random() < 0.015:  # 1.5% chance
                return (text[position + 1], text[position])
        return None
    
    @staticmethod
    def capitalization_typo(char: str) -> str:
        """Sometimes mess up capitalization"""
        if char.isalpha() and random.random() < 0.01:  # 1% chance
            return char.swapcase()
        return char

def test_typo_correction():
    """Test the enhanced typo correction system"""
    
    print("Testing Enhanced Typo Correction System")
    print("=" * 50)
    
    # Test immediate correction
    corrector = EnhancedTypoCorrector(correction_delay=0, batch_correction=False)
    
    test_text = "Hello, this is a test of the typo correction system."
    
    print(f"Original text: {test_text}")
    print("Typing with immediate correction...")
    
    for i, char in enumerate(test_text):
        corrector.update_position(i)
        corrector.type_with_guaranteed_correction(test_text, char, i, immediate_correction=True)
        time.sleep(random.uniform(0.05, 0.15))  # Simulate typing speed
    
    stats = corrector.get_correction_stats()
    print(f"\nStats: {stats}")
    
    # Test delayed correction
    print("\n" + "=" * 50)
    print("Testing delayed correction (Grammarly-style)...")
    
    corrector2 = EnhancedTypoCorrector(correction_delay=3.0, batch_correction=True)
    corrector2.start_delayed_corrections()
    
    for i, char in enumerate(test_text):
        corrector2.update_position(i)
        corrector2.type_with_guaranteed_correction(test_text, char, i, immediate_correction=False)
        time.sleep(random.uniform(0.05, 0.15))
    
    print("Waiting for delayed corrections...")
    time.sleep(5)  # Wait for corrections to happen
    
    stats2 = corrector2.get_correction_stats()
    print(f"\nStats: {stats2}")
    
    corrector2.stop()
    print("\nTest complete!")

if __name__ == "__main__":
    # Uncomment to run test
    # test_typo_correction()
    pass