# premium_notifications.py - Premium notification system

import tkinter as tk
from tkinter import ttk
import threading
import time
from premium_animations import SmoothTransition, create_glow_effect

class PremiumNotification:
    """Premium notification popup"""
    
    def __init__(self, parent, message, type="info", duration=3000):
        self.parent = parent
        self.message = message
        self.type = type
        self.duration = duration
        
        # Notification types
        self.types = {
            'success': {'bg': '#10B981', 'icon': '✅', 'fg': 'white'},
            'error': {'bg': '#EF4444', 'icon': '❌', 'fg': 'white'},
            'warning': {'bg': '#F59E0B', 'icon': '⚠️', 'fg': 'white'},
            'info': {'bg': '#3B82F6', 'icon': 'ℹ️', 'fg': 'white'},
            'premium': {'bg': '#410899', 'icon': '👑', 'fg': 'white'}
        }
        
        self.create_notification()
    
    def create_notification(self):
        """Create the notification window"""
        # Create notification window
        self.notification = tk.Toplevel(self.parent)
        self.notification.overrideredirect(True)
        self.notification.attributes('-topmost', True)
        
        # Get notification style
        style = self.types.get(self.type, self.types['info'])
        
        # Configure window
        self.notification.configure(bg=style['bg'])
        
        # Position notification (top-right corner)
        self.position_notification()
        
        # Create content
        self.create_content(style)
        
        # Show with animation
        self.show_notification()
    
    def position_notification(self):
        """Position notification in top-right corner"""
        # Update to get proper dimensions
        self.notification.update_idletasks()
        
        # Calculate position
        width = 320
        height = 80
        
        # Get parent window position
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        
        # Position in top-right
        x = parent_x + parent_width - width - 20
        y = parent_y + 20
        
        self.notification.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_content(self, style):
        """Create notification content"""
        # Main container
        container = tk.Frame(self.notification, bg=style['bg'])
        container.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Content frame
        content_frame = tk.Frame(container, bg=style['bg'])
        content_frame.pack(fill='both', expand=True, padx=16, pady=12)
        
        # Icon
        icon_label = tk.Label(content_frame,
                             text=style['icon'],
                             font=('Segoe UI', 16),
                             fg=style['fg'],
                             bg=style['bg'])
        icon_label.pack(side='left', padx=(0, 12))
        
        # Message container
        msg_frame = tk.Frame(content_frame, bg=style['bg'])
        msg_frame.pack(side='left', fill='both', expand=True)
        
        # Message text
        msg_label = tk.Label(msg_frame,
                            text=self.message,
                            font=('Segoe UI', 10, 'bold'),
                            fg=style['fg'],
                            bg=style['bg'],
                            wraplength=240,
                            justify='left')
        msg_label.pack(anchor='w')
        
        # Close button
        close_btn = tk.Button(content_frame,
                             text='×',
                             font=('Segoe UI', 12, 'bold'),
                             fg=style['fg'],
                             bg=style['bg'],
                             relief='flat',
                             bd=0,
                             cursor='hand2',
                             command=self.close_notification)
        close_btn.pack(side='right')
    
    def show_notification(self):
        """Show notification with slide-in animation"""
        # Start from off-screen
        original_x = self.notification.winfo_x()
        start_x = original_x + 350
        
        self.notification.geometry(f"+{start_x}+{self.notification.winfo_y()}")
        
        # Animate slide-in
        self.animate_slide_in(start_x, original_x)
        
        # Auto-hide after duration
        self.parent.after(self.duration, self.auto_hide)
    
    def animate_slide_in(self, start_x, target_x, duration=300):
        """Animate slide-in effect"""
        start_time = time.time() * 1000
        
        def update_position():
            current_time = time.time() * 1000
            elapsed = current_time - start_time
            progress = min(elapsed / duration, 1.0)
            
            # Ease-out cubic
            eased_progress = 1 - (1 - progress) ** 3
            
            current_x = start_x + (target_x - start_x) * eased_progress
            
            try:
                self.notification.geometry(f"+{int(current_x)}+{self.notification.winfo_y()}")
            except:
                return
            
            if progress < 1.0:
                self.parent.after(16, update_position)
        
        update_position()
    
    def auto_hide(self):
        """Auto-hide notification"""
        if hasattr(self, 'notification') and self.notification.winfo_exists():
            self.hide_notification()
    
    def hide_notification(self):
        """Hide notification with slide-out animation"""
        target_x = self.notification.winfo_x() + 350
        start_x = self.notification.winfo_x()
        
        self.animate_slide_out(start_x, target_x)
    
    def animate_slide_out(self, start_x, target_x, duration=200):
        """Animate slide-out effect"""
        start_time = time.time() * 1000
        
        def update_position():
            current_time = time.time() * 1000
            elapsed = current_time - start_time
            progress = min(elapsed / duration, 1.0)
            
            # Ease-in cubic
            eased_progress = progress ** 3
            
            current_x = start_x + (target_x - start_x) * eased_progress
            
            try:
                self.notification.geometry(f"+{int(current_x)}+{self.notification.winfo_y()}")
            except:
                return
            
            if progress < 1.0:
                self.parent.after(16, update_position)
            else:
                self.close_notification()
        
        update_position()
    
    def close_notification(self):
        """Close notification"""
        try:
            if hasattr(self, 'notification'):
                self.notification.destroy()
        except:
            pass


