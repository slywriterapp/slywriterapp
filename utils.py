import tkinter as tk
from tkinter import ttk, messagebox
import keyboard  # needed for hotkey validation

class Tooltip:
    """
    Attach to any widget to display a small text popup on hover.
    """
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


class HotkeyRecorder(ttk.Frame):
    """
    A widget to capture a global hotkey combination.
    callback: function(new_hotkey_str)
    current: the currently configured hotkey string
    """
    def __init__(self, parent, callback, current):
        super().__init__(parent)
        self.callback = callback
        self.current = current
        self.recording = False
        self.pressed = set()

        # Label showing the current hotkey
        self.label = ttk.Label(self, text=f"Current hotkey: {self.current}")
        self.label.pack(pady=5)

        # Read‑only entry displaying the in‑progress combo
        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(
            self, textvariable=self.entry_var, state='readonly', justify='center'
        )
        self.entry.pack(fill='x', padx=10)

        # Record / stop button
        self.btn = ttk.Button(self, text="Record Hotkey", command=self.start)
        self.btn.pack(pady=5)

    def start(self):
        if self.recording:
            return
        self.recording = True
        self.entry_var.set("Recording...")
        self.btn.config(state='disabled')
        self.master.bind_all('<KeyPress>', self.on_press)
        self.master.bind_all('<KeyRelease>', self.on_release)

    def on_press(self, event):
        self.pressed.add(event.keysym.lower())
        mods = [m for m in ('ctrl', 'alt', 'shift')
                if any(k.startswith(m) for k in self.pressed)]
        mains = [k for k in self.pressed if k not in mods]
        if mains:
            combo = '+'.join(mods + [mains[-1]])
            self.entry_var.set(combo)

    def on_release(self, event):
        key = event.keysym.lower()
        if key in self.pressed:
            self.pressed.remove(key)

        if event.keysym == 'Return':
            # Confirm new hotkey
            self.confirm_hotkey()
        elif event.keysym == 'Escape':
            # Cancel recording
            self.entry_var.set('')
            self._stop_recording()

    def _stop_recording(self):
        self.recording = False
        self.master.unbind_all('<KeyPress>')
        self.master.unbind_all('<KeyRelease>')
        self.btn.config(state='normal')
        final = self.entry_var.get() or self.current
        self.current = final
        self.label.config(text=f"Current hotkey: {final}")

    def confirm_hotkey(self):
        """
        External “Confirm” button can call this to accept entry_var.
        Validates the entered hotkey before sending it back.
        """
        new_hotkey = self.entry_var.get() or self.current

        # Validate hotkey using keyboard library
        try:
            keyboard.parse_hotkey_combinations(new_hotkey)
        except Exception:
            messagebox.showerror(
                "Invalid Hotkey",
                f"'{new_hotkey}' is not a valid or supported hotkey combination."
            )
            self.entry_var.set('')  # clear entry if invalid
            return

        self._stop_recording()
        self.callback(new_hotkey)

    def cancel_recording(self):
        """
        External “Cancel” button can call this to abort recording.
        """
        self.entry_var.set('')
        self._stop_recording()
