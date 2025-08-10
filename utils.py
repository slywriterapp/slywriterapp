import tkinter as tk
from tkinter import messagebox
import keyboard

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

class HotkeyRecorder(tk.Frame):
    """
    A widget to capture a global hotkey combination.
    callback: function(new_hotkey_str)
    current: the currently configured hotkey string
    get_all_hotkeys: function returning a list of all used hotkeys (to prevent duplicates)
    """
    _active_recorder = None  # Class-level: only one can record at once

    def __init__(self, parent, callback, current, get_all_hotkeys=None):
        super().__init__(parent)
        self.callback = callback
        self.current = current or ""
        self.get_all_hotkeys = get_all_hotkeys
        self.recording = False
        self.pressed = set()
        self.theme_dark = False

        # --- UI ---
        self.label = tk.Label(self, text=f"Current hotkey: {self.current}")
        self.label.pack(pady=5)

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            self, textvariable=self.entry_var, state='readonly', justify='center',
            relief="sunken"
        )
        self.entry.pack(fill='x', padx=10)

        # Buttons container
        self.btns_frame = tk.Frame(self)
        self.btns_frame.pack(pady=3)

        self.btn_record = tk.Button(
            self.btns_frame, text="Record Hotkey", command=self.start,
            relief="groove", borderwidth=2
        )
        self.btn_record.grid(row=0, column=0, padx=3)

        self.btn_confirm = tk.Button(
            self.btns_frame, text="Confirm", command=self.confirm_hotkey,
            relief="ridge", borderwidth=2
        )
        self.btn_confirm.grid(row=0, column=1, padx=3)

        self.btn_cancel = tk.Button(
            self.btns_frame, text="Cancel", command=self.cancel_recording,
            relief="ridge", borderwidth=2
        )
        self.btn_cancel.grid(row=0, column=2, padx=3)

        # Set theme AFTER widgets exist
        self.set_theme(False)

    def set_theme(self, dark):
        """
        Update widget for dark or light mode.
        """
        self.theme_dark = dark
        self.bg = "#181816" if dark else "#ffffff"
        self.fg = "#ffffff" if dark else "#000000"
        self.label.configure(bg=self.bg, fg=self.fg)
        self.configure(bg=self.bg)
        self.btns_frame.configure(bg=self.bg)
        # Modern button colors
        import config
        btn_bg = config.PRIMARY_BLUE if dark else config.PRIMARY_BLUE_LIGHT
        btn_fg = "white"  # White text on blue background
        for b in [self.btn_record, self.btn_confirm, self.btn_cancel]:
            b.configure(bg=btn_bg, fg=btn_fg, activebackground=btn_bg, activeforeground=btn_fg)
        # Entry: "Recording..." should be WHITE box, BLACK text in dark mode!
        if self.recording:
            self.entry.configure(bg="#ffffff", fg="#000000", insertbackground="#000000")
        else:
            entry_bg = "#242424" if dark else "#ffffff"
            entry_fg = "#ffffff" if dark else "#000000"
            self.entry.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)

    def start(self):
        if self.recording:
            return
        # Cancel any other active HotkeyRecorder!
        if HotkeyRecorder._active_recorder and HotkeyRecorder._active_recorder is not self:
            HotkeyRecorder._active_recorder.cancel_recording()
        HotkeyRecorder._active_recorder = self

        self.recording = True
        self.entry_var.set("Recording...")
        self.btn_record.config(state='disabled')
        self.set_theme(self.theme_dark)  # force white box for recording in dark
        self.master.bind_all('<KeyPress>', self.on_press)
        self.master.bind_all('<KeyRelease>', self.on_release)

    def on_press(self, event):
        # Enter/Escape are handled in on_release
        if event.keysym in ('Return', 'Escape'):
            return
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
            if self.entry_var.get().lower() not in ["", "recording..."]:
                self.confirm_hotkey()
            else:
                self._stop_recording()
        elif event.keysym == 'Escape':
            self.entry_var.set('')
            self._stop_recording()

    def _stop_recording(self):
        self.recording = False
        if HotkeyRecorder._active_recorder is self:
            HotkeyRecorder._active_recorder = None
        self.master.unbind_all('<KeyPress>')
        self.master.unbind_all('<KeyRelease>')
        self.btn_record.config(state='normal')
        self.set_theme(self.theme_dark)
        # Reset display to current hotkey
        final = self.entry_var.get() or self.current
        self.current = final
        self.label.config(text=f"Current hotkey: {final}")

    def confirm_hotkey(self):
        """
        Accept entry_var as new hotkey, validating uniqueness and validity.
        """
        new_hotkey = self.entry_var.get() or self.current
        # Never allow empty, Enter, or "recording..." as a hotkey!
        if not new_hotkey or new_hotkey.lower() in ["", "recording...", "return", "enter"]:
            self.entry_var.set('')
            self._stop_recording()
            return
        # Check for duplicates/conflicts if available
        if self.get_all_hotkeys:
            current_hotkeys = [hk.lower() for hk in self.get_all_hotkeys() if hk and hk != self.current]
            if new_hotkey.lower() in current_hotkeys:
                messagebox.showerror(
                    "Duplicate Hotkey",
                    f"'{new_hotkey}' is already in use as another hotkey. Please choose a unique combination."
                )
                self.entry_var.set('')
                return
        # Validate hotkey using keyboard library
        try:
            keyboard.parse_hotkey_combinations(new_hotkey)
        except Exception:
            messagebox.showerror(
                "Invalid Hotkey",
                f"'{new_hotkey}' is not a valid or supported hotkey combination."
            )
            self.entry_var.set('')
            return
        self._stop_recording()
        self.callback(new_hotkey)

    def cancel_recording(self):
        self.entry_var.set('')
        self._stop_recording()


# ═══════════════════════════════════════════════════════════════
# Centralized Premium Feature Management
# ═══════════════════════════════════════════════════════════════

def is_premium_user(app):
    """
    Centralized premium check to prevent feature leaks.
    Returns True if user has premium access, False otherwise.
    """
    try:
        # Check if app has account_tab with premium check
        if hasattr(app, 'account_tab') and hasattr(app.account_tab, 'is_premium'):
            return app.account_tab.is_premium()
        
        # Fallback: check user object directly  
        if hasattr(app, 'user') and app.user:
            plan = getattr(app.user, 'plan', 'free')
            return plan.lower() in ("pro", "premium", "enterprise")
        
        # No user logged in = not premium
        return False
    except Exception as e:
        print(f"Error checking premium status: {e}")
        return False  # Default to free if error

def get_user_plan(app):
    """
    Get the current user's plan name.
    Returns 'free' if not premium or error.
    """
    try:
        if hasattr(app, 'user') and app.user:
            return getattr(app.user, 'plan', 'free').lower()
        return 'free'
    except Exception:
        return 'free'

def require_premium(app, feature_name="this feature"):
    """
    Check premium status and show upgrade message if not premium.
    Returns True if premium, False if not (with message shown).
    """
    if is_premium_user(app):
        return True
    
    messagebox.showinfo(
        "Premium Required",
        f"Upgrade to SlyWriter Premium to unlock {feature_name}!"
    )
    return False
