import os
import json
import config
from tkinter import simpledialog, messagebox

# Path to your JSON config file
CONFIG_FILE = config.CONFIG_FILE

# Built-in profiles (always enforce typos_on=True)
BUILTIN_PROFILES = {
    "Default": {
        "min_delay":    config.MIN_DELAY_DEFAULT,
        "max_delay":    config.MAX_DELAY_DEFAULT,
        "typos_on":     True,
        "pause_freq":   config.LONG_PAUSE_DEFAULT,
    },
    "Speed-Type": {
        "min_delay":    0.01,
        "max_delay":    0.05,
        "typos_on":     True,
        "pause_freq":   1000,
    },
    "Ultra-Slow": {
        "min_delay":    0.15,
        "max_delay":    0.40,
        "typos_on":     True,
        "pause_freq":   30,
    },
}

def load_config():
    """
    Load (or initialize) the configuration JSON.
    Ensures necessary keys exist. No forced cleanup of profiles!
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    else:
        cfg = config.DEFAULT_CONFIG.copy()

    cfg.setdefault("profiles", [])
    cfg.setdefault("settings", {})
    cfg.setdefault("custom_presets", {})
    cfg.setdefault("active_profile", "Default")

    print(f"[DEBUG] Profiles at load: {cfg.get('profiles', [])}")
    print(f"[DEBUG] Custom presets after load: {list(cfg['custom_presets'].keys())}")
    print(f"[DEBUG] Active profile: {cfg.get('active_profile')}")
    return cfg

def save_config(cfg):
    """Persist the configuration back to disk."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)

def add_profile(app):
    """
    Prompt for a new profile name, then snapshot current settings—
    forcing typos_on=True for every new custom profile.
    """
    name = simpledialog.askstring("New Profile", "Enter profile name:")
    if not name:
        return
    name = name.strip()
    if name in BUILTIN_PROFILES or name in app.cfg["custom_presets"]:
        messagebox.showwarning("Cannot Add", f"'{name}' is reserved or already exists.")
        return

    s = app.cfg["settings"]
    snapshot = {
        "min_delay":    s.get("min_delay", config.MIN_DELAY_DEFAULT),
        "max_delay":    s.get("max_delay", config.MAX_DELAY_DEFAULT),
        "typos_on":     True,
        "pause_freq":   s.get("pause_freq", config.LONG_PAUSE_DEFAULT),
        "preview_only": s.get("preview_only", False),
        "adv_antidetect": s.get("adv_antidetect", False)
    }

    app.cfg["custom_presets"][name] = snapshot
    app.cfg["profiles"].append(name)
    save_config(app.cfg)

    # Refresh dropdown and switch immediately
    app.prof_box['values'] = app.cfg["profiles"]
    app.active_profile.set(name)
    on_profile_change(app)

def delete_profile(app):
    """
    Remove a user-created profile. Built-in profiles cannot be deleted.
    """
    name = app.active_profile.get()
    if name in BUILTIN_PROFILES:
        messagebox.showinfo("Cannot Delete", f"'{name}' is a built-in profile.")
        return
    if not messagebox.askyesno("Delete Profile", f"Remove '{name}'?"):
        return

    app.cfg["custom_presets"].pop(name, None)
    app.cfg["profiles"].remove(name)
    save_config(app.cfg)

    # Reset to Default
    app.prof_box['values'] = app.cfg["profiles"]
    app.active_profile.set("Default")
    on_profile_change(app)

def save_profile(app):
    """
    Overwrite the snapshot for the currently selected custom profile.
    """
    name = app.active_profile.get()
    if name in BUILTIN_PROFILES:
        messagebox.showinfo("Built-in Profile", f"'{name}' cannot be modified.")
        return

    s = app.cfg["settings"]
    snapshot = {
        "min_delay":    s["min_delay"],
        "max_delay":    s["max_delay"],
        "typos_on":     s["typos_on"],
        "pause_freq":   s["pause_freq"],
        "preview_only": s.get("preview_only", False),
        "adv_antidetect": s.get("adv_antidetect", False)
    }

    app.cfg["custom_presets"][name] = snapshot
    save_config(app.cfg)
    messagebox.showinfo("Saved", f"Profile '{name}' updated.")

def reset_typing_settings(app):
    """
    Reset typing controls to the baseline of the active profile
    (built-in or custom).
    """
    name = app.active_profile.get()
    if name in BUILTIN_PROFILES:
        preset = BUILTIN_PROFILES[name]
    else:
        preset = app.cfg["custom_presets"].get(name, BUILTIN_PROFILES["Default"])

    app.cfg["settings"].update(preset)
    save_config(app.cfg)
    # Push into UI
    app.typing_tab.update_from_config()

def on_setting_change(app):
    """
    Persist any slider/check changes, and if on a custom profile,
    update its snapshot too.
    """
    if not hasattr(app, "typing_tab"):
        return
    s = app.cfg["settings"]
    tt = app.typing_tab

    s["min_delay"]    = tt.min_delay_var.get()
    s["max_delay"]    = tt.max_delay_var.get()
    s["typos_on"]     = tt.typos_var.get()
    s["pause_freq"]   = tt.pause_freq_var.get()
    s["preview_only"] = tt.preview_only_var.get()
    s["adv_antidetect"] = tt.adv_antidetect_var.get()
    
    # Save overlay settings
    if hasattr(app, 'overlay_tab'):
        s["overlay_enabled"] = app.overlay_tab.overlay_enabled.get()
        s["overlay_opacity"] = app.overlay_tab.overlay_opacity.get()
        s["overlay_width"] = app.overlay_tab.overlay_width.get()
        s["overlay_height"] = app.overlay_tab.overlay_height.get()
        s["overlay_x"] = app.overlay_tab.overlay_x.get()
        s["overlay_y"] = app.overlay_tab.overlay_y.get()

    name = app.active_profile.get()
    if name in app.cfg["custom_presets"]:
        app.cfg["custom_presets"][name] = {
            "min_delay":    s["min_delay"],
            "max_delay":    s["max_delay"],
            "typos_on":     s["typos_on"],
            "pause_freq":   s["pause_freq"],
            "preview_only": s["preview_only"],
            "adv_antidetect": s["adv_antidetect"]
        }

    save_config(app.cfg)

def on_profile_change(app):
    """
    When the profile dropdown changes:
      1) Load the correct preset
      2) Persist active_profile
      3) Let TypingTab.update_from_config() drive **all** sliders/values
      4) Recompute WPM
    """
    name = app.active_profile.get()

    # 1 & 2
    app.cfg["active_profile"] = name
    if name in BUILTIN_PROFILES:
        preset = BUILTIN_PROFILES[name]
        print(f"[PROFILE] Loading built-in profile: {name}")
        print(f"[PROFILE] Preset values: min_delay={preset.get('min_delay')}, max_delay={preset.get('max_delay')}")
    else:
        preset = app.cfg["custom_presets"].get(name, BUILTIN_PROFILES["Default"])
        print(f"[PROFILE] Loading custom profile: {name}")
        print(f"[PROFILE] Preset values: min_delay={preset.get('min_delay')}, max_delay={preset.get('max_delay')}")

    # Update settings with preset values
    app.cfg["settings"].update(preset)
    print(f"[PROFILE] After update - settings: min_delay={app.cfg['settings'].get('min_delay')}, max_delay={app.cfg['settings'].get('max_delay')}")
    save_config(app.cfg)

    # 3 & 4: push everything into UI in one go
    app.typing_tab.update_from_config()
