# config.py

import os

# Base directory and config file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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

# Brand color - Changed to purple
LIME_GREEN = "#8B5CF6"  # Purple - renamed for compatibility but now purple

# ——————————————
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

# ——————————————
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
            "stop":  "ctrl+alt+x",
            "ai_generation": "ctrl+alt+g"
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

# Dark/light theme colors (2025 modern palette)
DARK_BG       = "#0F0F23"  # Very dark blue to match new premium theme
DARK_FG       = "#E8E8E8"  # Softer white
DARK_ENTRY_BG = "#1A1B3E"  # Slightly lighter dark blue for better contrast
DARK_CARD_BG  = "#2D2F5A"  # Lighter blue for card backgrounds
LIGHT_BG      = "#FAFAFA"  # Off-white instead of pure white  
LIGHT_FG      = "#2D2D30"  # Dark gray instead of pure black
LIGHT_ENTRY_BG = "#FFFFFF"
LIGHT_CARD_BG = "#F5F5F7"  # Light card backgrounds

# Modern color palette (2025 AI/Tech vibe)
PRIMARY_BLUE = "#003366"     # Much darker navy blue
PRIMARY_BLUE_HOVER = "#001a33"  # Even darker hover
PRIMARY_BLUE_LIGHT = "#003366"  # Same consistent dark navy for light mode
PRIMARY_BLUE_LIGHT_HOVER = "#001a33"

# Accent colors
SUCCESS_GREEN = "#8B5CF6"    # Modern purple - changed from green to match theme
WARNING_ORANGE = "#F59E0B"   # Modern orange  
DANGER_RED = "#EF4444"       # Modern red
ACCENT_PURPLE = "#8B5CF6"    # Modern purple

# Neutral grays
GRAY_100 = "#F3F4F6"
GRAY_200 = "#E5E7EB" 
GRAY_300 = "#D1D5DB"
GRAY_400 = "#9CA3AF"
GRAY_500 = "#6B7280"
GRAY_600 = "#4B5563"
GRAY_700 = "#374151"
GRAY_800 = "#1F2937"
GRAY_900 = "#111827"

# Typography (2025 modern fonts with fallbacks)
FONT_PRIMARY = "Segoe UI"        # Primary font - native Windows modern font
FONT_SECONDARY = "Inter"         # Fallback 1
FONT_TERTIARY = "Roboto"         # Fallback 2  
FONT_MONO = "Consolas"           # Code font - native Windows monospace

# Typography scale for consistent sizing
FONT_SIZE_XS = 8
FONT_SIZE_SM = 9
FONT_SIZE_BASE = 10
FONT_SIZE_LG = 11
FONT_SIZE_XL = 12
FONT_SIZE_2XL = 14
FONT_SIZE_3XL = 16
FONT_SIZE_4XL = 18

# Consistent spacing system (8px base)
SPACING_XS = 4
SPACING_SM = 8
SPACING_BASE = 12
SPACING_LG = 16
SPACING_XL = 20
SPACING_2XL = 24
SPACING_3XL = 32

# Modern shadows
SHADOW_SM = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
SHADOW_MD = "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
SHADOW_LG = "0 10px 15px -3px rgba(0, 0, 0, 0.1)"

# Border radius for modern rounded corners
BORDER_RADIUS_SM = 6
BORDER_RADIUS_MD = 8
BORDER_RADIUS_LG = 12
