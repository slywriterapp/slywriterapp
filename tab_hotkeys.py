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
        # Create scrollable frame
        from tkinter import ttk
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Create scrollable frame
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Add scrollable frame to canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # --- Start Typing Hotkey ---
        lbl_start = tk.Label(self.scrollable_frame, text="Start Typing Hotkey:", font=("Segoe UI", 11), bg=bg, fg=self._fg())
        lbl_start.pack(anchor="w", padx=10, pady=(10, 0))
        self.widgets.append(lbl_start)

        self.start_rec = HotkeyRecorder(
            self.scrollable_frame,
            self.app.set_start_hotkey,
            self.app.cfg["settings"]["hotkeys"]["start"],
            get_all_hotkeys=self.get_all_hotkeys
        )
        self.start_rec.pack(fill="x", padx=10, pady=(0, 8))
        self.widgets.append(self.start_rec)

        # --- Panic Stop Hotkey ---
        lbl_stop = tk.Label(self.scrollable_frame, text="Panic Stop Hotkey:", font=("Segoe UI", 11), bg=bg, fg=self._fg())
        lbl_stop.pack(anchor="w", padx=10, pady=(0, 0))
        self.widgets.append(lbl_stop)

        self.stop_rec = HotkeyRecorder(
            self.scrollable_frame,
            self.app.set_stop_hotkey,
            self.app.cfg["settings"]["hotkeys"]["stop"],
            get_all_hotkeys=self.get_all_hotkeys
        )
        self.stop_rec.pack(fill="x", padx=10, pady=(0, 8))
        self.widgets.append(self.stop_rec)

        # --- Pause/Resume Hotkey ---
        lbl_pause = tk.Label(self.scrollable_frame, text="Pause/Resume Hotkey:", font=("Segoe UI", 11), bg=bg, fg=self._fg())
        lbl_pause.pack(anchor="w", padx=10, pady=(0, 0))
        self.widgets.append(lbl_pause)

        self.pause_rec = HotkeyRecorder(
            self.scrollable_frame,
            self.app.set_pause_hotkey,
            self.app.cfg["settings"]["hotkeys"].get("pause", "ctrl+alt+p"),
            get_all_hotkeys=self.get_all_hotkeys
        )
        self.pause_rec.pack(fill="x", padx=10, pady=(0, 8))
        self.widgets.append(self.pause_rec)

        # --- Overlay Toggle Hotkey ---
        lbl_overlay = tk.Label(self.scrollable_frame, text="Toggle Overlay Hotkey:", font=("Segoe UI", 11), bg=bg, fg=self._fg())
        lbl_overlay.pack(anchor="w", padx=10, pady=(0, 0))
        self.widgets.append(lbl_overlay)

        self.overlay_rec = HotkeyRecorder(
            self.scrollable_frame,
            self.app.set_overlay_hotkey,
            self.app.cfg["settings"]["hotkeys"].get("overlay", "ctrl+alt+o"),
            get_all_hotkeys=self.get_all_hotkeys
        )
        self.overlay_rec.pack(fill="x", padx=10, pady=(0, 8))
        self.widgets.append(self.overlay_rec)

        # --- AI Text Generation Hotkey ---
        lbl_ai_gen = tk.Label(self.scrollable_frame, text="AI Text Generation Hotkey:", font=("Segoe UI", 11), bg=bg, fg=self._fg())
        lbl_ai_gen.pack(anchor="w", padx=10, pady=(0, 0))
        self.widgets.append(lbl_ai_gen)

        self.ai_gen_rec = HotkeyRecorder(
            self.scrollable_frame,
            self.app.set_ai_generation_hotkey,
            self.app.cfg["settings"]["hotkeys"].get("ai_generation", "ctrl+alt+g"),
            get_all_hotkeys=self.get_all_hotkeys
        )
        self.ai_gen_rec.pack(fill="x", padx=10, pady=(0, 8))
        self.widgets.append(self.ai_gen_rec)

        # --- Reset Hotkeys Button ---
        btn_frame = tk.Frame(self.scrollable_frame, bg=bg)
        btn_frame.pack(padx=10, pady=(10, 18), fill="x")
        self.widgets.append(btn_frame)

        reset_btn = tk.Button(
            btn_frame,
            text="Reset Hotkeys",
            command=self.app.reset_hotkeys,
            bg=config.ACCENT_PURPLE,  # Direct purple color
            fg='white',
            activebackground='#7C3AED',  # Darker purple on click
            activeforeground='white',
            relief="flat", borderwidth=0, height=1, width=20,
            cursor='hand2',
            font=('Segoe UI', 10, 'bold')
        )
        reset_btn.pack()
        
        # Ensure purple styling is applied FIRST
        reset_btn.config(
            bg=config.ACCENT_PURPLE,
            fg='white',
            activebackground='#7C3AED',
            activeforeground='white'
        )
        
        # Add hover effects with proper purple colors
        def on_enter(event):
            reset_btn.config(bg='#7C3AED')  # Darker purple on hover
        def on_leave(event):
            reset_btn.config(bg=config.ACCENT_PURPLE)  # Back to base purple
        
        reset_btn.bind('<Enter>', on_enter)
        reset_btn.bind('<Leave>', on_leave)
        
        Tooltip(reset_btn, "Reset to the default start/stop/pause hotkeys")
        self.widgets.append(reset_btn)

    def _fg(self):
        dark = self.app.cfg['settings'].get('dark_mode', False)
        return config.DARK_FG if dark else config.LIGHT_FG

    def _button_bg(self):
        # Use purple theme for consistency with other buttons
        return config.ACCENT_PURPLE

    def _button_fg(self):
        dark = self.app.cfg['settings'].get('dark_mode', False)
        return "white"  # White text looks good on both blue backgrounds

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
                        bg=config.ACCENT_PURPLE,  # Direct purple color
                        fg='white',
                        activebackground='#7C3AED',  # Darker purple on click
                        activeforeground='white'
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
            self.pause_rec.current,
            self.overlay_rec.current,
            self.ai_gen_rec.current
        ]
