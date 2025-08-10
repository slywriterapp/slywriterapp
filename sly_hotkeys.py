# sly_hotkeys.py

import keyboard
import ttkbootstrap as tb
import config

def register_hotkeys(app):
    for name in ['start', 'stop', 'pause', 'overlay', 'ai_generation']:
        try:
            keyboard.remove_hotkey(app.cfg['settings']['hotkeys'].get(name, ''))
        except Exception:
            pass
    keyboard.add_hotkey(app.cfg['settings']['hotkeys']['start'],
                        lambda: None if getattr(app.hotkeys_tab.start_rec, 'recording', False) else app.typing_tab.start_typing())
    keyboard.add_hotkey(app.cfg['settings']['hotkeys']['stop'],
                        lambda: None if getattr(app.hotkeys_tab.stop_rec, 'recording', False) else app.typing_tab.stop_typing_hotkey())
    keyboard.add_hotkey(app.cfg['settings']['hotkeys'].get('pause','ctrl+alt+p'),
                        lambda: None if getattr(app.hotkeys_tab.start_rec, 'recording', False) else app.typing_tab.toggle_pause())
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
    try:
        keyboard.parse_hotkey(hk)
        app.cfg['settings']['hotkeys'][key_name] = hk
        register_hotkeys(app)
        from sly_config import save_config
        save_config(app.cfg)
    except ValueError:
        tb.messagebox.showwarning("Invalid Hotkey", f"The hotkey '{hk}' is not valid.")

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
    if hasattr(app, 'overlay_tab'):
        current = app.overlay_tab.overlay_enabled.get()
        app.overlay_tab.overlay_enabled.set(not current)

def _ai_generation_hotkey(app):
    """Handle AI text generation hotkey press"""
    try:
        # Import here to avoid circular imports
        from ai_text_generator import trigger_ai_text_generation
        trigger_ai_text_generation(app)
    except Exception as e:
        print(f"[AI HOTKEY] Error triggering AI text generation: {e}")

def validate_and_set_hotkey(app, hk, key_name):
    _validate_and_set_hotkey(app, hk, key_name)
