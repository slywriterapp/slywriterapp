# modern_overlay.py - Modern 2025 Overlay System

import tkinter as tk
import config
import threading
import time

class ModernStatusOverlay:
    """Modern animated status overlay with colored indicators"""
    
    def __init__(self, parent):
        self.parent = parent
        self.overlay_window = None
        self.status_text = "Ready"
        self.status_color = config.SUCCESS_GREEN
        self.animation_thread = None
        self._should_animate = False
        
    def create_overlay(self, x=50, y=50, width=200, height=40):
        """Create modern overlay window"""
        if self.overlay_window:
            self.overlay_window.destroy()
            
        self.overlay_window = tk.Toplevel()
        self.overlay_window.withdraw()  # Start hidden
        
        # Modern window styling
        self.overlay_window.overrideredirect(True)  # Remove window decorations
        self.overlay_window.attributes('-topmost', True)  # Always on top
        self.overlay_window.attributes('-alpha', 0.9)  # Slight transparency
        
        # Position window
        self.overlay_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Get theme colors
        try:
            dark_mode = self.parent.app.cfg['settings'].get('dark_mode', False)
        except:
            dark_mode = False
            
        bg_color = config.DARK_CARD_BG if dark_mode else config.LIGHT_CARD_BG
        fg_color = config.DARK_FG if dark_mode else config.LIGHT_FG
        
        # Main frame with modern styling
        self.main_frame = tk.Frame(
            self.overlay_window,
            bg=bg_color,
            relief='flat',
            borderwidth=1,
            highlightbackground=config.GRAY_300 if not dark_mode else config.GRAY_600,
            highlightthickness=1
        )
        self.main_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Status indicator (colored circle)
        self.status_indicator = tk.Label(
            self.main_frame,
            text="●",
            font=(config.FONT_PRIMARY, 16),
            fg=self.status_color,
            bg=bg_color
        )
        self.status_indicator.pack(side='left', padx=(8, 4), pady=8)
        
        # Status text
        self.status_label = tk.Label(
            self.main_frame,
            text=self.status_text,
            font=(config.FONT_PRIMARY, 9),
            fg=fg_color,
            bg=bg_color
        )
        self.status_label.pack(side='left', pady=8, fill='x', expand=True)
        
    def show_overlay(self):
        """Show the overlay with fade-in effect"""
        if self.overlay_window:
            self.overlay_window.deiconify()
            self._fade_in()
    
    def hide_overlay(self):
        """Hide the overlay with fade-out effect"""
        if self.overlay_window:
            self._fade_out()
    
    def update_status(self, text, status_type="info"):
        """Update status text with animated colored indicator"""
        self.status_text = text
        
        # Set color based on status type
        if status_type == "success" or "done" in text.lower() or "completed" in text.lower():
            self.status_color = config.SUCCESS_GREEN
        elif status_type == "warning" or "pause" in text.lower() or "wait" in text.lower():
            self.status_color = config.WARNING_ORANGE
        elif status_type == "error" or "stop" in text.lower() or "cancel" in text.lower():
            self.status_color = config.DANGER_RED
        elif "typing" in text.lower() or "start" in text.lower():
            self.status_color = config.PRIMARY_BLUE
        else:
            self.status_color = config.GRAY_500
        
        if self.overlay_window and self.status_label:
            self.status_label.config(text=text)
            self.status_indicator.config(fg=self.status_color)
            
            # Start pulsing animation for active states
            if "typing" in text.lower() or "generating" in text.lower() or "processing" in text.lower():
                self._start_pulse_animation()
            else:
                self._stop_pulse_animation()
    
    def _fade_in(self):
        """Smooth fade-in animation"""
        if not self.overlay_window:
            return
            
        alpha = 0.0
        while alpha < 0.9:
            try:
                self.overlay_window.attributes('-alpha', alpha)
                alpha += 0.1
                time.sleep(0.02)
            except:
                break
    
    def _fade_out(self):
        """Smooth fade-out animation"""
        if not self.overlay_window:
            return
            
        alpha = 0.9
        while alpha > 0:
            try:
                self.overlay_window.attributes('-alpha', alpha)
                alpha -= 0.1
                time.sleep(0.02)
            except:
                break
        
        try:
            self.overlay_window.withdraw()
        except:
            pass
    
    def _start_pulse_animation(self):
        """Start pulsing animation for active status"""
        self._should_animate = True
        if not self.animation_thread or not self.animation_thread.is_alive():
            self.animation_thread = threading.Thread(target=self._pulse_animation, daemon=True)
            self.animation_thread.start()
    
    def _stop_pulse_animation(self):
        """Stop pulsing animation"""
        self._should_animate = False
    
    def _pulse_animation(self):
        """Animated pulsing effect for status indicator"""
        # Use different brightness levels instead of alpha transparency
        base_color = self.status_color
        if base_color == config.SUCCESS_GREEN:
            pulse_colors = [config.SUCCESS_GREEN, "#0D9488", "#059669", "#0D9488"]
        elif base_color == config.WARNING_ORANGE:
            pulse_colors = [config.WARNING_ORANGE, "#D97706", "#B45309", "#D97706"]
        elif base_color == config.DANGER_RED:
            pulse_colors = [config.DANGER_RED, "#DC2626", "#B91C1C", "#DC2626"]
        elif base_color == config.PRIMARY_BLUE:
            pulse_colors = [config.PRIMARY_BLUE, "#1D4ED8", "#1E40AF", "#1D4ED8"]
        else:
            pulse_colors = [base_color, config.GRAY_400, config.GRAY_500, config.GRAY_400]
        
        color_index = 0
        while self._should_animate:
            try:
                if self.status_indicator:
                    self.status_indicator.config(fg=pulse_colors[color_index])
                    color_index = (color_index + 1) % len(pulse_colors)
                time.sleep(0.3)
            except:
                break
        
        # Reset to original color when animation stops
        try:
            if self.status_indicator:
                self.status_indicator.config(fg=self.status_color)
        except:
            pass

# Global overlay instance
_global_overlay = None

def get_overlay_instance():
    """Get or create global overlay instance"""
    global _global_overlay
    return _global_overlay

def set_overlay_instance(overlay):
    """Set global overlay instance"""
    global _global_overlay
    _global_overlay = overlay

def update_overlay_text(text, status_type="info"):
    """Update overlay text with modern status indication"""
    overlay = get_overlay_instance()
    if overlay:
        overlay.update_status(text, status_type)