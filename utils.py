import tkinter as tk
from tkinter import messagebox
import keyboard
import webbrowser

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
        # Format hotkey for display (Cmd on Mac, Ctrl on Windows)
        display_hotkey = self._format_hotkey_for_display(self.current)
        self.label = tk.Label(self, text=f"Current hotkey: {display_hotkey}")
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

    def _format_hotkey_for_display(self, hotkey):
        """Format hotkey string for display - Cmd on Mac, Ctrl on Windows/Linux"""
        if not hotkey:
            return ""

        import platform
        if platform.system() == 'Darwin':  # Mac
            # Replace 'ctrl' with 'cmd' for Mac display
            return hotkey.replace('ctrl', 'cmd').replace('Ctrl', 'Cmd')
        return hotkey

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
        # Modern button colors - use purple theme
        import config
        btn_bg = config.ACCENT_PURPLE  # Use purple for all buttons
        btn_fg = "white"  # White text on purple background
        hover_bg = '#7C3AED'  # Darker purple for hover
        
        for b in [self.btn_record, self.btn_confirm, self.btn_cancel]:
            b.configure(
                bg=btn_bg, 
                fg=btn_fg, 
                activebackground=hover_bg, 
                activeforeground=btn_fg,
                relief='flat',
                bd=0,
                cursor='hand2',
                font=('Segoe UI', 9, 'bold')
            )
            
            # Add hover effects
            def make_hover_handlers(btn):
                def on_enter(event):
                    btn.config(bg=hover_bg)
                def on_leave(event):  
                    btn.config(bg=btn_bg)
                return on_enter, on_leave
            
            enter_handler, leave_handler = make_hover_handlers(b)
            b.bind('<Enter>', enter_handler)
            b.bind('<Leave>', leave_handler)
        # Entry: WHITE background with BLACK text for maximum visibility  
        self.entry.configure(bg="#ffffff", fg="#000000", insertbackground="#000000")

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

