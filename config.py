import os

# Base directory and config file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# Default delays for ~80 WPM (slightly slower for realism)
MIN_DELAY_DEFAULT = 0.07   # 70ms
MAX_DELAY_DEFAULT = 0.11   # 110ms

# Typo probability default
TYPO_PROBABILITY_DEFAULT = 0.02

# Default pause characters
PUNCTUATION_PAUSE_CHARS = ".!?,;"

# Long pause every X characters
LONG_PAUSE_DEFAULT = 50

# Log file (absolute path)
LOG_FILE = os.path.join(BASE_DIR, "typing_log.txt")

# Custom typos (if needed)
custom_typos = {
    "teh": "the",
    "adn": "and"
}

# Profile presets
PROFILE_PRESETS = {
    "Default":    {"min_delay": MIN_DELAY_DEFAULT, "max_delay": MAX_DELAY_DEFAULT, "typos_on": True, "pause_freq": LONG_PAUSE_DEFAULT},
    "Ultra‑Slow": {"min_delay": 0.15, "max_delay": 0.3,  "typos_on": True,  "pause_freq": 30},
    "Speed Type": {"min_delay": 0.01, "max_delay": 0.04, "typos_on": False, "pause_freq": 1000}
}

# Default config
DEFAULT_CONFIG = {
    "settings": {
        "dark_mode": False,
        "min_delay": MIN_DELAY_DEFAULT,
        "max_delay": MAX_DELAY_DEFAULT,
        "typos_on": True,
        "pause_freq": LONG_PAUSE_DEFAULT,
        "paste_go_url": "",
        "bg_mode": False,
        "autocap": False,
        "hotkeys": {"start": "ctrl+alt+s", "stop": "ctrl+alt+x"}
    },
    "profiles": ["Default", "Ultra‑Slow", "Speed Type"],
    "active_profile": "Default"
}

# Dark mode colors
DARK_BG = "#1e1e1e"
DARK_FG = "#f0f0f0"
DARK_ENTRY_BG = "#333333"
LIGHT_BG = "#ffffff"
LIGHT_FG = "#000000"
