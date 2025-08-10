"""Core functionality for SlyWriter."""

from .config import *
from .engine import *
from .auth import *

__all__ = [
    # Config
    "CONFIG_FILE", "LOG_FILE", "DEFAULT_CONFIG", "PROFILE_PRESETS",
    "MIN_DELAY_DEFAULT", "MAX_DELAY_DEFAULT", "LONG_PAUSE_DEFAULT",
    "PUNCTUATION_PAUSE_CHARS", "custom_typos", "LIME_GREEN",
    "DARK_BG", "LIGHT_BG", "DARK_FG", "LIGHT_FG", "DARK_ENTRY_BG",
    
    # Engine
    "start_typing_from_input", "stop_typing_func", "pause_typing", "resume_typing",
    "stop_flag", "pause_flag", "set_account_tab_reference", "set_stats_tab_reference",
    "stop_typing_hotkey", "pause_typing_hotkey", "resume_typing_hotkey",
    
    # Auth
    "get_saved_user", "save_user", "logout_user", "sign_in_with_google", "sign_out"
]