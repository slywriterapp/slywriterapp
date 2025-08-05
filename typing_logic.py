import config
import clipboard
from tkinter import filedialog, messagebox
import typing_engine as engine

# Import premium typing logic (you’ll need to create this module!)
try:
    from premium_typing import premium_type_with_filler
except ImportError:
    # If not yet created, define a dummy fallback
    def premium_type_with_filler(*args, **kwargs):
        messagebox.showinfo("Premium Typing", "Premium typing module not found.")

# how long each pause lasts (secs), for WPM calculation
PAUSE_DURATION = 0.5

def toggle_pause(tab):
    if tab.paused:
        engine.resume_typing()
        tab.pause_btn.config(text='Pause Typing')
        tab.paused = False
        update_status(tab, 'Resumed typing...')
    else:
        engine.pause_typing()
        tab.pause_btn.config(text='Resume Typing')
        tab.paused = True
        update_status(tab, 'Paused typing!')

def clear_input_placeholder(tab, event=None):
    if tab.text_input.get('1.0', 'end').strip() == tab.PLACEHOLDER_INPUT:
        tab.text_input.delete('1.0', 'end')
        tab.text_input.tag_remove("placeholder", "1.0", "end")
        tab.text_input.config(fg=tab._get_entry_fg())

def restore_input_placeholder(tab, event=None):
    if not tab.text_input.get('1.0', 'end').strip():
        tab.text_input.insert('1.0', tab.PLACEHOLDER_INPUT)
        tab.text_input.tag_add("placeholder", "1.0", "end")
        tab.text_input.config(fg=tab._get_placeholder_fg())

def update_wpm(tab):
    # Base per-character average
    avg_char   = (tab.min_delay_var.get() + tab.max_delay_var.get()) / 2
    # Add rough pause penalty
    pause_freq = tab.pause_freq_var.get()
    extra      = (PAUSE_DURATION / pause_freq) if pause_freq > 0 else 0
    effective  = avg_char + extra
    wpm        = int((1 / effective) * 60 / 5) if effective > 0 else 0

    tab.wpm_var.set(f"WPM: {wpm}")

    # Update label background/foreground
    dark = tab.app.cfg['settings'].get('dark_mode', False)
    bg   = config.DARK_BG if dark else config.LIGHT_BG
    tab.wpm_label.config(bg=bg, fg=config.LIME_GREEN)

def load_file(tab):
    path = filedialog.askopenfilename(filetypes=[('Text files', '*.txt')])
    if not path:
        return
    with open(path, 'r', encoding='utf-8') as f:
        txt = f.read()
    tab.text_input.delete('1.0', 'end')
    tab.text_input.insert('1.0', txt)
    tab.text_input.tag_remove("placeholder", "1.0", "end")
    tab.text_input.config(fg=tab._get_entry_fg())

def paste_clipboard(tab):
    txt = clipboard.paste()
    tab.text_input.delete('1.0', 'end')
    tab.text_input.insert('1.0', txt)
    tab.text_input.tag_remove("placeholder", "1.0", "end")
    tab.text_input.config(fg=tab._get_entry_fg())

def start_typing(tab, use_adv_antidetect=False):
    txt = tab.text_input.get('1.0', 'end').strip()
    if not txt or txt == tab.PLACEHOLDER_INPUT:
        txt = clipboard.paste().strip()
    if not txt:
        return messagebox.showwarning('No Text', 'Enter text or have something on clipboard.')

    # --- Anti-detection toggle (premium only) ---
    is_premium = hasattr(tab.app, 'account_tab') and tab.app.account_tab.is_premium()
    if use_adv_antidetect and is_premium:
        # Use premium logic with advanced anti-detection
        premium_type_with_filler(
            txt,
            live_preview_callback=lambda t: update_live_preview(tab, t),
            status_callback=lambda s: update_status(tab, s),
            min_delay=tab.min_delay_var.get(),
            max_delay=tab.max_delay_var.get(),
            typos_on=tab.typos_var.get(),
            pause_freq=tab.pause_freq_var.get(),
            paste_and_go_url=tab.paste_go_var.get(),
            autocap_enabled=tab.autocap_var.get()
        )
    else:
        # Use standard typing engine
        engine.start_typing_from_input(
            txt,
            live_preview_callback=lambda t: update_live_preview(tab, t),
            status_callback=lambda s: update_status(tab, s),
            min_delay=tab.min_delay_var.get(),
            max_delay=tab.max_delay_var.get(),
            typos_on=tab.typos_var.get(),
            pause_freq=tab.pause_freq_var.get(),
            paste_and_go_url=tab.paste_go_var.get(),
            autocap_enabled=tab.autocap_var.get()
        )
    tab.start_btn.config(bg='#0078d7')
    tab.stop_btn.config(bg='red')

def stop_typing_hotkey(tab):
    engine.stop_typing_func()
    update_status(tab, 'Typing stopped!')
    tab.start_btn.config(bg='#0078d7')
    tab.stop_btn.config(bg='red')

def update_live_preview(tab, text):
    entry_fg = tab._get_entry_fg()
    tab.live_preview.configure(state='normal')
    tab.live_preview.delete('1.0', 'end')
    if not text.strip():
        tab.live_preview.insert('1.0', tab.PLACEHOLDER_PREVIEW)
        tab.live_preview.tag_add("placeholder", "1.0", "end")
        tab.live_preview.config(fg=tab._get_placeholder_fg())
    else:
        tab.live_preview.insert('end', text)
        tab.live_preview.config(fg=entry_fg)
    tab.live_preview.see('end')
    tab.live_preview.configure(state='disabled')

def update_status(tab, text):
    tab.status_label.config(text=text)

def setup_traces(tab):
    # Whenever any slider or checkbox changes, persist + recalc WPM
    tab.min_delay_var.trace_add('write', lambda *a: [tab.app.on_setting_change(), update_wpm(tab)])
    tab.max_delay_var.trace_add('write', lambda *a: [tab.app.on_setting_change(), update_wpm(tab)])
    tab.typos_var.trace_add('write', lambda *a: tab.app.on_setting_change())
    tab.pause_freq_var.trace_add('write', lambda *a: [tab.app.on_setting_change(), update_wpm(tab)])
    tab.paste_go_var.trace_add('write', lambda *a: tab.app.on_setting_change())
    tab.autocap_var.trace_add('write', lambda *a: tab.app.on_setting_change())
