#!/usr/bin/env python3
"""
Simple test to check if Canvas background animation is visible
"""

import tkinter as tk
import os
from PIL import Image, ImageTk

class CanvasTest(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Canvas Visibility Test")
        self.geometry("800x600")
        
        # Create animated Canvas background
        self.load_gif_background()
        
        # Create some UI elements - no background specified to see if canvas shows through
        frame = tk.Frame(self)  # Default background
        frame.pack(fill='both', expand=True, padx=50, pady=50)
        
        label = tk.Label(frame, text="Test UI Element - Canvas should be visible behind this", 
                        font=('Arial', 16), 
                        fg='white', bg='#0F0F23',  # Semi-transparent dark
                        relief='raised', bd=2)
        label.pack(pady=20)
        
        button = tk.Button(frame, text="Test Button", 
                          font=('Arial', 12),
                          bg='#2D2F5A', fg='white')
        button.pack(pady=10)
    
    def load_gif_background(self):
        """Load the GIF background for testing"""
        gif_path = os.path.join('assets', 'backgrounds', 'main_bg.gif')
        
        if os.path.exists(gif_path):
            print(f"Loading GIF: {gif_path}")
            
            # Create Canvas background
            self.bg_canvas = tk.Canvas(self, highlightthickness=0, bd=0)
            self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Load GIF frames
            self.gif_frames = []
            gif_image = Image.open(gif_path)
            
            frame_num = 0
            while True:
                try:
                    gif_image.seek(frame_num)
                    frame = gif_image.copy()
                    frame = frame.resize((800, 600), Image.Resampling.LANCZOS)
                    photo_frame = ImageTk.PhotoImage(frame)
                    self.gif_frames.append(photo_frame)
                    frame_num += 1
                except EOFError:
                    break
            
            print(f"Loaded {len(self.gif_frames)} frames")
            
            # Create image on canvas
            if self.gif_frames:
                self.canvas_image = self.bg_canvas.create_image(0, 0, anchor='nw', 
                                                              image=self.gif_frames[0])
                
                # Start animation
                self.current_frame = 0
                self.animate_gif()
            
        else:
            print(f"GIF not found: {gif_path}")
            # Create a simple colored canvas for testing
            self.bg_canvas = tk.Canvas(self, bg='purple', highlightthickness=0, bd=0)
            self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
    
    def animate_gif(self):
        """Animate the GIF background"""
        try:
            if hasattr(self, 'gif_frames') and self.gif_frames:
                frame = self.gif_frames[self.current_frame]
                self.bg_canvas.itemconfig(self.canvas_image, image=frame)
                
                self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
                
                # Schedule next frame (12 FPS = ~83ms)
                self.after(83, self.animate_gif)
        except Exception as e:
            print(f"Animation error: {e}")

if __name__ == "__main__":
    app = CanvasTest()
    app.mainloop()