def show_upgrade_dialog(parent, feature_name="this feature", required_plan="Pro"):
    """
    Show a custom upgrade dialog with a link to pricing page.
    Returns True if user wants to upgrade, False otherwise.
    """
    dialog = tk.Toplevel(parent)
    dialog.title(f"{required_plan} Plan Required")
    dialog.geometry("400x220")
    dialog.resizable(False, False)

    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
    y = (dialog.winfo_screenheight() // 2) - (220 // 2)
    dialog.geometry(f"400x220+{x}+{y}")

    # Make it modal
    dialog.transient(parent)
    dialog.grab_set()

    # Icon and title
    title_frame = tk.Frame(dialog, bg="#f5f5f5", height=60)
    title_frame.pack(fill='x')
    title_frame.pack_propagate(False)

    icon_label = tk.Label(title_frame, text="🔒", font=('Segoe UI', 24), bg="#f5f5f5")
    icon_label.pack(pady=10)

    # Message
    message_frame = tk.Frame(dialog, bg="white")
    message_frame.pack(fill='both', expand=True, padx=20, pady=15)

    title_label = tk.Label(
        message_frame,
        text=f"{required_plan} Plan Required",
        font=('Segoe UI', 12, 'bold'),
        bg="white"
    )
    title_label.pack(pady=(0, 10))

    message_label = tk.Label(
        message_frame,
        text=f"{feature_name} requires a {required_plan} plan or higher.",
        font=('Segoe UI', 10),
        bg="white",
        wraplength=350
    )
    message_label.pack()

    # Buttons
    button_frame = tk.Frame(dialog, bg="white")
    button_frame.pack(fill='x', padx=20, pady=(0, 15))

    def open_pricing():
        webbrowser.open("https://www.slywriter.ai/pricing")
        dialog.destroy()

    upgrade_btn = tk.Button(
        button_frame,
        text="⬆️ View Plans",
        command=open_pricing,
        bg="#8b5cf6",
        fg="white",
        font=('Segoe UI', 10, 'bold'),
        relief='flat',
        padx=20,
        pady=8,
        cursor="hand2"
    )
    upgrade_btn.pack(side='left', padx=(0, 10))

    cancel_btn = tk.Button(
        button_frame,
        text="Cancel",
        command=dialog.destroy,
        bg="#e0e0e0",
        fg="#333",
        font=('Segoe UI', 10),
        relief='flat',
        padx=20,
        pady=8,
        cursor="hand2"
    )
    cancel_btn.pack(side='left')

    dialog.wait_window()

def require_premium(app, feature_name="this feature", required_plan="Pro"):
    """
    Check premium status and show upgrade dialog if not premium.
    Returns True if premium, False if not (with dialog shown).
    """
    if is_premium_user(app):
        return True

    # Show custom upgrade dialog
    show_upgrade_dialog(app, feature_name, required_plan)
    return False

def require_premium_old(app, feature_name="this feature"):
    """
    OLD VERSION - Check premium status and show upgrade message if not premium.
    Returns True if premium, False if not (with message shown).
    """
    if is_premium_user(app):
        return True

    messagebox.showinfo(
        "Premium Required",
        f"Upgrade to SlyWriter Premium to unlock {feature_name}!"
    )
    return False

def show_word_limit_dialog(app):
    """
    Show a dialog when user runs out of words, promoting referrals and upgrade options.
    Explains: Get 5 referrals = Free Premium forever!
    """
    # Check current referral count if available
    current_referrals = 0
    try:
        if hasattr(app, 'user') and app.user:
            current_referrals = app.user.get('referral_count', 0)
    except:
        current_referrals = 0

    dialog = tk.Toplevel(app)
    dialog.title("Word Limit Reached")
    dialog.geometry("450x340")
    dialog.resizable(False, False)

    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
    y = (dialog.winfo_screenheight() // 2) - (340 // 2)
    dialog.geometry(f"450x340+{x}+{y}")

    # Make it modal
    dialog.transient(app)
    dialog.grab_set()

    # Header with icon
    header_frame = tk.Frame(dialog, bg="#f5f5f5", height=70)
    header_frame.pack(fill='x')
    header_frame.pack_propagate(False)

    icon_label = tk.Label(header_frame, text="⚠️", font=('Segoe UI', 28), bg="#f5f5f5")
    icon_label.pack(pady=15)

    # Message content
    message_frame = tk.Frame(dialog, bg="white")
    message_frame.pack(fill='both', expand=True, padx=20, pady=15)

    title_label = tk.Label(
        message_frame,
        text="You've Used All Your Words This Week",
        font=('Segoe UI', 12, 'bold'),
        bg="white"
    )
    title_label.pack(pady=(0, 10))

    # Determine next referral milestone
    next_milestone = ""
    if current_referrals == 0:
        next_milestone = "Get your first referral = 1,000 bonus words!"
    elif current_referrals == 1:
        next_milestone = "1 more referral = 2,500 words total!"
    elif current_referrals == 2:
        next_milestone = "1 more referral = 1 WEEK of Pro!"
    elif current_referrals >= 3:
        next_milestone = f"You have {current_referrals} referrals! Keep going for bigger rewards!"
    else:
        next_milestone = "Refer friends to unlock amazing rewards!"

    message_text = f"""You've reached your weekly word limit.

💡 {next_milestone}

🎁 REFERRAL REWARDS:
• 1 referral = 1,000 words
• 2 referrals = 2,500 words
• 3 referrals = 1 WEEK Pro
• 5 referrals = 5,000 words
• Plus even bigger rewards for more!

⬆️ OR UPGRADE:
• Pro: 40,000 words/week
• Premium: 100,000 words/month"""

    message_label = tk.Label(
        message_frame,
        text=message_text,
        font=('Segoe UI', 9),
        bg="white",
        justify='left',
        wraplength=400
    )
    message_label.pack()

    # Buttons
    button_frame = tk.Frame(dialog, bg="white")
    button_frame.pack(fill='x', padx=20, pady=(0, 15))

    def view_referrals():
        """Navigate to Account tab and show referral info"""
        try:
            # Switch to Account tab
            if hasattr(app, 'notebook') and hasattr(app, 'tabs'):
                for tab_name, tab_frame in app.tabs.items():
                    if tab_name == 'Account':
                        app.notebook.select(tab_frame)
                        break

            # Show referral pass info dialog
            if hasattr(app, 'account_tab') and hasattr(app.account_tab, 'show_referral_pass_info'):
                app.account_tab.show_referral_pass_info()
        except Exception as e:
            print(f"Error navigating to referrals: {e}")
        finally:
            dialog.destroy()

    def view_upgrade():
        """Open pricing page"""
        webbrowser.open("https://www.slywriter.ai/pricing")
        dialog.destroy()

    # Referral button (primary action - purple)
    referral_btn = tk.Button(
        button_frame,
        text="🎁 Earn Rewards",
        command=view_referrals,
        bg="#8b5cf6",
        fg="white",
        font=('Segoe UI', 10, 'bold'),
        relief='flat',
        padx=15,
        pady=8,
        cursor="hand2"
    )
    referral_btn.pack(side='left', padx=(0, 8))

    # Upgrade button (secondary action - gray)
    upgrade_btn = tk.Button(
        button_frame,
        text="⬆️ View Plans",
        command=view_upgrade,
        bg="#6b7280",
        fg="white",
        font=('Segoe UI', 10, 'bold'),
        relief='flat',
        padx=15,
        pady=8,
        cursor="hand2"
    )
    upgrade_btn.pack(side='left', padx=(0, 8))

    # Cancel button
    cancel_btn = tk.Button(
        button_frame,
        text="Cancel",
        command=dialog.destroy,
        bg="#e0e0e0",
        fg="#333",
        font=('Segoe UI', 10),
        relief='flat',
        padx=15,
        pady=8,
        cursor="hand2"
    )
    cancel_btn.pack(side='left')

    dialog.wait_window()
