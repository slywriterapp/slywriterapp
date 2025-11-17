# mac_onboarding.py

import tkinter as tk
from tkinter import messagebox
import platform
import json
import os

CONFIG_FILE = "config.json"

def is_first_run_mac():
    """Check if this is the first run on macOS"""
    if platform.system() != 'Darwin':
        return False

    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return not config.get('settings', {}).get('mac_onboarding_completed', False)
        return True
    except:
        return True

def mark_onboarding_complete():
    """Mark Mac onboarding as completed"""
    try:
        config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)

        if 'settings' not in config:
            config['settings'] = {}

        config['settings']['mac_onboarding_completed'] = True

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error marking onboarding complete: {e}")

def show_mac_permission_dialog(parent):
    """
    Show macOS permission onboarding dialog with clear explanation.
    Returns True if user completed onboarding, False if they cancelled.
    """
    dialog = tk.Toplevel(parent)
    dialog.title("macOS Setup Required")
    dialog.geometry("550x450")
    dialog.resizable(False, False)

    # Center the dialog
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (550 // 2)
    y = (dialog.winfo_screenheight() // 2) - (450 // 2)
    dialog.geometry(f"550x450+{x}+{y}")

    # Make it modal
    dialog.transient(parent)
    dialog.grab_set()

    # Header with macOS icon
    header_frame = tk.Frame(dialog, bg="#f5f5f5", height=80)
    header_frame.pack(fill='x')
    header_frame.pack_propagate(False)

    icon_label = tk.Label(header_frame, text="🍎", font=('Segoe UI', 36), bg="#f5f5f5")
    icon_label.pack(pady=15)

    # Message content
    message_frame = tk.Frame(dialog, bg="white")
    message_frame.pack(fill='both', expand=True, padx=25, pady=20)

    title_label = tk.Label(
        message_frame,
        text="Welcome to SlyWriter!",
        font=('Segoe UI', 16, 'bold'),
        bg="white"
    )
    title_label.pack(pady=(0, 10))

    subtitle_label = tk.Label(
        message_frame,
        text="macOS Permission Setup",
        font=('Segoe UI', 12),
        fg="#666",
        bg="white"
    )
    subtitle_label.pack(pady=(0, 15))

    message_text = """SlyWriter needs Accessibility permission to simulate typing on your behalf.

🔒 WHY THIS IS SAFE:
• This is a standard macOS security feature
• SlyWriter is NOT a virus or malware
• You can revoke permission anytime in System Settings
• We only use it to type the text YOU provide

⚙️ WHAT WILL HAPPEN:
1. Click "Grant Permission" below
2. macOS will show a permission dialog
3. Click "Open System Settings"
4. Enable SlyWriter in Accessibility settings
5. Return here to start using SlyWriter

This is a ONE-TIME setup required by macOS for any app that automates typing."""

    message_label = tk.Label(
        message_frame,
        text=message_text,
        font=('Segoe UI', 10),
        bg="white",
        justify='left',
        wraplength=500
    )
    message_label.pack(pady=(0, 10))

    # Result variable
    result = {'completed': False}

    # Buttons
    button_frame = tk.Frame(dialog, bg="white")
    button_frame.pack(fill='x', padx=25, pady=(0, 20))

    def trigger_permission():
        """Trigger macOS permission dialog by simulating a test typing"""
        try:
            # Close the explanation dialog first
            dialog.destroy()

            # Show info about what's about to happen
            info_msg = messagebox.showinfo(
                "Requesting Permission",
                "SlyWriter will now test typing access.\n\n"
                "macOS will ask you to grant Accessibility permission.\n\n"
                "Please click 'Open System Settings' and enable SlyWriter."
            )

            # Import and trigger typing simulation
            import pyautogui

            # Try to type a single character to trigger permission dialog
            try:
                pyautogui.write("", interval=0.01)  # Empty string to just trigger check
            except Exception as perm_error:
                # Permission denied or not granted
                print(f"Permission test result: {perm_error}")

            # Show follow-up instructions
            followup = messagebox.showinfo(
                "Permission Setup",
                "After enabling SlyWriter in Accessibility settings:\n\n"
                "1. Quit SlyWriter completely\n"
                "2. Relaunch SlyWriter\n"
                "3. You're ready to start typing!\n\n"
                "If you didn't see the permission dialog, SlyWriter may already have access."
            )

            mark_onboarding_complete()
            result['completed'] = True

        except Exception as e:
            print(f"Error triggering permission: {e}")
            messagebox.showerror(
                "Setup Error",
                f"Could not complete permission setup.\n\n{str(e)}\n\n"
                "Please enable Accessibility permission manually in System Settings."
            )
            dialog.destroy()

    def skip_onboarding():
        """Skip onboarding (mark as complete anyway)"""
        if messagebox.askyesno(
            "Skip Setup?",
            "Are you sure you want to skip this setup?\n\n"
            "SlyWriter will NOT work without Accessibility permission.\n\n"
            "You can grant permission later in macOS System Settings."
        ):
            mark_onboarding_complete()
            result['completed'] = False
            dialog.destroy()

    # Grant permission button (primary action - purple)
    grant_btn = tk.Button(
        button_frame,
        text="🔓 Grant Permission",
        command=trigger_permission,
        bg="#8b5cf6",
        fg="white",
        font=('Segoe UI', 11, 'bold'),
        relief='flat',
        padx=20,
        pady=10,
        cursor="hand2"
    )
    grant_btn.pack(side='left', padx=(0, 10))

    # Skip button (secondary action)
    skip_btn = tk.Button(
        button_frame,
        text="Skip for Now",
        command=skip_onboarding,
        bg="#e0e0e0",
        fg="#333",
        font=('Segoe UI', 10),
        relief='flat',
        padx=20,
        pady=10,
        cursor="hand2"
    )
    skip_btn.pack(side='left')

    dialog.wait_window()
    return result['completed']

def check_and_show_mac_onboarding(app):
    """
    Check if Mac onboarding is needed and show dialog if so.
    Call this during app startup.
    Returns True if onboarding was shown, False otherwise.
    """
    if is_first_run_mac():
        return show_mac_permission_dialog(app)
    return False
