# sly_hotkeys.py

import keyboard
import ttkbootstrap as tb
import config

def register_hotkeys(app):
    # Clear ALL existing hotkeys first to prevent conflicts
    try:
        keyboard.unhook_all_hotkeys()
        print("[HOTKEYS] Cleared all existing hotkeys")
    except Exception as e:
        print(f"[HOTKEYS] Warning: Could not clear all hotkeys: {e}")
    
    # Also try to remove specific hotkeys as backup
    for name in ['start', 'stop', 'pause', 'overlay', 'ai_generation']:
        try:
            hotkey = app.cfg['settings']['hotkeys'].get(name, '')
            if hotkey:
                keyboard.remove_hotkey(hotkey)
                print(f"[HOTKEYS] Removed old {name} hotkey: {hotkey}")
        except Exception as e:
            print(f"[HOTKEYS] Could not remove {name} hotkey: {e}")
            pass
    keyboard.add_hotkey(app.cfg['settings']['hotkeys']['start'],
                        lambda: None if getattr(app.hotkeys_tab.start_rec, 'recording', False) else _start_typing_hotkey(app))
    keyboard.add_hotkey(app.cfg['settings']['hotkeys']['stop'],
                        lambda: None if getattr(app.hotkeys_tab.stop_rec, 'recording', False) else _stop_typing_hotkey(app))
    keyboard.add_hotkey(app.cfg['settings']['hotkeys'].get('pause','ctrl+alt+p'),
                        lambda: None if getattr(app.hotkeys_tab.start_rec, 'recording', False) else _pause_typing_hotkey(app))
    keyboard.add_hotkey(app.cfg['settings']['hotkeys'].get('overlay','ctrl+alt+o'),
                        lambda: None if getattr(app.hotkeys_tab, 'overlay_rec', None) and getattr(app.hotkeys_tab.overlay_rec, 'recording', False) else _toggle_overlay_hotkey(app))
    keyboard.add_hotkey(app.cfg['settings']['hotkeys'].get('ai_generation','ctrl+alt+g'),
                        lambda: None if getattr(app.hotkeys_tab, 'ai_gen_rec', None) and getattr(app.hotkeys_tab.ai_gen_rec, 'recording', False) else _ai_generation_hotkey(app))

def set_start_hotkey(app, hk):
    _validate_and_set_hotkey(app, hk, 'start')

def set_stop_hotkey(app, hk):
    _validate_and_set_hotkey(app, hk, 'stop')

def set_pause_hotkey(app, hk):
    _validate_and_set_hotkey(app, hk, 'pause')

def set_overlay_hotkey(app, hk):
    _validate_and_set_hotkey(app, hk, 'overlay')

def set_ai_generation_hotkey(app, hk):
    _validate_and_set_hotkey(app, hk, 'ai_generation')

def _validate_and_set_hotkey(app, hk, key_name):
    print(f"[HOTKEYS] _validate_and_set_hotkey called: {key_name} = {hk}")
    try:
        keyboard.parse_hotkey(hk)
        print(f"[HOTKEYS] Hotkey validated successfully: {hk}")
        app.cfg['settings']['hotkeys'][key_name] = hk
        print(f"[HOTKEYS] Saved to config: {key_name} = {hk}")
        register_hotkeys(app)
        print(f"[HOTKEYS] Re-registered all hotkeys")
        from sly_config import save_config
        save_config(app.cfg)
        print(f"[HOTKEYS] Config saved to disk")
    except ValueError as e:
        print(f"[HOTKEYS] Invalid hotkey error: {e}")
        tb.messagebox.showwarning("Invalid Hotkey", f"The hotkey '{hk}' is not valid.")
    except Exception as e:
        print(f"[HOTKEYS] Unexpected error in _validate_and_set_hotkey: {e}")

