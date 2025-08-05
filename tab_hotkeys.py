import tkinter as tk
from utils import HotkeyRecorder, Tooltip
import config

class HotkeysTab(tk.Frame):
    def __init__(self, parent, app):
        dark = app.cfg['settings'].get('dark_mode', False)
        bg = config.DARK_BG if dark else config.LIGHT_BG

        super().__init__(parent, bg=bg)
        self.app = app
        self.widgets = []

        self.build_ui(bg)
        
    def build_ui(self, bg):
        # --- Start Typing Hotkey ---
        lbl_start = tk.Label(self, text="Start Typing Hotkey:", font=("Segoe UI", 11), bg=bg, fg=self._fg())
        lbl_start.pack(anchor="w", padx=10, pady=(10, 0))
        self.widgets.append(lbl_start)

        self.start_rec = HotkeyRecorder(
            self,
            self.app.set_start_hotkey,
            self.app.cfg["settings"]["hotkeys"]["start"],
            get_all_hotkeys=self.get_all_hotkeys
        )
        self.start_rec.pack(fill="x", padx=10, pady=(0, 8))
        self.widgets.append(self.start_rec)

        # --- Panic Stop Hotkey ---
        lbl_stop = tk.Label(self, text="Panic Stop Hotkey:", font=("Segoe UI", 11), bg=bg, fg=self._fg())
        lbl_stop.pack(anchor="w", padx=10, pady=(0, 0))
        self.widgets.append(lbl_stop)

        self.stop_rec = HotkeyRecorder(
            self,
            self.app.set_stop_hotkey,
            self.app.cfg["settings"]["hotkeys"]["stop"],
            get_all_hotkeys=self.get_all_hotkeys
        )
        self.stop_rec.pack(fill="x", padx=10, pady=(0, 8))
        self.widgets.append(self.stop_rec)

        # --- Pause/Resume Hotkey ---
        lbl_pause = tk.Label(self, text="Pause/Resume Hotkey:", font=("Segoe UI", 11), bg=bg, fg=self._fg())
        lbl_pause.pack(anchor="w", padx=10, pady=(0, 0))
        self.widgets.append(lbl_pause)

        self.pause_rec = HotkeyRecorder(
            self,
            self.app.set_pause_hotkey,
            self.app.cfg["settings"]["hotkeys"].get("pause", "ctrl+alt+p"),
            get_all_hotkeys=self.get_all_hotkeys
        )
        self.pause_rec.pack(fill="x", padx=10, pady=(0, 8))
        self.widgets.append(self.pause_rec)

        # --- Reset Hotkeys Button ---
        btn_frame = tk.Frame(self, bg=bg)
        btn_frame.pack(padx=10, pady=(10, 18), fill="x")
        self.widgets.append(btn_frame)

        reset_btn = tk.Button(
            btn_frame,
            text="Reset Hotkeys",
            command=self.app.reset_hotkeys,
            bg=self._button_bg(),
            fg=self._button_fg(),
            activebackground=self._button_bg(),
            activeforeground=self._button_fg(),
            relief="ridge", borderwidth=2, height=1, width=20
        )
        reset_btn.pack()
        Tooltip(reset_btn, "Reset to the default start/stop/pause hotkeys")
        self.widgets.append(reset_btn)

    def _fg(self):
        dark = self.app.cfg['settings'].get('dark_mode', False)
        return config.DARK_FG if dark else config.LIGHT_FG

    def _button_bg(self):
        dark = self.app.cfg['settings'].get('dark_mode', False)
        return "#23272f" if dark else "#e0e0e0"

    def _button_fg(self):
        dark = self.app.cfg['settings'].get('dark_mode', False)
        return "#ffffff" if dark else "#000000"

    def set_theme(self, dark):
        bg = config.DARK_BG if dark else config.LIGHT_BG
        fg = config.DARK_FG if dark else config.LIGHT_FG
        self.config(bg=bg)

        # Update all labels and frames
        for widget in self.widgets:
            if isinstance(widget, (tk.Label, tk.Frame)):
                try:
                    widget.config(bg=bg, fg=fg)
                except Exception:
                    try:
                        widget.config(bg=bg)
                    except Exception:
                        pass
            elif isinstance(widget, tk.Button):
                try:
                    widget.config(
                        bg=self._button_bg(),
                        fg=self._button_fg(),
                        activebackground=self._button_bg(),
                        activeforeground=self._button_fg()
                    )
                except Exception:
                    pass
            if hasattr(widget, "set_theme"):
                widget.set_theme(dark)

    def get_all_hotkeys(self):
        # Return all current hotkeys in use
        return [
            self.start_rec.current,
            self.stop_rec.current,
            self.pause_rec.current
        ]
