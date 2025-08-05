import threading
import time
import random
import requests

# ------------------ Configurable Parameters -------------------
EDIT_POINT_CHARS = " .,!?;"      # "Edit-friendly" points (space, punct, etc)
BASE_FAKE_EDIT_CHANCE = 0.015    # 1.5% at every char
EDIT_POINT_BONUS_CHANCE = 0.18   # +18% at edit points (~20% total at those chars)
LONG_BREAK_CHANCE = 0.001        # 0.1% chance per char (avg 1 in 1000 chars)
LONG_BREAK_MIN = 20              # seconds (zoning out)
LONG_BREAK_MAX = 75
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
def generate_filler(goal_text, min_words=3, max_words=10, status_callback=None):
    """
    Returns a plausible, on-topic filler phrase using OpenAI via your Flask server,
    or falls back to local if server fails. Prints debug info.
    """
    prompt = (
        "Write a short, incomplete or re-thought-out phrase or clause a human might start typing, "
        f"while working on a paragraph like:\n\n\"{goal_text[:120]}...\"\n\n"
        "Make it sound natural and plausible, like a quick draft someone would delete. "
        "Return only the phrase."
    )
    try:
        if status_callback:
            status_callback("[AI Filler] Requesting from server…")
        print("[AI Filler] Sending prompt to server...")
        response = requests.post(
            FILLER_SERVER_URL,
            json={"prompt": prompt},
            timeout=8
        )
        if response.status_code == 200 and "filler" in response.json():
            filler = response.json()["filler"]
            if status_callback:
                status_callback(f"[AI Filler] Success: “{filler}”")
            print("[AI Filler] Server response:", filler)
            return ' '.join(filler.split()[:random.randint(min_words, max_words)])
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
        return fallback

# --------- Utility: Backspace up to nearest word boundary -----
def backspace_to_word_boundary(preview, current_idx, live_preview_callback):
    # Delete from current_idx backwards to last space or start
    while current_idx > 0 and preview[current_idx-1].isalpha():
        current_idx -= 1
        preview = preview[:current_idx]
        live_preview_callback(preview)
        time.sleep(random.uniform(BACKSPACE_DELAY_MIN, BACKSPACE_DELAY_MAX))
    return preview, current_idx

# ---------------- Utility: Micro-hesitation -------------------
def do_micro_hesitation(preview, live_preview_callback):
    hesitation = random.choice(MICRO_HESITATIONS)
    for ch in hesitation:
        preview += ch
        live_preview_callback(preview)
        time.sleep(random.uniform(0.04, 0.12))
    for _ in hesitation:
        preview = preview[:-1]
        live_preview_callback(preview)
        time.sleep(random.uniform(0.04, 0.09))
    return preview

# ------------- Main Typing Worker (threaded) ------------------
def premium_type_with_filler(
    goal_text,
    live_preview_callback,
    status_callback,
    min_delay,
    max_delay,
    typos_on,
    pause_freq,
    paste_and_go_url,
    autocap_enabled
):
    stop_flag = threading.Event()

    def humanized_type_char(preview, ch):
        # Random burst variability to simulate different speeds
        burst = random.uniform(-TYPING_BURST_VARIABILITY, TYPING_BURST_VARIABILITY)
        char_delay = max(0.015, random.uniform(min_delay, max_delay) * (1 + burst))
        preview += ch
        live_preview_callback(preview)
        time.sleep(char_delay)
        return preview

    def worker():
        preview = ""
        idx = 0
        length = len(goal_text)
        last_space = 0
        words_since_last_pause = 0

        while idx < length:
            ch = goal_text[idx]
            # ---- LONG ZONE-OUT BREAK ----
            if random.random() < LONG_BREAK_CHANCE:
                status_callback("Thinking… (zoned out)")
                t = random.uniform(LONG_BREAK_MIN, LONG_BREAK_MAX)
                for i in range(int(t)):
                    if i % 10 == 0:
                        status_callback(f"Thinking… ({t-i:.0f}s left)")
                    time.sleep(1)
                status_callback("Resuming…")

            # ---- MICRO-HESITATION (e.g. "um" + delete) ----
            if random.random() < MICRO_HESITATION_CHANCE:
                preview = do_micro_hesitation(preview, live_preview_callback)

            # ---- CHANCE FOR FAKE EDIT EVENT ----
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
                status_callback("Pausing to rethink…")
                time.sleep(random.uniform(THINKING_PAUSE_MIN, THINKING_PAUSE_MAX))

                # --- Generate & type a filler phrase ---
                filler = generate_filler(goal_text, FILLER_MIN_WORDS, FILLER_MAX_WORDS, status_callback=status_callback)
                for fch in filler:
                    preview = humanized_type_char(preview, fch)
                    # Mini-hesitation in the middle of a filler?
                    if random.random() < 0.06:
                        preview = do_micro_hesitation(preview, live_preview_callback)
                status_callback("Regretting…")
                time.sleep(random.uniform(REGRET_PAUSE_MIN, REGRET_PAUSE_MAX))

                # --- Backspace all of filler ---
                for _ in filler:
                    preview = preview[:-1]
                    live_preview_callback(preview)
                    time.sleep(random.uniform(BACKSPACE_DELAY_MIN, BACKSPACE_DELAY_MAX))

                # --- Optional "regret" pause ---
                time.sleep(random.uniform(THINKING_PAUSE_MIN, THINKING_PAUSE_MAX))
                status_callback("Resuming…")

            # ---- TYPE ACTUAL CHARACTER (user text) ----
            preview = humanized_type_char(preview, ch)

            # ---- Handle human-like long pauses and word tracking ----
            if ch.isspace():
                words_since_last_pause += 1
                if pause_freq and words_since_last_pause >= pause_freq:
                    status_callback("Thinking (pause)...")
                    time.sleep(max_delay)
                    words_since_last_pause = 0

            idx += 1

        # End: Handle "paste and go" URL if set
        import webbrowser
        if paste_and_go_url:
            webbrowser.open(paste_and_go_url)

        status_callback("Done")

    t = threading.Thread(target=worker, daemon=True)
    t.start()
