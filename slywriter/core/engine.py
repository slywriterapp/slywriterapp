"""Core typing engine with threading and keystroke simulation."""

import threading
import time
import random
import sys
import os
from datetime import datetime
import keyboard  # for actual keystrokes

from .config import PUNCTUATION_PAUSE_CHARS, custom_typos, LOG_FILE, MIN_DELAY_DEFAULT, MAX_DELAY_DEFAULT, LONG_PAUSE_DEFAULT

_typing_thread = None

# Global event flags (singletons)
stop_flag = threading.Event()
pause_flag = threading.Event()

print("[engine] stop_flag id at module load:", id(stop_flag))
print("[engine] pause_flag id at module load:", id(pause_flag))

_punctuations = PUNCTUATION_PAUSE_CHARS
_custom_typos = custom_typos

_account_tab = None
_stats_tab = None


def make_ui_callback(widget, func):
    """Create a thread-safe UI callback."""
    def callback(*args, **kwargs):
        widget.after(0, lambda: func(*args, **kwargs))
    return callback


def set_account_tab_reference(tab):
    """Set reference to account tab for usage tracking."""
    global _account_tab
    _account_tab = tab
    print("Account tab reference set in typing_engine")


def set_stats_tab_reference(tab):
    """Set reference to stats tab for session tracking."""
    global _stats_tab
    _stats_tab = tab
    print("Stats tab reference set in typing_engine")


