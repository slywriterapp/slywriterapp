import tkinter as tk
from tkinter import ttk
from utils import HotkeyRecorder, Tooltip

class HotkeysTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.build_ui()

    def build_ui(self):
        # ── Start Typing Hotkey ─────────────────────────
        ttk.Label(self, text="Start Typing Hotkey:", font=("Segoe UI", 11))\
            .pack(anchor="w", padx=10, pady=(10, 0))
        self.start_rec = HotkeyRecorder(
            self,
            callback=self.app.set_start_hotkey,
            current=self.app.cfg["settings"]["hotkeys"]["start"]
        )
        self.start_rec.pack(fill="x", padx=10)

        start_btns = ttk.Frame(self)
        start_btns.pack(fill="x", padx=10, pady=(5, 20))
        ttk.Button(start_btns, text="Record", command=self.start_rec.start).pack(side="left")
        ttk.Button(start_btns, text="Confirm", command=self.start_rec.confirm_hotkey).pack(side="left", padx=5)
        ttk.Button(start_btns, text="Cancel", command=self.start_rec.cancel_recording).pack(side="left", padx=5)

        # ── Panic Stop Hotkey ──────────────────────────
        ttk.Label(self, text="Panic Stop Hotkey:", font=("Segoe UI", 11))\
            .pack(anchor="w", padx=10, pady=(0, 0))
        self.stop_rec = HotkeyRecorder(
            self,
            callback=self.app.set_stop_hotkey,
            current=self.app.cfg["settings"]["hotkeys"]["stop"]
        )
        self.stop_rec.pack(fill="x", padx=10)

        stop_btns = ttk.Frame(self)
        stop_btns.pack(fill="x", padx=10, pady=(5, 20))
        ttk.Button(stop_btns, text="Record", command=self.stop_rec.start).pack(side="left")
        ttk.Button(stop_btns, text="Confirm", command=self.stop_rec.confirm_hotkey).pack(side="left", padx=5)
        ttk.Button(stop_btns, text="Cancel", command=self.stop_rec.cancel_recording).pack(side="left", padx=5)

        # ── Pause/Resume Hotkey (NEW) ──────────────────
        ttk.Label(self, text="Pause/Resume Hotkey:", font=("Segoe UI", 11))\
            .pack(anchor="w", padx=10, pady=(0, 0))
        self.pause_rec = HotkeyRecorder(
            self,
            callback=self.app.set_pause_hotkey,
            current=self.app.cfg["settings"]["hotkeys"].get("pause", "ctrl+alt+p")
        )
        self.pause_rec.pack(fill="x", padx=10)

        pause_btns = ttk.Frame(self)
        pause_btns.pack(fill="x", padx=10, pady=(5, 20))
        ttk.Button(pause_btns, text="Record", command=self.pause_rec.start).pack(side="left")
        ttk.Button(pause_btns, text="Confirm", command=self.pause_rec.confirm_hotkey).pack(side="left", padx=5)
        ttk.Button(pause_btns, text="Cancel", command=self.pause_rec.cancel_recording).pack(side="left", padx=5)

        # ── Reset to defaults ──────────────────────────
        reset_btn = ttk.Button(self, text="Reset Hotkeys", command=self.app.reset_hotkeys)
        reset_btn.pack(padx=10, pady=(0, 20))
        Tooltip(reset_btn, "Reset to the default start/stop/pause hotkeys")
