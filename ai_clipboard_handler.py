# ai_clipboard_handler.py - Clipboard handling for AI text generation

import time
import keyboard
import pyperclip
import threading
from typing import Optional


class ClipboardHandler:
    """Handles clipboard operations for AI text generation workflow"""
    
    def __init__(self):
        self.original_clipboard = None
        self.captured_text = None
        
    def capture_highlighted_text(self) -> Optional[str]:
        """
        Capture currently highlighted text via clipboard.
        Saves original clipboard content and restores it after capturing.
        
        Returns:
            str: The captured text, or None if no text was selected
        """
        try:
            # Save original clipboard content
            try:
                self.original_clipboard = pyperclip.paste()
            except:
                self.original_clipboard = ""
                
            # Clear clipboard to detect if copy worked
            pyperclip.copy("")
            
            # Simulate Ctrl+C to copy selected text
            keyboard.send('ctrl+c')
            
            # Wait a bit for clipboard to update
            time.sleep(0.1)
            
            # Get the copied text
            captured = pyperclip.paste()
            
            # Check if we actually got text (not empty and different from cleared state)
            if captured and captured.strip():
                self.captured_text = captured.strip()
                print(f"[CLIPBOARD] Captured text: '{self.captured_text[:100]}...'")
                return self.captured_text
            else:
                print("[CLIPBOARD] No text was selected or clipboard operation failed")
                self.restore_clipboard()
                return None
                
        except Exception as e:
            print(f"[CLIPBOARD] Error capturing text: {e}")
            self.restore_clipboard()
            return None
    
    def restore_clipboard(self):
        """Restore the original clipboard content"""
        try:
            if self.original_clipboard is not None:
                pyperclip.copy(self.original_clipboard)
                print("[CLIPBOARD] Original clipboard content restored")
        except Exception as e:
            print(f"[CLIPBOARD] Error restoring clipboard: {e}")
    
    def get_captured_text(self) -> Optional[str]:
        """Get the last captured text"""
        return self.captured_text
    
    def clear_captured_text(self):
        """Clear the captured text"""
        self.captured_text = None


# Global instance for use across the application
clipboard_handler = ClipboardHandler()


def capture_highlighted_text_async(callback):
    """
    Asynchronously capture highlighted text and call callback with result.
    
    Args:
        callback: Function to call with captured text (str or None)
    """
    def worker():
        text = clipboard_handler.capture_highlighted_text()
        callback(text)
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()