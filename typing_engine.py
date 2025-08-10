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
import keyboard  # for actual keystrokes

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
    """Update both status callback and overlay"""
    status_callback(text)
    if _overlay_tab:
        try:
            _overlay_tab.update_overlay_text(text)
        except Exception as e:
            print(f"Error updating overlay: {e}")

def stop_typing_func():
    _stop_flag.set()
    _pause_flag.clear()
    if _typing_thread and _typing_thread.is_alive():
        _typing_thread.join(timeout=0.1)
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
    preview_only: bool = False
):
    global _typing_thread
    stop_typing_func()

    def _worker():
        if _account_tab and not _account_tab.has_words_remaining():
            status_callback("Limit reached – upgrade plan to continue.")
            print("⛔ Typing blocked: word limit reached.")
            return

        for i in range(5, 0, -1):
            if _stop_flag.is_set():
                _update_status_and_overlay(status_callback, "Cancelled")
                return
            _update_status_and_overlay(status_callback, f"Starting in {i}...")
            for _ in range(10):
                if _stop_flag.is_set():
                    _update_status_and_overlay(status_callback, "Cancelled")
                    return
                time.sleep(0.1)

        preview = ""
        last_pause = 0
        _update_status_and_overlay(status_callback, "Typing…")
        word_count = 0
        words_since_last_report = 0

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

        for idx, ch in enumerate(text):
            if _stop_flag.is_set():
                status_callback("Stopped")
                return

            while _pause_flag.is_set() and not _stop_flag.is_set():
                status_callback("Paused…")
                time.sleep(0.1)

            if _stop_flag.is_set():
                status_callback("Stopped")
                return

            if _account_tab and not _account_tab.has_words_remaining():
                status_callback("Limit reached – upgrade plan to continue.")
                print("⛔ Typing interrupted: limit reached mid-session.")
                return


            if typos_on and random.random() < config.TYPO_PROBABILITY_DEFAULT:
                wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
                if not preview_only:
                    keyboard.write(wrong_char)
                    time.sleep(0.05)
                    keyboard.send("backspace")
                live_preview_callback(preview)

            if not preview_only:
                keyboard.write(ch)
            preview += ch
            live_preview_callback(preview)

            if ch in _punctuations:
                # Regular punctuation pause
                time.sleep(max_delay * 2)
                
                # Longer sentence breaks for period, exclamation, question mark
                if ch in ".!?":
                    # Simulate user looking elsewhere, checking other tabs, etc.
                    sentence_break_chance = 0.3  # 30% chance
                    if random.random() < sentence_break_chance:
                        sentence_break_duration = random.uniform(2.0, 5.0)  # 2-5 second break
                        _update_status_and_overlay(status_callback, f"Taking a break ({sentence_break_duration:.1f}s)...")
                        
                        # Check for stop/pause during the break
                        for i in range(int(sentence_break_duration * 10)):
                            if _stop_flag.is_set():
                                status_callback("Stopped")
                                return
                            while _pause_flag.is_set() and not _stop_flag.is_set():
                                status_callback("Paused…")
                                time.sleep(0.1)
                            time.sleep(0.1)
                        
                        _update_status_and_overlay(status_callback, "Resuming typing...")

            if pause_freq and (idx - last_pause) >= pause_freq:
                time.sleep(max_delay)
                last_pause = idx

            time.sleep(random.uniform(min_delay, max_delay))

            if ch.isspace():
                word_count += 1
                words_since_last_report += 1
                print(f"📝 Word typed. Total so far: {word_count}")
                if words_since_last_report >= 10:
                    if _account_tab:
                        print("🔁 10 words typed — incrementing usage bar")
                        _account_tab.increment_words_used()
                    else:
                        print("⚠️ No account tab set — cannot update usage bar")
                    words_since_last_report = 0


        _update_status_and_overlay(status_callback, "Done")

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