def reset_hotkeys(app):
    app.cfg['settings']['hotkeys'] = config.DEFAULT_CONFIG['settings']['hotkeys'].copy()
    default = app.cfg['settings']['hotkeys']
    app.hotkeys_tab.start_rec.current = default['start']
    app.hotkeys_tab.start_rec.label.config(text=f"Current hotkey: {default['start']}")
    app.hotkeys_tab.stop_rec.current  = default['stop']
    app.hotkeys_tab.stop_rec.label.config(text=f"Current hotkey: {default['stop']}")
    app.hotkeys_tab.pause_rec.current = default.get('pause','ctrl+alt+p')
    app.hotkeys_tab.pause_rec.label.config(text=f"Current hotkey: {default.get('pause','ctrl+alt+p')}")
    app.hotkeys_tab.overlay_rec.current = default.get('overlay','ctrl+alt+o')
    app.hotkeys_tab.overlay_rec.label.config(text=f"Current hotkey: {default.get('overlay','ctrl+alt+o')}")
    app.hotkeys_tab.ai_gen_rec.current = default.get('ai_generation','ctrl+alt+g')
    app.hotkeys_tab.ai_gen_rec.label.config(text=f"Current hotkey: {default.get('ai_generation','ctrl+alt+g')}")
    register_hotkeys(app)
    from sly_config import save_config
    save_config(app.cfg)

def _toggle_overlay_hotkey(app):
    # Check if user is logged in
    if not hasattr(app, 'user') or not app.user:
        print("[HOTKEY] Overlay toggle blocked - user not logged in")
        return

    # Check for overlay tab in different locations
    overlay_tab = None
    if hasattr(app, 'overlay_tab'):
        overlay_tab = app.overlay_tab
    elif hasattr(app, 'tabs') and 'Overlay' in app.tabs:
        overlay_tab = app.tabs['Overlay']

    if overlay_tab:
        current = overlay_tab.overlay_enabled.get()
        overlay_tab.overlay_enabled.set(not current)
        print(f"[HOTKEY] Toggled overlay: {not current}")

def _ai_generation_hotkey(app):
    """Handle AI text generation hotkey press"""
    try:
        # Check if user is logged in
        if not hasattr(app, 'user') or not app.user:
            print("[HOTKEY] AI generation blocked - user not logged in")
            return

        # Import here to avoid circular imports
        from ai_text_generator import trigger_ai_text_generation
        trigger_ai_text_generation(app)
    except Exception as e:
        print(f"[AI HOTKEY] Error triggering AI text generation: {e}")

def _start_typing_hotkey(app):
    """Handle start typing hotkey press"""
    try:
        # Check if user is logged in
        if not hasattr(app, 'user') or not app.user:
            print("[HOTKEY] Start typing blocked - user not logged in")
            return

        # Check for typing tab in different locations
        typing_tab = None
        if hasattr(app, 'typing_tab'):
            typing_tab = app.typing_tab
        elif hasattr(app, 'tabs') and 'Typing' in app.tabs:
            typing_tab = app.tabs['Typing']

        if typing_tab and hasattr(typing_tab, 'start_typing'):
            typing_tab.start_typing()
            print("[HOTKEY] Started typing")
    except Exception as e:
        print(f"[START HOTKEY] Error starting typing: {e}")

def _stop_typing_hotkey(app):
    """Handle stop typing hotkey press"""
    try:
        # Check if user is logged in
        if not hasattr(app, 'user') or not app.user:
            print("[HOTKEY] Stop typing blocked - user not logged in")
            return

        # Check for typing tab in different locations
        typing_tab = None
        if hasattr(app, 'typing_tab'):
            typing_tab = app.typing_tab
        elif hasattr(app, 'tabs') and 'Typing' in app.tabs:
            typing_tab = app.tabs['Typing']

        if typing_tab and hasattr(typing_tab, 'stop_typing_hotkey'):
            typing_tab.stop_typing_hotkey()
            print("[HOTKEY] Stopped typing")
    except Exception as e:
        print(f"[STOP HOTKEY] Error stopping typing: {e}")

def _pause_typing_hotkey(app):
    """Handle pause typing hotkey press"""
    try:
        # Check if user is logged in
        if not hasattr(app, 'user') or not app.user:
            print("[HOTKEY] Pause typing blocked - user not logged in")
            return

        # Check for typing tab in different locations
        typing_tab = None
        if hasattr(app, 'typing_tab'):
            typing_tab = app.typing_tab
        elif hasattr(app, 'tabs') and 'Typing' in app.tabs:
            typing_tab = app.tabs['Typing']

        if typing_tab and hasattr(typing_tab, 'toggle_pause'):
            typing_tab.toggle_pause()
            print("[HOTKEY] Toggled pause")
    except Exception as e:
        print(f"[PAUSE HOTKEY] Error toggling pause: {e}")

def validate_and_set_hotkey(app, hk, key_name):
    _validate_and_set_hotkey(app, hk, key_name)
