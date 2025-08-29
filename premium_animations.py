# premium_animations.py - Smooth animations and transitions

import tkinter as tk
import math
import time

class SmoothTransition:
    """Smooth transition effects for premium UI"""
    
    def __init__(self, widget, duration=300):
        self.widget = widget
        self.duration = duration  # milliseconds
        self.start_time = None
        self.active = False
    
    def fade_in(self, from_alpha=0.0, to_alpha=1.0, callback=None):
        """Fade in animation"""
        self.start_time = time.time() * 1000
        self.active = True
        self._animate_alpha(from_alpha, to_alpha, callback)
    
    def fade_out(self, from_alpha=1.0, to_alpha=0.0, callback=None):
        """Fade out animation"""
        self.start_time = time.time() * 1000
        self.active = True
        self._animate_alpha(from_alpha, to_alpha, callback)
    
    def _animate_alpha(self, from_alpha, to_alpha, callback):
        """Animate alpha transparency"""
        if not self.active:
            return
            
        current_time = time.time() * 1000
        elapsed = current_time - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        # Ease-out cubic function
        eased_progress = 1 - (1 - progress) ** 3
        
        current_alpha = from_alpha + (to_alpha - from_alpha) * eased_progress
        
        try:
            # Apply alpha (simulated with color intensity)
            self._apply_alpha_effect(current_alpha)
        except:
            pass
        
        if progress < 1.0:
            self.widget.after(16, lambda: self._animate_alpha(from_alpha, to_alpha, callback))
        else:
            self.active = False
            if callback:
                callback()
    
    def _apply_alpha_effect(self, alpha):
        """Apply alpha effect by adjusting colors"""
        try:
            # Get current background color
            bg = self.widget.cget('bg')
            if bg and bg != 'transparent':
                # Calculate new color based on alpha
                # This is a simplified alpha simulation
                if alpha < 0.5:
                    # Fade towards background
                    new_bg = self._blend_color(bg, '#0F0F23', alpha * 2)
                else:
                    new_bg = bg
                
                self.widget.configure(bg=new_bg)
        except:
            pass
    
    def _blend_color(self, color1, color2, ratio):
        """Blend two colors"""
        # Simple color blending (would need proper hex parsing in production)
        return color1


class HoverAnimation:
    """Hover animation effects"""
    
    def __init__(self, widget, hover_color, normal_color, duration=200):
        self.widget = widget
        self.hover_color = hover_color
        self.normal_color = normal_color
        self.duration = duration
        self.is_hovering = False
        
        # Bind events
        widget.bind('<Enter>', self.on_enter)
        widget.bind('<Leave>', self.on_leave)
    
    def on_enter(self, event):
        """Handle mouse enter"""
        self.is_hovering = True
        self._animate_to_color(self.hover_color)
    
    def on_leave(self, event):
        """Handle mouse leave"""
        self.is_hovering = False
        self._animate_to_color(self.normal_color)
    
    def _animate_to_color(self, target_color):
        """Animate to target color"""
        try:
            # Immediate color change for now (would implement smooth transition in production)
            self.widget.configure(bg=target_color)
        except:
            pass


class SlideAnimation:
    """Slide in/out animations"""
    
    def __init__(self, widget):
        self.widget = widget
        self.original_x = widget.winfo_x()
        self.original_y = widget.winfo_y()
    
    def slide_in_from_left(self, duration=400):
        """Slide in from left"""
        # Store original position
        target_x = self.widget.winfo_x()
        
        # Start from off-screen left
        start_x = target_x - 300
        self.widget.place(x=start_x)
        
        # Animate to target position
        self._animate_position(start_x, target_x, duration)
    
    def slide_out_to_left(self, duration=400):
        """Slide out to left"""
        start_x = self.widget.winfo_x()
        target_x = start_x - 300
        
        self._animate_position(start_x, target_x, duration)
    
    def _animate_position(self, start_x, target_x, duration):
        """Animate position change"""
        start_time = time.time() * 1000
        
        def update_position():
            current_time = time.time() * 1000
            elapsed = current_time - start_time
            progress = min(elapsed / duration, 1.0)
            
            # Ease-out function
            eased_progress = 1 - (1 - progress) ** 3
            
            current_x = start_x + (target_x - start_x) * eased_progress
            
            try:
                self.widget.place(x=current_x)
            except:
                return
            
            if progress < 1.0:
                self.widget.after(16, update_position)
        
        update_position()


