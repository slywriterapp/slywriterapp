"""Configuration settings and defaults for SlyWriter."""

import os

# Base directory and config file path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up to project root
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# Default typing delays for ~80 WPM (slightly slower for realism)
MIN_DELAY_DEFAULT = 0.07   # 70 ms
MAX_DELAY_DEFAULT = 0.11   # 110 ms

# Typo probability default (currently unused)
TYPO_PROBABILITY_DEFAULT = 0.02

# Default pause logic
PUNCTUATION_PAUSE_CHARS = ".!?,;"
LONG_PAUSE_DEFAULT = 50

# Log file (absolute)
LOG_FILE = os.path.join(BASE_DIR, "typing_log.txt")

# Brand color
LIME_GREEN = "#32CD32"

# Custom typos map: common misspellings → corrections
custom_typos = {
    "teh":       "the",
    "adn":       "and",
    "becuase":   "because",
    "definately":"definitely",
    "recieve":   "receive",
    "seperate":  "separate",
    "occurence": "occurrence",
    "untill":    "until",
    "thier":     "their",
    "adress":    "address",
    "goverment": "government",
    "reccomend": "recommend",
    "wierd":     "weird",
    "alot":      "a lot",
    "accomodate":"accommodate",
    "embarass":  "embarrass",
}

# Built-in profile presets (always enforce typos_on=True)
PROFILE_PRESETS = {
    "Default": {
        "min_delay":    MIN_DELAY_DEFAULT,
        "max_delay":    MAX_DELAY_DEFAULT,
        "typos_on":     True,
        "pause_freq":   LONG_PAUSE_DEFAULT,
        "autocap":      False
    },
    "Speed-Type": {
        "min_delay":    0.01,
        "max_delay":    0.05,
        "typos_on":     True,
        "pause_freq":   1000,
        "autocap":      False
    },
    "Ultra-Slow": {
        "min_delay":    0.15,
        "max_delay":    0.30,
        "typos_on":     True,
        "pause_freq":   30,
        "autocap":      False
    },
}

# Default on-disk config structure
DEFAULT_CONFIG = {
    "settings": {
        "dark_mode": False,
        "min_delay": MIN_DELAY_DEFAULT,
        "max_delay": MAX_DELAY_DEFAULT,
        "typos_on": True,
        "pause_freq": LONG_PAUSE_DEFAULT,
        "bg_mode": False,
        "autocap": False,
        "hotkeys": {
            "start": "ctrl+alt+s",
            "stop":  "ctrl+alt+x"
        },
        "humanizer": {
            "grade_level":   3,
            "tone":          "Neutral",
            "depth":         3,
            "rewrite_style": "Clear",
            "use_of_evidence": "Optional"
        }
    },
    "profiles": ["Default", "Speed-Type", "Ultra-Slow"],
    "active_profile": "Default"
}

# Dark/light theme colors
DARK_BG       = "#1e1e1e"
DARK_FG       = "#f0f0f0"
DARK_ENTRY_BG = "#333333"
LIGHT_BG      = "#ffffff"
LIGHT_FG      = "#000000"