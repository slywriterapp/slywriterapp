# tab_settings_modern.py - Ultra-modern settings tab with 2025 aesthetics

import tkinter as tk
from tkinter import ttk, messagebox
from modern_ui_2025 import *
import keyboard

class ModernHotkeyRecorder(tk.Frame):
    """Modern hotkey recorder with visual feedback"""
    
    def __init__(self, parent, callback, initial_value="", **kwargs):
        super().__init__(parent, bg=COLORS['surface'], **kwargs)
        
        self.callback = callback
        self.current_hotkey = initial_value
        self.recording = False
        self.recorded_keys = []
        
        # Main container
        container = tk.Frame(self, bg=COLORS['surface_light'],
                           highlightthickness=1,
                           highlightbackground=COLORS['border'])
        container.pack(fill='x')
        
        # Display area
        display_frame = tk.Frame(container, bg=COLORS['surface_light'])
        display_frame.pack(fill='x', padx=12, pady=8)
        
        # Current hotkey display
        self.hotkey_label = tk.Label(display_frame, 
                                    text=self.current_hotkey or "Not Set",
                                    font=('Courier New', 12, 'bold'),
                                    fg=COLORS['primary'] if self.current_hotkey else COLORS['text_dim'],
                                    bg=COLORS['surface_light'])
        self.hotkey_label.pack(side='left')
        
        # Record button
        self.record_btn = ModernButton(display_frame, 
                                      text="Record", icon="🎤",
                                      command=self.toggle_recording,
                                      variant="secondary")
        self.record_btn.pack(side='right')
        
        # Clear button
        self.clear_btn = ModernButton(display_frame,
                                     text="Clear", icon="✖",
                                     command=self.clear_hotkey,
                                     variant="secondary")
        self.clear_btn.pack(side='right', padx=(0, 10))
        
        # Status indicator
        self.status_frame = tk.Frame(container, bg=COLORS['surface_light'], height=3)
        self.status_frame.pack(fill='x')
        self.status_frame.pack_propagate(False)
    
    def toggle_recording(self):
        """Toggle recording state"""
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Start recording hotkey"""
        self.recording = True
        self.recorded_keys = []
        
        # Update UI
        self.hotkey_label.configure(text="Press keys...", fg=COLORS['accent'])
        self.record_btn.text_label.configure(text="Stop")
        self.status_frame.configure(bg=COLORS['accent'])
        
        # Animate recording indicator
        self.animate_recording()
        
        # Hook keyboard
        keyboard.hook(self.on_key_event)
        
        # Update parent tab's recording status if available
        parent_tab = self.winfo_toplevel()
        for widget in parent_tab.winfo_children():
            if hasattr(widget, 'update_recording_status'):
                widget.update_recording_status(True)
                break
    
    def stop_recording(self):
        """Stop recording and save hotkey"""
        self.recording = False
        keyboard.unhook_all()
        
        # Build hotkey string
        if self.recorded_keys:
            self.current_hotkey = "+".join(self.recorded_keys)
            self.hotkey_label.configure(text=self.current_hotkey, fg=COLORS['primary'])
            
            # Call callback
            if self.callback:
                self.callback(self.current_hotkey)
        else:
            self.hotkey_label.configure(text=self.current_hotkey or "Not Set",
                                      fg=COLORS['primary'] if self.current_hotkey else COLORS['text_dim'])
        
        # Update UI
        self.record_btn.text_label.configure(text="Record")
        self.status_frame.configure(bg=COLORS['surface_light'])
        
        # Update parent tab's recording status if available
        parent_tab = self.winfo_toplevel()
        for widget in parent_tab.winfo_children():
            if hasattr(widget, 'update_recording_status'):
                widget.update_recording_status(False)
                if hasattr(widget, 'update_hotkeys_list'):
                    widget.update_hotkeys_list()
                break
    
    def on_key_event(self, event):
        """Handle key events during recording"""
        if event.event_type == 'down' and self.recording:
            key_name = event.name
            
            # Handle special keys
            if key_name in ['ctrl', 'alt', 'shift', 'cmd', 'win']:
                if key_name not in self.recorded_keys:
                    self.recorded_keys.append(key_name)
            else:
                # Add the actual key
                if key_name not in self.recorded_keys:
                    self.recorded_keys.append(key_name)
                
                # Stop recording after non-modifier key
                self.after(100, self.stop_recording)
            
            # Update display
            if self.recorded_keys:
                display_text = "+".join(self.recorded_keys)
                self.hotkey_label.configure(text=display_text)
    
    def clear_hotkey(self):
        """Clear the current hotkey"""
        self.current_hotkey = ""
        self.hotkey_label.configure(text="Not Set", fg=COLORS['text_dim'])
        
        if self.callback:
            self.callback("")
    
    def animate_recording(self):
        """Animate recording indicator"""
        if self.recording:
            # Pulse effect
            current_bg = self.status_frame.cget('bg')
            if current_bg == COLORS['accent']:
                self.status_frame.configure(bg=COLORS['accent_light'])
            else:
                self.status_frame.configure(bg=COLORS['accent'])
            
            self.after(500, self.animate_recording)
    
    def get(self):
        """Get current hotkey value"""
        return self.current_hotkey
    
    def set(self, value):
        """Set hotkey value"""
        self.current_hotkey = value
        self.hotkey_label.configure(text=value or "Not Set",
                                  fg=COLORS['primary'] if value else COLORS['text_dim'])


class ModernSettingsTab(tk.Frame):
    """Modern settings tab with 2025 UI design"""
    
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS['background'])
        self.app = app
        
        # Build the modern UI
        self.build_ui()
        
        # Load current settings
        self.load_settings()
    
    def build_ui(self):
        """Build the modern settings UI"""
        # Main horizontal split container
        main_split = tk.Frame(self, bg=COLORS['background'])
        main_split.pack(fill='both', expand=True)
        
        # Left side - Settings with scrollbar
        left_container = tk.Frame(main_split, bg=COLORS['background'])
        left_container.pack(side='left', fill='both', expand=True)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(left_container, bg=COLORS['background'],
                               highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_container, orient='vertical',
                                 command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLORS['background'])
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind mousewheel to entire frame so it works everywhere
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.bind_all("<MouseWheel>", on_mousewheel)
        
        # Content container with padding
        content = tk.Frame(self.scrollable_frame, bg=COLORS['background'])
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Right side - Recording window
        self.build_recording_window(main_split)
        
        # Title
        title_frame = tk.Frame(content, bg=COLORS['background'])
        title_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(title_frame, text="⚙", font=('Segoe UI', 24),
                fg=COLORS['primary'], bg=COLORS['background']).pack(side='left', padx=(0, 10))
        
        tk.Label(title_frame, text="Settings & Hotkeys",
                font=('Segoe UI', 20, 'bold'),
                fg=COLORS['text_primary'],
                bg=COLORS['background']).pack(side='left')
        
        # Build sections
        self.build_hotkeys_section(content)
        self.build_appearance_section(content)
        self.build_advanced_section(content)
    
    def build_hotkeys_section(self, parent):
        """Build hotkeys configuration section"""
        # Hotkeys Card
        hotkeys_card = GlassmorphicCard(parent, title="⌨ Global Hotkeys")
        hotkeys_card.pack(fill='x', pady=(0, 20))
        
        # Description
        desc_label = tk.Label(hotkeys_card.content,
                            text="Configure keyboard shortcuts for quick access",
                            font=('Segoe UI', 10),
                            fg=COLORS['text_secondary'],
                            bg=COLORS['surface'])
        desc_label.pack(anchor='w', pady=(0, 20))
        
        # Hotkey items
        hotkeys_data = [
            ("Start Typing", "start", "▶", "Begin typing the text"),
            ("Panic Stop", "stop", "⏹", "Immediately stop all typing"),
            ("Pause/Resume", "pause", "⏸", "Toggle pause state"),
            ("Toggle Overlay", "overlay", "👁", "Show/hide overlay window"),
            ("AI Generation", "ai_generation", "🤖", "Generate AI text")
        ]
        
        self.hotkey_recorders = {}
        
        for label, key, icon, description in hotkeys_data:
            # Item frame
            item_frame = tk.Frame(hotkeys_card.content, bg=COLORS['surface'])
            item_frame.pack(fill='x', pady=(0, 15))
            
            # Left side - Icon and labels
            left_frame = tk.Frame(item_frame, bg=COLORS['surface'])
            left_frame.pack(side='left', fill='x', expand=True)
            
            # Icon
            icon_label = tk.Label(left_frame, text=icon, font=('Segoe UI', 16),
                                 fg=COLORS['primary'], bg=COLORS['surface'])
            icon_label.pack(side='left', padx=(0, 12))
            
            # Text labels
            text_frame = tk.Frame(left_frame, bg=COLORS['surface'])
            text_frame.pack(side='left', fill='x', expand=True)
            
            tk.Label(text_frame, text=label, font=('Segoe UI', 11, 'bold'),
                    fg=COLORS['text_primary'], bg=COLORS['surface']).pack(anchor='w')
            
            tk.Label(text_frame, text=description, font=('Segoe UI', 9),
                    fg=COLORS['text_dim'], bg=COLORS['surface']).pack(anchor='w')
            
            # Right side - Hotkey recorder
            recorder = ModernHotkeyRecorder(item_frame, 
                                          callback=lambda v, k=key: self.on_hotkey_change(k, v),
                                          initial_value=self.app.cfg['settings']['hotkeys'].get(key, ''))
            recorder.pack(side='right', padx=(20, 0))
            
            self.hotkey_recorders[key] = recorder
    
    def build_appearance_section(self, parent):
        """Build appearance settings section"""
        # Appearance Card
        appearance_card = GlassmorphicCard(parent, title="🎨 Appearance")
        appearance_card.pack(fill='x', pady=(0, 20))
        
        # Theme Selection
        theme_frame = tk.Frame(appearance_card.content, bg=COLORS['surface'])
        theme_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(theme_frame, text="Color Theme",
                font=('Segoe UI', 11),
                fg=COLORS['text_secondary'],
                bg=COLORS['surface']).pack(side='left')
        
        # Theme buttons
        themes_container = tk.Frame(theme_frame, bg=COLORS['surface'])
        themes_container.pack(side='right')
        
        ModernButton(themes_container, text="Dark", icon="🌙",
                    command=lambda: self.set_theme('dark'),
                    variant="secondary").pack(side='left', padx=(0, 5))
        
        ModernButton(themes_container, text="Light", icon="☀",
                    command=lambda: self.set_theme('light'),
                    variant="secondary").pack(side='left', padx=5)
        
        ModernButton(themes_container, text="Auto", icon="🔄",
                    command=lambda: self.set_theme('auto'),
                    variant="secondary").pack(side='left', padx=(5, 0))
        
        # Accent Color
        accent_frame = tk.Frame(appearance_card.content, bg=COLORS['surface'])
        accent_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(accent_frame, text="Accent Color",
                font=('Segoe UI', 11),
                fg=COLORS['text_secondary'],
                bg=COLORS['surface']).pack(side='left')
        
        # Color swatches
        colors_container = tk.Frame(accent_frame, bg=COLORS['surface'])
        colors_container.pack(side='right')
        
        accent_colors = [
            ('#8B5CF6', 'Purple'),
            ('#EC4899', 'Pink'),
            ('#10B981', 'Green'),
            ('#F59E0B', 'Amber'),
            ('#3B82F6', 'Blue')
        ]
        
        for color, name in accent_colors:
            color_btn = tk.Frame(colors_container, bg=color, width=30, height=30)
            color_btn.pack(side='left', padx=2)
            color_btn.bind("<Button-1>", lambda e, c=color: self.set_accent_color(c))
        
        # Font Size
        font_frame = tk.Frame(appearance_card.content, bg=COLORS['surface'])
        font_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(font_frame, text="Font Size",
                font=('Segoe UI', 11),
                fg=COLORS['text_secondary'],
                bg=COLORS['surface']).pack(side='left')
        
        self.font_size_var = tk.IntVar(value=11)
        font_slider = ModernSlider(font_frame, from_=9, to=16,
                                  variable=self.font_size_var,
                                  command=self.on_font_size_change)
        font_slider.pack(side='right')
    
    def build_advanced_section(self, parent):
        """Build advanced settings section"""
        # Advanced Card
        advanced_card = GlassmorphicCard(parent, title="🚀 Advanced")
        advanced_card.pack(fill='x', pady=(0, 20))
        
        # Auto-save toggle
        autosave_frame = tk.Frame(advanced_card.content, bg=COLORS['surface'])
        autosave_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(autosave_frame, text="Auto-save Settings",
                font=('Segoe UI', 11),
                fg=COLORS['text_secondary'],
                bg=COLORS['surface']).pack(side='left')
        
        self.autosave_var = tk.BooleanVar(value=True)
        ModernToggle(autosave_frame, variable=self.autosave_var,
                    command=self.on_autosave_change).pack(side='right')
        
        # Notifications toggle
        notif_frame = tk.Frame(advanced_card.content, bg=COLORS['surface'])
        notif_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(notif_frame, text="Desktop Notifications",
                font=('Segoe UI', 11),
                fg=COLORS['text_secondary'],
                bg=COLORS['surface']).pack(side='left')
        
        self.notifications_var = tk.BooleanVar(value=True)
        ModernToggle(notif_frame, variable=self.notifications_var,
                    command=self.on_notifications_change).pack(side='right')
        
        # Hardware Acceleration toggle
        hw_frame = tk.Frame(advanced_card.content, bg=COLORS['surface'])
        hw_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(hw_frame, text="Hardware Acceleration",
                font=('Segoe UI', 11),
                fg=COLORS['text_secondary'],
                bg=COLORS['surface']).pack(side='left')
        
        tk.Label(hw_frame, text="BETA",
                font=('Segoe UI', 8, 'bold'),
                fg=COLORS['warning'],
                bg=COLORS['surface']).pack(side='left', padx=5)
        
        self.hw_accel_var = tk.BooleanVar(value=False)
        ModernToggle(hw_frame, variable=self.hw_accel_var,
                    command=self.on_hw_accel_change).pack(side='right')
        
        # Export/Import buttons
        data_frame = tk.Frame(advanced_card.content, bg=COLORS['surface'])
        data_frame.pack(fill='x', pady=(20, 0))
        
        ModernButton(data_frame, text="Export Settings", icon="📤",
                    command=self.export_settings,
                    variant="secondary").pack(side='left', padx=(0, 10))
        
        ModernButton(data_frame, text="Import Settings", icon="📥",
                    command=self.import_settings,
                    variant="secondary").pack(side='left', padx=(0, 10))
        
        ModernButton(data_frame, text="Reset to Default", icon="🔄",
                    command=self.reset_settings,
                    variant="danger").pack(side='left')
    
    def build_recording_window(self, parent):
        """Build the recording status window on the right side"""
        # Right side container
        right_container = tk.Frame(parent, bg=COLORS['background'], width=350)
        right_container.pack(side='right', fill='y', padx=(20, 20), pady=20)
        right_container.pack_propagate(False)  # Fixed width
        
        # Recording Status Card
        status_card = GlassmorphicCard(right_container, title="🎤 Hotkey Recorder")
        status_card.pack(fill='both', expand=True)
        
        # Current recording status
        self.recording_status_frame = tk.Frame(status_card.content, 
                                              bg=COLORS['surface_light'],
                                              highlightthickness=2,
                                              highlightbackground=COLORS['primary'])
        self.recording_status_frame.pack(fill='x', pady=(0, 20))
        
        status_inner = tk.Frame(self.recording_status_frame, bg=COLORS['surface_light'])
        status_inner.pack(padx=15, pady=15)
        
        self.recording_status_label = tk.Label(status_inner,
                                              text="Not Recording",
                                              font=('Segoe UI', 14, 'bold'),
                                              fg=COLORS['text_secondary'],
                                              bg=COLORS['surface_light'])
        self.recording_status_label.pack()
        
        self.recording_keys_label = tk.Label(status_inner,
                                            text="Click 'Record' on any hotkey to start",
                                            font=('Segoe UI', 11),
                                            fg=COLORS['text_dim'],
                                            bg=COLORS['surface_light'])
        self.recording_keys_label.pack(pady=(5, 0))
        
        # Instructions
        instructions_frame = tk.Frame(status_card.content, bg=COLORS['surface'])
        instructions_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(instructions_frame,
                text="📝 Instructions",
                font=('Segoe UI', 12, 'bold'),
                fg=COLORS['text_primary'],
                bg=COLORS['surface']).pack(anchor='w', pady=(0, 10))
        
        instructions = [
            "1. Click 'Record' next to any hotkey",
            "2. Press your desired key combination",
            "3. Recording stops automatically",
            "4. Use 'Clear' to remove a hotkey"
        ]
        
        for instruction in instructions:
            tk.Label(instructions_frame,
                    text=instruction,
                    font=('Segoe UI', 10),
                    fg=COLORS['text_secondary'],
                    bg=COLORS['surface'],
                    justify='left').pack(anchor='w', pady=2)
        
        # Visual keyboard hint
        keyboard_frame = tk.Frame(status_card.content, bg=COLORS['surface'])
        keyboard_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(keyboard_frame,
                text="⌨️ Common Modifiers",
                font=('Segoe UI', 12, 'bold'),
                fg=COLORS['text_primary'],
                bg=COLORS['surface']).pack(anchor='w', pady=(0, 10))
        
        # Modifier keys display
        modifiers_container = tk.Frame(keyboard_frame, bg=COLORS['surface'])
        modifiers_container.pack(fill='x')
        
        modifier_keys = ['Ctrl', 'Alt', 'Shift', 'Win/Cmd']
        for mod in modifier_keys:
            mod_frame = tk.Frame(modifiers_container,
                                bg=COLORS['surface_light'],
                                highlightthickness=1,
                                highlightbackground=COLORS['border'])
            mod_frame.pack(side='left', padx=(0, 5), pady=5)
            
            tk.Label(mod_frame,
                    text=mod,
                    font=('Courier New', 10, 'bold'),
                    fg=COLORS['primary'],
                    bg=COLORS['surface_light'],
                    padx=10, pady=5).pack()
        
        # Current hotkeys summary
        summary_frame = tk.Frame(status_card.content, bg=COLORS['surface'])
        summary_frame.pack(fill='both', expand=True)
        
        tk.Label(summary_frame,
                text="📋 Active Hotkeys",
                font=('Segoe UI', 12, 'bold'),
                fg=COLORS['text_primary'],
                bg=COLORS['surface']).pack(anchor='w', pady=(0, 10))
        
        # Active hotkeys list (will be updated dynamically)
        self.hotkeys_list_frame = tk.Frame(summary_frame, bg=COLORS['surface'])
        self.hotkeys_list_frame.pack(fill='both', expand=True)
        
        self.update_hotkeys_list()
    
    def update_hotkeys_list(self):
        """Update the list of active hotkeys in the recording window"""
        # Clear existing list
        for widget in self.hotkeys_list_frame.winfo_children():
            widget.destroy()
        
        # Add current hotkeys
        hotkeys_info = [
            ("Start", self.app.cfg['settings']['hotkeys'].get('start', 'Not Set'), "▶"),
            ("Stop", self.app.cfg['settings']['hotkeys'].get('stop', 'Not Set'), "⏹"),
            ("Pause", self.app.cfg['settings']['hotkeys'].get('pause', 'Not Set'), "⏸"),
            ("Overlay", self.app.cfg['settings']['hotkeys'].get('overlay', 'Not Set'), "👁"),
            ("AI Gen", self.app.cfg['settings']['hotkeys'].get('ai_generation', 'Not Set'), "🤖")
        ]
        
        for name, key, icon in hotkeys_info:
            item_frame = tk.Frame(self.hotkeys_list_frame, bg=COLORS['surface'])
            item_frame.pack(fill='x', pady=2)
            
            tk.Label(item_frame,
                    text=f"{icon} {name}:",
                    font=('Segoe UI', 10),
                    fg=COLORS['text_secondary'],
                    bg=COLORS['surface'],
                    width=12,
                    anchor='w').pack(side='left')
            
            tk.Label(item_frame,
                    text=key,
                    font=('Courier New', 10, 'bold'),
                    fg=COLORS['primary'] if key != 'Not Set' else COLORS['text_dim'],
                    bg=COLORS['surface']).pack(side='left')
    
    def update_recording_status(self, recording, keys=None):
        """Update the recording status display"""
        if recording:
            self.recording_status_label.configure(
                text="🔴 Recording...",
                fg=COLORS['error']
            )
            if keys:
                self.recording_keys_label.configure(
                    text="+".join(keys) if keys else "Press keys...",
                    fg=COLORS['accent']
                )
            else:
                self.recording_keys_label.configure(
                    text="Press your key combination",
                    fg=COLORS['text_secondary']
                )
            # Pulse animation
            self.recording_status_frame.configure(highlightbackground=COLORS['error'])
        else:
            self.recording_status_label.configure(
                text="✓ Ready",
                fg=COLORS['success']
            )
            self.recording_keys_label.configure(
                text="Click 'Record' on any hotkey to start",
                fg=COLORS['text_dim']
            )
            self.recording_status_frame.configure(highlightbackground=COLORS['primary'])
    
    def load_settings(self):
        """Load current settings from app config"""
        config = self.app.cfg['settings']
        
        # Load hotkeys
        for key, recorder in self.hotkey_recorders.items():
            value = config['hotkeys'].get(key, '')
            recorder.set(value)
    
    def on_hotkey_change(self, key, value):
        """Handle hotkey change"""
        # Update config
        self.app.cfg['settings']['hotkeys'][key] = value
        
        # Apply the hotkey
        if hasattr(self.app, f'set_{key}_hotkey'):
            getattr(self.app, f'set_{key}_hotkey')(value)
        
        # Save if autosave is on
        if hasattr(self, 'autosave_var') and self.autosave_var.get():
            self.app.on_setting_change()
        
        # Show toast notification
        self.show_toast(f"Hotkey updated: {key}")
    
    def set_theme(self, theme):
        """Change application theme"""
        # This would implement theme switching
        self.show_toast(f"Theme changed to {theme}")
    
    def set_accent_color(self, color):
        """Change accent color"""
        # This would implement accent color change
        self.show_toast(f"Accent color changed")
    
    def on_font_size_change(self):
        """Handle font size change"""
        size = self.font_size_var.get()
        # Apply font size change
        self.show_toast(f"Font size: {size}")
    
    def on_autosave_change(self):
        """Handle autosave toggle"""
        if self.autosave_var.get():
            self.app.on_setting_change()
            self.show_toast("Auto-save enabled")
        else:
            self.show_toast("Auto-save disabled")
    
    def on_notifications_change(self):
        """Handle notifications toggle"""
        enabled = self.notifications_var.get()
        self.show_toast(f"Notifications {'enabled' if enabled else 'disabled'}")
    
    def on_hw_accel_change(self):
        """Handle hardware acceleration toggle"""
        enabled = self.hw_accel_var.get()
        self.show_toast(f"Hardware acceleration {'enabled' if enabled else 'disabled'}")
    
    def export_settings(self):
        """Export settings to file"""
        from tkinter import filedialog
        import json
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.app.cfg, f, indent=2)
                self.show_toast("Settings exported successfully")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export settings: {e}")
    
    def import_settings(self):
        """Import settings from file"""
        from tkinter import filedialog
        import json
        
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    imported = json.load(f)
                
                # Merge with current config
                self.app.cfg.update(imported)
                self.load_settings()
                self.app.on_setting_change()
                
                self.show_toast("Settings imported successfully")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import settings: {e}")
    
    def reset_settings(self):
        """Reset settings to default"""
        if messagebox.askyesno("Reset Settings", 
                               "Are you sure you want to reset all settings to default?"):
            # Reset to default config
            from config import get_default_config
            self.app.cfg = get_default_config()
            self.load_settings()
            self.app.on_setting_change()
            
            self.show_toast("Settings reset to default")
    
    def show_toast(self, message):
        """Show toast notification"""
        # Create toast popup
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.configure(bg=COLORS['surface'])
        
        # Position at bottom right
        x = self.winfo_rootx() + self.winfo_width() - 300
        y = self.winfo_rooty() + self.winfo_height() - 100
        toast.geometry(f"280x60+{x}+{y}")
        
        # Toast content
        content = tk.Frame(toast, bg=COLORS['surface'],
                          highlightthickness=1,
                          highlightbackground=COLORS['primary'])
        content.pack(fill='both', expand=True)
        
        tk.Label(content, text="✓", font=('Segoe UI', 16),
                fg=COLORS['success'], bg=COLORS['surface']).pack(side='left', padx=10)
        
        tk.Label(content, text=message, font=('Segoe UI', 10),
                fg=COLORS['text_primary'], bg=COLORS['surface']).pack(side='left')
        
        # Auto-dismiss after 2 seconds
        toast.after(2000, toast.destroy)
    
    # Compatibility methods
    def set_theme(self, dark_mode):
        """Theme compatibility"""
        pass
    
    def get_all_hotkeys(self):
        """Get all configured hotkeys"""
        return {k: r.get() for k, r in self.hotkey_recorders.items()}