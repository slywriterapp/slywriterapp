import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import config
from config import LIME_GREEN
import typing_logic
from modern_components import ModernCard, ModernTextArea, ModernPanel, ModernProgressBar
from utils import Tooltip

PLACEHOLDER_INPUT = "Type here..."
PLACEHOLDER_PREVIEW = "Preview will appear here..."

def build_typing_ui(tab):
    # --- Control variables MUST be attached to tab *before* this function is called! ---
    # (Do NOT create them here.)

    tab.text_widgets = []
    tab.widgets_to_style = []

    # --- Top-level container for theme switching ---
    tab.container = tk.Frame(tab)
    tab.container.pack(fill='both', expand=True)

    # Scrollable canvas area
    tab.canvas = tk.Canvas(tab.container, borderwidth=0, highlightthickness=0)
    tab.vsb = ttk.Scrollbar(tab.container, orient='vertical', command=tab.canvas.yview)
    tab.canvas.configure(yscrollcommand=tab.vsb.set)
    tab.vsb.pack(side='right', fill='y')
    tab.canvas.pack(side='left', fill='both', expand=True)

    tab.canvas.bind("<Enter>", lambda e: tab.canvas.bind_all(
        "<MouseWheel>", lambda ev: tab.canvas.yview_scroll(-int(ev.delta / 120), "units")
    ))
    tab.canvas.bind("<Leave>", lambda e: tab.canvas.unbind_all("<MouseWheel>"))

    tab.content = tk.Frame(tab.canvas)
    tab.canvas.create_window((0, 0), window=tab.content, anchor='nw')
    tab.content.bind("<Configure>", lambda e: tab.canvas.configure(scrollregion=tab.canvas.bbox('all')))

    # ─── Input box with placeholder ─────────────────────────
    tab.frame_in = tk.Frame(tab.content)
    tab.frame_in.pack(fill='both', expand=True, padx=10, pady=(10, 5))

    tab.text_input = tk.Text(tab.frame_in, height=10, wrap='word', font=('Segoe UI', 11))
    tab.sb_in = ttk.Scrollbar(tab.frame_in, orient='vertical', command=tab.text_input.yview)
    tab.text_input.configure(yscrollcommand=tab.sb_in.set)
    tab.text_input.pack(side='left', fill='both', expand=True)
    tab.sb_in.pack(side='right', fill='y')

    tab.text_input.insert('1.0', PLACEHOLDER_INPUT)
    tab.text_input.tag_add("placeholder", "1.0", "end")
    tab.text_input.bind("<FocusIn>", lambda e: typing_logic.clear_input_placeholder(tab, e))
    tab.text_input.bind("<FocusOut>", lambda e: typing_logic.restore_input_placeholder(tab, e))
    # Enable undo/redo functionality
    tab.text_input.config(undo=True, maxundo=20)
    tab.text_input.bind("<Control-z>", lambda e: tab._handle_undo(e))
    tab.text_input.bind("<Control-y>", lambda e: tab._handle_redo(e))
    tab.text_widgets.append(tab.text_input)

    # ─── Status & live preview ──────────────────────────────
    tab.status_label = tk.Label(
        tab.content, text='', font=('Segoe UI', 12, 'bold')
    )
    tab.status_label.pack(pady=(0, 5))
    tab.widgets_to_style.append(tab.status_label)

    tab.lp_frame = tk.Frame(tab.content)
    tab.lp_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

    tab.live_preview = tk.Text(tab.lp_frame, height=8, wrap='word', state='disabled')
    tab.sb_lp = ttk.Scrollbar(tab.lp_frame, orient='vertical', command=tab.live_preview.yview)
    tab.live_preview.configure(yscrollcommand=tab.sb_lp.set)
    tab.live_preview.pack(side='left', fill='both', expand=True)
    tab.sb_lp.pack(side='right', fill='y')

    tab.live_preview.configure(state='normal')
    tab.live_preview.insert('1.0', PLACEHOLDER_PREVIEW)
    tab.live_preview.tag_add("placeholder", "1.0", "end")
    tab.live_preview.configure(state='disabled')
    tab.text_widgets.append(tab.live_preview)

    # ─── Controls ────────────────────────────────────────────
    tab.ctrl = tk.Frame(tab.content)
    tab.ctrl.pack(fill='x', padx=10, pady=5)
    ttk.Button(tab.ctrl, text='Load from File', command=tab.load_file).pack(side='left')
    ttk.Button(tab.ctrl, text='Paste Clipboard', command=tab.paste_clipboard).pack(side='left', padx=5)
    ttk.Button(tab.ctrl, text='Clear All', command=tab.clear_text_areas).pack(side='left', padx=5)

    # Modern buttons will be created by the theme system
    # Just create placeholders that will be replaced by ModernButton
    tab.start_btn = None
    tab.pause_btn = None  
    tab.stop_btn = None

    # ─── Settings panel ──────────────────────────────────────
    tab.sf = tk.LabelFrame(tab.content, text="Settings", padx=10, pady=10, font=('Segoe UI', 11, 'bold'))
    tab.sf.pack(fill='x', padx=10, pady=10)
    tab.sf.columnconfigure(1, weight=1)

    tab.wpm_var   = tk.StringVar(value="WPM: 0")
    tab.wpm_label = tk.Label(tab.sf, textvariable=tab.wpm_var, font=('Segoe UI', 11, 'bold'), fg=config.SUCCESS_GREEN)
    tab.wpm_label.grid(row=0, column=1, sticky='w')
    tab.widgets_to_style.append(tab.wpm_label)
    
    # Add Find Your WPM button
    tab.find_wpm_btn = tk.Button(tab.sf, text="📊 Find Your WPM", 
                                command=tab.show_wpm_test,
                                font=('Segoe UI', 9), 
                                cursor='hand2',
                                padx=8, pady=2)
    tab.find_wpm_btn.grid(row=0, column=2, sticky='w', padx=(10, 0))
    tab.widgets_to_style.append(tab.find_wpm_btn)

    # Min delay with tooltip
    min_delay_label = tk.Label(tab.sf, text="Min delay (sec):", font=('Segoe UI', 11))
    min_delay_label.grid(row=1, column=0, sticky='w')
    tab.min_delay_scale = ttk.Scale(tab.sf, from_=0.01, to=0.3, variable=tab.min_delay_var)
    tab.min_delay_scale.grid(row=1, column=1, sticky='ew', pady=3)
    Tooltip(min_delay_label, "Minimum time between keystrokes - lower = faster typing")

    # Max delay with tooltip
    max_delay_label = tk.Label(tab.sf, text="Max delay (sec):", font=('Segoe UI', 11))
    max_delay_label.grid(row=2, column=0, sticky='w')
    tab.max_delay_scale = ttk.Scale(tab.sf, from_=0.05, to=0.5, variable=tab.max_delay_var)
    tab.max_delay_scale.grid(row=2, column=1, sticky='ew', pady=3)
    Tooltip(max_delay_label, "Maximum time between keystrokes - creates natural typing rhythm variation")

    # Typos with tooltip
    tab.typos_check = ttk.Checkbutton(tab.sf, text="Enable typos", variable=tab.typos_var)
    tab.typos_check.grid(row=3, column=0, columnspan=2, sticky='w', pady=3)
    Tooltip(tab.typos_check, "Randomly makes typing mistakes then corrects them automatically for human-like behavior")

    # Pause freq with tooltip
    pause_freq_label = tk.Label(tab.sf, text="Pause every X chars:", font=('Segoe UI', 11))
    pause_freq_label.grid(row=4, column=0, sticky='w')
    tab.pause_freq_scale = ttk.Scale(tab.sf, from_=10, to=200, variable=tab.pause_freq_var)
    tab.pause_freq_scale.grid(row=4, column=1, sticky='ew', pady=3)
    Tooltip(pause_freq_label, "How many characters to type before taking a brief pause - lower = more frequent pauses")

    # Reset button with tooltip
    tab.reset_btn = ttk.Button(tab.sf, text="Reset to Defaults", command=tab.app.reset_typing_settings)
    tab.reset_btn.grid(row=5, column=0, columnspan=2, pady=8)
    Tooltip(tab.reset_btn, "Reset all typing settings to their default values")