class NotificationManager:
    """Manages multiple notifications"""
    
    def __init__(self, parent):
        self.parent = parent
        self.notifications = []
        self.max_notifications = 3
    
    def show_success(self, message, duration=3000):
        """Show success notification"""
        return self.show_notification(message, "success", duration)
    
    def show_error(self, message, duration=4000):
        """Show error notification"""
        return self.show_notification(message, "error", duration)
    
    def show_warning(self, message, duration=3500):
        """Show warning notification"""
        return self.show_notification(message, "warning", duration)
    
    def show_info(self, message, duration=3000):
        """Show info notification"""
        return self.show_notification(message, "info", duration)
    
    def show_premium(self, message, duration=4000):
        """Show premium notification"""
        return self.show_notification(message, "premium", duration)
    
    def show_notification(self, message, type="info", duration=3000):
        """Show a notification"""
        # Clean up old notifications
        self.cleanup_notifications()
        
        # Limit number of notifications
        if len(self.notifications) >= self.max_notifications:
            # Remove oldest
            old_notification = self.notifications.pop(0)
            try:
                old_notification.close_notification()
            except:
                pass
        
        # Create new notification
        notification = PremiumNotification(self.parent, message, type, duration)
        self.notifications.append(notification)
        
        return notification
    
    def cleanup_notifications(self):
        """Clean up destroyed notifications"""
        self.notifications = [n for n in self.notifications 
                             if hasattr(n, 'notification') and 
                             n.notification.winfo_exists()]
    
    def clear_all(self):
        """Clear all notifications"""
        for notification in self.notifications[:]:
            try:
                notification.close_notification()
            except:
                pass
        self.notifications.clear()


