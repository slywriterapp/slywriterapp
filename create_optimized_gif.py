#!/usr/bin/env python3
"""
Create a more optimized animated GIF (60 frames instead of 240)
"""

import os
import math
from PIL import Image, ImageDraw, ImageFilter

def create_optimized_animation():
    """Create optimized animation - 60 frames @ 12fps = 5 second loop"""
    
    # Animation settings
    width, height = 1400, 900
    num_frames = 60  # Reduced from 240
    fps = 12  # Reduced from 24
    
    print(f"Creating optimized animation: {num_frames} frames @ {fps} FPS")
    
    # Create base gradient
    def create_base():
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Dark gradient
        top_color = (15, 15, 35)      # #0F0F23
        bottom_color = (26, 27, 62)   # #1A1B3E
        
        for y in range(height):
            ratio = y / height
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        return img
    
    # Create soft blob
    def create_blob():
        size = 250  # Slightly smaller
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        center = size // 2
        max_radius = center * 0.7
        
        steps = 15  # Fewer steps for performance
        for i in range(steps):
            radius = max_radius * (1 - i / steps)
            alpha = int(180 * (1 - i / steps) ** 1.5)  # Less intense
            
            x0 = center - radius
            y0 = center - radius
            x1 = center + radius
            y1 = center + radius
            
            color = (93, 31, 179, alpha)  # Purple with alpha
            draw.ellipse([x0, y0, x1, y1], fill=color)
        
        # Less blur for performance
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        return img
    
    print("Creating base gradient...")
    base = create_base()
    
    print("Creating blob...")
    blob = create_blob()
    
    frames = []
    
    print("Generating frames...")
    for frame in range(num_frames):
        # Time progress for seamless loop
        t = (frame / num_frames) * 2 * math.pi
        
        # Simple circular motion
        center_x = width // 2
        center_y = height // 2
        
        # Orbital motion
        radius_x = width * 0.2
        radius_y = height * 0.15
        
        blob_x = center_x + radius_x * math.cos(t)
        blob_y = center_y + radius_y * math.sin(t * 0.7)
        
        # Create frame
        frame_img = base.copy()
        
        # Paste blob
        blob_size = blob.size[0]
        paste_x = int(blob_x - blob_size // 2)
        paste_y = int(blob_y - blob_size // 2)
        
        # Ensure blob stays within bounds
        if (paste_x > -blob_size and paste_x < width and 
            paste_y > -blob_size and paste_y < height):
            frame_img.paste(blob, (paste_x, paste_y), blob)
        
        frames.append(frame_img)
        
        if frame % 10 == 0:
            print(f"Generated frame {frame}/{num_frames}")
    
    # Save as GIF with optimization
    print("Saving optimized GIF...")
    gif_path = os.path.join('assets', 'backgrounds', 'main_bg_optimized.gif')
    
    # Save with better optimization
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / fps),  # 83ms per frame for 12 FPS
        loop=0,
        optimize=True,
        colors=128  # Reduce color palette for smaller file
    )
    
    print(f"Optimized GIF created: {gif_path}")
    
    # Check file size
    size_mb = os.path.getsize(gif_path) / (1024 * 1024)
    print(f"File size: {size_mb:.1f} MB")
    
    return gif_path

if __name__ == "__main__":
    create_optimized_animation()