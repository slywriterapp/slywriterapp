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

def set_account_tab_reference(tab):
    global _account_tab
    _account_tab = tab
    print("✅ Account tab reference set in typing_engine")

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
    paste_and_go_url: str = "",
    autocap_enabled: bool = False
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
                status_callback("Cancelled")
                return
            status_callback(f"Starting in {i}...")
            for _ in range(10):
                if _stop_flag.is_set():
                    status_callback("Cancelled")
                    return
                time.sleep(0.1)

        preview = ""
        last_pause = 0
        status_callback("Typing…")
        word_count = 0
        words_since_last_report = 0

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

            if autocap_enabled and ch.isalpha():
                if idx == 0 or text[idx - 1] in ".!?":
                    ch = ch.upper()

            if typos_on and random.random() < config.TYPO_PROBABILITY_DEFAULT:
                wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
                keyboard.write(wrong_char)
                time.sleep(0.05)
                keyboard.send("backspace")
                live_preview_callback(preview)

            keyboard.write(ch)
            preview += ch
            live_preview_callback(preview)

            if ch in _punctuations:
                time.sleep(max_delay * 2)

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

        if paste_and_go_url:
            webbrowser.open(paste_and_go_url)

        status_callback("Done")
        _log_session(text)

    _typing_thread = threading.Thread(target=_worker, daemon=True)
    _typing_thread.start()

def _log_session(text: str):
    try:
        with open(config.LOG_FILE, 'a', encoding='utf-8') as f:
            ts = datetime.now().isoformat()
            f.write(f"[{ts}] {text}\n")
    except Exception:
        pass
