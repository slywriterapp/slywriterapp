import threading
import time
import random
import requests
import keyboard

# ------------------ Configurable Parameters -------------------
EDIT_POINT_CHARS = " .,!?;"      # "Edit-friendly" points (space, punct, etc)
BASE_FAKE_EDIT_CHANCE = 0.002    # 0.2% at every char (4x lower than before)
EDIT_POINT_BONUS_CHANCE = 0.10   # +10% at edit points (reduced from 18%)
LONG_BREAK_CHANCE = 0.0005       # 0.05% chance per char (reduced from 0.1%)
LONG_BREAK_MIN = 15              # seconds (reduced from 20)
LONG_BREAK_MAX = 45              # seconds (reduced from 75)
FILLER_MIN_WORDS = 3
FILLER_MAX_WORDS = 10
THINKING_PAUSE_MIN = 0.2         # seconds before/after fake edit
THINKING_PAUSE_MAX = 1.4
REGRET_PAUSE_MIN = 0.1           # seconds before delete
REGRET_PAUSE_MAX = 1.2
BACKSPACE_DELAY_MIN = 0.04
BACKSPACE_DELAY_MAX = 0.14
MICRO_HESITATION_CHANCE = 0.03   # 3% chance per char to "um" and backspace
MICRO_HESITATIONS = ["um", "ah", "er", "uh"]
TYPING_BURST_VARIABILITY = 0.08  # up to ±8% speed variation stretch

FILLER_SERVER_URL = "https://slywriterapp.onrender.com/generate_filler"

# ------------- Utility: AI Filler generator with debug ---------------
def generate_filler(goal_text, min_words=3, max_words=10, status_callback=None, preceding_context="", stop_flag=None):
    """
    Returns a plausible, on-topic filler phrase using OpenAI via your Flask server,
    or falls back to local if server fails. Uses preceding context for smarter filler.
    """
    # Check for stop before starting
    if stop_flag and stop_flag.is_set():
        return ""
    
    # Create smarter prompt with preceding context
    context_part = f"Given what was just typed: \"{preceding_context[-100:]}\"" if preceding_context else "While working on"
    prompt = (
        f"Write a short, incomplete or re-thought-out phrase or clause a human might start typing, "
        f"{context_part} a paragraph like:\n\n\"{goal_text[:120]}...\"\n\n"
        f"Make it contextually relevant to what came before, sound natural and plausible, "
        f"like a quick draft someone would delete and rethink. Return only the phrase."
    )
    try:
        if status_callback:
            status_callback("[AI Filler] Requesting from server…")
        print("[AI Filler] Sending prompt to server...")
        
        # Check for stop during server request
        if stop_flag and stop_flag.is_set():
            return ""
            
        response = requests.post(
            FILLER_SERVER_URL,
            json={"prompt": prompt},
            timeout=8
        )
        
        # Check for stop after server response
        if stop_flag and stop_flag.is_set():
            return ""
        if response.status_code == 200:
            result = response.json()
            print(f"[AI Filler] Full server response: {result}")
            if "filler" in result and result["filler"]:
                filler = result["filler"]
                if status_callback:
                    status_callback(f"[AI Filler] Success: \"{filler}\"")
                print("[AI Filler] Server response:", filler)
            else:
                print(f"[AI Filler] No filler in response or filler is empty: {result}")
                raise Exception("Empty filler response")
            
            # Process the filler text
            processed_filler = ' '.join(filler.split()[:random.randint(min_words, max_words)])
            
            # Fix capitalization - only capitalize if it's a new sentence
            if processed_filler and preceding_context:
                # Check if we're at the start of a new sentence (after . ! ?)
                stripped_context = preceding_context.rstrip()
                is_new_sentence = stripped_context.endswith('.') or stripped_context.endswith('!') or stripped_context.endswith('?')
                
                if not is_new_sentence and processed_filler[0].isupper():
                    # Not a new sentence, so don't capitalize
                    processed_filler = processed_filler[0].lower() + processed_filler[1:]
            
            # Fix spacing logic based on context
            if preceding_context and not preceding_context.endswith(' '):
                # No space at end of context, add one before filler
                processed_filler = ' ' + processed_filler
            # If context ends with space, don't add another space (current behavior)
            
            return processed_filler
        else:
            raise Exception(response.text)
    except Exception as e:
        msg = f"[AI Filler] Server error: {e}"
        print(msg)
        if status_callback:
            status_callback(msg)
        fallback = random.choice([
            "But actually, what if", "Wait, maybe I should", "No, that's not it", "Let me rethink this",
            "Actually, perhaps", "On second thought,", "Hmm, maybe I should"
        ])
        
        # Apply same capitalization logic to fallback
        if fallback and preceding_context:
            # Check if we're at the start of a new sentence (after . ! ?)
            stripped_context = preceding_context.rstrip()
            is_new_sentence = stripped_context.endswith('.') or stripped_context.endswith('!') or stripped_context.endswith('?')
            
            if not is_new_sentence and fallback[0].isupper():
                # Not a new sentence, so don't capitalize
                fallback = fallback[0].lower() + fallback[1:]
        
        # Apply same spacing logic to fallback
        if preceding_context and not preceding_context.endswith(' '):
            fallback = ' ' + fallback
            
        return fallback

