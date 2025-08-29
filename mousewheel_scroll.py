# mousewheel_scroll.py - Mousewheel scrolling utilities

import tkinter as tk
from tkinter import ttk

def bind_mousewheel_to_canvas(canvas):
    """Bind mousewheel scrolling to a canvas"""
    def _on_mousewheel(event):
        try:
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except:
            # Handle different systems
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
    
    def _bind_to_mousewheel(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        # Linux
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)
    
    def _unbind_from_mousewheel(event):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")
    
    # Bind when mouse enters the canvas area
    canvas.bind('<Enter>', _bind_to_mousewheel)
    canvas.bind('<Leave>', _unbind_from_mousewheel)

def bind_mousewheel_to_text(text_widget):
    """Bind mousewheel scrolling to a text widget"""
    def _on_mousewheel(event):
        try:
            text_widget.yview_scroll(int(-1*(event.delta/120)), "units")
        except:
            # Handle different systems
            if event.num == 4:
                text_widget.yview_scroll(-1, "units")
            elif event.num == 5:
                text_widget.yview_scroll(1, "units")
    
    def _bind_to_mousewheel(event):
        text_widget.bind_all("<MouseWheel>", _on_mousewheel)
        # Linux
        text_widget.bind_all("<Button-4>", _on_mousewheel)
        text_widget.bind_all("<Button-5>", _on_mousewheel)
    
    def _unbind_from_mousewheel(event):
        text_widget.unbind_all("<MouseWheel>")
        text_widget.unbind_all("<Button-4>")
        text_widget.unbind_all("<Button-5>")
    
    # Bind when mouse enters the text widget
    text_widget.bind('<Enter>', _bind_to_mousewheel)
    text_widget.bind('<Leave>', _unbind_from_mousewheel)

def bind_mousewheel_to_listbox(listbox):
    """Bind mousewheel scrolling to a listbox widget"""
    def _on_mousewheel(event):
        try:
            listbox.yview_scroll(int(-1*(event.delta/120)), "units")
        except:
            # Handle different systems
            if event.num == 4:
                listbox.yview_scroll(-1, "units")
            elif event.num == 5:
                listbox.yview_scroll(1, "units")
    
    def _bind_to_mousewheel(event):
        listbox.bind_all("<MouseWheel>", _on_mousewheel)
        # Linux
        listbox.bind_all("<Button-4>", _on_mousewheel)
        listbox.bind_all("<Button-5>", _on_mousewheel)
    
    def _unbind_from_mousewheel(event):
        listbox.unbind_all("<MouseWheel>")
        listbox.unbind_all("<Button-4>")
        listbox.unbind_all("<Button-5>")
    
    # Bind when mouse enters the listbox
    listbox.bind('<Enter>', _bind_to_mousewheel)
    listbox.bind('<Leave>', _unbind_from_mousewheel)

def add_mousewheel_to_widget(widget):
    """Auto-detect widget type and add appropriate mousewheel scrolling"""
    if isinstance(widget, tk.Canvas):
        bind_mousewheel_to_canvas(widget)
    elif isinstance(widget, tk.Text):
        bind_mousewheel_to_text(widget)
    elif isinstance(widget, tk.Listbox):
        bind_mousewheel_to_listbox(widget)
    else:
        # Try to find canvas, text, or listbox children
        for child in widget.winfo_children():
            add_mousewheel_to_widget(child)

def setup_mousewheel_scrolling_for_tab(tab_widget):
    """Setup mousewheel scrolling for all scrollable widgets in a tab"""
    add_mousewheel_to_widget(tab_widget)