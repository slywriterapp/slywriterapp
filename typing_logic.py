import config
import clipboard
from tkinter import filedialog, messagebox
import typing_engine as engine
from utils import is_premium_user

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
        # Update overlay
        if hasattr(tab.app, 'overlay_tab') and tab.app.overlay_tab:
            tab.app.overlay_tab.update_overlay_text('Resumed typing...')
    else:
        engine.pause_typing()
        tab.pause_btn.config(text='Resume Typing')
        tab.paused = True
        update_status(tab, 'Paused typing!')
        # Update overlay
        if hasattr(tab.app, 'overlay_tab') and tab.app.overlay_tab:
            tab.app.overlay_tab.update_overlay_text('Paused')

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

    # Update label background/foreground with modern colors and enhanced styling
    dark = tab.app.cfg['settings'].get('dark_mode', False)
    bg   = config.DARK_BG if dark else config.LIGHT_BG
    tab.wpm_label.config(
        bg=bg, 
        fg=config.SUCCESS_GREEN, 
        font=(config.FONT_PRIMARY, config.FONT_SIZE_LG, 'bold'),
        padx=config.SPACING_BASE,
        pady=config.SPACING_XS
    )

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

def start_typing(tab, use_adv_antidetect=False, preview_only=False):
    txt = tab.text_input.get('1.0', 'end').strip()
    if not txt or txt == tab.PLACEHOLDER_INPUT:
        txt = clipboard.paste().strip()
    if not txt:
        return messagebox.showwarning('No Text', 'Enter text or have something on clipboard.')

    # --- Anti-detection toggle (premium only) ---
    is_premium = is_premium_user(tab.app)
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
            preview_only=preview_only,
            stop_flag=engine._stop_flag,
            pause_flag=engine._pause_flag
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
            preview_only=preview_only
        )
    tab.start_btn.config(bg='#003366')
    tab.stop_btn.config(bg='red')

def stop_typing_hotkey(tab):
    engine.stop_typing_func()
    update_status(tab, 'Typing stopped!')
    # Update overlay
    if hasattr(tab.app, 'overlay_tab') and tab.app.overlay_tab:
        tab.app.overlay_tab.update_overlay_text('Stopped')
    tab.start_btn.config(bg='#003366')
    tab.stop_btn.config(bg='red')

def update_live_preview(tab, text):
    entry_fg = tab._get_entry_fg()
    tab.live_preview.configure(state='normal')
    
    # Get current content to avoid unnecessary full replacement
    current_content = tab.live_preview.get('1.0', 'end-1c')
    
    if not text.strip():
        if current_content != tab.PLACEHOLDER_PREVIEW:
            tab.live_preview.delete('1.0', 'end')
            tab.live_preview.insert('1.0', tab.PLACEHOLDER_PREVIEW)
            tab.live_preview.tag_add("placeholder", "1.0", "end")
            tab.live_preview.config(fg=tab._get_placeholder_fg())
    else:
        # Only update if content actually changed
        if current_content != text:
            # For incremental updates during typing, append only new characters
            if text.startswith(current_content) and len(text) > len(current_content):
                # Append new characters only
                new_chars = text[len(current_content):]
                tab.live_preview.insert('end', new_chars)
            else:
                # Full replacement needed
                tab.live_preview.delete('1.0', 'end')
                tab.live_preview.insert('end', text)
            tab.live_preview.config(fg=entry_fg)
        
    # Only scroll to end if we're near the end already (avoid fighting user scrolling)
    if tab.live_preview.yview()[1] > 0.9:
        tab.live_preview.see('end')
    
    tab.live_preview.configure(state='disabled')

def update_status(tab, text):
    tab.status_label.config(text=text)
    
    # Update overlay with status
    if hasattr(tab.app, 'overlay_tab') and tab.app.overlay_tab:
        tab.app.overlay_tab.update_overlay_text(text)
    
    # Unlock profile selector when typing is done/cancelled/stopped
    if text in ["Done", "Stopped", "Cancelled"]:
        tab.app.prof_box.configure(state='readonly')

def setup_traces(tab):
    # Whenever any slider or checkbox changes, persist + recalc WPM
    tab.min_delay_var.trace_add('write', lambda *a: [tab.app.on_setting_change(), update_wpm(tab)])
    tab.max_delay_var.trace_add('write', lambda *a: [tab.app.on_setting_change(), update_wpm(tab)])
    tab.typos_var.trace_add('write', lambda *a: tab.app.on_setting_change())
    tab.pause_freq_var.trace_add('write', lambda *a: [tab.app.on_setting_change(), update_wpm(tab)])
