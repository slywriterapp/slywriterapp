"""
Grammarly-style correction simulator for realistic typing
"""

import random
import time
import keyboard

# Common typing mistakes that Grammarly would catch
COMMON_MISTAKES = {
    # Wrong word forms
    'their': ['there', 'theyre'],
    'there': ['their', 'theyre'],
    'your': ['youre', 'ur'],
    'its': ['it\'s', 'its\''],
    'affect': ['effect'],
    'effect': ['affect'],
    'then': ['than'],
    'than': ['then'],
    'to': ['too', 'two'],
    'too': ['to', 'two'],
    
    # Missing apostrophes
    'don\'t': ['dont'],
    'can\'t': ['cant'],
    'won\'t': ['wont'],
    'isn\'t': ['isnt'],
    'aren\'t': ['arent'],
    'wasn\'t': ['wasnt'],
    'weren\'t': ['werent'],
    'hasn\'t': ['hasnt'],
    'haven\'t': ['havent'],
    'couldn\'t': ['couldnt'],
    'wouldn\'t': ['wouldnt'],
    'shouldn\'t': ['shouldnt'],
    
    # Double letters
    'necessary': ['neccessary', 'necesary'],
    'accommodate': ['accomodate', 'acommodate'],
    'occurred': ['occured', 'ocurred'],
    'tomorrow': ['tommorow', 'tommorrow'],
    'beginning': ['begining', 'beggining'],
    
    # Common misspellings
    'definitely': ['definately', 'definatly', 'definitly'],
    'separate': ['seperate'],
    'believe': ['beleive', 'belive'],
    'receive': ['recieve'],
    'weird': ['wierd'],
    'friend': ['freind'],
    'finally': ['finaly'],
    'beautiful': ['beautifull', 'beutiful'],
}

def simulate_grammarly_correction(text, correction_delay=2.0, mistake_probability=0.15):
    """
    Simulates Grammarly-style corrections by:
    1. Intentionally typing common mistakes
    2. Waiting a delay (as if Grammarly is processing)
    3. Going back and correcting the mistakes
    """
    words = text.split()
    corrections_needed = []
    chars_typed = 0
    
    for word_idx, word in enumerate(words):
        word_lower = word.lower().rstrip('.,!?;:')
        
        # Check if we should make a mistake with this word
        if random.random() < mistake_probability and word_lower in COMMON_MISTAKES:
            # Type the mistake
            mistake = random.choice(COMMON_MISTAKES[word_lower])
            
            # Preserve original capitalization
            if word[0].isupper():
                mistake = mistake[0].upper() + mistake[1:]
            
            # Type the mistaken word
            keyboard.write(mistake)
            chars_typed += len(mistake)
            
            # Record correction needed
            corrections_needed.append({
                'position': chars_typed,
                'wrong_text': mistake,
                'correct_text': word,
                'word_index': word_idx
            })
            
            # Add punctuation if present
            if word[-1] in '.,!?;:':
                keyboard.write(word[-1])
                chars_typed += 1
        else:
            # Type the word correctly
            keyboard.write(word)
            chars_typed += len(word)
        
        # Add space after word (except last word)
        if word_idx < len(words) - 1:
            keyboard.write(' ')
            chars_typed += 1
        
        # Small delay between words
        time.sleep(random.uniform(0.05, 0.15))
    
    # Wait before corrections (simulating Grammarly processing)
    if corrections_needed:
        time.sleep(correction_delay)
        
        # Now go back and make corrections
        for correction in reversed(corrections_needed):  # Start from the end
            # Calculate how many characters to go back
            chars_to_delete = len(correction['wrong_text'])
            
            # Move cursor to the mistake (simplified - would need more complex logic in practice)
            # This is a simplified version - in reality would need to track cursor position
            
            # Select the wrong word (Ctrl+Shift+Left arrow multiple times)
            for _ in range(chars_to_delete):
                keyboard.send('shift+left')
                time.sleep(0.01)
            
            # Type the correction
            keyboard.write(correction['correct_text'])
            time.sleep(random.uniform(0.1, 0.2))
            
            # Move cursor back to end
            keyboard.send('end')
            time.sleep(0.05)

def add_grammarly_mistakes_to_text(text, mistake_probability=0.15):
    """
    Returns text with intentional mistakes that Grammarly would catch
    """
    words = text.split()
    result_words = []
    
    for word in words:
        word_lower = word.lower().rstrip('.,!?;:')
        punctuation = ''
        if word[-1] in '.,!?;:':
            punctuation = word[-1]
            word = word[:-1]
        
        if random.random() < mistake_probability and word_lower in COMMON_MISTAKES:
            mistake = random.choice(COMMON_MISTAKES[word_lower])
            if word[0].isupper():
                mistake = mistake[0].upper() + mistake[1:]
            result_words.append(mistake + punctuation)
        else:
            result_words.append(word + punctuation)
    
    return ' '.join(result_words)