# --------- Utility: Backspace up to nearest word boundary -----

# ------------- Main Typing Worker (threaded) ------------------
def premium_type_with_filler(
    goal_text,
    live_preview_callback,
    status_callback,
    min_delay,
    max_delay,
    typos_on,
    pause_freq,
    preview_only=False,
    stop_flag=None,
    pause_flag=None
):
    if stop_flag is None:
        stop_flag = threading.Event()
    if pause_flag is None:
        pause_flag = threading.Event()

    def backspace_to_word_boundary(preview, current_idx, live_preview_callback):
        # Delete from current_idx backwards to last space or start
        while current_idx > 0 and preview[current_idx-1].isalpha():
            if stop_flag.is_set():
                return preview, current_idx
            if not preview_only:
                keyboard.send("backspace")
            current_idx -= 1
            preview = preview[:current_idx]
            live_preview_callback(preview)
            time.sleep(random.uniform(BACKSPACE_DELAY_MIN, BACKSPACE_DELAY_MAX))
        return preview, current_idx

    def do_micro_hesitation(preview, live_preview_callback):
        hesitation = random.choice(MICRO_HESITATIONS)
        for ch in hesitation:
            if stop_flag.is_set():
                return preview
            if not preview_only:
                keyboard.write(ch)
            preview += ch
            live_preview_callback(preview)
            time.sleep(random.uniform(0.04, 0.12))
        for _ in hesitation:
            if stop_flag.is_set():
                return preview
            if not preview_only:
                keyboard.send("backspace")
            preview = preview[:-1]
            live_preview_callback(preview)
            time.sleep(random.uniform(0.04, 0.09))
        return preview

    def humanized_type_char(preview, ch):
        if stop_flag.is_set():
            return preview
            
        # Random burst variability to simulate different speeds
        burst = random.uniform(-TYPING_BURST_VARIABILITY, TYPING_BURST_VARIABILITY)
        char_delay = max(0.015, random.uniform(min_delay, max_delay) * (1 + burst))
        
        # Actually type the character if not in preview_only mode
        if not preview_only:
            keyboard.write(ch)
        
        preview += ch
        live_preview_callback(preview)
        time.sleep(char_delay)
        return preview

    def worker():
        # Track session stats like regular engine
        start_time = time.time()
        words_in_session = 0
        
        # Add 5-second countdown like regular engine
        for i in range(5, 0, -1):
            if stop_flag.is_set():
                status_callback("Cancelled")
                _update_overlay("Cancelled")
                return
            status_text = f"Starting in {i}..."
            status_callback(status_text)
            _update_overlay(status_text)
            for _ in range(10):
                if stop_flag.is_set():
                    status_callback("Cancelled")
                    _update_overlay("Cancelled")
                    return
                time.sleep(0.1)

        preview = ""
        idx = 0
        length = len(goal_text)
        last_space = 0
        words_since_last_pause = 0
        typing_start_time = time.time()  # Track when actual typing starts
        status_text = "🤖 AI Typing…"
        status_callback(status_text)
        _update_overlay(status_text)

        while idx < length:
            # Check for stop flag
            if stop_flag.is_set():
                status_callback("Stopped")
                return
                
            # Check for pause flag
            while pause_flag.is_set():
                if stop_flag.is_set():
                    status_callback("Stopped")
                    return
                time.sleep(0.1)  # Wait while paused
                
            ch = goal_text[idx]
            # ---- LONG ZONE-OUT BREAK ----
            if random.random() < LONG_BREAK_CHANCE:
                status_text = "😴 Break…"
                status_callback(status_text)
                _update_overlay(status_text)
                t = random.uniform(LONG_BREAK_MIN, LONG_BREAK_MAX)
                for i in range(int(t)):
                    if stop_flag.is_set():
                        status_callback("Stopped")
                        _update_overlay("Stopped")
                        return
                    if i % 10 == 0:
                        status_text = f"😴 Break ({t-i:.0f}s)"
                        status_callback(status_text)
                        _update_overlay(status_text)
                    time.sleep(1)
                status_text = "✍️ Typing…"
                status_callback(status_text)
                _update_overlay(status_text)

            # ---- MICRO-HESITATION (e.g. "um" + delete) ----
            if random.random() < MICRO_HESITATION_CHANCE:
                preview = do_micro_hesitation(preview, live_preview_callback)

            # ---- CHANCE FOR FAKE EDIT EVENT ----
            # Don't allow filler in first 15 seconds (insufficient context)
            elapsed_typing_time = time.time() - typing_start_time
            if elapsed_typing_time >= 15:
                edit_chance = BASE_FAKE_EDIT_CHANCE
                if ch in EDIT_POINT_CHARS:
                    edit_chance += EDIT_POINT_BONUS_CHANCE
                if random.random() < edit_chance:
                    # --- If mid-word, backspace to word boundary first ---
                    if idx > 0 and goal_text[idx-1].isalpha() and not ch.isspace():
                        preview, _ = backspace_to_word_boundary(preview, len(preview), live_preview_callback)
                        # Move idx forward to next space (skip rest of word)
                        while idx < length and goal_text[idx].isalpha():
                            idx += 1
                        if idx >= length:
                            break
                        ch = goal_text[idx]

                    # --- Pause for "thinking" ---
                    status_text = "💭 Thinking…"
                    status_callback(status_text)
                    _update_overlay(status_text)
                    if stop_flag.is_set():
                        status_callback("Stopped")
                        _update_overlay("Stopped")
                        return
                    time.sleep(random.uniform(THINKING_PAUSE_MIN, THINKING_PAUSE_MAX))

                    # --- Generate & type a filler phrase ---
                    status_text = "🤖 AI Filler…"
                    status_callback(status_text)
                    _update_overlay(status_text)
                    filler = generate_filler(goal_text, FILLER_MIN_WORDS, FILLER_MAX_WORDS, status_callback=status_callback, preceding_context=preview, stop_flag=stop_flag)
                    for fch in filler:
                        if stop_flag.is_set():
                            status_callback("Stopped")
                            return
                        preview = humanized_type_char(preview, fch)
                        # Mini-hesitation in the middle of a filler?
                        if random.random() < 0.06:
                            preview = do_micro_hesitation(preview, live_preview_callback)
                            if stop_flag.is_set():
                                status_callback("Stopped")
                                return
                                
                    status_text = "❌ Deleting…"
                    status_callback(status_text)
                    _update_overlay(status_text)
                    if stop_flag.is_set():
                        status_callback("Stopped")
                        _update_overlay("Stopped")
                        return
                    time.sleep(random.uniform(REGRET_PAUSE_MIN, REGRET_PAUSE_MAX))

                    # --- Backspace all of filler ---
                    for _ in filler:
                        if stop_flag.is_set():
                            status_callback("Stopped")
                            return
                        if not preview_only:
                            keyboard.send("backspace")
                        preview = preview[:-1]
                        live_preview_callback(preview)
                        time.sleep(random.uniform(BACKSPACE_DELAY_MIN, BACKSPACE_DELAY_MAX))

                    # --- Optional "regret" pause ---
                    if stop_flag.is_set():
                        status_callback("Stopped")
                        return
                    time.sleep(random.uniform(THINKING_PAUSE_MIN, THINKING_PAUSE_MAX))
                    status_callback("✍️ Resuming…")

            # ---- TYPE ACTUAL CHARACTER (user text) ----
            preview = humanized_type_char(preview, ch)
            
            # ---- PREMIUM SENTENCE BREAKS (longer and more frequent than normal) ----
            if ch in ".!?":
                # Premium users get longer, more frequent sentence breaks
                premium_sentence_break_chance = 0.5  # 50% chance (vs 30% in normal)
                if random.random() < premium_sentence_break_chance:
                    premium_break_duration = random.uniform(3.0, 8.0)  # 3-8 seconds (vs 2-5 in normal)
                    status_text = f"📱 Break ({premium_break_duration:.0f}s)"
                    status_callback(status_text)
                    _update_overlay(status_text)
                    
                    # Check for stop/pause during the premium break
                    for i in range(int(premium_break_duration * 10)):
                        if stop_flag.is_set():
                            status_callback("Stopped")
                            _update_overlay("Stopped")
                            return
                        while pause_flag.is_set():
                            if stop_flag.is_set():
                                status_callback("Stopped")
                                _update_overlay("Stopped")
                                return
                            time.sleep(0.1)
                        time.sleep(0.1)
                    
                    status_callback("✍️ Typing…")
                    _update_overlay("✍️ Typing…")

            # ---- Handle human-like long pauses and word tracking ----
            if ch.isspace():
                words_since_last_pause += 1
                words_in_session += 1  # Track for stats
                if pause_freq and words_since_last_pause >= pause_freq:
                    status_callback("⏸️ Pause…")
                    time.sleep(max_delay)
                    words_since_last_pause = 0

            idx += 1


        status_callback("Done")
        _update_overlay("Done")
        
        # Report session stats like regular engine
        end_time = time.time()
        duration = end_time - start_time
        wpm = int(words_in_session / (duration / 60)) if duration > 0 else 0
        
        # Get profile name (try to match regular engine approach)
        profile_name = "Premium"
        try:
            if hasattr(typing_engine, '_account_tab') and typing_engine._account_tab:
                if hasattr(typing_engine._account_tab, 'get_active_profile_name'):
                    profile_name = typing_engine._account_tab.get_active_profile_name()
        except:
            pass
        
        # Notify stats tab
        if hasattr(typing_engine, '_stats_tab') and typing_engine._stats_tab:
            if hasattr(typing_engine._stats_tab, "receive_session"):
                try:
                    typing_engine._stats_tab.receive_session(words_in_session, wpm, f"{profile_name} (Premium)")
                except Exception as e:
                    print(f"Error updating premium stats: {e}")

    # CRITICAL: Stop any existing typing before starting (like regular engine does)
    import typing_engine
    typing_engine.stop_typing_func()  # Stop any existing typing first
    
    def _update_overlay(text):
        """Helper to update overlay if available"""
        if hasattr(typing_engine, '_overlay_tab') and typing_engine._overlay_tab:
            try:
                typing_engine._overlay_tab.update_overlay_text(text)
            except Exception as e:
                print(f"Error updating overlay: {e}")
    
    # Register with global typing engine thread system for stop button to work
    t = threading.Thread(target=worker, daemon=True)
    typing_engine._typing_thread = t  # This allows stop_typing_func() to join() our thread
    t.start()