class PremiumTooltip:
    """Premium tooltip with modern styling"""
    
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip = None
        self.timer = None
        
        # Bind events
        self.widget.bind('<Enter>', self.on_enter)
        self.widget.bind('<Leave>', self.on_leave)
        self.widget.bind('<Motion>', self.on_motion)
    
    def on_enter(self, event):
        """Handle mouse enter"""
        self.timer = self.widget.after(self.delay, self.show_tooltip)
    
    def on_leave(self, event):
        """Handle mouse leave"""
        if self.timer:
            self.widget.after_cancel(self.timer)
            self.timer = None
        self.hide_tooltip()
    
    def on_motion(self, event):
        """Handle mouse motion"""
        if self.tooltip:
            self.update_position(event)
    
    def show_tooltip(self):
        """Show the tooltip"""
        if self.tooltip:
            return
        
        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.overrideredirect(True)
        self.tooltip.attributes('-topmost', True)
        
        # Style tooltip
        self.tooltip.configure(bg='#1A1B3E', relief='solid', bd=1)
        
        # Create content
        content_frame = tk.Frame(self.tooltip, bg='#1A1B3E')
        content_frame.pack(padx=8, pady=6)
        
        label = tk.Label(content_frame,
                        text=self.text,
                        font=('Segoe UI', 9),
                        fg='#FFFFFF',
                        bg='#1A1B3E',
                        wraplength=200)
        label.pack()
        
        # Position tooltip
        self.position_tooltip()
    
    def position_tooltip(self):
        """Position tooltip relative to widget"""
        if not self.tooltip:
            return
        
        # Get widget position
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tooltip.geometry(f"+{x}+{y}")
    
    def update_position(self, event):
        """Update tooltip position with mouse"""
        if not self.tooltip:
            return
        
        x = event.x_root + 10
        y = event.y_root + 10
        
        self.tooltip.geometry(f"+{x}+{y}")
    
    def hide_tooltip(self):
        """Hide the tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class PremiumDialog:
    """Premium dialog boxes"""
    
    @staticmethod
    def show_confirm(parent, title, message, on_confirm=None, on_cancel=None):
        """Show confirmation dialog"""
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.transient(parent)
        dialog.grab_set()
        dialog.configure(bg='#1A1B3E')
        
        # Center dialog
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 100
        dialog.geometry(f"400x200+{x}+{y}")
        
        # Content
        content_frame = tk.Frame(dialog, bg='#1A1B3E')
        content_frame.pack(fill='both', expand=True, padx=32, pady=32)
        
        # Title
        title_label = tk.Label(content_frame,
                              text=title,
                              font=('Segoe UI', 14, 'bold'),
                              fg='#FFFFFF',
                              bg='#1A1B3E')
        title_label.pack(pady=(0, 16))
        
        # Message
        msg_label = tk.Label(content_frame,
                            text=message,
                            font=('Segoe UI', 10),
                            fg='#B4B4B8',
                            bg='#1A1B3E',
                            wraplength=300,
                            justify='center')
        msg_label.pack(pady=(0, 24))
        
        # Buttons
        button_frame = tk.Frame(content_frame, bg='#1A1B3E')
        button_frame.pack()
        
        def confirm():
            dialog.destroy()
            if on_confirm:
                on_confirm()
        
        def cancel():
            dialog.destroy()
            if on_cancel:
                on_cancel()
        
        # Cancel button
        cancel_btn = tk.Button(button_frame,
                              text="Cancel",
                              font=('Segoe UI', 10),
                              fg='#B4B4B8',
                              bg='transparent',
                              relief='flat',
                              bd=0,
                              cursor='hand2',
                              command=cancel)
        cancel_btn.pack(side='left', padx=(0, 12))
        
        # Confirm button
        confirm_btn = tk.Button(button_frame,
                               text="Confirm",
                               font=('Segoe UI', 10, 'bold'),
                               fg='#FFFFFF',
                               bg='#410899',
                               relief='flat',
                               bd=0,
                               cursor='hand2',
                               command=confirm)
        confirm_btn.pack(side='left')
        
        return dialog


# Quick utility functions
def show_success(parent, message):
    """Quick success notification"""
    if not hasattr(parent, '_notification_manager'):
        parent._notification_manager = NotificationManager(parent)
    return parent._notification_manager.show_success(message)

def show_error(parent, message):
    """Quick error notification"""
    if not hasattr(parent, '_notification_manager'):
        parent._notification_manager = NotificationManager(parent)
    return parent._notification_manager.show_error(message)

def show_info(parent, message):
    """Quick info notification"""
    if not hasattr(parent, '_notification_manager'):
        parent._notification_manager = NotificationManager(parent)
    return parent._notification_manager.show_info(message)

def show_premium(parent, message):
    """Quick premium notification"""
    if not hasattr(parent, '_notification_manager'):
        parent._notification_manager = NotificationManager(parent)
    return parent._notification_manager.show_premium(message)

# Export main classes
__all__ = [
    'PremiumNotification', 'NotificationManager', 'PremiumTooltip', 'PremiumDialog',
    'show_success', 'show_error', 'show_info', 'show_premium'
]