# typing_engine.py

import threading
import time
import random
import sys
import os
from datetime import datetime
import config
import clipboard
import webbrowser
import platform

# Cross-platform keyboard handling
IS_MACOS = platform.system() == 'Darwin'
if IS_MACOS:
    import pyautogui
    # macOS-compatible keyboard wrapper
    class KeyboardWrapper:
        @staticmethod
        def write(text, delay=0):
            pyautogui.write(text, interval=delay)

        @staticmethod
        def send(key):
            pyautogui.press(key)

    keyboard = KeyboardWrapper()
else:
    import keyboard  # Windows/Linux - use original library

_typing_thread = None
_stop_flag = threading.Event()
_pause_flag = threading.Event()

_punctuations = config.PUNCTUATION_PAUSE_CHARS
_custom_typos = config.custom_typos

_account_tab = None
_stats_tab = None   # Diagnostics tab reference
_overlay_tab = None  # Overlay tab reference

def set_account_tab_reference(tab):
    global _account_tab
    _account_tab = tab
    print("Account tab reference set in typing_engine")

def set_stats_tab_reference(tab):  # Diagnostics setter
    global _stats_tab
    _stats_tab = tab
    print("Stats tab reference set in typing_engine")

def _get_user_log_file():
    """Get user-specific log file path"""
    try:
        # Try to get user info from the account tab
        if _account_tab and hasattr(_account_tab, 'app') and _account_tab.app.user:
            user_id = _account_tab.app.user.get('id', 'unknown')
            # Create user-specific log file name
            base_dir = os.path.dirname(config.LOG_FILE)
            user_log_file = os.path.join(base_dir, f"typing_log_{user_id}.txt")
            return user_log_file
        else:
            # No user logged in - use default log file
            return config.LOG_FILE
    except Exception:
        # Fallback to default log file
        return config.LOG_FILE

def set_overlay_tab_reference(tab):  # Overlay setter
    global _overlay_tab
    _overlay_tab = tab
    print("Overlay tab reference set in typing_engine")

def _update_status_and_overlay(status_callback, text):
    """Update status callback (which will broadcast via WebSocket)"""
    status_callback(text)

def stop_typing_func():
    _stop_flag.set()
    _pause_flag.clear()
    if _typing_thread and _typing_thread.is_alive():
        _typing_thread.join(timeout=2.0)  # Give more time for thread to stop
    _stop_flag.clear()

def pause_typing():
    _pause_flag.set()

def resume_typing():
    _pause_flag.clear()

