"""Utility classes and helper functions."""

import tkinter as tk
from tkinter import messagebox
import keyboard


class Tooltip:
    """Attach to any widget to display a small text popup on hover."""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tipwindow:
            return
        x, y = self.widget.winfo_pointerxy()
        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x+20}+{y+20}")
        label = tk.Label(
            tw,
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9)
        )
        label.pack()
        self.tipwindow = tw

    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


class HotkeyRecorder(tk.Frame):
    """Widget to capture a global hotkey combination."""
    
    _active_recorder = None  # Class-level: only one can record at once

    def __init__(self, parent, callback, current, get_all_hotkeys=None):
        super().__init__(parent)
        self.callback = callback
        self.current_hotkey = current
        self.get_all_hotkeys = get_all_hotkeys or (lambda: [])
        self.recording = False
        self._setup_ui()

    def _setup_ui(self):
        """Setup the recorder UI."""
        self.entry = tk.Entry(self, width=20, state='readonly')
        self.entry.pack(side='left', padx=(0, 5))
        self.entry.insert(0, self.current_hotkey)
        
        self.record_btn = tk.Button(self, text="Record", command=self._start_recording)
        self.record_btn.pack(side='left', padx=(0, 2))
        
        self.clear_btn = tk.Button(self, text="Clear", command=self._clear)
        self.clear_btn.pack(side='left')

    def _start_recording(self):
        """Start recording a new hotkey."""
        if HotkeyRecorder._active_recorder and HotkeyRecorder._active_recorder != self:
            HotkeyRecorder._active_recorder._stop_recording()
        
        HotkeyRecorder._active_recorder = self
        self.recording = True
        self.record_btn.config(text="Recording...", state='disabled')
        self.entry.config(state='normal')
        self.entry.delete(0, 'end')
        self.entry.insert(0, "Press hotkey combination...")
        self.entry.config(state='readonly')
        
        # Start listening for hotkeys
        self._listen_for_hotkey()

    def _listen_for_hotkey(self):
        """Listen for hotkey input."""
        try:
            # Simple implementation - in real app you'd want more sophisticated key detection
            self.after(100, self._check_recording)
        except Exception as e:
            print(f"Error in hotkey recording: {e}")
            self._stop_recording()

    def _check_recording(self):
        """Check if recording should continue."""
        if self.recording:
            self.after(100, self._check_recording)

    def _stop_recording(self):
        """Stop recording hotkey."""
        self.recording = False
        self.record_btn.config(text="Record", state='normal')
        if HotkeyRecorder._active_recorder == self:
            HotkeyRecorder._active_recorder = None

    def _clear(self):
        """Clear the current hotkey."""
        self.current_hotkey = ""
        self.entry.config(state='normal')
        self.entry.delete(0, 'end')
        self.entry.config(state='readonly')
        if self.callback:
            self.callback("")

    def set_hotkey(self, hotkey_str):
        """Set the hotkey value."""
        self.current_hotkey = hotkey_str
        self.entry.config(state='normal')
        self.entry.delete(0, 'end')
        self.entry.insert(0, hotkey_str)
        self.entry.config(state='readonly')