#!/usr/bin/env python3
"""
Test if the GIF can be loaded and animated properly
"""

import tkinter as tk
from PIL import Image, ImageTk
import os

def test_gif_animation():
    """Test GIF animation in a simple window"""
    
    root = tk.Tk()
    root.title("GIF Animation Test")
    root.geometry("800x600")
    root.configure(bg='black')
    
    gif_path = os.path.join('assets', 'backgrounds', 'main_bg.gif')
    
    if not os.path.exists(gif_path):
        print(f"GIF not found: {gif_path}")
        return
    
    try:
        # Load GIF frames
        gif_image = Image.open(gif_path)
        frames = []
        frame_delays = []
        
        frame_num = 0
        while True:
            try:
                gif_image.seek(frame_num)
                # Resize to fit window
                frame = gif_image.resize((800, 600), Image.Resampling.LANCZOS)
                photo_frame = ImageTk.PhotoImage(frame)
                frames.append(photo_frame)
                
                # Get delay
                delay = gif_image.info.get('duration', 42)
                frame_delays.append(delay)
                
                frame_num += 1
            except EOFError:
                break
        
        print(f"Loaded {len(frames)} frames from GIF")
        
        if not frames:
            print("No frames found in GIF!")
            return
        
        # Create label for animation
        label = tk.Label(root, bd=0, highlightthickness=0)
        label.pack(fill='both', expand=True)
        
        # Animation variables
        current_frame = 0
        
        def animate_frame():
            nonlocal current_frame
            
            # Get current frame
            frame = frames[current_frame]
            delay = frame_delays[current_frame]
            
            # Update label
            label.configure(image=frame)
            label.image = frame  # Keep reference
            
            # Next frame
            current_frame = (current_frame + 1) % len(frames)
            
            # Schedule next frame
            root.after(delay, animate_frame)
        
        # Start animation
        animate_frame()
        
        print("Animation started! Close window to stop.")
        root.mainloop()
        
    except Exception as e:
        print(f"Error testing GIF: {e}")

if __name__ == "__main__":
    test_gif_animation()