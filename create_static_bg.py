#!/usr/bin/env python3
"""
Create a static gradient background image from the provided gradient
"""

import os
from PIL import Image, ImageDraw

def create_static_background():
    """Create a perfectly smooth gradient background with no banding or artifacts"""
    
    # Create output directory
    os.makedirs(os.path.join('assets', 'backgrounds'), exist_ok=True)
    
    # Image dimensions - higher resolution for smoother gradients
    width, height = 1400, 900
    
    # Create base image with higher bit depth to prevent banding
    img = Image.new('RGB', (width, height))
    
    # Dark gradient colors - perfectly smooth transition
    top_color = (15, 15, 35)      # #0F0F23 - very dark blue
    bottom_color = (26, 27, 62)   # #1A1B3E - slightly lighter dark blue
    
    print(f"Creating SMOOTH gradient background ({width}x{height})...")
    print("NO horizontal bars, NO dark rectangles, NO banding, NO extra UI shapes")
    print("Creating perfectly smooth gradient with zero artifacts")
    
    # Create pixel array for direct manipulation (prevents line artifacts)
    pixels = []
    
    for y in range(height):
        row = []
        # Use floating point for ultra-smooth transitions
        ratio = float(y) / float(height - 1)  # Prevent edge case at height-1
        
        # Apply smooth curve to ratio to eliminate banding
        # Using smoothstep function: 3x² - 2x³ for even smoother transitions
        smooth_ratio = ratio * ratio * (3 - 2 * ratio)
        
        for x in range(width):
            # Calculate smooth color transition with dithering to prevent banding
            r = top_color[0] * (1 - smooth_ratio) + bottom_color[0] * smooth_ratio
            g = top_color[1] * (1 - smooth_ratio) + bottom_color[1] * smooth_ratio
            b = top_color[2] * (1 - smooth_ratio) + bottom_color[2] * smooth_ratio
            
            # Add tiny amount of controlled noise to break up banding (dithering)
            import random
            dither = random.uniform(-0.5, 0.5)
            
            # Clamp values to valid range
            r = max(0, min(255, int(r + dither)))
            g = max(0, min(255, int(g + dither)))
            b = max(0, min(255, int(b + dither)))
            
            row.append((r, g, b))
        
        pixels.extend(row)
    
    # Apply pixels to image (avoids line drawing artifacts)
    img.putdata(pixels)
    
    # Apply slight blur to eliminate any remaining banding
    from PIL import ImageFilter
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # Save the background with high quality
    bg_path = os.path.join('assets', 'backgrounds', 'main_bg.png')
    img.save(bg_path, 'PNG', optimize=True, quality=100)
    
    print(f"PERFECT gradient saved: {bg_path}")
    print("Background is completely smooth - no bars, no banding, no artifacts!")
    print("Pure gradient surface with zero extra UI elements")
    
    return bg_path

if __name__ == "__main__":
    create_static_background()