def start_typing_from_input(
    text: str,
    live_preview_callback,
    status_callback,
    *,
    min_delay: float = config.MIN_DELAY_DEFAULT,
    max_delay: float = config.MAX_DELAY_DEFAULT,
    typos_on: bool = True,
    pause_freq: int = config.LONG_PAUSE_DEFAULT,
    preview_only: bool = False,
    grammarly_mode: bool = False,
    grammarly_delay: float = 2.0,
    typo_rate: float = 2.0  # Percentage chance of typos
):
    global _typing_thread
    stop_typing_func()

    def _worker():
        if _account_tab and not _account_tab.has_words_remaining():
            status_callback("Limit reached – upgrade plan to continue.")
            print("[BLOCKED] Typing blocked: word limit reached.")
            return

        for i in range(5, 0, -1):
            if _stop_flag.is_set():
                _update_status_and_overlay(status_callback, "❌ Cancelled")
                return
            
            # Check for pause during countdown
            while _pause_flag.is_set() and not _stop_flag.is_set():
                _update_status_and_overlay(status_callback, "⏸️ Paused")
                time.sleep(0.1)
            
            if _stop_flag.is_set():
                _update_status_and_overlay(status_callback, "❌ Cancelled")
                return
                
            _update_status_and_overlay(status_callback, f"Starting in {i}...")
            for _ in range(10):
                if _stop_flag.is_set():
                    _update_status_and_overlay(status_callback, "❌ Cancelled")
                    return
                
                # Check for pause during each 0.1s interval
                while _pause_flag.is_set() and not _stop_flag.is_set():
                    _update_status_and_overlay(status_callback, "⏸️ Paused")
                    time.sleep(0.1)
                
                if _stop_flag.is_set():
                    _update_status_and_overlay(status_callback, "❌ Cancelled")
                    return
                    
                time.sleep(0.1)

        preview = ""
        last_pause = 0
        _update_status_and_overlay(status_callback, "⌨️ Typing...")
        word_count = 0
        words_since_last_report = 0
        typos_made = 0  # Track typos for live stats
        delayed_corrections = []  # Track mistakes for later correction

        # --- WPM/session logging additions ---
        start_time = time.time()
        profile_name = None
        try:
            # Try to get the profile name from the account tab or app
            if _account_tab:
                if hasattr(_account_tab, "get_active_profile_name"):
                    profile_name = _account_tab.get_active_profile_name()
                elif hasattr(_account_tab, "app") and hasattr(_account_tab.app, "active_profile"):
                    profile_name = _account_tab.app.active_profile.get()
        except Exception:
            profile_name = "Default"
        # --- end additions ---

        # Track when we last took a break
        last_break_idx = 0
        
        for idx, ch in enumerate(text):
            if _stop_flag.is_set():
                _update_status_and_overlay(status_callback, "⏹️ Stopped")
                return

            while _pause_flag.is_set() and not _stop_flag.is_set():
                _update_status_and_overlay(status_callback, "⏸️ Paused")
                time.sleep(0.1)

            if _stop_flag.is_set():
                _update_status_and_overlay(status_callback, "⏹️ Stopped")
                return

            if _account_tab and not _account_tab.has_words_remaining():
                status_callback("Limit reached – upgrade plan to continue.")
                print("[LIMIT] Typing interrupted: limit reached mid-session.")
                return
            
            # Add random breaks throughout typing (not just at punctuation)
            chars_since_break = idx - last_break_idx
            if chars_since_break > random.randint(150, 300):  # Break every 150-300 chars
                if random.random() < 0.7:  # 70% chance when due
                    break_type = random.choice(['thinking', 'distracted', 'coffee'])
                    if break_type == 'thinking':
                        break_duration = random.uniform(1.5, 3.5)
                        _update_status_and_overlay(status_callback, f"💭 Thinking ({break_duration:.1f}s)...")
                    elif break_type == 'distracted':
                        break_duration = random.uniform(2.0, 4.0)
                        _update_status_and_overlay(status_callback, f"👀 Distracted ({break_duration:.1f}s)...")
                    else:
                        break_duration = random.uniform(3.0, 6.0)
                        _update_status_and_overlay(status_callback, f"☕ Coffee break ({break_duration:.1f}s)...")
                    
                    for i in range(int(break_duration * 10)):
                        if _stop_flag.is_set():
                            _update_status_and_overlay(status_callback, "⏹️ Stopped")
                            return
                        while _pause_flag.is_set() and not _stop_flag.is_set():
                            _update_status_and_overlay(status_callback, "⏸️ Paused")
                            time.sleep(0.1)
                        time.sleep(0.1)
                    
                    _update_status_and_overlay(status_callback, "⌨️ Typing...")
                    last_break_idx = idx


            # Delayed correction mode: intentionally make mistakes on certain words
            # Only do this if we haven't made too many mistakes recently
            if grammarly_mode and ch.isspace() and preview and not preview_only and len(delayed_corrections) < 2:
                # Check if we just typed a word that should have a "mistake"
                last_word = preview.split()[-1] if preview.split() else ""
                # Common words to make mistakes with (15% chance - reduced to be more natural)
                common_words = ['the', 'and', 'that', 'have', 'with', 'this', 'from', 'they', 'would', 'there', 'their', 'what', 'about', 'which', 'when', 'been', 'were', 'being']
                if last_word.lower().rstrip('.,!?;:') in common_words and random.random() < 0.15:
                    # Make a deliberate mistake
                    mistake_types = [
                        ('the', 'teh'),
                        ('and', 'adn'),
                        ('that', 'taht'),
                        ('have', 'ahve'),
                        ('with', 'wiht'),
                        ('this', 'thsi'),
                        ('from', 'form'),
                        ('they', 'tehy'),
                        ('would', 'woudl'),
                        ('there', 'thier'),
                        ('their', 'thier'),
                        ('what', 'waht'),
                        ('about', 'abuot'),
                        ('which', 'whcih'),
                        ('when', 'wehn'),
                        ('been', 'bene'),
                        ('were', 'wer'),
                        ('being', 'bieng')
                    ]
                    
                    # Find the mistake to make
                    mistake_word = None
                    for correct, wrong in mistake_types:
                        if last_word.lower().rstrip('.,!?;:') == correct:
                            mistake_word = wrong
                            break
                    
                    if mistake_word:
                        # Go back and fix the word
                        _update_status_and_overlay(status_callback, "✏️ Making typo...")
                        
                        # Delete the correct word
                        for _ in range(len(last_word)):
                            keyboard.send("backspace")
                            preview = preview[:-1]
                            time.sleep(0.02)
                        
                        # Type the mistake
                        for char in mistake_word:
                            keyboard.write(char)
                            preview += char
                            time.sleep(random.uniform(0.03, 0.08))
                        
                        # Continue typing and record for later correction
                        delayed_corrections.append({
                            'position': len(preview),
                            'word': mistake_word,
                            'correct_word': last_word,
                            'chars_after': 0
                        })
                        
                        _update_status_and_overlay(status_callback, "⌨️ Typing...")
            
            # Normal typos - immediate correction (like catching yourself)
            # Reduce chance if delayed correction mode is active to avoid too much chaos
            typo_chance = typo_rate / 100.0  # Convert percentage to probability
            if grammarly_mode:
                typo_chance = typo_chance * 0.5  # Half the normal typo rate when delayed correction is on
            
            if typos_on and random.random() < typo_chance and not ch.isspace():
                # Don't make a typo if we're about to correct a delayed mistake
                skip_typo = False
                for mistake in delayed_corrections:
                    if mistake['chars_after'] >= 14:  # About to correct
                        skip_typo = True
                        break
                
                if not skip_typo:
                    # More realistic typos based on keyboard proximity
                    keyboard_neighbors = {
                        'a': 'qwsz', 'b': 'vghn', 'c': 'xdfv', 'd': 'serfcx', 'e': 'wrsdf',
                        'f': 'drtgvc', 'g': 'ftyhbv', 'h': 'gyujnb', 'i': 'ujklo', 'j': 'huikmn',
                        'k': 'jiolm', 'l': 'kop', 'm': 'njk', 'n': 'bhjm', 'o': 'iklp',
                        'p': 'ol', 'q': 'wa', 'r': 'edft', 's': 'awedxz', 't': 'rfgy',
                        'u': 'yhji', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc', 'y': 'tghu',
                        'z': 'asx', ' ': 'cvbnm'
                    }
                    
                    # Choose wrong character based on what key we're trying to type
                    ch_lower = ch.lower()
                    if ch_lower in keyboard_neighbors:
                        # Hit adjacent key instead
                        wrong_char = random.choice(keyboard_neighbors[ch_lower])
                        if ch.isupper():
                            wrong_char = wrong_char.upper()
                    else:
                        # For special characters, just skip the typo
                        wrong_char = None
                    
                    if wrong_char and not preview_only:
                        keyboard.write(wrong_char)
                        # Human-like delay before noticing the typo (0.1-0.3 seconds)
                        time.sleep(random.uniform(0.1, 0.3))
                        keyboard.send("backspace")
                        # Small pause after correction
                        time.sleep(random.uniform(0.05, 0.1))
                        typos_made += 1
                        # Broadcast typo count update
                        if status_callback:
                            try:
                                # Try to send typo update via status callback
                                status_callback(f"TYPO_UPDATE:{typos_made}")
                            except:
                                pass
                    live_preview_callback(preview)

            if not preview_only:
                keyboard.write(ch)
            preview += ch
            live_preview_callback(preview)
            
            # Update chars_after for all delayed corrections
            for mistake in delayed_corrections:
                mistake['chars_after'] += 1
            
            # Check if we should correct any delayed mistakes (after typing 20-40 more chars)
            if grammarly_mode and delayed_corrections and not preview_only:
                for i, mistake in enumerate(delayed_corrections):
                    # More natural correction timing - wait longer
                    if mistake['chars_after'] >= random.randint(20, 40):
                        # Time to correct this mistake!
                        _update_status_and_overlay(status_callback, "📝 Auto-correcting...")
                        
                        # Pause like we're noticing the error
                        time.sleep(random.uniform(0.5, grammarly_delay))
                        
                        # Calculate how many characters to backspace
                        chars_to_delete = len(preview) - mistake['position'] + len(mistake['word'])
                        deleted_text = preview[-chars_to_delete:]
                        
                        # Backspace to the mistake
                        for _ in range(chars_to_delete):
                            keyboard.send("backspace")
                            preview = preview[:-1]
                            live_preview_callback(preview)
                            time.sleep(0.015)
                        
                        # Type the correct word
                        correct_word = mistake['correct_word']
                        for char in correct_word:
                            keyboard.write(char)
                            preview += char
                            live_preview_callback(preview)
                            time.sleep(random.uniform(0.02, 0.05))
                        
                        # Retype the text that was after the mistake
                        retype_text = deleted_text[len(mistake['word']):]
                        for char in retype_text:
                            keyboard.write(char)
                            preview += char
                            live_preview_callback(preview)
                            time.sleep(random.uniform(min_delay * 0.7, min_delay))
                        
                        # Remove this mistake from the list
                        delayed_corrections.pop(i)
                        
                        _update_status_and_overlay(status_callback, "⌨️ Typing...")
                        break  # Only correct one mistake at a time

            if ch in _punctuations:
                # Regular punctuation pause
                time.sleep(max_delay * 2)
                
                # Longer sentence breaks for period, exclamation, question mark
                if ch in ".!?":
                    # Simulate user looking elsewhere, checking other tabs, etc.
                    sentence_break_chance = 0.3  # 30% chance
                    if random.random() < sentence_break_chance:
                        sentence_break_duration = random.uniform(2.0, 5.0)  # 2-5 second break
                        _update_status_and_overlay(status_callback, f"☕ Taking a break ({sentence_break_duration:.1f}s)...")
                        
                        # Check for stop/pause during the break
                        for i in range(int(sentence_break_duration * 10)):
                            if _stop_flag.is_set():
                                _update_status_and_overlay(status_callback, "⏹️ Stopped")
                                return
                            while _pause_flag.is_set() and not _stop_flag.is_set():
                                _update_status_and_overlay(status_callback, "⏸️ Paused")
                                time.sleep(0.1)
                            time.sleep(0.1)
                        
                        _update_status_and_overlay(status_callback, "⌨️ Resuming typing...")

            if pause_freq and (idx - last_pause) >= pause_freq:
                time.sleep(max_delay)
                last_pause = idx

            # Human-like variable typing speed
            if grammarly_mode or typos_on:
                # More variation in typing speed for human mode
                if random.random() < 0.1:  # 10% chance of hesitation
                    time.sleep(random.uniform(max_delay * 2, max_delay * 3))
                elif random.random() < 0.2:  # 20% chance of fast burst
                    time.sleep(random.uniform(min_delay * 0.5, min_delay))
                else:
                    time.sleep(random.uniform(min_delay, max_delay))
            else:
                time.sleep(random.uniform(min_delay, max_delay))

            if ch.isspace():
                word_count += 1
                words_since_last_report += 1
                # Removed emoji that causes encoding error
                print(f"Word typed. Total so far: {word_count}")
                if words_since_last_report >= 10:
                    if _account_tab:
                        print("[UPDATE] 10 words typed - incrementing usage bar")
                        _account_tab.increment_words_used()
                    else:
                        print("[WARNING] No account tab set - cannot update usage bar")
                    words_since_last_report = 0


        _update_status_and_overlay(status_callback, "✅ Complete!")

        # --- Compute duration, WPM, and log session ---
        end_time = time.time()
        duration = end_time - start_time

        # Count total words in session
        words_in_session = len(text.split())
        wpm = int(words_in_session / (duration / 60)) if duration > 0 else 0

        _log_session(text, duration=duration, profile=profile_name)

        # --- Notify stats tab of session for per-app-run tracking ---
        if _stats_tab and hasattr(_stats_tab, "receive_session"):
            try:
                _stats_tab.receive_session(words_in_session, wpm, profile_name)
            except Exception as e:
                print(f"Error updating per-session stats: {e}")

        # --- Track usage with backend API ---
        if _account_tab and hasattr(_account_tab, 'app'):
            try:
                import requests

                # Get user ID from logged-in user
                user_id = None
                if _account_tab.app.user:
                    user_id = _account_tab.app.user.get('id')

                if user_id and words_in_session > 0:
                    # Track usage with backend
                    response = requests.post(
                        "https://slywriterapp.onrender.com/api/usage/track",
                        params={"user_id": user_id, "words": words_in_session},
                        timeout=5
                    )

                    if response.status_code == 200:
                        data = response.json()
                        print(f"[BACKEND] Tracked {words_in_session} words. Total: {data['usage']}")

                        # Update UI with server's word count
                        if hasattr(_account_tab, 'refresh_usage'):
                            _account_tab.refresh_usage()
                    else:
                        print(f"[BACKEND] Tracking failed: {response.status_code}")
                else:
                    print("[INFO] No user logged in or no words typed - skipping backend tracking")

            except requests.exceptions.RequestException as e:
                print(f"[WARNING] Backend tracking failed: {e}")
                # Don't fail the session - just log the error
            except Exception as e:
                print(f"[ERROR] Unexpected error tracking usage: {e}")

    _typing_thread = threading.Thread(target=_worker, daemon=True)
    _typing_thread.start()

def _log_session(text: str, duration=None, profile=None):
    try:
        # Get user-specific log file
        log_file = _get_user_log_file()
        if log_file:
            with open(log_file, 'a', encoding='utf-8') as f:
                ts = datetime.now().isoformat()
                profile_str = f" (profile={profile}, duration={duration:.2f})" if duration and profile else ""
                f.write(f"[{ts}] {text}{profile_str}\n")
    except Exception:
        pass
    # Live update Diagnostics tab for all-time stats/log display
    if _stats_tab:
        try:
            _stats_tab.update_stats()
        except Exception as e:
            print(f"Error updating stats tab: {e}")
