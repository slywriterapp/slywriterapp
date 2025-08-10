"""Hotkey management and registration."""

import keyboard
import ttkbootstrap as tb
from ..core.config import DEFAULT_CONFIG


def register_hotkeys(app):
    """Register all global hotkeys for the application."""
    for name in ['start', 'stop', 'pause']:
        try:
            keyboard.remove_hotkey(app.cfg['settings']['hotkeys'].get(name, ''))
        except Exception:
            pass
    
    keyboard.add_hotkey(
        app.cfg['settings']['hotkeys']['start'],
        lambda: None if getattr(app.hotkeys_tab.start_rec, 'recording', False) 
                else app.typing_tab.start_typing()
    )
    keyboard.add_hotkey(
        app.cfg['settings']['hotkeys']['stop'],
        lambda: None if getattr(app.hotkeys_tab.stop_rec, 'recording', False) 
                else app.typing_tab.stop_typing_hotkey()
    )
    keyboard.add_hotkey(
        app.cfg['settings']['hotkeys'].get('pause', 'ctrl+alt+p'),
        lambda: None if getattr(app.hotkeys_tab.start_rec, 'recording', False) 
                else app.typing_tab.toggle_pause()
    )


def set_start_hotkey(app, hk):
    """Set the start typing hotkey."""
    _validate_and_set_hotkey(app, hk, 'start')


def set_stop_hotkey(app, hk):
    """Set the stop typing hotkey."""
    _validate_and_set_hotkey(app, hk, 'stop')


def set_pause_hotkey(app, hk):
    """Set the pause typing hotkey."""
    _validate_and_set_hotkey(app, hk, 'pause')


def _validate_and_set_hotkey(app, hk, key_name):
    """Validate and set a hotkey."""
    try:
        keyboard.parse_hotkey(hk)
        app.cfg['settings']['hotkeys'][key_name] = hk
        register_hotkeys(app)
        from ..core.config import save_config  # Import here to avoid circular imports
        save_config(app.cfg)
    except ValueError:
        tb.messagebox.showwarning("Invalid Hotkey", f"The hotkey '{hk}' is not valid.")


def reset_hotkeys(app):
    """Reset all hotkeys to defaults."""
    app.cfg['settings']['hotkeys'] = DEFAULT_CONFIG['settings']['hotkeys'].copy()
    default = app.cfg['settings']['hotkeys']
    
    app.hotkeys_tab.start_rec.current = default['start']
    app.hotkeys_tab.start_rec.label.config(text=f"Current hotkey: {default['start']}")
    app.hotkeys_tab.stop_rec.current = default['stop']
    app.hotkeys_tab.stop_rec.label.config(text=f"Current hotkey: {default['stop']}")
    app.hotkeys_tab.pause_rec.current = default.get('pause', 'ctrl+alt+p')
    app.hotkeys_tab.pause_rec.label.config(text=f"Current hotkey: {default.get('pause', 'ctrl+alt+p')}")
    
    register_hotkeys(app)
    from ..core.config import save_config  # Import here to avoid circular imports
    save_config(app.cfg)


def validate_and_set_hotkey(app, hk, key_name):
    """Validate and set a hotkey (alias for backward compatibility)."""
    _validate_and_set_hotkey(app, hk, key_name)