def _async_raise(tid, exctype):
    """Forcibly raise an exception in another thread."""
    import ctypes
    if not isinstance(exctype, type):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("Invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def kill_thread(thread):
    """Forcibly terminate a thread (emergency use only)."""
    if not thread or not thread.is_alive():
        return
    print(f"[engine][PANIC] Forcibly killing thread ident={thread.ident}")
    _async_raise(thread.ident, SystemExit)


def stop_typing_func():
    """Stop the current typing operation."""
    global _typing_thread
    print("[engine] stop_typing_func called. stop_flag id:", id(stop_flag), "pause_flag id:", id(pause_flag))
    stop_flag.set()
    pause_flag.clear()
    if _typing_thread and _typing_thread.is_alive():
        print("[engine] Waiting for _typing_thread to join... (ident:", _typing_thread.ident, ")")
        _typing_thread.join(timeout=1.0)
        if _typing_thread.is_alive():
            print("[engine][PANIC] Thread still alive after join! Forcibly killing.")
            kill_thread(_typing_thread)
        else:
            print("[engine] Thread joined (should be dead or dying).")
    stop_flag.clear()
    pause_flag.clear()
    print("[engine] Flags cleared after stop.")


def pause_typing():
    """Pause the current typing operation."""
    print("[engine] pause_typing called. pause_flag id:", id(pause_flag))
    pause_flag.set()


def resume_typing():
    """Resume the paused typing operation."""
    print("[engine] resume_typing called. pause_flag id:", id(pause_flag))
    pause_flag.clear()


def _debug_thread(tag=""):
    """Debug helper to print thread state."""
    print(f"[engine][{tag}] thread ident: {threading.current_thread().ident} stop_flag: {stop_flag.is_set()} pause_flag: {pause_flag.is_set()}")


def start_typing_worker(worker_func, *args, **kwargs):
    """Start a new typing worker thread."""
    global _typing_thread
    stop_typing_func()
    stop_flag.clear()
    pause_flag.clear()
    _typing_thread = threading.Thread(target=worker_func, args=args, kwargs=kwargs, daemon=True)
    print("[engine] Spawning typing thread for:", worker_func)
    _typing_thread.start()


def classic_typing_worker(
    text,
    live_preview_callback,
    status_callback,
    min_delay,
    max_delay,
    typos_on,
    pause_freq,
    autocap_enabled,
    preview_only=False,
):
    """Core typing worker that simulates human-like typing."""
    _debug_thread("CLASSIC_WORKER_START")
    
    # Always clear preview and set typing status at the start
    live_preview_callback("")
    status_callback("Starting...")

    if _account_tab and hasattr(_account_tab, "has_words_remaining") and not _account_tab.has_words_remaining():
        status_callback("Limit reached – upgrade plan to continue.")
        print("⛔ Typing blocked: word limit reached.")
        return

    # 5s cancelable countdown (pauseable and stoppable!)
    i = 5
    while i > 0:
        if stop_flag.is_set():
            status_callback("Stopped")
            live_preview_callback("")
            print("[engine] classic_worker: stop_flag was set during countdown.")
            return
            
        if pause_flag.is_set():
            status_callback("Paused…")
            print("[engine] classic_worker: paused during countdown.")
            while pause_flag.is_set() and not stop_flag.is_set():
                time.sleep(0.08)
            if stop_flag.is_set():
                status_callback("Stopped")
                live_preview_callback("")
                print("[engine] classic_worker: stop_flag set while paused in countdown.")
                return
            status_callback(f"Starting in {i}...")
            
        status_callback(f"Starting in {i}...")
        for _ in range(10):
            if stop_flag.is_set():
                status_callback("Stopped")
                live_preview_callback("")
                print("[engine] classic_worker: stop_flag set during 0.1s chunk in countdown.")
                return
            if pause_flag.is_set():
                status_callback("Paused…")
                print("[engine] classic_worker: paused inside 0.1s chunk in countdown.")
                while pause_flag.is_set() and not stop_flag.is_set():
                    time.sleep(0.08)
                if stop_flag.is_set():
                    status_callback("Stopped")
                    live_preview_callback("")
                    print("[engine] classic_worker: stop_flag set while paused inside 0.1s chunk in countdown.")
                    return
                status_callback(f"Starting in {i}...")
            time.sleep(0.1)
        i -= 1

    preview = ""
    word_count = 0
    words_since_last_report = 0
    preview_batch = []
    BATCH_SIZE = 5  # Increased batch size to reduce UI update frequency
    last_preview_update = 0
    MIN_UPDATE_INTERVAL = 0.05  # Minimum 50ms between preview updates

    # Only set status to typing if not stopped
    if not stop_flag.is_set():
        status_callback("Typing…")

    start_time = time.time()
    for idx, ch in enumerate(text):
        if stop_flag.is_set():
            status_callback("Stopped")
            live_preview_callback(preview)
            print("[engine] classic_worker: stop_flag set during main loop.")
            _debug_thread("CLASSIC_STOP_LOOP")
            return
            
        while pause_flag.is_set() and not stop_flag.is_set():
            status_callback("Paused…")
            print("[engine] classic_worker: paused during main loop.")
            _debug_thread("CLASSIC_PAUSED")
            time.sleep(0.08)

        if stop_flag.is_set():
            status_callback("Stopped")
            live_preview_callback(preview)
            print("[engine] classic_worker: stop_flag set after pause loop.")
            _debug_thread("CLASSIC_STOP_AFTER_PAUSE")
            return

        preview += ch
        preview_batch.append(ch)

        # Update preview with time-based throttling
        current_time = time.time()
        should_update = (len(preview_batch) >= BATCH_SIZE or 
                        idx == len(text) - 1 or 
                        current_time - last_preview_update > MIN_UPDATE_INTERVAL * 3)
        
        if should_update and current_time - last_preview_update >= MIN_UPDATE_INTERVAL:
            print(f"[engine] Preview update (batch): {''.join(preview_batch)!r} (idx={idx})")
            live_preview_callback(preview)
            preview_batch.clear()
            last_preview_update = current_time

        # Skip actual key press/release if preview_only
        if not preview_only:
            keyboard.press(ch)
            keyboard.release(ch)

        # Character delay
        char_delay = random.uniform(min_delay, max_delay)
        t_end = time.time() + char_delay
        while time.time() < t_end:
            if stop_flag.is_set():
                status_callback("Stopped")
                live_preview_callback(preview)
                print("[engine] classic_worker: stopped during char delay.")
                return
            while pause_flag.is_set() and not stop_flag.is_set():
                status_callback("Paused…")
                time.sleep(0.04)

        # Punctuation pause
        if ch in _punctuations:
            t_end = time.time() + (max_delay * 2)
            while time.time() < t_end:
                if stop_flag.is_set():
                    status_callback("Stopped")
                    live_preview_callback(preview)
                    print("[engine] classic_worker: stopped during punctuation pause.")
                    return
                while pause_flag.is_set() and not stop_flag.is_set():
                    status_callback("Paused…")
                    time.sleep(0.04)

        # Word counting
        if ch.isspace():
            word_count += 1
            words_since_last_report += 1
            if words_since_last_report >= 10:
                if _account_tab:
                    _account_tab.increment_words_used()
                words_since_last_report = 0

        # Periodic pause
        if pause_freq and idx and idx % pause_freq == 0:
            t_end = time.time() + max_delay
            while time.time() < t_end:
                if stop_flag.is_set():
                    status_callback("Stopped")
                    live_preview_callback(preview)
                    print("[engine] classic_worker: stopped during word pause.")
                    return
                while pause_flag.is_set() and not stop_flag.is_set():
                    status_callback("Paused…")
                    time.sleep(0.04)

    if stop_flag.is_set():
        status_callback("Stopped")
        live_preview_callback(preview)
    else:
        status_callback("Done")
        live_preview_callback(preview)

    end_time = time.time()
    duration = end_time - start_time
    wpm = int(word_count / (duration / 60)) if duration > 0 else 0
    _log_session(preview, duration=duration, profile="Classic")

    if _stats_tab and hasattr(_stats_tab, "receive_session"):
        try:
            _stats_tab.receive_session(word_count, wpm, "Classic")
        except Exception as e:
            print(f"Error updating per-session stats: {e}")

    _debug_thread("CLASSIC_WORKER_EXIT")


def start_typing_from_input(
    text: str,
    live_preview_callback,
    status_callback,
    *,
    min_delay: float = MIN_DELAY_DEFAULT,
    max_delay: float = MAX_DELAY_DEFAULT,
    typos_on: bool = True,
    pause_freq: int = LONG_PAUSE_DEFAULT,
    autocap_enabled: bool = False,
    parent_widget=None,
    preview_only=False
):
    """Start typing with the given parameters."""
    # Wrap all callbacks to ensure they're main-thread safe!
    if parent_widget is not None:
        safe_live_preview_callback = make_ui_callback(parent_widget, live_preview_callback)
        safe_status_callback = make_ui_callback(parent_widget, status_callback)
    else:
        safe_live_preview_callback = live_preview_callback
        safe_status_callback = status_callback

    start_typing_worker(
        classic_typing_worker,
        text,
        safe_live_preview_callback,
        safe_status_callback,
        min_delay,
        max_delay,
        typos_on,
        pause_freq,
        autocap_enabled,
        preview_only=preview_only
    )


def _log_session(text: str, duration=None, profile=None):
    """Log a typing session to file."""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            ts = datetime.now().isoformat()
            profile_str = f" (profile={profile}, duration={duration:.2f})" if duration and profile else ""
            f.write(f"[{ts}] {text}{profile_str}\n")
    except Exception:
        pass
    if _stats_tab:
        try:
            _stats_tab.update_stats()
        except Exception as e:
            print(f"Error updating stats tab: {e}")


# Hotkey handlers
def stop_typing_hotkey(self=None):
    """Hotkey handler for stopping typing."""
    print("[engine] stop_typing_hotkey called. stop_flag id:", id(stop_flag))
    stop_typing_func()


def pause_typing_hotkey(self=None):
    """Hotkey handler for pausing typing."""
    print("[engine] pause_typing_hotkey called. pause_flag id:", id(pause_flag))
    pause_typing()


def resume_typing_hotkey(self=None):
    """Hotkey handler for resuming typing."""
    print("[engine] resume_typing_hotkey called. pause_flag id:", id(pause_flag))
    resume_typing()


# Legacy compatibility
STOP_FLAG = stop_flag
PAUSE_FLAG = pause_flag

print("[engine] Module fully loaded. stop_flag id:", id(stop_flag), "pause_flag id:", id(pause_flag))