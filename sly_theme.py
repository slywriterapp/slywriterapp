# sly_theme.py

import config

def apply_app_theme(app):
    dark = app.cfg['settings'].get('dark_mode', False)

    # Get colors safely, fallback if needed
    def get_color(name, default):
        try:
            return app.tb_style.colors.get(name)
        except Exception:
            return default

    bg        = get_color('bg', config.DARK_BG if dark else config.LIGHT_BG)
    fg        = get_color('fg', config.DARK_FG if dark else config.LIGHT_FG)
    entry_bg  = get_color('inputbg', config.DARK_ENTRY_BG if dark else "white")
    entry_fg  = get_color('inputfg', config.DARK_FG if dark else config.LIGHT_FG)
    accent    = get_color('primary', config.PRIMARY_BLUE)

    app.configure(bg=bg)

    # Combobox colors update + force redraw to fix selected text color bug
    app.prof_box.configure(background=entry_bg, foreground=entry_fg)
    app.prof_box.event_generate('<FocusOut>')
    app.prof_box.event_generate('<FocusIn>')

    # Update all tabs for theme change
    app.typing_tab.set_theme(dark)
    app.hotkeys_tab.set_theme(dark)
    app.stats_tab.set_theme(dark)
    app.humanizer_tab.set_theme(dark)
    app.account_tab.set_theme(dark)
    app.overlay_tab.set_theme(dark)
    app.learn_tab.set_theme(dark)

    # Force idle update to refresh widgets fully
    app.update_idletasks()

def force_theme_refresh(app):
    current = app.cfg.get('settings', {}).get('dark_mode', False)
    app.cfg['settings']['dark_mode'] = not current
    apply_app_theme(app)
    app.cfg['settings']['dark_mode'] = current
    apply_app_theme(app)