class PulseAnimation:
    """Pulse animation for notifications"""
    
    def __init__(self, widget):
        self.widget = widget
        self.active = False
    
    def start_pulse(self, duration=1000, cycles=3):
        """Start pulse animation"""
        self.active = True
        self.start_time = time.time() * 1000
        self.duration = duration
        self.cycles = cycles
        self._animate_pulse()
    
    def stop_pulse(self):
        """Stop pulse animation"""
        self.active = False
    
    def _animate_pulse(self):
        """Animate pulse effect"""
        if not self.active:
            return
        
        current_time = time.time() * 1000
        elapsed = current_time - self.start_time
        
        # Calculate pulse progress
        cycle_duration = self.duration / self.cycles
        cycle_progress = (elapsed % cycle_duration) / cycle_duration
        
        # Sine wave for smooth pulsing
        pulse_value = math.sin(cycle_progress * math.pi * 2)
        scale = 1.0 + pulse_value * 0.1  # 10% size variation
        
        try:
            # Apply scale effect (simplified)
            pass  # Would implement actual scaling in production
        except:
            pass
        
        # Check if animation should continue
        if elapsed < self.duration * self.cycles:
            self.widget.after(16, self._animate_pulse)
        else:
            self.active = False


class LoadingSpinner:
    """Loading spinner animation"""
    
    def __init__(self, parent, size=32):
        self.parent = parent
        self.size = size
        self.active = False
        
        # Create canvas for spinner
        self.canvas = tk.Canvas(parent, width=size, height=size, 
                               bg='transparent', highlightthickness=0)
        
        self.angle = 0
    
    def start(self):
        """Start spinner animation"""
        self.active = True
        self.canvas.pack()
        self._animate_spinner()
    
    def stop(self):
        """Stop spinner animation"""
        self.active = False
        self.canvas.pack_forget()
    
    def _animate_spinner(self):
        """Animate the spinner"""
        if not self.active:
            return
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Draw spinner arc
        center = self.size // 2
        radius = center - 4
        
        # Calculate arc coordinates
        x1 = center - radius
        y1 = center - radius
        x2 = center + radius
        y2 = center + radius
        
        # Draw arc
        self.canvas.create_arc(x1, y1, x2, y2,
                              start=self.angle, extent=90,
                              outline='#410899', width=3,
                              style='arc')
        
        # Update angle
        self.angle = (self.angle + 10) % 360
        
        # Schedule next frame
        self.parent.after(50, self._animate_spinner)


class ProgressAnimation:
    """Animated progress bar"""
    
    def __init__(self, parent, width=200, height=8):
        self.parent = parent
        self.width = width
        self.height = height
        self.progress = 0.0
        
        # Create progress bar
        self.container = tk.Frame(parent, bg='#374151', height=height)
        self.container.pack(fill='x', pady=5)
        self.container.pack_propagate(False)
        
        self.fill = tk.Frame(self.container, bg='#410899', height=height)
        self.fill.place(x=0, y=0, width=0, height=height)
    
    def set_progress(self, progress, animated=True):
        """Set progress value (0.0 to 1.0)"""
        target_width = int(self.width * progress)
        
        if animated:
            self._animate_to_width(target_width)
        else:
            self.fill.place(width=target_width)
        
        self.progress = progress
    
    def _animate_to_width(self, target_width):
        """Animate to target width"""
        current_width = self.fill.winfo_width()
        if current_width == target_width:
            return
        
        # Simple linear animation
        diff = target_width - current_width
        step = diff / 20  # 20 frames
        
        def update_width():
            new_width = self.fill.winfo_width() + step
            if (step > 0 and new_width >= target_width) or (step < 0 and new_width <= target_width):
                new_width = target_width
            
            self.fill.place(width=int(new_width))
            
            if new_width != target_width:
                self.parent.after(16, update_width)
        
        update_width()


# Utility functions for premium animations
def create_glow_effect(widget, glow_color='#410899', glow_size=2):
    """Create a glow effect around a widget"""
    try:
        # Simulate glow with border highlight
        widget.configure(highlightbackground=glow_color, 
                        highlightcolor=glow_color,
                        highlightthickness=glow_size)
    except:
        pass

def remove_glow_effect(widget):
    """Remove glow effect from a widget"""
    try:
        widget.configure(highlightthickness=0)
    except:
        pass

def shake_widget(widget, intensity=5, duration=300):
    """Shake widget for error feedback"""
    original_x = widget.winfo_x()
    start_time = time.time() * 1000
    
    def shake_frame():
        current_time = time.time() * 1000
        elapsed = current_time - start_time
        
        if elapsed < duration:
            # Calculate shake offset
            progress = elapsed / duration
            offset = math.sin(progress * math.pi * 8) * intensity * (1 - progress)
            
            try:
                widget.place(x=original_x + int(offset))
            except:
                return
            
            widget.after(16, shake_frame)
        else:
            try:
                widget.place(x=original_x)
            except:
                pass

# Export main classes
__all__ = [
    'SmoothTransition', 'HoverAnimation', 'SlideAnimation',
    'PulseAnimation', 'LoadingSpinner', 'ProgressAnimation',
    'create_glow_effect', 'remove_glow_effect', 'shake_widget'
]