"""
Terms of Service and Privacy Policy Acceptance Dialog

This dialog MUST be accepted before the user can use the application.
It forces the user to scroll through the entire document before accepting.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import os

class TermsDialog:
    """Scrollable Terms and Privacy Policy acceptance dialog"""

    def __init__(self, parent=None):
        self.accepted = False
        self.root = tb.Toplevel() if parent else tb.Window(themename="flatly")

        # Configure window
        self.root.title("SlyWriter - Terms of Service & Privacy Policy")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Make it modal and always on top
        if parent:
            self.root.transient(parent)
        self.root.grab_set()

        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        # Prevent closing without accepting
        self.root.protocol("WM_DELETE_WINDOW", self._on_decline)

        self._create_ui()

    def _create_ui(self):
        """Create the UI components"""

        # Main container
        main_frame = tb.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)

        # Header
        header_frame = tb.Frame(main_frame)
        header_frame.pack(fill=X, pady=(0, 15))

        title_label = tb.Label(
            header_frame,
            text="⚖️ Legal Agreement Required",
            font=("Segoe UI", 18, "bold"),
            bootstyle="danger"
        )
        title_label.pack()

        subtitle_label = tb.Label(
            header_frame,
            text="You must read and accept these terms before using SlyWriter",
            font=("Segoe UI", 10),
            bootstyle="secondary"
        )
        subtitle_label.pack(pady=(5, 0))

        # Important warning box
        warning_frame = tb.Frame(main_frame, bootstyle="danger")
        warning_frame.pack(fill=X, pady=(0, 15))

        warning_label = tb.Label(
            warning_frame,
            text="⚠️ IMPORTANT: This software can be misused. Read carefully to understand your responsibilities and our limitations of liability.",
            font=("Segoe UI", 10, "bold"),
            wraplength=850,
            bootstyle="inverse-danger",
            padding=15
        )
        warning_label.pack(fill=X)

        # Tabbed interface for Terms and Privacy Policy
        tab_notebook = tb.Notebook(main_frame, bootstyle="dark")
        tab_notebook.pack(fill=BOTH, expand=YES, pady=(0, 15))

        # Terms of Service Tab
        terms_frame = tb.Frame(tab_notebook)
        tab_notebook.add(terms_frame, text="📜 Terms of Service")

        # Privacy Policy Tab
        privacy_frame = tb.Frame(tab_notebook)
        tab_notebook.add(privacy_frame, text="🔒 Privacy Policy")

        # Load and display Terms of Service
        self.terms_text = self._create_scrolled_text(terms_frame)
        self._load_terms_content(self.terms_text)

        # Load and display Privacy Policy
        self.privacy_text = self._create_scrolled_text(privacy_frame)
        self._load_privacy_content(self.privacy_text)

        # Track which tabs have been scrolled to bottom
        self.terms_scrolled = False
        self.privacy_scrolled = False

        # Bind scroll events
        self.terms_text.bind('<MouseWheel>', lambda e: self._on_scroll(e, 'terms'))
        self.privacy_text.bind('<Button-4>', lambda e: self._on_scroll(e, 'terms'))
        self.privacy_text.bind('<Button-5>', lambda e: self._on_scroll(e, 'terms'))

        self.privacy_text.bind('<MouseWheel>', lambda e: self._on_scroll(e, 'privacy'))
        self.privacy_text.bind('<Button-4>', lambda e: self._on_scroll(e, 'privacy'))
        self.privacy_text.bind('<Button-5>', lambda e: self._on_scroll(e, 'privacy'))

        # Scroll instruction
        scroll_label = tb.Label(
            main_frame,
            text="📖 Please scroll to the bottom of BOTH tabs to enable the Accept button",
            font=("Segoe UI", 10, "bold"),
            bootstyle="warning",
            padding=10
        )
        scroll_label.pack(fill=X, pady=(0, 10))

        # Checkboxes for explicit consent
        self.checkbox_frame = tb.Frame(main_frame)
        self.checkbox_frame.pack(fill=X, pady=(0, 15))

        self.consent_var1 = tk.BooleanVar(value=False)
        self.consent_var2 = tk.BooleanVar(value=False)
        self.consent_var3 = tk.BooleanVar(value=False)

        cb1 = tb.Checkbutton(
            self.checkbox_frame,
            text="✓ I have read and understand the Terms of Service",
            variable=self.consent_var1,
            bootstyle="danger-round-toggle",
            command=self._check_enable_accept
        )
        cb1.pack(anchor=W, pady=2)

        cb2 = tb.Checkbutton(
            self.checkbox_frame,
            text="✓ I have read and understand the Privacy Policy",
            variable=self.consent_var2,
            bootstyle="danger-round-toggle",
            command=self._check_enable_accept
        )
        cb2.pack(anchor=W, pady=2)

        cb3 = tb.Checkbutton(
            self.checkbox_frame,
            text="✓ I agree to use this software only for lawful purposes and accept all risks",
            variable=self.consent_var3,
            bootstyle="danger-round-toggle",
            command=self._check_enable_accept
        )
        cb3.pack(anchor=W, pady=2)

        # Button frame
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X)

        self.decline_btn = tb.Button(
            button_frame,
            text="✖ Decline and Exit",
            command=self._on_decline,
            bootstyle="danger",
            width=20
        )
        self.decline_btn.pack(side=LEFT, padx=(0, 10))

        self.accept_btn = tb.Button(
            button_frame,
            text="✓ I Accept - Continue to App",
            command=self._on_accept,
            bootstyle="success",
            width=25,
            state=DISABLED  # Disabled until scrolled and checked
        )
        self.accept_btn.pack(side=RIGHT)

    def _create_scrolled_text(self, parent):
        """Create a scrolled text widget"""
        text_frame = tb.Frame(parent)
        text_frame.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        # Create text widget with scrollbar
        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            relief=SUNKEN,
            borderwidth=2,
            padx=15,
            pady=15
        )

        scrollbar = tb.Scrollbar(text_frame, command=text_widget.yview, bootstyle="round")
        text_widget.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=RIGHT, fill=Y)
        text_widget.pack(side=LEFT, fill=BOTH, expand=YES)

        # Configure text tags for formatting
        text_widget.tag_configure("heading", font=("Segoe UI", 14, "bold"), spacing1=10, spacing3=5)
        text_widget.tag_configure("subheading", font=("Segoe UI", 11, "bold"), spacing1=8, spacing3=3)
        text_widget.tag_configure("bold", font=("Consolas", 9, "bold"))
        text_widget.tag_configure("warning", foreground="#dc3545", font=("Consolas", 9, "bold"))

        return text_widget

    def _load_terms_content(self, text_widget):
        """Load Terms of Service from file"""
        try:
            terms_path = os.path.join(os.path.dirname(__file__), "TERMS_OF_SERVICE.md")
            with open(terms_path, 'r', encoding='utf-8') as f:
                content = f.read()

            text_widget.insert('1.0', content)
            text_widget.configure(state=DISABLED)  # Make read-only

        except Exception as e:
            text_widget.insert('1.0', f"ERROR: Could not load Terms of Service.\n\n{str(e)}")
            text_widget.configure(state=DISABLED)

    def _load_privacy_content(self, text_widget):
        """Load Privacy Policy from file"""
        try:
            privacy_path = os.path.join(os.path.dirname(__file__), "PRIVACY_POLICY.md")
            with open(privacy_path, 'r', encoding='utf-8') as f:
                content = f.read()

            text_widget.insert('1.0', content)
            text_widget.configure(state=DISABLED)  # Make read-only

        except Exception as e:
            text_widget.insert('1.0', f"ERROR: Could not load Privacy Policy.\n\n{str(e)}")
            text_widget.configure(state=DISABLED)

    def _on_scroll(self, event, tab_name):
        """Check if user has scrolled to the bottom"""
        if tab_name == 'terms':
            text_widget = self.terms_text
        else:
            text_widget = self.privacy_text

        # Check if scrolled to bottom (within 5 pixels)
        yview = text_widget.yview()
        if yview[1] >= 0.95:  # 95% or more scrolled
            if tab_name == 'terms':
                self.terms_scrolled = True
            else:
                self.privacy_scrolled = True

            self._check_enable_accept()

    def _check_enable_accept(self):
        """Enable accept button only if all conditions are met"""
        all_scrolled = self.terms_scrolled and self.privacy_scrolled
        all_checked = (
            self.consent_var1.get() and
            self.consent_var2.get() and
            self.consent_var3.get()
        )

        if all_scrolled and all_checked:
            self.accept_btn.configure(state=NORMAL)
        else:
            self.accept_btn.configure(state=DISABLED)

    def _on_accept(self):
        """Handle accept button click"""
        self.accepted = True
        self.root.destroy()

    def _on_decline(self):
        """Handle decline button click"""
        self.accepted = False
        self.root.destroy()

    def show(self):
        """Show the dialog and wait for response"""
        self.root.wait_window()
        return self.accepted


def show_terms_dialog(parent=None):
    """
    Show terms acceptance dialog.
    Returns True if accepted, False if declined.
    """
    dialog = TermsDialog(parent)
    return dialog.show()


def check_terms_acceptance():
    """
    Check if user has accepted terms in config.
    Returns True if already accepted, False otherwise.
    """
    from sly_config import load_config

    cfg = load_config()
    return cfg.get("legal", {}).get("terms_accepted", False)


def save_terms_acceptance():
    """Save terms acceptance to config"""
    from sly_config import load_config, save_config

    cfg = load_config()
    if "legal" not in cfg:
        cfg["legal"] = {}

    cfg["legal"]["terms_accepted"] = True
    cfg["legal"]["terms_accepted_version"] = "1.0"  # Version tracking
    cfg["legal"]["terms_accepted_date"] = __import__('datetime').datetime.now().isoformat()

    save_config(cfg)


if __name__ == "__main__":
    # Test the dialog
    root = tb.Window(themename="flatly")
    root.withdraw()

    accepted = show_terms_dialog(root)

    if accepted:
        print("✓ Terms accepted")
        save_terms_acceptance()
    else:
        print("✖ Terms declined")

    root.destroy()
