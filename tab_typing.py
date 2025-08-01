import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import typing_engine as engine
import clipboard
from utils import Tooltip

PLACEHOLDER_INPUT   = "Type here..."
PLACEHOLDER_PREVIEW = "Preview will appear here..."

class TypingTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.paused = False
        self.build_ui()
        self.update_wpm()

    def build_ui(self):
        # ── Scrollable container ─────────────────────────
        container = ttk.Frame(self)
        container.pack(fill='both', expand=True)
        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        vsb = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        canvas.bind("<Enter>", lambda e: canvas.bind_all(
            "<MouseWheel>",
            lambda ev: canvas.yview_scroll(-int(ev.delta/120), "units")
        ))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        content = ttk.Frame(canvas)
        canvas.create_window((0,0), window=content, anchor='nw')
        content.bind("<Configure>",
                     lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        # ── Text input area ──────────────────────────────
        frame_in = ttk.Frame(content)
        frame_in.pack(fill='both', expand=True, padx=10, pady=(10,5))
        self.text_input = tk.Text(frame_in, height=10, wrap='word', font=('Segoe UI',11))
        sb_in = ttk.Scrollbar(frame_in, orient='vertical', command=self.text_input.yview)
        self.text_input.configure(yscrollcommand=sb_in.set)
        self.text_input.pack(side='left', fill='both', expand=True)
        sb_in.pack(side='right', fill='y')

        self.text_input.insert('1.0', PLACEHOLDER_INPUT)
        self.text_input.bind("<FocusIn>",  self._clear_input_placeholder)
        self.text_input.bind("<FocusOut>", self._restore_input_placeholder)

        # ── Status label ─────────────────────────────────
        self.status_label = ttk.Label(
            content, text='', foreground='#2a7ae2', font=('Segoe UI',12,'bold')
        )
        self.status_label.pack(pady=(0,5))

        # ── Live preview area ────────────────────────────
        lp_frame = ttk.Frame(content)
        lp_frame.pack(fill='both', expand=True, padx=10, pady=(0,10))
        self.live_preview = tk.Text(
            lp_frame, height=8, wrap='word',
            state='disabled', background='#e9ecef'
        )
        self.live_preview.configure(state='normal')
        self.live_preview.insert('1.0', PLACEHOLDER_PREVIEW)
        self.live_preview.configure(state='disabled')
        sb_lp = ttk.Scrollbar(lp_frame, orient='vertical', command=self.live_preview.yview)
        self.live_preview.configure(yscrollcommand=sb_lp.set)
        self.live_preview.pack(side='left', fill='both', expand=True)
        sb_lp.pack(side='right', fill='y')

        # ── Control buttons ─────────────────────────────
        ctrl = ttk.Frame(content)
        ctrl.pack(fill='x', padx=10, pady=5)
        ttk.Button(ctrl, text='Load from File', command=self.load_file).pack(side='left')
        ttk.Button(ctrl, text='Paste Clipboard', command=self.paste_clipboard).pack(side='left', padx=5)

        self.start_btn = tk.Button(ctrl, text='Start Typing', command=self.start_typing,
                                  bg='#0078d7', activebackground='#0078d7')
        self.start_btn.pack(side='left', padx=5)

        self.pause_btn = tk.Button(ctrl, text='Pause Typing', command=self.toggle_pause,
                                   bg='orange', activebackground='orange')
        self.pause_btn.pack(side='left', padx=5)

        self.stop_btn = tk.Button(ctrl, text='Panic Stop', command=self.stop_typing_hotkey,
                                  bg='red', activebackground='red')
        self.stop_btn.pack(side='right')

        # ── Settings panel ──────────────────────────────
        sf = ttk.LabelFrame(content, text="Settings", padding=(10,10))
        sf.pack(fill='x', padx=10, pady=10)
        sf.columnconfigure(1, weight=1)

        # WPM readout
        ttk.Label(sf, text="Est. Speed (WPM):", font=('Segoe UI',11))\
            .grid(row=0, column=0, sticky='w')
        self.wpm_var = tk.IntVar(value=0)
        ttk.Label(sf, textvariable=self.wpm_var, font=('Segoe UI',11,'bold'))\
            .grid(row=0, column=1, sticky='w')

        # Min delay
        ttk.Label(sf, text="Min delay (sec):", font=('Segoe UI',11))\
            .grid(row=1, column=0, sticky='w')
        self.min_delay_var = tk.DoubleVar(value=self.app.cfg['settings']['min_delay'])
        self.min_delay_var.trace_add('write',
            lambda *a: [self.app.on_setting_change(), self.update_wpm()]
        )
        ttk.Scale(sf, from_=0.01, to=0.3, variable=self.min_delay_var)\
            .grid(row=1, column=1, sticky='ew', pady=3)

        # Max delay
        ttk.Label(sf, text="Max delay (sec):", font=('Segoe UI',11))\
            .grid(row=2, column=0, sticky='w')
        self.max_delay_var = tk.DoubleVar(value=self.app.cfg['settings']['max_delay'])
        self.max_delay_var.trace_add('write',
            lambda *a: [self.app.on_setting_change(), self.update_wpm()]
        )
        ttk.Scale(sf, from_=0.05, to=0.5, variable=self.max_delay_var)\
            .grid(row=2, column=1, sticky='ew', pady=3)

        # Enable typos
        self.typos_var = tk.BooleanVar(value=self.app.cfg['settings']['typos_on'])
        self.typos_var.trace_add('write', lambda *a: self.app.on_setting_change())
        ttk.Checkbutton(sf, text="Enable typos", variable=self.typos_var)\
            .grid(row=3, column=0, columnspan=2, sticky='w', pady=3)

        # Pause frequency
        ttk.Label(sf, text="Pause every X chars:", font=('Segoe UI',11))\
            .grid(row=4, column=0, sticky='w')
        self.pause_freq_var = tk.IntVar(value=self.app.cfg['settings']['pause_freq'])
        self.pause_freq_var.trace_add('write', lambda *a: self.app.on_setting_change())
        ttk.Scale(sf, from_=10, to=200, variable=self.pause_freq_var)\
            .grid(row=4, column=1, sticky='ew', pady=3)

        # Paste & Go URL
        ttk.Label(sf, text="Paste & Go URL:", font=('Segoe UI',11))\
            .grid(row=5, column=0, sticky='w')
        self.paste_go_var = tk.StringVar(value=self.app.cfg['settings'].get('paste_go_url',''))
        self.paste_go_var.trace_add('write', lambda *a: self.app.on_setting_change())
        ttk.Entry(sf, textvariable=self.paste_go_var)\
            .grid(row=5, column=1, sticky='ew', pady=3)

        # Auto-capitalize
        self.autocap_var = tk.BooleanVar(value=self.app.cfg['settings'].get('autocap', False))
        self.autocap_var.trace_add('write', lambda *a: self.app.on_setting_change())
        ttk.Checkbutton(sf, text="Auto-capitalize sentences", variable=self.autocap_var)\
            .grid(row=6, column=0, columnspan=2, sticky='w', pady=3)

        # Reset button
        ttk.Button(sf, text="Reset to Defaults", command=self.app.reset_typing_settings)\
            .grid(row=7, column=0, columnspan=2, pady=8)

    def toggle_pause(self):
        """Toggle pause and resume typing."""
        if self.paused:
            engine.resume_typing()
            self.pause_btn.config(text='Pause Typing')
            self.paused = False
            self.update_status('Resumed typing...')
        else:
            engine.pause_typing()
            self.pause_btn.config(text='Resume Typing')
            self.paused = True
            self.update_status('Paused typing!')

    def _clear_input_placeholder(self, event):
        if self.text_input.get('1.0','end').strip() == PLACEHOLDER_INPUT:
            self.text_input.delete('1.0','end')

    def _restore_input_placeholder(self, event):
        if not self.text_input.get('1.0','end').strip():
            self.text_input.insert('1.0', PLACEHOLDER_INPUT)

    def update_wpm(self):
        avg_char = (self.min_delay_var.get() + self.max_delay_var.get()) / 2
        wpm = int((1 / avg_char) * 60 / 5) if avg_char > 0 else 0
        self.wpm_var.set(wpm)

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[('Text files','*.txt')])
        if not path:
            return
        with open(path,'r',encoding='utf-8') as f:
            txt = f.read()
        self.text_input.delete('1.0','end')
        self.text_input.insert('1.0', txt)

    def paste_clipboard(self):
        txt = clipboard.paste()
        self.text_input.delete('1.0','end')
        self.text_input.insert('1.0', txt)

    def start_typing(self):
        txt = self.text_input.get('1.0','end').strip()

        # Clipboard fallback restored
        if (not txt or txt == PLACEHOLDER_INPUT):
            txt = clipboard.paste().strip()

        if not txt:
            return messagebox.showwarning('No Text','Enter text or have something on clipboard.')

        engine.start_typing_from_input(
            txt,
            live_preview_callback=self.update_live_preview,
            status_callback=self.update_status,
            min_delay=self.min_delay_var.get(),
            max_delay=self.max_delay_var.get(),
            typos_on=self.typos_var.get(),
            pause_freq=self.pause_freq_var.get(),
            paste_and_go_url=self.paste_go_var.get(),
            autocap_enabled=self.autocap_var.get()
        )
        self.start_btn.config(bg='#0078d7')
        self.stop_btn.config(bg='red')

    def stop_typing_hotkey(self):
        engine.stop_typing_func()
        self.update_status('Typing stopped!')
        self.start_btn.config(bg='#0078d7')
        self.stop_btn.config(bg='red')

    def update_live_preview(self, text):
        self.live_preview.configure(state='normal')
        self.live_preview.delete('1.0','end')
        self.live_preview.insert('end', text)
        self.live_preview.see('end')
        self.live_preview.configure(state='disabled')

    def update_status(self, text):
        self.status_label.config(text=text)
